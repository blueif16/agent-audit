# AccessVision — Complete Execution Flow

## Scoring System

Two scores drive the entire pipeline:

1. **`priority_score`** (1–10, assigned in Phase 1) — How important this page is to real users. A checkout page is a 10. A blog post about company picnics is a 2. This score is assigned ONCE during discovery and never changes.

2. **`severity`** (Critical / Serious / Moderate / Minor, assigned in Phase 3) — How bad each individual WCAG violation is on that page. A keyboard trap on a login form is Critical. A slightly vague heading is Minor. Each violation gets its own severity. The page-level severity is the MAX severity among all its violations.

Final report ordering: pages sorted by `priority_score × severity_weight`, where Critical=4, Serious=3, Moderate=2, Minor=1. A Critical violation on a high-priority page surfaces to the top. A Minor issue on a blog post sinks to the bottom.

---

## Phase 1: Discover + Rank

**Goal:** Find every page on the target site, then use an LLM to pick the top N most audit-worthy pages.

**Duration:** ~8 seconds total

### Step 1.1 — Site Mapping via Firecrawl `/map`

**Input:** Root URL (e.g. `https://target-site.com`)

**Tool:** Firecrawl `/map` endpoint

**What happens:**
- Firecrawl hits the site's `sitemap.xml` (if it exists) and simultaneously crawls the link graph starting from the root URL.
- Returns up to 30,000 discovered URLs with their page titles.
- Handles JS-rendered sites, follows redirects, deduplicates automatically.
- Takes ~2–3 seconds regardless of site size.

**Output:**
```json
[
  {"url": "https://target.com/", "title": "Acme Corp - Home"},
  {"url": "https://target.com/pricing", "title": "Pricing Plans"},
  {"url": "https://target.com/login", "title": "Sign In"},
  {"url": "https://target.com/blog/post-47", "title": "Why We Love Cats"},
  // ... ~300 entries typical
]
```

**Why Firecrawl over DIY Playwright crawling:**
- 2–3 seconds vs minutes of recursive link following
- Handles sitemap + link graph fusion automatically
- Powered by Gemini 2.5 Pro under the hood for intelligent crawling
- 1 credit per scrape, `/map` is lightweight discovery — no full page scraping needed here

### Step 1.2 — LLM Page Ranking

**Input:** The full list of URL+title pairs from Step 1.1

**Model:** `gemini-3-flash-preview`

**What happens:**
- A single Gemini Flash call receives all ~300 URL+title pairs.
- The prompt instructs the model to rank pages by accessibility audit priority.
- The model uses URL path structure and page titles as signals.

**Ranking criteria baked into the prompt:**
- **High priority:** User-critical flows (login, signup, checkout, account settings, forms), high-traffic public pages (home, products, pricing, search), pages with likely heavy interaction (dashboards, filters, configurators), onboarding flows
- **Medium priority:** Content pages with some interaction (FAQ with accordions, documentation with nav), contact/support pages with forms
- **Low priority:** Blog posts (templated, low interaction), legal pages (terms, privacy — mostly static text), deep-nested pages unlikely to receive direct traffic, duplicate/variant pages (pagination, tag archives)

**Output:**
```json
[
  {"url": "https://target.com/", "title": "Home", "priority_score": 10, "reason": "Landing page, highest traffic, first impression"},
  {"url": "https://target.com/login", "title": "Sign In", "priority_score": 10, "reason": "Authentication flow, blocks all account access"},
  {"url": "https://target.com/checkout", "title": "Checkout", "priority_score": 10, "reason": "Revenue-critical form flow"},
  {"url": "https://target.com/search", "title": "Search Results", "priority_score": 8, "reason": "Dynamic content, filters, keyboard-heavy"},
  {"url": "https://target.com/contact", "title": "Contact Us", "priority_score": 6, "reason": "Form submission, moderate traffic"}
]
```

The model returns exactly N pages. N is user-configurable (default 20, demo uses 5).

---

## Phase 2: Capture

**Goal:** Visit each of the N ranked pages and collect everything needed for analysis — screenshot, clean description, DOM data, and automated scan results.

**Duration:** ~5 seconds wall clock (all N pages captured in parallel)

**Parallelism:** N concurrent Playwright pages + N concurrent Firecrawl `/scrape` calls. Each page has two parallel data sources.

### Step 2.1 — Firecrawl `/scrape` (per page, parallel)

**Input:** Page URL

**Tool:** Firecrawl `/scrape` endpoint

