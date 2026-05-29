from __future__ import annotations

from .models import ParsedURL, SegmentKind, TemplateCandidate

# Kinds replaced at the "specific" level: clearly dynamic identifiers and file names
_SPECIFIC_REPLACE: frozenset[SegmentKind] = frozenset({
    SegmentKind.NUMERIC_ID,
    SegmentKind.LONG_ID,
    SegmentKind.UUID,
    SegmentKind.DATE_LIKE,
    SegmentKind.TECHNICAL_DOCUMENT_FILE,
    SegmentKind.DOCUMENT_FILE,
    SegmentKind.ASSET_FILE,
})

# Additional kinds replaced at the "medium" level
_MEDIUM_EXTRA: frozenset[SegmentKind] = frozenset({
    SegmentKind.LANGUAGE,
    SegmentKind.SLUG,
    SegmentKind.CODE_SLUG,
})

_MEDIUM_REPLACE: frozenset[SegmentKind] = _SPECIFIC_REPLACE | _MEDIUM_EXTRA


def _build_template(segments: list, replace: frozenset[SegmentKind]) -> str:
    if not segments:
        return "/"
    parts = []
    for seg in segments:
        if seg.kind in replace:
            parts.append("{" + seg.kind.value + "}")
        else:
            parts.append(seg.raw)
    return "/" + "/".join(parts)


def infer_templates(parsed: ParsedURL) -> list[TemplateCandidate]:
    """Return deduplicated template candidates ordered from most-exact to most-abstract."""
    segments = parsed.segments
    host_prefix = f"{parsed.scheme}://{parsed.host}"

    exact_path = parsed.path or "/"
    specific_path = _build_template(segments, _SPECIFIC_REPLACE)
    medium_path = _build_template(segments, _MEDIUM_REPLACE)

    seen: set[str] = set()
    candidates: list[TemplateCandidate] = []

    for level, path in (("exact", exact_path), ("specific", specific_path), ("medium", medium_path)):
        if path not in seen:
            seen.add(path)
            candidates.append(
                TemplateCandidate(
                    level=level,
                    template=path,
                    host_prefix=host_prefix,
                    full_template=host_prefix + path,
                )
            )

    return candidates
