from __future__ import annotations

import re

from .models import ParsedURL, PatternStats, SegmentKind, SourceContext

# ---------------------------------------------------------------------------
# Token sets used across URL scoring
# ---------------------------------------------------------------------------

_LEGAL_TOKENS: frozenset[str] = frozenset({
    "privacy", "legal", "cookie", "cookies", "terms", "disclaimer", "gdpr", "dsgvo",
})
_CAREER_TOKENS: frozenset[str] = frozenset({
    "career", "careers", "jobs", "job", "recruitment", "hiring",
})
_PRESS_TOKENS: frozenset[str] = frozenset({
    "press", "news", "media", "investor", "investors", "ir",
})
_AUTH_TOKENS: frozenset[str] = frozenset({
    "login", "signin", "sign-in", "account", "social", "share", "auth", "oauth",
})
_DOWNLOAD_TOKENS: frozenset[str] = frozenset({
    "download", "downloads", "download-center", "downloadcenter",
    "document-center", "documentcenter",
})
_SOFT_NOISE_TOKENS: frozenset[str] = frozenset({
    # Contact/utility pages rarely contain technical documents
    "contact", "contactus",
    # Confirmation/thank-you pages (form submissions etc.)
    "thank-you", "thankyou",
    # Trade fair / event pages
    "fairs", "fair",
    # Archive and history sections
    "archive", "archives",
    "history",
})
_RESOURCE_TOKENS: frozenset[str] = frozenset({
    "resources", "literature", "documents", "documentation", "library",
})
_PRODUCT_TOKENS: frozenset[str] = frozenset({
    "product", "products", "grade", "material", "materials",
    "polymer", "polymers", "chemical", "chemicals",
})
_ENGLISH_QUERY_KEYS: frozenset[str] = frozenset({"language", "lang", "locale"})
_ENGLISH_VALUES: frozenset[str] = frozenset({"en", "en-us", "en_us"})

_ANCHOR_TECH_KEYWORDS: tuple[str, ...] = (
    "tds", "sds", "msds", "pds",
    "datasheet", "data sheet",
    "download", "technical data",
)

_BROCHURE_NOISE_TOKENS: frozenset[str] = frozenset({
    "brochure", "flyer", "leaflet", "wallchart", "newsletter",
    "methodology", "catalogue", "catalog",
})
_LEGAL_DOC_FILENAME_TOKENS: frozenset[str] = frozenset({
    "conditions", "gtc", "agb", "cgv",
    "terms", "sale", "sales", "purchase", "purchasing",
    "procurement", "disclaimer", "privacy",
})


def _segment_word_parts(raw: str) -> frozenset[str]:
    """Return the segment itself plus each hyphen/underscore-delimited word."""
    lower = raw.lower()
    parts = re.split(r"[-_]", lower)
    return frozenset([lower] + parts)


def _doc_stem_words(raw: str) -> frozenset[str]:
    """Return lowercase words from a document filename stem (strips extension first)."""
    stem = raw.rsplit(".", 1)[0] if "." in raw else raw
    lower = stem.lower()
    parts = re.split(r"[-_\s]+", lower)
    return frozenset([lower] + [p for p in parts if p])


def _path_matches(segments: list, token_set: frozenset[str]) -> str | None:
    for seg in segments:
        if _segment_word_parts(seg.raw) & token_set:
            return seg.raw
    return None


# ---------------------------------------------------------------------------
# URL-level score
# ---------------------------------------------------------------------------


