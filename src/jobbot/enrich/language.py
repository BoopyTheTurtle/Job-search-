"""Language detection with lingua, restricted to a candidate set. SPEC §8.1."""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache

from lingua import IsoCode639_1, Language, LanguageDetector, LanguageDetectorBuilder

# Profile languages plus the neighbours most likely to appear in European IT postings.
# Restricting the set makes short Latvian/Spanish texts far less likely to be misread.
DEFAULT_CANDIDATES: tuple[str, ...] = (
    "en",
    "fr",
    "lv",
    "es",
    "de",
    "nl",
    "pl",
    "it",
    "pt",
    "ru",
    "lt",
    "et",
)
SHORT_TEXT_CHARS = 200
MIN_CONFIDENCE = 0.8
MIN_CONFIDENCE_SHORT = 0.6


@lru_cache(maxsize=4)
def _detector(candidates: tuple[str, ...]) -> LanguageDetector:
    languages = [Language.from_iso_code_639_1(getattr(IsoCode639_1, c.upper())) for c in candidates]
    return LanguageDetectorBuilder.from_languages(*languages).build()


def detect_language(
    text: str,
    candidates: Iterable[str] = DEFAULT_CANDIDATES,
    *,
    sample_chars: int = 2000,
) -> tuple[str | None, float]:
    """Return (iso-639-1 code or None, confidence). Short texts use a lower bar."""
    sample = " ".join(text.split())[:sample_chars]
    if not sample:
        return None, 0.0
    values = _detector(tuple(candidates)).compute_language_confidence_values(sample)
    if not values:
        return None, 0.0
    best = values[0]
    confidence = float(best.value)
    threshold = MIN_CONFIDENCE if len(sample) >= SHORT_TEXT_CHARS else MIN_CONFIDENCE_SHORT
    code = best.language.iso_code_639_1.name.lower()
    return (code if confidence >= threshold else None), confidence