**What happens:**
- Firecrawl renders the page (handles JS), then uses Gemini 2.5 Pro internally to produce clean, structured markdown.
- Strips navigation chrome, ads, footers, cookie banners — extracts the meaningful content.
- Returns markdown that describes WHAT the page is and WHAT it does.

**Output per page:**
```json
{
  "markdown": "# Checkout\n\n## Order Summary\nYour cart (3 items)...\n\n## Shipping Information\n**First Name** [text field]\n**Last Name** [text field]\n**Address** [text field]\n...\n\n## Payment\n**Card Number** [text field]\n**Expiry** [text field]\n**CVV** [text field]\n\n[Place Order] button",
  "metadata": {
    "title": "Checkout",
    "description": "Complete your purchase",
    "language": "en",
    "sourceURL": "https://target.com/checkout",
    "statusCode": 200
  },
  "links": [...]
}
```

**Why this matters:** This markdown is the page description that flows into the vision model. It tells the model "this is a checkout page with form fields for shipping and payment, and a submit button" — enabling contextual WCAG analysis rather than blind pattern matching.

### Step 2.2 — Playwright Capture (per page, parallel with 2.1)

**Input:** Page URL

**Tool:** Playwright (Chromium, headless)

**What happens (sequential within each page):**

**a) Page load + screenshot:**
- Navigate to URL, wait for `networkidle`
- Set viewport to consistent size (1280×936 — matching Computer Use model dimensions)
- Capture full-page screenshot as PNG
- This screenshot is the exact image fed to the vision model and used for annotation

**b) axe-core injection + scan:**
```javascript
// Inject axe-core library into page context
await page.addScriptTag({ path: 'node_modules/axe-core/axe.min.js' });

// Run scan targeting WCAG 2.2 AA criteria
const results = await page.evaluate(() => {
  return axe.run(document, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag22aa'] }
  });
});
```
- Returns structured JSON: `violations[]`, `passes[]`, `incomplete[]`
- Each violation includes: rule ID, WCAG criteria tags, impact level, affected HTML elements with CSS selectors, help text

**c) Element map extraction:**
```javascript
// Extract every interactive/semantic element with its bounding box
const elementMap = await page.evaluate(() => {
  const selectors = 'img, a, button, input, select, textarea, [role], h1, h2, h3, h4, h5, h6, label, nav, form, [tabindex]';
  const elements = document.querySelectorAll(selectors);
  return [...elements].map((el, i) => {
    const rect = el.getBoundingClientRect();
    return {
      index: i,
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute('role'),
      text: (el.textContent || '').trim().slice(0, 120),
      alt: el.getAttribute('alt'),
      aria_label: el.getAttribute('aria-label'),
      aria_describedby: el.getAttribute('aria-describedby'),
      href: el.getAttribute('href'),
      type: el.getAttribute('type'),
      name: el.getAttribute('name'),
      placeholder: el.getAttribute('placeholder'),
      bbox: {
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        w: Math.round(rect.width),
        h: Math.round(rect.height)
      },
      visible: rect.width > 0 && rect.height > 0,
      focusable: el.tabIndex >= 0
    };
  }).filter(e => e.visible);
});
```
- This element map serves two purposes:
  1. Gives the vision model a numbered index of elements it can reference (instead of guessing pixel coordinates)
  2. Provides known bounding boxes for the annotation step — no need for the vision model to estimate positions

**d) Accessibility tree extraction:**
```javascript
// Get the browser's computed accessibility tree
const a11yTree = await page.accessibility.snapshot({ interestingOnly: true });
```
- Returns the page's accessibility tree as the browser/screen reader sees it
- Reveals what a screen reader would actually announce for each element
- Shows programmatic names, roles, states, and parent/child relationships

**Output per page — merged `PageCapture` object:**
```python
@dataclass
class PageCapture:
    url: str
    title: str
    priority_score: int                # from Phase 1
    reason: str                        # from Phase 1
    screenshot: bytes                  # PNG from Playwright
    markdown_description: str          # from Firecrawl
    axe_results: dict                  # from axe-core
    element_map: list[dict]            # from Playwright
    accessibility_tree: dict           # from Playwright
```

---

## Phase 3: Analyze

**Goal:** For each captured page, run the visual WCAG audit, generate an annotated screenshot, and produce a solution PR with code fixes.

**Duration:** ~30 seconds wall clock (limited by slowest vertical pipe across N pages)

**Parallelism:** N independent vertical pipelines run simultaneously. Within each pipeline, Steps B and C run in parallel (both depend only on Step A output, not on each other).

