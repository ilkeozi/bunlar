from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlparse, urlunparse

from .models import ParsedSegment, ParsedURL
from .segment_predicates import classify_segment


def parse_url(url: str) -> ParsedURL:
    """Parse and canonicalize a URL.

    The canonical_url strips the fragment so it can be used as a fetch target.
    The original fragment is preserved in ParsedURL.fragment (decoded).
    """
    raw = url.strip()
    parsed = urlparse(raw)

    scheme = parsed.scheme.lower()
    host = parsed.netloc.lower()
    path = parsed.path or "/"
    query = parsed.query

    # Canonical fetch URL: lowercase scheme + host, no fragment
    canonical = urlunparse((scheme, host, path, "", query, ""))

    query_params: dict[str, list[str]] = parse_qs(query, keep_blank_values=True)

    # Split and decode path segments
    raw_parts = [s for s in path.split("/") if s]
    decoded_parts = [unquote(s) for s in raw_parts]

    segments = [
        ParsedSegment(
            raw=decoded,
            kind=classify_segment(decoded, i, len(decoded_parts)),
            index=i,
        )
        for i, decoded in enumerate(decoded_parts)
    ]

    return ParsedURL(
        original_url=raw,
        canonical_url=canonical,
        scheme=scheme,
        host=host,
        path=path,
        query_params=query_params,
        fragment=unquote(parsed.fragment),
        segments=segments,
    )
