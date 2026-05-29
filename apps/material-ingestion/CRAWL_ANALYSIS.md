# Crawler Pipeline Analysis — Run 28 (2026-05-26 → ongoing)

> **Scope:** Run `core_run_20260526_152345`, started 2026-05-26 15:23 UTC, no `ended_at` (still running as of 2026-05-28).
> All counts from live DB. Hypotheses are marked **[H]**. Code references are line-precise.

---

## 0. Headline Finding

`https://plastics-rubber.basf.com/global/en/performance_polymers/downloads` is a publicly accessible download page returning **959 TDS in English alone** — Elastollan®, Ultradur®, Ultraform®, Ultramid®, ecovio®, ecoflex®, WALLTITE®, Nypel®, Petra®, ULTRAMID® ADVANCED across Global / EMEA / North America / Asia Pacific. This page was never crawled. The root domain got one frontier item, was `eval_defer`ed, and the entire domain went dark. See §4 for the exact code path that caused it.

This is the clearest illustration of the resource inversion in §7.1: the pipeline spent **80+ hours GETting 120,000 JS shells** on `products.basf.com` that yielded zero extractable text, while a single download index with 959 real TDS was silently skipped.

---

## 1. Pipeline Stages and Code Paths

```
Sitemap crawl → Builder → [frontier: queued]
                                ↓
                          HEAD fetch (web_crawl_frontier_fetch_service.py)
                                ↓ head_metadata_success
                          Evaluate (web_crawl_frontier_evaluate_service.py)
                                ↓ eval_promote
                          GET fetch (web_crawl_frontier_get_service.py)
                                ↓ get_body_success
                          Candidate scoring (inside get service)
```

Discovered links from GET → `raw_web_uri_identity` only.
**There is no code path that feeds `raw_web_extracted_link` back into the frontier.** See §2.

---

## 2. Discover / Build Phase

### Code
[web_crawl_frontier_builder_service.py](src/material_ingestion/services/web_crawl_frontier_builder_service.py)

The builder reads exclusively from `raw_web_sitemap_entry` (line 72):
```python
query = session.query(RawWebSitemapEntry).filter(RawWebSitemapEntry.id > last_seen_id)
```

It applies `raw_web_frontier_score_rule` rules to each sitemap URL (lines 144–157). Score threshold is `MATERIAL_INGESTION_FRONTIER_SCORE_THRESHOLD` (default 5, line 43). URLs below threshold are either **dropped silently** or moved to `deferred/low_score_pre_fetch` depending on `MATERIAL_INGESTION_FRONTIER_LOW_SCORE_MODE` (default `drop`, line 44).

**Crucially: links extracted during GET crawling are written to `raw_web_uri_identity` and `raw_web_extracted_link` — but there is no service that reads those tables and adds them to the frontier.** Discovered links can only re-enter the pipeline if they appear in a sitemap.

### Frontier score rules (applied at build time)

| pattern | match_type | weight |
|---|---|---|
| `\.(pdf\|doc\|docx\|xls\|xlsx\|ppt\|pptx)(\?\|$)` | regex | +15 |
| `(datasheet\|technical-data-sheet\|tds\|sds\|msds\|specification)` | regex | +10 |
| `(download\|document\|product-detail\|product)` | regex | +5 |
| `(legal\|privacy\|cookie\|career\|jobs\|press\|news\|investor\|media)` | regex | -8 |

Score threshold: **5**. A URL with no matching rules scores 0 and is **dropped** (not deferred — it never enters the frontier).

### Actual numbers

| metric | count |
|---|---|
| Total URI identities discovered | 89,586 |
| URIs that ever entered the frontier | 6,136 |
| **Discovered but never crawled** | **83,450 (93.1%)** |

### Why 83k URLs are stuck

All 83k were found via link extraction during GET, not via sitemap. Without a sitemap entry they cannot enter the frontier. Top pools:

| domain | discovered, never crawled |
|---|---|
| www.basf.com | 68,447 |
| care360.basf.com | 4,251 |
| agriculture.basf.com | 3,169 |
| www.lgchemon.com | 2,179 |
| www.lgchem.com | 418 |
| automotive-transportation.basf.com | 192 |
| fuel-and-lubricants.basf.com | 83 |

**[H]** These domains are in the allowlist (`*.basf.com`, `*.lgchemon.com`) but have no sitemap coverage in this run. Adding extracted links as a secondary frontier input — with the same scoring filter — would unlock this pool without requiring sitemap presence.

### Builder hreflang filter (line 112–118)