### Step A — Vision Analysis + Bounding Box Detection

**Input per page:**
- Playwright screenshot (PNG)
- Firecrawl markdown description
- Element map with bounding boxes
- axe-core results (so the model knows what's already been caught and doesn't duplicate)

**Model:** `gemini-3.1-pro-preview`

**Configuration:**
- `thinking_level`: `MEDIUM` for thorough reasoning about each criterion
- For bounding box output specifically, consider setting `thinking_level` to `MINIMAL` if bbox accuracy degrades with extended reasoning (test both)
- Response format: structured JSON

**Prompt structure (this is the core IP — needs serious iteration and testing):**

The prompt must systematically walk the model through each P0 WCAG criterion. It should NOT be a vague "find accessibility issues." It should be a checklist-driven analysis where the model evaluates each criterion explicitly and reports pass/fail/violation for each.

Critical prompt design requirements:
- **Criterion-by-criterion evaluation:** The model must address each criterion individually, not just report whatever catches its eye
- **Use the markdown description for context:** "This is a checkout page. The form fields for payment are the most critical interactive elements."
- **Reference the element map by index:** "Element #14 (submit button) at bbox {x:400, y:800, w:200, h:48} — evaluate focus visibility, target size, label match"
- **Cross-reference axe-core results:** "axe-core already flagged elements #3 and #7 for missing alt text. Confirm these and check if the alt text on OTHER images is actually meaningful."
- **Request box_2d in Gemini's native format:** `[y_min, x_min, y_max, x_max]` normalized to 1000×1000 grid — this is how Gemini is trained to return spatial data

**P0 WCAG Criteria to test (minimum for hackathon demo):**

1. **1.1.1 Alt Text Quality** — Look at each image, read its alt text from element map, determine if the alt text accurately describes the visual content. Flag generic alt text ("image", "photo", "banner", "logo"), missing alt text on informative images, or alt text that doesn't match what the image actually shows.

2. **1.4.1 Color-Only Information** — Scan for patterns where color alone conveys meaning: red/green for error/success states, colored dots for status, links distinguished from body text only by color (no underline), required fields marked only in red, chart/graph data series differentiated only by color.

3. **1.4.3 Contrast Over Images** — Find text rendered over background images, gradients, or complex visual backgrounds where axe-core's CSS-based contrast check can't see the actual visual contrast. The screenshot reveals what the user actually sees.

4. **2.4.4 Link Purpose** — Identify all links. Flag generic/repetitive link text ("Click Here", "Learn More", "Read More", "Here") that appears multiple times without distinguishing context. Evaluate whether each link's purpose is clear.

5. **2.4.7 Focus Visibility** — Examine interactive elements and assess whether they likely have visible focus indicators. Note: without actually tabbing through (that's Computer Use territory), the model can still check if focus styles are visually defined by examining element styling context.

6. **4.1.2 Visual Label Match** — Compare what's visually displayed on interactive elements (from the screenshot) against their programmatic names (from the element map's `aria_label`, `text` fields). Flag mismatches where a button shows "Send" but has `aria-label="Submit"`.

7. **1.4.5 Images of Text** — Use vision to detect text baked into images (banners, buttons with image backgrounds containing text, infographics with embedded text). These should use real text instead.

8. **3.3.1 Error Identification** — Based on the page context (is this a form?), assess whether error states are likely communicated via text (not just color) and positioned near their related fields.

**Output per page:**
```json
{
  "page_url": "https://target.com/checkout",
  "violations": [
    {
      "id": "v1",
      "element_index": 14,
      "box_2d": [780, 350, 830, 550],
      "criterion": "2.4.7",
      "criterion_name": "Focus Visible",
      "severity": "Critical",
      "description": "The 'Place Order' button has no visible focus indicator. Keyboard users cannot see when this critical action is focused.",
      "remediation_hint": "Add :focus-visible outline style to .btn-checkout"
    },
    {
      "id": "v2",
      "element_index": 8,
      "box_2d": [400, 50, 460, 300],
      "criterion": "1.4.1",
      "criterion_name": "Use of Color",
      "severity": "Serious",
      "description": "Required fields are indicated only by red asterisks. Color-blind users cannot distinguish required from optional fields.",
      "remediation_hint": "Add '(required)' text label or use aria-required with visible text indicator"
    }
  ],
  "passes": ["1.1.1", "1.4.3", "1.4.5"],
  "summary": "Checkout page has 2 violations (1 Critical, 1 Serious). Primary risk: keyboard users cannot complete purchase flow."
}
```

