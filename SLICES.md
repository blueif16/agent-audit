# AccessVision — Slice Plan

> **How to use:** Each slice is one `/cm` unit. Run `/cm implement Slice N from FLOW.md` — CloudMate reads the referenced sections, builds a DAG, and executes. Slices are ordered by dependency. Slices without dependency links can run in parallel worktrees.

---

## Environment Setup

**Handled at the git layer, not application layer. No per-project code needed.**

A global git `post-checkout` hook copies `.env` from main worktree into new worktrees automatically. Fires when `claude -w` creates any worktree — correct timing, zero per-project config.

**One-time global setup (do this once, works for all projects forever):**
```bash
mkdir -p ~/.config/git/hooks
cat << 'EOF' > ~/.config/git/hooks/post-checkout
#!/bin/bash
# Copy .env from main worktree into new linked worktrees.
[ "$3" = "1" ] || exit 0
MAIN=$(git worktree list | head -1 | awk '{print $1}')
[ "$MAIN" = "$(pwd)" ] && exit 0
[ -f "$MAIN/.env" ] || exit 0
[ -f ".env" ] && exit 0
cp "$MAIN/.env" .env
EOF
chmod +x ~/.config/git/hooks/post-checkout

# Tell git to use this hooks directory:
git config --global core.hooksPath ~/.config/git/hooks
```

**Required keys for this project:**
| Key | Used By | First needed |
|-----|---------|-------|
| `GOOGLE_API_KEY` | Gemini Flash, Gemini Pro, Nano Banana | Slice 2 Tier 2, Slice 3+ |
| `FIRECRAWL_API_KEY` | Firecrawl `/map` and `/scrape` | Slice 2 Tier 2, Slice 3+ |

**Per-project setup after Slice 1 merges (runs on main, not a worktree):**
```bash
cd ~/Desktop/agent-audit
cp .env.example .env
# fill in your two keys — every future worktree gets them via the global hook
```

Slices 1-2 Tier 1 tests use mocked responses and don't need real keys. Slice 3 is the first slice that hits real APIs.

`config.py` is a plain `load_dotenv()` + `os.environ.get()` — no git tricks, no fallback chains. The `.env` is already in the working directory by the time any code runs.

> **Note:** If you already have project-level `.git/hooks/` that you need, the global `core.hooksPath` overrides them. In that case, have your global hook check for and source a local hook: `[ -x .git/hooks/post-checkout ] && .git/hooks/post-checkout "$@"`. For most solo projects this isn't an issue.

---

## Test Fixtures Strategy

Fixtures flow forward through the slice chain. Each slice commits its output as the next slice's test input. No slice depends on fixtures that haven't been produced yet.

```
Slice 1 → hand-written dicts (scoring math, type validation)
Slice 2 → hand-written sample_firecrawl_map.json (10 fake {url, title} entries)
Slice 3 → PRODUCES real fixtures by capturing a live page (screenshot, axe, element map, a11y tree)
            Commits to tests/fixtures/ as part of acceptance criteria
Slice 4 → CONSUMES Slice 3 fixtures, PRODUCES sample_violations.json
            Commits violation output as fixture for Slice 5
Slice 5 → CONSUMES Slice 3 screenshot + Slice 4 violations
            PRODUCES sample_annotated.png + sample_fix.md
Slice 6 → CONSUMES all upstream fixtures for report assembly tests
```

**Two test tiers per slice:**
- **Tier 1 (no API calls, runs in CI and during `/cm`):** Mocked responses, fixture data, pure logic validation.
- **Tier 2 (hits real APIs, run manually after merge):** Real Gemini/Firecrawl calls. Slice 3 Tier 2 is the most important — it generates the golden fixture set.

---

## Slice Index

| Slice | Name | FLOW.md Sections | Depends On | Est. Level |
|-------|------|-----------------|------------|------------|
| 1 | Project scaffold + types | Scoring System, Tech Stack, PageCapture dataclass (Phase 2) | — | L1 |
| 2 | Site discovery + ranking | Phase 1 (all) | Slice 1 | L2 |
| 3 | Capture pipeline + fixture generation | Phase 2 (all) | Slice 1 | L2-L3 |
| 4 | Vision analysis | Phase 3 Step A | Slices 1, 3 | L2 |
| 5 | Annotation + solution PRs | Phase 3 Steps B + C | Slices 1, 4 | L2 |
| 6 | Report assembly + CLI | Final Output Assembly, Timing Estimates | Slices 1-5 | L2 |

