# AccessVision — Slice Plan

> Run `/cm` with any slice block below. Slices are ordered by dependency.
> After Slice 1 merges: `cp .env.example .env` and fill in keys. All worktrees resolve from main.

## Environment

| Key | Service | First needed |
|-----|---------|-------------|
| `GOOGLE_API_KEY` | Gemini Flash, Gemini Pro, Nano Banana | Slice 2 Tier 2 |
| `FIRECRAWL_API_KEY` | Firecrawl `/map` and `/scrape` | Slice 2 Tier 2 |

## Slice Index

| # | Name | Spec sections | Depends on | Est. Level |
|---|------|--------------|------------|------------|
| 1 | Scaffold + shared types | Scoring System, Tech Stack, PageCapture (Phase 2) | — | L1 |
| 2 | Discovery + ranking | Phase 1 (all) | 1 | L2 |
| 3 | Capture pipeline | Phase 2 (all) | 1 | L2-L3 |
| 4 | Vision analysis | Phase 3 Step A | 1, 3 | L2 |
| 5 | Annotation + solution PRs | Phase 3 Steps B + C | 1, 4 | L2 |
| 6 | Report assembly + CLI | Final Output Assembly, Timing Estimates | 1-5 | L2 |

## Dependency Graph

```
Slice 1 (scaffold) ← runs on main
├──→ Slice 2 (discovery)   ──┐
└──→ Slice 3 (capture)     ──┼──→ Slice 4 (vision) ──→ Slice 5 (annotate + fix) ──→ Slice 6 (report + CLI)
                              │
                              └── 2 & 3 can run in parallel
```

---

### Slice 1 — Scaffold + Shared Types

**Read:** Scoring System, Tech Stack, `PageCapture` dataclass in Phase 2

**Deliver:**
- `pyproject.toml` — all deps: playwright, firecrawl-py, google-genai, pillow, pytest, python-dotenv
- `src/accessvision/__init__.py`
- `src/accessvision/models.py` — `PageCapture`, `Violation`, `PageAudit` dataclasses, `SeverityLevel` enum (Critical=4, Serious=3, Moderate=2, Minor=1), `composite_score()` function
- `src/accessvision/config.py` — worktree-aware env loading: resolves main worktree via `git worktree list --porcelain`, loads `{main}/.env` with python-dotenv, exposes `GOOGLE_API_KEY`, `FIRECRAWL_API_KEY`, model name constants, default N=5, raises on missing keys
- `src/accessvision/__main__.py` — async entrypoint stub with argparse (url, --pages N, --output)
- `.gitignore` — `.env`, `__pycache__`, `.pytest_cache`, `tests/fixtures/*.png`
- Empty stubs with docstrings: `discovery.py`, `ranking.py`, `capture/`, `analysis/`, `output/`, `report/`
- `tests/conftest.py`, `tests/test_models.py` — scoring math with hand-written dicts

**Fixtures produced:** none — hand-written mocks
**Fixtures required:** none

**Acceptance:**
- `python -m accessvision --help` runs and shows usage
- `from accessvision.models import PageCapture, Violation, SeverityLevel` imports cleanly
- `pytest tests/test_models.py` passes — scoring: Critical×10=40, Minor×6=6, sort order correct
- `from accessvision.config import GOOGLE_API_KEY` works when `.env` exists in main worktree

---

### Slice 2 — Site Discovery + LLM Ranking

**Read:** Phase 1: Discover + Rank (Steps 1.1 and 1.2 — full section)

**Deliver:**
- `src/accessvision/discovery.py` — async: root URL → Firecrawl `/map` → list of `{url, title}` dicts
- `src/accessvision/ranking.py` — async: URL+title list + N → Gemini Flash → top N with `priority_score` (1-10), `reason`
- `src/accessvision/prompts/ranking.py` — prompt with exact priority criteria from FLOW.md Step 1.2 (login/checkout=high, blog=low)
- `tests/fixtures/sample_firecrawl_map.json` — hand-written, 10 fake `{url, title}` entries
- `tests/test_discovery.py` — Tier 1: mock Firecrawl, assert URL parsing
- `tests/test_ranking.py` — Tier 1: mock Gemini response, assert N items with valid scores 1-10

**Fixtures produced:** `tests/fixtures/sample_firecrawl_map.json` (hand-written)
**Fixtures required:** none

**Acceptance:**
- `pytest tests/test_discovery.py tests/test_ranking.py` passes with mocks
- Ranking prompt contains all FLOW.md Step 1.2 criteria (user-critical flows, blog deprioritization)
- Gemini response parsing handles malformed JSON without crashing

---

### Slice 3 — Parallel Capture Pipeline

**Read:** Phase 2: Capture (Steps 2.1 and 2.2 — full section, including all JS snippets)

**Deliver:**
- `src/accessvision/capture/scraper.py` — async: URL → Firecrawl `/scrape` → markdown + metadata
- `src/accessvision/capture/browser.py` — async: URL → Playwright page → screenshot (1280×936 PNG), axe-core scan (WCAG 2.2 AA), element map extraction, a11y tree snapshot. JS scripts must match FLOW.md Step 2.2b/c exactly
- `src/accessvision/capture/pipeline.py` — async: ranked pages → `asyncio.gather` N-way parallel (scraper + browser per page) → list of `PageCapture`
- `scripts/save_fixtures.py` — captures one real URL (default `https://example.com`), saves all outputs to `tests/fixtures/`
- `tests/test_capture.py` — Tier 1: mock Playwright + Firecrawl, assert PageCapture assembly, verify element map fields (tag, bbox, visible, focusable)