**Bounding box coordinate handling:**
- Gemini returns `box_2d` as `[y_min, x_min, y_max, x_max]` in a 1000×1000 normalized grid
- Convert to actual pixel coordinates: `pixel_x = (x_norm / 1000) * screenshot_width`
- These coordinates drive the annotation in Step B
- Where possible, cross-reference with element map bboxes for higher accuracy — the element map has pixel-perfect coordinates from the DOM, and the vision model's box_2d confirms visual location

### Step B — Annotated Screenshot Generation (parallel with Step C)

**Input:**
- Original Playwright screenshot (PNG)
- Violation list from Step A with `box_2d` coordinates
- Severity levels for color coding

**Model:** Nano Banana Pro (`gemini-3-pro-image`) or Nano Banana 2 (`gemini-3.1-flash-image`)

**What happens:**
- Feed the original screenshot + instruction to draw colored annotation overlays at specific locations
- Each violation gets a numbered marker and colored bounding box:
  - Critical = red
  - Serious = orange
  - Moderate = yellow
  - Minor = blue
- Numbered badges correspond to violation IDs in the report

**Fallback (if Nano Banana annotation is unreliable):**
- Use Pillow (PIL) in Python to draw rectangles, numbered badges, and severity-colored borders directly onto the screenshot PNG
- This is deterministic, pixel-perfect, and takes <100ms per image
- Build this fallback FIRST as baseline, then try Nano Banana on top

**Output:** Annotated screenshot PNG with visual markers highlighting every violation location.

### Step C — Solution PR Generation (parallel with Step B)

**Input:**
- Step A violation list (structured JSON)
- axe-core results
- Firecrawl markdown description
- Element map (for CSS selectors, tag names, attributes)
- NO image input needed — this is purely text-to-text

**Model:** `gemini-3-flash-preview` (fast, strong reasoning, excellent for structured text generation)

**What happens:**
- The model generates a remediation document structured like a pull request
- Each violation gets a concrete code fix with before/after
- Fixes are ordered by severity (Critical first)
- The page's `priority_score` from Phase 1 is included so the final report can sort across pages

**Output per page — the Page Audit PR:**
```markdown
# Accessibility Audit: Checkout (/checkout)
**Priority Score:** 10/10
**Max Severity:** Critical
**Violations Found:** 2 (vision) + 3 (axe-core) = 5 total

---

## Critical: Focus Indicator Missing on Submit Button
**WCAG 2.4.7 — Focus Visible**
**Element:** `button.btn-checkout` ("Place Order")
**Detected by:** Vision analysis

The primary call-to-action for completing a purchase has no visible 
focus indicator. Keyboard-only users cannot see when this button is 
focused, making it impossible to confidently submit an order.

### Fix
\```css
/* Before: no focus style defined */
.btn-checkout:focus {
  outline: none; /* ← actively removing focus indicator */
}

/* After: visible, high-contrast focus ring */
.btn-checkout:focus-visible {
  outline: 3px solid #005fcc;
  outline-offset: 2px;
}
\```

---

## Serious: Color-Only Required Field Indicators  
**WCAG 1.4.1 — Use of Color**
**Elements:** `.form-field.required` (6 instances)
**Detected by:** Vision analysis

Required fields are marked with red asterisks only. Users with color 
vision deficiency (affecting ~8% of males) cannot distinguish required 
from optional fields.

### Fix
\```html
<!-- Before -->
<label class="required">Card Number <span class="red">*</span></label>

<!-- After -->
<label class="required">Card Number <span class="required-indicator">* (required)</span></label>
\```

---

## [axe-core violations follow, merged into same format...]
```

**Severity assignment rules (baked into the Step C prompt):**
- **Critical:** Blocks users from completing a task entirely (keyboard traps, missing form labels on required fields, no focus indicator on submit buttons, images conveying essential info with no alt text)
- **Serious:** Significantly degrades the experience but workaround may exist (color-only information, poor contrast on important text, generic link text repeated many times)
- **Moderate:** Causes confusion or extra effort (slightly vague headings, minor label mismatches, images of text where real text could work)
- **Minor:** Best practice violations that don't directly block users (decorative images with non-empty alt text, minor target size issues on non-critical elements)

---

## Final Output Assembly

No separate synthesis phase needed. The N Page Audit PRs from Phase 3 are the deliverable.