### Dependency Graph

```
Slice 1 (scaffold + types)
├──→ Slice 2 (discover + rank)  ──┐
└──→ Slice 3 (capture + fixtures) ┼──→ Slice 4 (vision) ──→ Slice 5 (annotate + fix) ──→ Slice 6 (report)
                                   │
                                   └── Slices 2 & 3 can run in parallel
```

---

## Slice Details

### Slice 1 — Project Scaffold + Shared Types

**Read:** Scoring System, Tech Stack, `PageCapture` dataclass definition in Phase 2

**Deliver:**
- `pyproject.toml` with all deps: playwright, firecrawl-py, google-genai, pillow, pytest, python-dotenv
- `src/accessvision/` package with `__init__.py`
- `src/accessvision/models.py` — all shared types:
  - `PageCapture` dataclass (url, title, priority_score, reason, screenshot bytes, markdown, axe results, element map, a11y tree)
  - `Violation` dataclass (id, element_index, box_2d, criterion, criterion_name, severity, description, remediation_hint)
  - `PageAudit` dataclass (page capture + violations + annotated screenshot + fix markdown)
  - `SeverityLevel` enum: Critical=4, Serious=3, Moderate=2, Minor=1
  - `composite_score()` function: `priority_score × severity_weight`
- `src/accessvision/config.py` — plain `load_dotenv()` + `os.environ.get()`. Model name constants. Default N=5. Raises clear error if keys are missing
- `src/accessvision/__main__.py` — async entrypoint stub with argparse (root URL, --pages N, --output path)
- `.env.example` — lists required keys with no values
- `.gitignore` — `.env`, `__pycache__`, `*.pyc`, `.pytest_cache`
- Empty module stubs with docstrings: `discovery.py`, `ranking.py`, `capture/`, `analysis/`, `output/`, `report/`
- `tests/conftest.py` — pytest config (will be extended by later slices as fixtures arrive)
- `tests/test_models.py` — scoring math tests with hand-written dicts

**Acceptance:**
- `python -m accessvision --help` runs and shows usage
- All types importable: `from accessvision.models import PageCapture, Violation, SeverityLevel`
- `pytest tests/test_models.py` passes:
  - Critical on priority 10 → composite score 40
  - Minor on priority 6 → composite score 6
  - Sort order: [40, 30, 24, 14, 6] given mixed inputs
- `config.py` loads `.env` from working directory and reads keys via `os.environ`

---

### Slice 2 — Site Discovery + LLM Ranking (Phase 1)

**Read:** Phase 1: Discover + Rank (Steps 1.1 and 1.2)

**Fixtures created by this slice:**
- `tests/fixtures/sample_firecrawl_map.json` — hand-written, 10 fake `{url, title}` entries covering high/medium/low priority page types

**Deliver:**
- `src/accessvision/discovery.py` — async function: takes root URL, calls Firecrawl `/map`, returns list of `{url, title}` dicts
- `src/accessvision/ranking.py` — async function: takes URL+title list and N, calls Gemini Flash, returns top N pages with `priority_score` (1-10) and `reason`
- `src/accessvision/prompts/ranking.py` — ranking prompt following exact criteria from FLOW.md Step 1.2 (high/medium/low priority categories)
- `tests/test_discovery.py` — Tier 1: mock Firecrawl response with `sample_firecrawl_map.json`, assert URL list parsing
- `tests/test_ranking.py` — Tier 1: mock Gemini response as realistic JSON, assert output has N items with valid priority_scores 1-10 and non-empty reasons

**Acceptance:**
- Tier 1: `pytest tests/test_discovery.py tests/test_ranking.py` passes with mocked responses
- Ranking prompt includes all criteria from FLOW.md Step 1.2 (login/checkout = high, blog = low, etc.)
- Output: list of dicts with `url` (str), `title` (str), `priority_score` (int 1-10), `reason` (str)
- Gemini response parsing handles malformed JSON gracefully (retry or error, no crash)

---

### Slice 3 — Parallel Capture Pipeline + Fixture Generation (Phase 2)

**Read:** Phase 2: Capture (Steps 2.1 and 2.2, full PageCapture dataclass)

