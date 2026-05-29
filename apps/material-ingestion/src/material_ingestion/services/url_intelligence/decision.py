from __future__ import annotations

import re

from .models import (
    NextAction,
    ParsedSegment,
    ParsedURL,
    PatternStats,
    ScoreBreakdown,
    SegmentKind,
    SourceContext,
    TemplateCandidate,
    URLDecision,
    URLRole,
)
from .scoring import score_pattern, score_source, score_url
from .template_inference import infer_templates
from .uri_parser import parse_url

# ---------------------------------------------------------------------------
# Noise token sets (mirrored from scoring to avoid a cross-import cycle)
# ---------------------------------------------------------------------------

_LEGAL_TOKENS: frozenset[str] = frozenset({
    "privacy", "legal", "cookie", "cookies", "terms", "disclaimer", "gdpr", "dsgvo",
})
_CAREER_TOKENS: frozenset[str] = frozenset({
    "career", "careers", "jobs", "job", "recruitment",
})
_PRESS_TOKENS: frozenset[str] = frozenset({
    "press", "news", "media", "investor", "investors",
})
_AUTH_TOKENS: frozenset[str] = frozenset({
    "login", "signin", "sign-in", "account", "social", "share", "auth",
})
_LISTING_TOKENS: frozenset[str] = frozenset({
    "download", "downloads", "download-center", "downloadcenter",
    "document-center", "documentcenter", "documents", "documentation",
    "resources", "literature", "library",
})
_PRODUCT_TOKENS: frozenset[str] = frozenset({
    "product", "products", "grade", "material", "materials",
    "polymer", "polymers", "chemical", "chemicals",
})
_LEGAL_DOC_FILENAME_TOKENS: frozenset[str] = frozenset({
    "conditions", "gtc", "agb", "cgv",
    "terms", "sale", "sales", "purchase", "purchasing",
    "procurement", "disclaimer", "privacy",
})


def _seg_words(raw: str) -> frozenset[str]:
    lower = raw.lower()
    return frozenset([lower] + re.split(r"[-_]", lower))


def _has_token(segs: list[ParsedSegment], tokens: frozenset[str]) -> bool:
    return any(bool(_seg_words(s.raw) & tokens) for s in segs)


def _has_legal_doc_filename(segs: list[ParsedSegment]) -> bool:
    """Return True if any DOCUMENT_FILE segment's filename stem contains legal-doc tokens."""
    for seg in segs:
        if seg.kind == SegmentKind.DOCUMENT_FILE:
            stem = seg.raw.rsplit(".", 1)[0] if "." in seg.raw else seg.raw
            lower = stem.lower()
            words = frozenset([lower] + re.split(r"[-_\s]+", lower))
            if words & _LEGAL_DOC_FILENAME_TOKENS:
                return True
    return False


# ---------------------------------------------------------------------------
# Role classification
# ---------------------------------------------------------------------------


def _classify_role(segs: list[ParsedSegment], url_score: int) -> URLRole:
    # Technical document: strongest signal, always wins
    if any(s.kind == SegmentKind.TECHNICAL_DOCUMENT_FILE for s in segs):
        return URLRole.TECHNICAL_DOCUMENT

    # Asset: never useful to crawl as content
    if any(s.kind == SegmentKind.ASSET_FILE for s in segs):
        return URLRole.ASSET

    # Strong noise signals (legal/career/press/auth override document role)
    noise_reasons = sum([
        _has_token(segs, _LEGAL_TOKENS),
        _has_token(segs, _CAREER_TOKENS),
        _has_token(segs, _PRESS_TOKENS),
        _has_token(segs, _AUTH_TOKENS),
    ])

    if any(s.kind == SegmentKind.DOCUMENT_FILE for s in segs):
        # Legal/career path or legal-doc filename overrides document role
        if noise_reasons >= 1 or _has_legal_doc_filename(segs):
            return URLRole.NOISE
        return URLRole.DOCUMENT

    if noise_reasons >= 1:
        return URLRole.NOISE

    if _has_token(segs, _LISTING_TOKENS):
        return URLRole.DOCUMENT_LISTING

    if _has_token(segs, _PRODUCT_TOKENS):
        return URLRole.PRODUCT_LIKE_PAGE

    if url_score > 10:
        return URLRole.GENERIC_HTML

    return URLRole.UNKNOWN