**Sorting:** Pages ordered by `priority_score × severity_weight` where the severity_weight is derived from the page's worst (maximum) violation severity.

```
Page Audit PR: /checkout     → 10 × 4 (Critical)  = 40  ← top
Page Audit PR: /login        → 10 × 3 (Serious)   = 30
Page Audit PR: /search       →  8 × 3 (Serious)   = 24
Page Audit PR: /products     →  7 × 2 (Moderate)   = 14
Page Audit PR: /contact      →  6 × 1 (Minor)      =  6  ← bottom
```

**Each Page Audit PR contains:**
1. Annotated screenshot (from Step B) — visual proof of every issue
2. Violation list with WCAG criterion, severity, description, and element reference (from Step A)
3. axe-core results merged in (from Phase 2)
4. Code fix suggestions ordered by severity (from Step C)
5. Page metadata: URL, title, priority_score, max severity

**Final report format:** HTML report (or JSON for API consumption) containing all N Page Audit PRs in sorted order, with:
- Executive summary: "Audited N pages, found X violations across Y WCAG criteria. Z critical issues require immediate attention."
- Per-page sections with annotated screenshots and fix PRs
- Comparison callout: "axe-core found A issues. AccessVision found A + B additional issues that require visual judgment."

---

## Timing Estimates

| Phase | Work | Wall Clock |
|-------|------|-----------|
| Phase 1: Firecrawl /map | Discover ~300 URLs | ~3s |
| Phase 1: Flash ranking | Rank and select top N | ~3-5s |
| Phase 2: Capture (N parallel) | Firecrawl scrape + Playwright per page | ~5s |
| Phase 3: Step A (N parallel) | Vision analysis per page | ~8-15s |
| Phase 3: Steps B+C (N parallel, within-page parallel) | Annotation + solution PR | ~10-30s |
| **Total for N=5** | | **~35-55s** |
| **Total for N=20** | | **~45-70s** |

Phase 3 dominates. The bottleneck is the slowest single page's vertical pipeline (likely Nano Banana image generation). All N pages run simultaneously, so wall clock ≈ single-page time regardless of N (up to API rate limits).

---

## Model Usage Summary

| Model | Used In | Purpose |
|-------|---------|---------|
| `gemini-3-flash-preview` | Phase 1 ranking, Phase 3 Step C | Text reasoning — page ranking, solution PR generation |
| `gemini-3.1-pro-preview` | Phase 3 Step A | Vision + bounding box — WCAG visual analysis |
| Nano Banana Pro or 2 | Phase 3 Step B | Image generation — annotated screenshot overlays |
| Firecrawl (Gemini 2.5 Pro internally) | Phase 1 mapping, Phase 2 scraping | Web crawling and clean markdown extraction |

All models are Google/Gemini family. The hackathon requires Gemini + Google Cloud, and this architecture uses Gemini at every layer — including through Firecrawl's Gemini-powered extraction engine.

---

## API Calls Per Audit (N pages)

| Call | Count | Model |
|------|-------|-------|
| Firecrawl `/map` | 1 | — |
| Gemini Flash (ranking) | 1 | 3-flash-preview |
| Firecrawl `/scrape` | N | — |
| Gemini 3.1 Pro (vision) | N | 3.1-pro-preview |
| Nano Banana (annotation) | N | 3-pro-image / 3.1-flash-image |
| Gemini Flash (solution PR) | N | 3-flash-preview |
| **Total Gemini API calls** | **2 + 3N** | |

For N=5: 17 API calls. For N=20: 62 API calls. On Tier 1 (150+ RPM on Flash, similar on Pro), this completes in a single burst with no rate limit waits.

---

## Tech Stack

- **Language:** Python 3.12+
- **Agent Framework:** Google ADK (Agent Development Kit)
- **Browser Automation:** Playwright (Chromium, headless)
- **Web Data:** Firecrawl API (`/map` + `/scrape`)
- **Accessibility Scanner:** axe-core (injected via Playwright)
- **Vision Model:** Gemini 3.1 Pro Preview (via Google GenAI SDK)
- **Text Model:** Gemini 3 Flash Preview (via Google GenAI SDK)
- **Image Generation:** Nano Banana Pro/2 (via Google GenAI SDK)
- **Image Annotation Fallback:** Pillow (PIL)
- **Hosting:** Google Cloud Run
- **Storage:** Google Cloud Storage (screenshots, reports)
- **IaC:** Terraform (bonus points)
- **Async Runtime:** asyncio + aiohttp for parallel execution
