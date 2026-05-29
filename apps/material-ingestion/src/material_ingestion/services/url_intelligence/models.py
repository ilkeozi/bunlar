from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SegmentKind(str, Enum):
    LITERAL = "literal"
    LANGUAGE = "language"
    MARKET_OR_REGION = "market_or_region"
    NUMERIC_ID = "numeric_id"
    LONG_ID = "long_id"
    UUID = "uuid"
    DATE_LIKE = "date_like"
    SLUG = "slug"
    CODE_SLUG = "code_slug"
    DOCUMENT_FILE = "document_file"
    TECHNICAL_DOCUMENT_FILE = "technical_document_file"
    ASSET_FILE = "asset_file"


class URLRole(str, Enum):
    TECHNICAL_DOCUMENT = "technical_document"
    DOCUMENT = "document"
    DOCUMENT_LISTING = "document_listing"
    PRODUCT_LIKE_PAGE = "product_like_page"
    GENERIC_HTML = "generic_html"
    ASSET = "asset"
    NOISE = "noise"
    UNKNOWN = "unknown"


class NextAction(str, Enum):
    FETCH_DOCUMENT = "fetch_document"
    INSPECT_STATIC_HTML = "inspect_static_html"
    SAMPLE_STATIC_HTML = "sample_static_html"
    STOP_STATIC_GET = "stop_static_get"
    RENDER_SAMPLE = "render_sample"
    API_DISCOVERY = "api_discovery"
    DEFER = "defer"
    REJECT = "reject"


@dataclass(slots=True)
class ParsedSegment:
    raw: str
    kind: SegmentKind
    index: int


@dataclass(slots=True)
class ParsedURL:
    original_url: str
    canonical_url: str
    scheme: str
    host: str
    path: str
    query_params: dict[str, list[str]]
    fragment: str
    segments: list[ParsedSegment]


@dataclass(slots=True)
class TemplateCandidate:
    level: str
    template: str
    host_prefix: str
    full_template: str


@dataclass(slots=True)
class SourceContext:
    source_type: str = ""
    anchor_text: str = ""
    source_page_role: str = ""
    source_template_score: float = 0.0
    has_english_hreflang: bool = False
    came_from_sitemap: bool = False
    source_page_produced_document_candidates: bool = False
    source_is_navigation_heavy: bool = False


@dataclass(slots=True)
class PatternStats:
    sample_count: int = 0
    success_count: int = 0
    avg_total_ms: float = 0.0
    render_needed_count: int = 0
    candidate_document_count: int = 0
    technical_document_count: int = 0
    noise_count: int = 0
    useful_link_count: int = 0


@dataclass(slots=True)
class ScoreBreakdown:
    url_score: int
    source_score: int
    pattern_score: int
    final_score: int
    url_reasons: list[str] = field(default_factory=list)
    source_reasons: list[str] = field(default_factory=list)
    pattern_reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class URLDecision:
    canonical_url: str
    url_role: URLRole
    templates: list[TemplateCandidate]
    selected_template: str
    scores: ScoreBreakdown
    next_action: NextAction
    reason_codes: list[str]
    debug: dict