**Fixtures created by this slice (committed after Tier 2 run):**
```
tests/fixtures/
├── sample_screenshot.png          # real Playwright screenshot of https://example.com
├── sample_axe_results.json        # real axe-core output from same page
├── sample_element_map.json        # real DOM element map with bboxes
├── sample_a11y_tree.json          # real browser a11y tree
├── sample_firecrawl_scrape.json   # real /scrape markdown + metadata
└── sample_page_capture.json       # assembled PageCapture metadata (screenshot ref'd by filename)
```

**Deliver:**
- `src/accessvision/capture/__init__.py`
- `src/accessvision/capture/scraper.py` — async: takes URL, calls Firecrawl `/scrape`, returns markdown + metadata
- `src/accessvision/capture/browser.py` — async: takes URL, launches Playwright page, runs sequential capture:
  - a) Navigate + screenshot (1280×936 viewport, PNG bytes)
  - b) axe-core injection + scan (WCAG 2.2 AA tags, JS from FLOW.md Step 2.2b)
  - c) Element map extraction (JS from FLOW.md Step 2.2c — all interactive/semantic elements with bboxes)
  - d) Accessibility tree snapshot (`page.accessibility.snapshot()`)
- `src/accessvision/capture/pipeline.py` — async: takes list of ranked pages, runs scraper + browser concurrently per page (`asyncio.gather`), assembles `PageCapture` objects
- `scripts/save_fixtures.py` — runs pipeline on a single URL (default: `https://example.com`), saves each output field to `tests/fixtures/`. Run once after Tier 2 validation, commit results
- `tests/conftest.py` — updated: `page_capture` pytest fixture that loads all fixture files into a `PageCapture` object. Returns `pytest.skip` if fixtures don't exist yet
- `tests/test_capture.py` — Tier 1: mock Playwright page + Firecrawl response, assert `PageCapture` assembly works. Verify element map entries have required fields (tag, bbox, visible, focusable)

**Acceptance:**
- Tier 1: `pytest tests/test_capture.py` passes — PageCapture assembly from mocked sources
- axe-core JS injection matches FLOW.md Step 2.2b (runOnly: wcag2a, wcag2aa, wcag22aa)
- Element map JS matches FLOW.md Step 2.2c (selectors, fields, visible filter)
- Pipeline uses `asyncio.gather` for N-way parallelism (not sequential)
- **Post-merge manual step:** Run `python scripts/save_fixtures.py`, verify fixtures look correct, commit them. This is the ONE manual step in the entire workflow — it produces the golden fixture set that all downstream slices depend on

---

### Slice 4 — Vision WCAG Analysis (Phase 3, Step A)

**Read:** Phase 3 Step A — Vision Analysis + Bounding Box Detection (entire section including all 8 P0 criteria)

**Requires fixtures from:** Slice 3 (`sample_screenshot.png`, `sample_element_map.json`, `sample_axe_results.json`, `sample_firecrawl_scrape.json`)

**Fixtures created by this slice (committed after Tier 2 run):**
- `tests/fixtures/sample_violations.json` — real Gemini vision output parsed into Violation objects

**Deliver:**
- `src/accessvision/analysis/__init__.py`
- `src/accessvision/analysis/vision.py` — async: takes `PageCapture`, sends screenshot + element map + axe results + markdown to Gemini 3.1 Pro, parses response into list of `Violation` objects
- `src/accessvision/prompts/vision_audit.py` — criterion-by-criterion prompt covering all 8 P0 criteria:
  1. 1.1.1 Alt Text Quality
  2. 1.4.1 Color-Only Information
  3. 1.4.3 Contrast Over Images
  4. 2.4.4 Link Purpose
  5. 2.4.7 Focus Visibility
  6. 4.1.2 Visual Label Match
  7. 1.4.5 Images of Text
  8. 3.3.1 Error Identification
- `src/accessvision/analysis/coordinates.py` — converts Gemini's `box_2d` (`[y_min, x_min, y_max, x_max]` in 1000×1000 grid) to pixel coords based on screenshot dimensions
- `src/accessvision/analysis/merge.py` — merges vision violations with axe-core violations, deduplicates by element + criterion
- `tests/test_coordinates.py` — Tier 1: box_2d → pixel conversion. `[780, 350, 830, 550]` on 1280×936 → expected pixel rect
- `tests/test_merge.py` — Tier 1: hand-written vision + axe violations with overlap, assert dedup keeps higher-severity entry
- `tests/test_vision.py` — Tier 1: mock Gemini response (realistic violation JSON), assert parsing into `Violation` objects