The builder only admits a sitemap URL if it has an `hreflang="en"` alternate pointing at the same canonical URI. URLs with no alternate metadata are admitted unconditionally (line 109). This explains partial coverage on multilingual BASF sites: pages with German/French alternates but no English alternate are silently dropped.

---

## 3. HEAD Fetch Phase

### Code
[web_crawl_frontier_fetch_service.py](src/material_ingestion/services/web_crawl_frontier_fetch_service.py) — `_head_scan_url()` starting at line 104.

Issues a plain HTTP HEAD with `User-Agent: material-ingestion-bot/1.0` (line 132). On `HTTPError` captures status code and `Retry-After` (lines 167–171). On generic exception captures only the exception string — no status code (line 172–173). HEAD failures land in `deferred/head_request_failed` with **no retry scheduling**.

### Actual numbers

| reason_code | count |
|---|---|
| `head_metadata_success` | 5,884 |
| `head_request_failed` | **7,241** |

**HEAD failure rate: 55.2%.** All 7,241 permanently deferred.

### By domain

| domain | HEAD total | success | failed | fail % |
|---|---|---|---|---|
| products.basf.com | 11,651 | 4,963 | 6,688 | **57.4%** |
| furniture-wood.basf.com | 478 | 122 | 356 | **74.5%** |
| nutrition.basf.com | 119 | 30 | 89 | **74.8%** |
| www.basf.com | 233 | 148 | 85 | 36.5% |
| chemicals.basf.com | 206 | 185 | 21 | 10.2% |
| www.lgchemon.com | 294 | **294** | 0 | **0%** |

**[H]** BASF actively blocks HTTP HEAD from bot user agents at 57–75% rates across subdomains. LG Chem ON has 0% failure. Testing GET-instead-of-HEAD on BASF domains may be more efficient than issuing HEAD first.

**Problem:** The fetch service does not distinguish `4xx` (permanent) from timeout/network (retryable) HEAD failures. All go to `deferred/head_request_failed` permanently. A transient block or timeout means the URL is lost for the run.

---

## 4. Evaluate Phase

### Code
[web_crawl_frontier_evaluate_service.py](src/material_ingestion/services/web_crawl_frontier_evaluate_service.py)

**Promote threshold** (line 86–90):
```python
promote_threshold = get_runtime_int_config(
    key="core_evaluation_promote_threshold",
    default=int(os.getenv("MATERIAL_INGESTION_EVALUATION_PROMOTE_THRESHOLD", "6")),
)
```
Default: **6**.

**Haystack construction** (lines 169–177) — what rules are matched against:
```python
haystack = " ".join([
    str(canonical_uri or ""),
    str(content_type or ""),
    str(content_language or ""),
    str(content_disposition or ""),
    str(link or ""),
])
```
Rules match against the full URL **plus** HTTP response headers from the HEAD request.

**Decision logic** (lines 188–202):
```python
if "skip" in matched_actions:
    → eval_skip
elif "promote" in matched_actions and score >= promote_threshold:
    → eval_promote
else:
    → eval_defer  # ← default for everything that doesn't positively match
```

### Evaluation rules (current)

| action | match_type | pattern | weight | priority |
|---|---|---|---|---|
| skip | regex | `(legal\|privacy\|cookie)` | -8 | 200 |
| skip | regex | `(career\|jobs)` | -6 | 210 |
| defer | regex | `(press\|news\|investor\|media)` | -4 | 220 |
| promote | contains | `/product` | +6 | 20 |
| promote | contains | `/document/` | +8 | 30 |
| promote | contains | `/datasheet` | +10 | 40 |

### Critical bug: `/product` pattern matches every URL on `products.basf.com`

The `contains` match is a substring check on the full URL string. `https://products.basf.com/global/en/ci/30036817` → the scheme `https://` produces `//products` which **contains** `/product` as a substring. Every URL on `products.basf.com` scores +6 and hits the promote threshold of 6 — including CI code pages with no product content at all.

This is confirmed by the data: **products.basf.com has 0 eval_defer rows** despite having 140,000+ frontier items.

The same accidental match applies to `www.lgchemon.com/s/em/products/...` where the path actually contains `/products/`.

### Domains being wrongly deferred

The default branch is `eval_defer` — anything that does not positively match a `promote` rule is deferred. High-value entry points with no promote signal:

| URL | why deferred |
|---|---|
| `nutrition.basf.com/global/en/human-nutrition/downloads` | `/downloads` not in ruleset |
| `myindustryworld.basf.com/emea/en/downloads` | `/downloads` not in ruleset |
| `myindustryworld.basf.com/emea/en/discover/protected-area/Acronal--BC-6410-X--Document-Preview` | no matching rule |
| `plastics-rubber.basf.com/` (root) | no matching rule → entire domain dark |
| `chemicals.basf.com/Intermediates/download_center` | no matching rule |