def score_url(parsed: ParsedURL) -> tuple[int, list[str]]:
    """Score the URL itself, ignoring source context and pattern history."""
    score = 0
    reasons: list[str] = []
    segs = parsed.segments

    has_tech_doc = any(s.kind == SegmentKind.TECHNICAL_DOCUMENT_FILE for s in segs)
    has_doc = any(s.kind == SegmentKind.DOCUMENT_FILE for s in segs)
    has_asset = any(s.kind == SegmentKind.ASSET_FILE for s in segs)

    if has_tech_doc:
        score += 100
        reasons.append("TECH_DOC_FILE_URL")
    elif has_doc:
        score += 40
        reasons.append("DOC_FILE_URL")
        # Filename-stem penalties: legal takes priority over brochure
        doc_segs = [s for s in segs if s.kind == SegmentKind.DOCUMENT_FILE]
        for seg in doc_segs:
            words = _doc_stem_words(seg.raw)
            if words & _LEGAL_DOC_FILENAME_TOKENS:
                score -= 80
                reasons.append("LEGAL_DOC_FILENAME")
                break
            if words & _BROCHURE_NOISE_TOKENS:
                score -= 30
                reasons.append("BROCHURE_FILENAME")
                break

    if _path_matches(segs, _DOWNLOAD_TOKENS):
        score += 60
        reasons.append("DOWNLOAD_PATH")

    if _path_matches(segs, _RESOURCE_TOKENS):
        score += 40
        reasons.append("RESOURCE_PATH")

    if _path_matches(segs, _PRODUCT_TOKENS):
        score += 25
        reasons.append("PRODUCT_PATH")

    # English language signal: path segment or query param
    has_en_seg = any(
        s.kind == SegmentKind.LANGUAGE and s.raw.lower() in _ENGLISH_VALUES
        for s in segs
    )
    has_en_query = any(
        k.lower() in _ENGLISH_QUERY_KEYS
        and any(v.lower() in _ENGLISH_VALUES for v in vals)
        for k, vals in parsed.query_params.items()
    )
    if has_en_seg or has_en_query:
        score += 10
        reasons.append("ENGLISH_SIGNAL")

    # Noise signals (applied even when a document was found, so callers can
    # inspect the reasons and override if needed)
    if _path_matches(segs, _LEGAL_TOKENS):
        score -= 100
        reasons.append("LEGAL_NOISE")

    if _path_matches(segs, _CAREER_TOKENS):
        score -= 80
        reasons.append("CAREER_NOISE")

    if _path_matches(segs, _PRESS_TOKENS):
        score -= 70
        reasons.append("PRESS_NOISE")

    if _path_matches(segs, _AUTH_TOKENS):
        score -= 60
        reasons.append("AUTH_NOISE")

    if has_asset:
        score -= 40
        reasons.append("ASSET_FILE_URL")

    # Soft demotion for page types that rarely contain technical documents.
    # Penalty is light enough that a DOWNLOAD_PATH or RESOURCE_PATH signal on
    # the same page still brings the URL to SAMPLE_STATIC_HTML, but a bare
    # contact/archive/fairs page falls below the SAMPLE threshold (< 25) and
    # lands in DEFER instead.
    if _path_matches(segs, _SOFT_NOISE_TOKENS):
        score -= 20
        reasons.append("SOFT_NOISE")

    # Cap url_score for non-technical document files.  Path bonuses like
    # PRODUCT_PATH, RESOURCE_PATH, and DOWNLOAD_PATH make sense for HTML pages
    # but must not inflate a generic PDF to TDS/SDS priority.
    # Legal-filename docs intentionally go negative; brochures cap at 30;
    # all other generic docs cap at 45.  Tech docs are uncapped.
    if has_doc and not has_tech_doc:
        if "LEGAL_DOC_FILENAME" in reasons:
            pass  # Already negative from -80 penalty; no upper cap needed
        elif "BROCHURE_FILENAME" in reasons:
            if score > 30:
                score = 30
                reasons.append("DOC_URL_SCORE_CAPPED")
        else:
            if score > 45:
                score = 45
                reasons.append("DOC_URL_SCORE_CAPPED")

    return score, reasons


# ---------------------------------------------------------------------------
# Source / context score
# ---------------------------------------------------------------------------