**Acceptance:**
- Tier 1: `pytest tests/test_coordinates.py tests/test_merge.py tests/test_vision.py` passes
- Vision prompt explicitly names and evaluates all 8 P0 criteria
- Coordinate math: `pixel_x = (x_norm / 1000) * screenshot_width` tested with known values
- Merge: same element + same criterion from axe and vision → keep one, prefer vision's severity
- **Post-merge manual step:** Run vision on Slice 3 fixtures, save `sample_violations.json`

---

### Slice 5 — Annotation + Solution PR Generation (Phase 3, Steps B + C)

**Read:** Phase 3 Step B (Annotated Screenshot) and Step C (Solution PR Generation)

**Requires fixtures from:** Slice 3 (`sample_screenshot.png`), Slice 4 (`sample_violations.json`)

**Deliver:**
- `src/accessvision/output/__init__.py`
- `src/accessvision/output/annotator.py` — takes screenshot PNG bytes + list of `Violation` objects, draws with Pillow:
  - Colored bounding box per violation: Critical=red `#FF0000`, Serious=orange `#FF8C00`, Moderate=yellow `#FFD700`, Minor=blue `#4169E1`
  - Numbered badge (white text on severity-colored circle) at top-left of each box
  - 3px border, slight transparency on fill
  - Returns annotated PNG bytes
- `src/accessvision/output/solution_pr.py` — async: takes violations + page context, calls Gemini Flash, returns markdown fix document with before/after code per violation, ordered by severity
- `src/accessvision/prompts/solution_pr.py` — prompt for fix generation (criterion, element, description, code block)
- `tests/test_annotator.py` — Tier 1: load `sample_screenshot.png`, create 2 fake violations with known bboxes, run annotator, assert output is valid PNG and pixels differ at bbox locations
- `tests/test_solution_pr.py` — Tier 1: mock Gemini response, assert output markdown contains severity-ordered sections with code blocks

**Acceptance:**
- Tier 1: `pytest tests/test_annotator.py tests/test_solution_pr.py` passes
- Annotator: output PNG has visible colored rectangles (pixel diff test against input)
- Solution PR: one section per violation, each with before/after code block, Critical first
- Both async-compatible for `asyncio.gather` parallel execution

---

### Slice 6 — Report Assembly + CLI Entrypoint

**Read:** Final Output Assembly, Timing Estimates, API Calls Per Audit

**Requires fixtures from:** All upstream slices

**Deliver:**
- `src/accessvision/report/__init__.py`
- `src/accessvision/report/builder.py` — takes list of `PageAudit` objects, sorts by `priority_score × severity_weight`, generates HTML report
- `src/accessvision/report/template.html` — HTML/CSS template (inline styles). Sections:
  - Executive summary: pages audited, total violations, severity breakdown, axe vs vision count comparison
  - Per-page sections sorted by composite score: annotated screenshot (base64 embedded), violation table, fix suggestions
- `src/accessvision/__main__.py` — complete CLI: `python -m accessvision <url> --pages N --output report.html`
  - Orchestrates: discover → rank → capture → analyze → annotate + fix → report
  - Progress output to stderr with phase names + timing
- `tests/test_report.py` — Tier 1: 3 hand-built `PageAudit` objects with different scores, assert HTML sort order and summary stats
- `tests/test_e2e.py` — Tier 2 (manual): `python -m accessvision https://example.com --pages 1 --output test_report.html`

**Acceptance:**
- Tier 1: `pytest tests/test_report.py` passes — sort order correct, summary numbers match
- CLI: `python -m accessvision --help` shows all options
- Report: pages sorted descending by composite score, Critical+high-priority at top
- Executive summary: "axe-core found X issues, vision analysis found Y additional issues"

---

> **Future: Overlord Orchestrator** — An agent that reads this slice index, spawns one `/cm` per slice across worktree slots, monitors status panes, and auto-triggers dependent slices when predecessors ship. For now, you are the orchestrator. Run slices manually via `/cm implement Slice N from FLOW.md`.
