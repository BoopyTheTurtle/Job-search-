from jobbot.models import canonical_url, dedup_key


def test_canonical_url_strips_tracking_and_fragment() -> None:
    url = "https://Example.com/jobs/123/?utm_source=x&ref=y&page=2#apply"
    assert canonical_url(url) == "https://example.com/jobs/123?page=2"


def test_dedup_key_is_stable_across_tracking_params() -> None:
    a = dedup_key("Backend Dev", "Acme", "https://acme.com/jobs/1?utm_source=remotive")
    b = dedup_key("Backend Dev", "Acme", "https://acme.com/jobs/1/")
    assert a == b


def test_dedup_key_without_url_uses_company_and_title() -> None:
    a = dedup_key("Backend  Dev!", "ACME Inc", "")
    b = dedup_key("backend dev", "acme inc", "")
    assert a == b