def score_source(ctx: SourceContext) -> tuple[int, list[str]]:
    """Score based on how the URL was discovered."""
    score = 0
    reasons: list[str] = []

    if ctx.came_from_sitemap or ctx.source_type == "sitemap":
        score += 15
        reasons.append("SRC_FROM_SITEMAP")

    if ctx.has_english_hreflang:
        score += 10
        reasons.append("SRC_EN_HREFLANG")

    if ctx.source_page_produced_document_candidates:
        score += 20
        reasons.append("SRC_PRODUCED_DOCS")

    if ctx.source_page_role == "document_listing":
        score += 30
        reasons.append("SRC_PAGE_IS_DOC_LISTING")

    if ctx.anchor_text:
        anchor_lower = ctx.anchor_text.lower()
        if any(kw in anchor_lower for kw in _ANCHOR_TECH_KEYWORDS):
            score += 20
            reasons.append("SRC_ANCHOR_TEXT_TECH")

    if ctx.source_is_navigation_heavy:
        score -= 30
        reasons.append("SRC_NAVIGATION_HEAVY")

    return score, reasons


# ---------------------------------------------------------------------------
# Pattern-yield score
# ---------------------------------------------------------------------------


def score_pattern(stats: PatternStats | None) -> tuple[int, list[str], dict]:
    """Score based on historical per-pattern crawl outcomes.

    Returns ``(score, reason_codes, pattern_details)``.

    ``reason_codes`` are stable categorical identifiers (no embedded numerics).
    ``pattern_details`` carries the raw numeric values for debug/reporting; it
    is empty when stats are None or sample_count == 0.

    Returns ``(0, [], {})`` when stats are None or sample_count is 0 — callers
    must not treat a zero pattern score as evidence of low yield.
    """
    if stats is None or stats.sample_count == 0:
        return 0, [], {}

    reasons: list[str] = []
    n = stats.sample_count

    if n < 10:
        modifier = 0.3
        confidence = "low"
        reasons.append("PATTERN_LOW_CONFIDENCE")
    elif n >= 50:
        modifier = 1.0
        confidence = "high"
        reasons.append("PATTERN_HIGH_CONFIDENCE")
    elif n >= 30:
        modifier = 0.7
        confidence = "medium"
        reasons.append("PATTERN_MEDIUM_CONFIDENCE")
    else:
        modifier = 0.5
        confidence = "medium"  # 10–29 samples: no confidence reason code, moderate weight

    def _smoothed(successes: int) -> float:
        return (successes + 1) / (n + 5)

    tech_yield = _smoothed(stats.technical_document_count)
    doc_yield = _smoothed(stats.candidate_document_count)
    link_yield = _smoothed(stats.useful_link_count)
    render_rate = _smoothed(stats.render_needed_count)
    noise_rate = _smoothed(stats.noise_count)

    raw_score: float = 0.0
    raw_score += 80.0 * tech_yield * modifier
    raw_score += 40.0 * doc_yield * modifier
    raw_score += 25.0 * link_yield * modifier
    raw_score -= 60.0 * render_rate * modifier
    raw_score -= 50.0 * noise_rate * modifier

    if stats.avg_total_ms > 0:
        cost_penalty = max(-20.0, -stats.avg_total_ms / 500.0) * modifier
        raw_score += cost_penalty
        if cost_penalty < -5:
            reasons.append("PATTERN_SLOW")

    if 80.0 * tech_yield * modifier > 5:
        reasons.append("PATTERN_TECH_DOC_YIELD")
    if 60.0 * render_rate * modifier > 20:
        reasons.append("PATTERN_RENDER_HEAVY")
    if 50.0 * noise_rate * modifier > 15:
        reasons.append("PATTERN_NOISY")

    details: dict = {
        "sample_count": n,
        "confidence": confidence,
        "avg_total_ms": stats.avg_total_ms,
        "render_needed_rate": round(render_rate, 3),
        "noise_rate": round(noise_rate, 3),
        "technical_document_yield": round(tech_yield, 3),
        "candidate_document_yield": round(doc_yield, 3),
        "technical_document_count": stats.technical_document_count,
        "candidate_document_count": stats.candidate_document_count,
    }

    return int(raw_score), reasons, details
