"""France Travail Offres d'emploi v2 (France). Docs: https://francetravail.io/data/api/offres-emploi

Token: POST https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire
(client credentials, scope `api_offresdemploiv2 o2dsoffre`).
Search: GET https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search
Keyed: FRANCE_TRAVAIL_CLIENT_ID / FRANCE_TRAVAIL_CLIENT_SECRET (the pipeline skips the
source when either is unset). There is no remote flag, so we search the IT domain
(`grandDomaine=M18`) for `motsCles=télétravail`, newest first (`sort=1`), with
`publieeDepuis` set to the smallest allowed window (1, 3, 7, 14, 31 days) covering `since`.

Pages are `range=a-b`, 150 per page; the API answers 206 while more results remain, 200
on the last page and 204 (empty body) when nothing matches. Rate limit: 3 requests/s.
Postings are French; the language filter accepts fr.

params: `keywords` (a query or a list of queries, each run separately; default
"télétravail"), `domain` (default "M18"; null searches every domain), `page_size` (max
150), `max_pages` (per query, default 3), `page_delay` (seconds, default 0.4).
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

import httpx

from jobbot.http import SourceError, get_text
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import MAX_PAGES, from_iso, is_older, text

TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
API_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
SCOPE = "api_offresdemploiv2 o2dsoffre"
MAX_PAGE_SIZE = 150
WINDOWS = (1, 3, 7, 14, 31)
_CONTRACTS = {"CDD": "contract", "MIS": "contract", "SAI": "contract", "LIB": "freelance"}
_HOURS = {"temps plein": "full_time", "temps partiel": "part_time"}


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def published_window(since: datetime | None, now: datetime | None = None) -> int:
    """Smallest `publieeDepuis` value (days) that reaches back to `since`; 7 when unknown."""
    if since is None:
        return 7
    days = ((now or datetime.now(tz=UTC)) - since).total_seconds() / 86400
    return next((w for w in WINDOWS if w >= days), WINDOWS[-1])


def employment_raw(item: dict[str, Any]) -> str | None:
    contract = _CONTRACTS.get(str(item.get("typeContrat") or "").upper())
    if contract:
        return contract
    hours = (text(item.get("dureeTravailLibelleConverti")) or "").lower()
    return _HOURS.get(hours)


class FranceTravail:
    name = "francetravail"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        keywords = params.get("keywords", "télétravail")
        items = keywords if isinstance(keywords, list) else [keywords]
        self._keywords = [str(k) for k in items if str(k).strip()]
        self._domain = params.get("domain", "M18")
        size = int(params.get("page_size", MAX_PAGE_SIZE))
        self._page_size = max(1, min(size, MAX_PAGE_SIZE))
        self._max_pages = max(1, min(int(params.get("max_pages", 3)), MAX_PAGES))
        self._page_delay = float(params.get("page_delay", 0.4))

    def _token(self, client_id: str, secret: str) -> str:
        try:
            response = self._client.post(
                TOKEN_URL,
                params={"realm": "/partenaire"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": secret,
                    "scope": SCOPE,
                },
            )
            response.raise_for_status()
            token = response.json().get("access_token")
        except (httpx.HTTPError, ValueError) as exc:
            # Credentials travel in the form body, never in the URL, so the message is safe.
            raise SourceError(f"France Travail token request failed: {exc}") from exc
        if not token:
            raise SourceError("France Travail token response had no access_token")
        return str(token)

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        client_id = os.environ.get("FRANCE_TRAVAIL_CLIENT_ID", "").strip()
        secret = os.environ.get("FRANCE_TRAVAIL_CLIENT_SECRET", "").strip()
        if not client_id or not secret:
            raise SourceError(
                "FRANCE_TRAVAIL_CLIENT_ID and FRANCE_TRAVAIL_CLIENT_SECRET must be set"
            )
        headers = {"Authorization": f"Bearer {self._token(client_id, secret)}"}
        size = min(self._page_size, limit) if limit else self._page_size
        base: dict[str, Any] = {"sort": 1, "publieeDepuis": published_window(since)}
        if self._domain:
            base["grandDomaine"] = self._domain
        emitted = 0
        seen: set[str] = set()
        requests = 0
        for keywords in self._keywords:
            query = {**base, "motsCles": keywords}
            for page in range(self._max_pages):
                if requests and self._page_delay > 0:
                    time.sleep(self._page_delay)
                requests += 1
                start = page * size
                body = get_text(
                    self._client,
                    API_URL,
                    params={**query, "range": f"{start}-{start + size - 1}"},
                    headers=headers,
                )
                payload = json.loads(body) if body.strip() else {}
                items = payload.get("resultats") or [] if isinstance(payload, dict) else []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    job = self._to_raw(item)
                    # Overlapping queries return the same offer more than once.
                    if job.source_id in seen or is_older(job.posted_at, since):
                        continue
                    seen.add(job.source_id)
                    yield job
                    emitted += 1
                    if limit and emitted >= limit:
                        return
                if len(items) < size:
                    break

    @staticmethod
    def _to_raw(item: dict[str, Any]) -> RawJob:
        offer_id = str(item["id"])
        origin = _obj(item.get("origineOffre"))
        return RawJob(
            source="francetravail",
            source_id=offer_id,
            url=text(origin.get("urlOrigine"))
            or f"https://candidat.francetravail.fr/offres/recherche/detail/{offer_id}",
            title=str(item["intitule"]).strip(),
            company=text(_obj(item.get("entreprise")).get("nom")),
            location_raw=text(_obj(item.get("lieuTravail")).get("libelle")),
            description_text=text(item.get("description")),
            posted_at=from_iso(item.get("dateCreation")),
            salary_raw=text(_obj(item.get("salaire")).get("libelle")),
            employment_type_raw=employment_raw(item),
            remote_hint=None,
            tags=[t for t in (text(item.get("romeLibelle")),) if t],
            extra={
                "typeContrat": item.get("typeContrat"),
                "experienceExige": item.get("experienceExige"),
                "experienceLibelle": item.get("experienceLibelle"),
            },
        )


@register("francetravail")
def _factory(client: httpx.Client, params: dict[str, Any]) -> FranceTravail:
    return FranceTravail(client, params)