### Actual promotion vs deferral by domain

| domain | promoted | deferred | get completed |
|---|---|---|---|
| products.basf.com | 8,310 | **0** | 120,580 |
| www.basf.com | 114 | **925** | 3,016 |
| myindustryworld.basf.com | 42 | **129** | 294 |
| nutrition.basf.com | 2 | **616** | 20 |
| aroma-ingredients.basf.com | 0 | **46** | 0 |
| packaging-print.basf.com | 0 | **45** | 0 |
| plastics-rubber.basf.com | 0 | **1** | 0 |

`nutrition.basf.com/global/en/human-nutrition/downloads` appears **multiple times** in the frontier all with `eval_defer` — the same URL is being re-inserted by the build stage. Missing deduplication guard at insert time.

---

## 5. GET Fetch Phase

### Code
[web_crawl_frontier_get_service.py](src/material_ingestion/services/web_crawl_frontier_get_service.py)

`_get_url()` (line 241) issues a full GET with `Accept-Encoding: gzip, deflate`. Decompresses gzip/deflate responses before decoding (added recently). Parses HTML with BeautifulSoup/lxml via `_parse_page()` (line 161). Stores text to `raw_web_page_text`, metadata to `raw_web_page_metadata`, JSON-LD to `raw_web_structured_data_record`.

`render_needed` flag (lines 710–713): set when `text_length < 300` OR `text_ratio < 0.07`.

### Actual numbers

| reason_code | count |
|---|---|
| `get_body_success` | 132,710 |
| `get_timeout` | 3,422 |
| `get_request_failed` | 762 |
| `get_network_error` | 230 |

### Time cost by domain

| domain | GET requests | avg (s) | total (min) |
|---|---|---|---|
| **products.basf.com** | **124,458** | **2.32** | **4,817** |
| chemicals.basf.com | 4,293 | 3.06 | 219 |
| www.basf.com | 3,227 | 3.31 | 178 |
| furniture-wood.basf.com | 2,572 | 3.25 | 139 |

### Yield: text extraction quality

| domain | pages extracted | render_needed | avg text ratio |
|---|---|---|---|
| products.basf.com | 66,516 | **66,503 (99.98%)** | 0.0026 |
| chemicals.basf.com | 2,492 | 2,492 (100%) | 0.0030 |
| furniture-wood.basf.com | 1,680 | 1,680 (100%) | 0.0036 |
| www.basf.com | 1,596 | 1,596 (100%) | 0.0101 |
| nutrition.basf.com | 14 | 14 (100%) | 0.0019 |

**100% of all BASF HTML pages are flagged `render_needed`.** All are JS-rendered SPAs. Static GET yields only nav/footer boilerplate. The entire 4,817 minutes on `products.basf.com` produced zero extractable product content.

### LG Chem ON gap

`www.lgchemon.com` had 487 successful GET fetches — all between 2026-05-26 19:29 and 19:33 UTC, **before `raw_web_page_text` was created** (first row: 2026-05-27 21:56 UTC). Zero text extracted. Pages are Salesforce Experience Cloud (`/s/em/products/...`) — also JS-rendered, so re-crawl without a renderer would still yield nothing.

### Candidate scoring inside GET (lines 677–860)

Two signals applied per successfully fetched URL:

**1. PDF/document URL signal** (lines 668–702): If `content_type` contains `application/pdf` or URL contains `.pdf` → upsert `raw_web_candidate_document` with `decision_reason_code="phase_b_get_pdf_signal"`, score 0.

**2. Extracted link authority signal** (lines 814–860): After batch completes, for each target URL that was linked from ≥1 source: query `raw_web_extracted_link` for `distinct_source_count`, compute authority score via `_authority_score_for_distinct_sources()` (lines 82–93), add `doc_hint_score=10`. Total becomes `authority_score + 10`. Promote to `promoted_authority` if `distinct_source_count >= 5`.

`_authority_score_for_distinct_sources()` caps at 40 for ≥100 sources:
```python
if count >= 100: return 40
if count >= 50:  return 30
if count >= 20:  return 20
if count >= 5:   return 10
return 0
```

---

## 6. Candidate Scoring Analysis

### Current state

| decision_state | unique targets | avg score | max sources |
|---|---|---|---|
| `promoted_authority` | 22 | 48.1 | 1,915 |
| `new` | 234 | 10.0 | 4 |

