from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_TRACKING_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "mc_cid",
    "mc_eid",
}


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return url.strip()

    query_pairs = []
    for k, v in parse_qsl(parsed.query, keep_blank_values=True):
        low = k.strip().lower()
        if low in _TRACKING_KEYS:
            continue
        query_pairs.append((k.strip(), v.strip()))
    query_pairs.sort(key=lambda p: (p[0].lower(), p[1]))

    clean = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        fragment="",
        query=urlencode(query_pairs, doseq=True),
    )
    return urlunparse(clean)