**Fixtures produced (after Tier 2):** `sample_screenshot.png`, `sample_axe_results.json`, `sample_element_map.json`, `sample_a11y_tree.json`, `sample_firecrawl_scrape.json`, `sample_page_capture.json`
**Fixtures required:** none

**Acceptance:**
- `pytest tests/test_capture.py` passes with mocks
- Pipeline uses `asyncio.gather`, not sequential loops
- axe-core injection JS matches FLOW.md Step 2.2b (runOnly: wcag2a, wcag2aa, wcag22aa)
- **Post-merge:** run `python scripts/save_fixtures.py`, verify outputs, commit to `tests/fixtures/`

---

### Slice 4 — Vision WCAG Analysis

**Read:** Phase 3 Step A — Vision Analysis + Bounding Box Detection (full section, all 8 P0 criteria)

**Deliver:**
- `src/accessvision/analysis/vision.py` — async: `PageCapture` → Gemini 3.1 Pro (screenshot + element map + axe + markdown) → list of `Violation`
- `src/accessvision/prompts/vision_audit.py` — criterion-by-criterion prompt evaluating all 8 P0: 1.1.1 Alt Text, 1.4.1 Color-Only, 1.4.3 Contrast Over Images, 2.4.4 Link Purpose, 2.4.7 Focus Visible, 4.1.2 Label Match, 1.4.5 Images of Text, 3.3.1 Error ID
- `src/accessvision/analysis/coordinates.py` — Gemini `box_2d` `[y_min, x_min, y_max, x_max]` 1000×1000 grid → pixel coords
- `src/accessvision/analysis/merge.py` — merges vision + axe violations, dedup by element+criterion, keep higher severity
- `tests/test_coordinates.py` — Tier 1: known conversions on 1280×936
- `tests/test_merge.py` — Tier 1: overlapping violations, assert dedup logic
- `tests/test_vision.py` — Tier 1: mock Gemini response, assert Violation parsing

**Fixtures produced (after Tier 2):** `tests/fixtures/sample_violations.json`
**Fixtures required:** Slice 3 fixtures (`sample_screenshot.png`, `sample_element_map.json`, `sample_axe_results.json`, `sample_firecrawl_scrape.json`)

**Acceptance:**
- `pytest tests/test_coordinates.py tests/test_merge.py tests/test_vision.py` passes
- Vision prompt explicitly names and evaluates all 8 P0 criteria as separate sections
- Coordinate math: `pixel_x = (x_norm / 1000) * width` verified with test values
- **Post-merge:** run vision on Slice 3 fixtures, save `sample_violations.json`

---

### Slice 5 — Annotation + Solution PR Generation

**Read:** Phase 3 Step B (Annotated Screenshot) and Step C (Solution PR Generation)

**Deliver:**
- `src/accessvision/output/annotator.py` — Pillow-based: screenshot PNG + violations → colored bounding boxes (Critical=red #FF0000, Serious=orange #FF8C00, Moderate=yellow #FFD700, Minor=blue #4169E1), numbered badges, 3px border → annotated PNG bytes
- `src/accessvision/output/solution_pr.py` — async: violations + page context → Gemini Flash → markdown fix doc with before/after code per violation, severity-ordered
- `src/accessvision/prompts/solution_pr.py` — prompt following FLOW.md Step C format
- `tests/test_annotator.py` — Tier 1: load Slice 3 screenshot, 2 fake violations, assert output PNG differs at bbox locations
- `tests/test_solution_pr.py` — Tier 1: mock Gemini, assert markdown has severity-ordered sections with code blocks

**Fixtures produced:** `tests/fixtures/sample_annotated.png`, `tests/fixtures/sample_fix.md`
**Fixtures required:** Slice 3 (`sample_screenshot.png`), Slice 4 (`sample_violations.json`)

**Acceptance:**
- `pytest tests/test_annotator.py tests/test_solution_pr.py` passes
- Annotator output has colored rectangles at bbox locations (pixel diff test)
- Solution PR markdown has one section per violation with before/after code blocks
- Both functions are async-compatible for `asyncio.gather`

---

### Slice 6 — Report Assembly + CLI

**Read:** Final Output Assembly, Timing Estimates, API Calls Per Audit

**Deliver:**
- `src/accessvision/report/builder.py` — list of `PageAudit` → sort by `priority_score × severity_weight` → HTML report
- `src/accessvision/report/template.html` — inline-styled HTML: executive summary (pages, violations, severity breakdown, axe vs vision comparison), per-page sections (annotated screenshot base64, violation table, fixes)
- `src/accessvision/__main__.py` — complete CLI wiring: `python -m accessvision <url> --pages N --output report.html`, orchestrates full pipeline, stderr progress with phase timing
- `tests/test_report.py` — Tier 1: 3 hand-built PageAudit objects, assert HTML sort order + summary stats
- `tests/test_e2e.py` — Tier 2: `python -m accessvision https://example.com --pages 1 --output test_report.html`

**Fixtures produced:** none (consumes all upstream)
**Fixtures required:** all upstream slices

**Acceptance:**
- `pytest tests/test_report.py` passes — sort order correct, summary numbers match
- `python -m accessvision --help` shows all options (url, --pages, --output)
- Report pages sorted descending by composite score
- Executive summary includes axe vs vision violation count comparison