### What the authority signal actually measures

The authority score counts how many distinct crawled pages link to a URL. On a manufacturer's site, the highest link counts go to:
- **Navigation hubs** linked in every page header/footer (downloads centres, login pages)
- **Legal PDFs** linked in every product page footer

`myindustryworld.basf.com/emea/en/downloads` — 1,915 inbound links — is a gated login page, not a document.
Chemetall AGB legal terms PDFs — 24 inbound links — score 30 (beating actual TDS).
Actual TDS in `/tds-sheets/Palatinol_DOTP_TDS_202305.pdf` — 1 inbound link — score 10.

**The signal measures navigational prominence, not document relevance.**

### Confirmed TDS found: 20

All have `_TDS_`, `TI_`, or `/tds-sheets/` in the URL. All score 10 (single source, doc_hint_score only). None promoted. Examples:

| URL | score | sources |
|---|---|---|
| `.../tds-sheets/Palatinol_DOTP_TDS_202305.pdf` | 10 | 1 |
| `.../tds-sheets/Hexamoll_DINCH_TDS_202305.pdf` | 10 | 1 |
| `.../tds-sheets/Palamoll_652_TDS_202305.pdf` | 10 | 1 |
| (17 more in `/tds-sheets/`) | 10 | 1 |

### 182 total PDF candidates — category breakdown

| category | count | notes |
|---|---|---|
| Confirmed TDS (`_TDS_`, `TI_`, `/tds-sheets/`) | 20 | all `decision_state=new` |
| Technical brochures / product one-pagers | ~10 | not TDS |
| Legal / GTC / purchase conditions | ~25 | high authority scores, noise |
| Sustainability / CDP / ESG reports | ~20 | noise |
| IT/security docs (RSA tokens, VPN, PKI) | ~15 | noise from www.basf.com |
| Corporate / investor materials | ~40 | noise |
| Refinery catalyst journal papers | ~8 | publications, not TDS |
| External / unrelated | ~5 | FAO report, RecyClass |

---

## 7. Cross-Cutting Problems

### 7.1 Resource allocation is inverted

| domain | GET time (min) | render_needed % | useful content |
|---|---|---|---|
| products.basf.com | **4,817** | 99.98% | **zero** |
| plastics-rubber.basf.com | 0 | — | **959 TDS missed** |
| nutrition.basf.com | 1 | 100% | near zero |

80+ hours of GET time was spent on a domain whose every page is a JS shell. The domain with 959 confirmed TDS was never crawled.

### 7.2 Builder only reads sitemaps — extracted links are a dead end