# ---------------------------------------------------------------------------
# Action determination
# ---------------------------------------------------------------------------


def _determine_action(
    url_role: URLRole,
    segs: list[ParsedSegment],
    final_score: int,
    stats: PatternStats | None,
) -> NextAction:
    # Technical documents always get fetched — pattern stats cannot veto this
    if any(s.kind == SegmentKind.TECHNICAL_DOCUMENT_FILE for s in segs):
        return NextAction.FETCH_DOCUMENT

    if url_role == URLRole.DOCUMENT:
        return NextAction.FETCH_DOCUMENT if final_score >= 50 else NextAction.DEFER

    if url_role in (URLRole.ASSET, URLRole.NOISE):
        return NextAction.REJECT

    if url_role == URLRole.DOCUMENT_LISTING:
        return NextAction.INSPECT_STATIC_HTML

    # Pattern-stat driven decisions for generic pages
    if stats and stats.sample_count >= 50:
        render_rate = stats.render_needed_count / stats.sample_count
        if (
            render_rate >= 0.95
            and stats.candidate_document_count == 0
            and stats.technical_document_count == 0
        ):
            return NextAction.STOP_STATIC_GET
        if render_rate > 0.7:
            return NextAction.RENDER_SAMPLE

    if final_score >= 25:
        return NextAction.SAMPLE_STATIC_HTML

    if final_score < -20:
        return NextAction.REJECT

    return NextAction.DEFER


# ---------------------------------------------------------------------------
# Template selection
# ---------------------------------------------------------------------------


def _select_template(templates: list[TemplateCandidate], url_role: URLRole) -> str:
    if not templates:
        return ""
    prefer = "specific" if url_role in (URLRole.TECHNICAL_DOCUMENT, URLRole.DOCUMENT) else "medium"
    for t in templates:
        if t.level == prefer:
            return t.template
    for t in templates:
        if t.level != "exact":
            return t.template
    return templates[0].template


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def decide(
    url: str,
    context: SourceContext | None = None,
    stats: PatternStats | None = None,
) -> URLDecision:
    """Analyse a URL and return a structured crawl decision.

    Parameters
    ----------
    url:
        The URL to analyse.
    context:
        Optional source-context metadata describing how the URL was discovered.
    stats:
        Optional per-pattern historical crawl stats.  Only applied when
        sample_count is large enough to be meaningful.
    """
    ctx = context if context is not None else SourceContext()
    parsed: ParsedURL = parse_url(url)

    url_score, url_reasons = score_url(parsed)
    source_score, source_reasons = score_source(ctx)
    pattern_score, pattern_reasons, pattern_details = score_pattern(stats)
    final_score = url_score + source_score + pattern_score

    url_role = _classify_role(parsed.segments, url_score)
    next_action = _determine_action(url_role, parsed.segments, final_score, stats)
    templates = infer_templates(parsed)
    selected = _select_template(templates, url_role)

    all_reasons = url_reasons + source_reasons + pattern_reasons

    debug: dict = {
        "original_url": parsed.original_url,
        "fragment": parsed.fragment,
        "query_params": dict(parsed.query_params),
        "segments": [
            {"raw": s.raw, "kind": s.kind.value, "index": s.index}
            for s in parsed.segments
        ],
    }
    if pattern_details:
        debug["pattern_details"] = pattern_details

    return URLDecision(
        canonical_url=parsed.canonical_url,
        url_role=url_role,
        templates=templates,
        selected_template=selected,
        scores=ScoreBreakdown(
            url_score=url_score,
            source_score=source_score,
            pattern_score=pattern_score,
            final_score=final_score,
            url_reasons=url_reasons,
            source_reasons=source_reasons,
            pattern_reasons=pattern_reasons,
        ),
        next_action=next_action,
        reason_codes=all_reasons,
        debug=debug,
    )