[web_crawl_frontier_builder_service.py:72](src/material_ingestion/services/web_crawl_frontier_builder_service.py#L72) queries only `RawWebSitemapEntry`. `raw_web_extracted_link` is never read by the builder. A URL discovered as a link during GET can only re-enter the frontier via a sitemap — and `plastics-rubber.basf.com/global/en/performance_polymers/downloads` is not in any sitemap we've seen.

### 7.3 Eval `/product` pattern bug

The `contains` pattern `/product` (weight 6) matches every URL on `products.basf.com` because `https://products.basf.com/...` contains the substring `/product` in `//products`. This is unintentional — it causes 100% promotion on a domain where 100% of pages need JS rendering to be useful.

Fix: change to a regex with path boundary anchors, e.g. `(/|^)products?(/|$)` or scope it more narrowly.

[web_crawl_frontier_evaluate_service.py:39–49](src/material_ingestion/services/web_crawl_frontier_evaluate_service.py#L39)

### 7.4 `/downloads` is not a promote signal

Every BASF subdomain has a `/downloads` or `/download_center` page that is the primary TDS entry point. None of these match any current promote rule. They all get `eval_defer`ed. The missing rule is simple:

```sql
INSERT INTO raw_web_evaluation_rule (action, match_type, pattern, weight, priority, note, enabled)
VALUES ('promote', 'contains', '/download', 10, 50, 'Download index pages', true);
```

### 7.5 HEAD failures are permanently abandoned

[web_crawl_frontier_fetch_service.py:172–173](src/material_ingestion/services/web_crawl_frontier_fetch_service.py#L172) — generic exception path captures no status code and does not schedule a retry. 7,241 URLs are stranded in `deferred/head_request_failed` for the run regardless of failure reason. No separation of permanent (4xx) vs retryable (timeout, network).

### 7.6 Frontier build inserts duplicates

`nutrition.basf.com/global/en/human-nutrition/downloads` has multiple `eval_defer` rows in `raw_web_frontier_item`. The builder checks for existing items (line 121–132) but only within `crawl_run_id` — if the same URL is processed from different sitemap sources in the same run it can be inserted twice.

### 7.7 Candidate scoring rewards navigational prominence not document quality

`_authority_score_for_distinct_sources()` [web_crawl_frontier_get_service.py:82](src/material_ingestion/services/web_crawl_frontier_get_service.py#L82) is calibrated for a web authority model (more links = more important). On a manufacturer site this promotes download hubs and legal boilerplate — exactly the wrong signal for finding TDS. A URL path signal (`/tds-sheets/`, `_TDS_`, `_SDS_`) should be sufficient for promotion regardless of link count.

### 7.8 URL canonicalization misses session tokens

BASF DAM URLs appear with and without `?vid=...` query parameters, generating duplicate `raw_web_uri_identity` entries and therefore duplicate `raw_web_candidate_document` rows for the same physical PDF. Example: `Palatinol_DOTP_TDS_202305.pdf` and `Palatinol_DOTP_TDS_202305.pdf?vid=4z0AAlAw...` are treated as separate documents.

---

## 8. Hypotheses for Further Investigation

| # | hypothesis | evidence | how to test |
|---|---|---|---|
| H1 | BASF blocks HTTP HEAD from bots but allows GET — HEAD failure is method-specific | lgchemon 0% HEAD fail vs BASF 57–75%; HEAD and GET use same `User-Agent` | Retry a sample of `head_request_failed` URLs with GET; compare success rates |
| H2 | `//products` substring match in evaluate is the reason products.basf.com has 0 deferrals | URL `https://products.basf.com/...` contains `/product` at position of `//` | Check `raw_web_crawl_decision.detail_json` for a products.basf.com item — should show `matched_rule_ids` including the `/product` rule |
| H3 | `nutrition.basf.com/human-nutrition/downloads` contains direct `<a href="...pdf">` links that would yield dozens of TDS if GETted | Page deferred, never fetched | HEAD the URL manually; fetch it with Playwright |
| H4 | LG Chem ON product pages contain property tables in JS-rendered DOM invisible to static GET | 487 GET successes, zero candidates, zero text | Playwright fetch of `lgchemon.com/s/em/products/pbt/lupox-pbt-compound` |
| H5 | BASF DAM PDFs without `?vid=` token are publicly accessible | TDS files in `/tds-sheets/` appear without vid param | Fetch the 20 confirmed TDS URLs directly |
| H6 | Build stage duplicate inserts come from multiple sitemap sources covering the same URL | `nutrition.basf.com/downloads` appears N times in frontier | Check `raw_web_sitemap_entry` for duplicate entries for that URI |

---

## 9. What Needs to Change (General, Not BASF-Specific)

These are structural issues that will reproduce on any manufacturer crawl.

### Build / Discover
- Add a second frontier input path from `raw_web_extracted_link` (with the same score filter). Currently discovered links are a dead end unless they appear in a sitemap.
- Strip query parameters that are session/tracking tokens before canonicalisation (`?vid=`, `?sid=`, `?token=`, etc.) to avoid duplicate URI identities.

### Evaluate
- Fix the `/product` pattern — use a regex with word/path boundaries, not a raw substring. The current rule accidentally promotes every URL on `products.basf.com`.
- Add `/download` and `/downloads` as promote rules (weight ≥ 10). These are the highest-value entry points on any manufacturer site.
- Add domain-level policy: mark a domain as `html_only_defer` so only `.pdf` URLs are promoted; all HTML deferred until a renderer exists.

### HEAD
- Classify HEAD failures by type: 4xx → permanent (don't retry), timeout/network → retryable (schedule retry).
- Consider skipping HEAD for domains with historically high failure rates and going directly to GET.

### Candidate Scoring
- Add URL-path signal to promotion: `_TDS_`, `/tds-sheets/`, `TI_[0-9]`, `_SDS_`, `_MSDS_`, `_PDS_` in filename → immediate `promoted_authority` regardless of inbound link count.
- Separate authority (inbound link count) from navigability — a URL linked 1,915 times from product page footers is a navigation hub, not a candidate document. Apply a content-type filter: only promote URLs whose path ends in `.pdf` or similar.

### Rendering
- All `*.basf.com` HTML pages are JS SPAs. 100% render_needed rate confirms static GET is not useful for BASF HTML. A renderer-first strategy (skip static GET for known SPA domains, go straight to Playwright) would recover 80+ hours per run.

---

*Generated 2026-05-28 from run `core_run_20260526_152345`.*
