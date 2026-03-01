# AccessVision — Visual Accessibility Audit Agent

## Project Plan & Complete Context Document

This document is a complete briefing for any LLM or developer to understand the project concept, the problem domain, the technical approach, and the execution plan. It is NOT implementation code — it is the knowledge base from which implementation should be derived.

---

## 1. The Hackathon: Gemini Live Agent Challenge

**Deadline:** March 16, 2026, 5:00 PM PDT
**Category:** UI Navigator — "Build an agent that becomes the user's hands on screen."
**Mandatory Tech:** Gemini multimodal to interpret screenshots/screen recordings and output executable actions. Agents hosted on Google Cloud. Must use Google GenAI SDK or ADK. Must use at least one Google Cloud service.

**Judging Criteria:**

- Innovation & Multimodal User Experience: 40% — Does it break the "text box" paradigm? Does it feel seamless, live, and context-aware? Distinct persona/voice?
- Technical Implementation & Agent Architecture: 30% — Effective use of GenAI SDK/ADK? Robust GCP hosting? Sound agent logic? Error handling? Grounding (anti-hallucination)?
- Demo & Presentation: 30% — Clear problem/solution? Architecture diagram? Visual proof of Cloud deployment? Working software in video?

**Bonus Points:**

- Published blog/video with `#GeminiLiveAgentChallenge`
- Automated Cloud Deployment via IaC (Terraform/scripts) in repo
- Google Developer Group membership with public GDG profile link

**Submission Requirements:**

- Text description of features, tech, learnings
- Public GitHub repo with spin-up instructions in README
- Proof of GCP deployment (screen recording of console OR code file showing GCP API usage)
- Architecture diagram
- Demo video under 4 minutes, real working software, no mockups

---

## 2. The Problem: Web Accessibility Testing Is Broken

### 2.1 What Is Web Accessibility?

Web accessibility means designing websites so people with disabilities can perceive, understand, navigate, and interact with them. Disabilities include visual (blindness, low vision, color blindness), auditory (deafness, hard of hearing), motor (inability to use a mouse, limited fine motor control), and cognitive (learning disabilities, attention disorders).

The governing standard is WCAG (Web Content Accessibility Guidelines), published by the W3C (World Wide Web Consortium). The current version is WCAG 2.2, though WCAG 2.1 AA is the most commonly required legal standard.

### 2.2 Legal Context

Web accessibility is not optional. In the US, the ADA (Americans with Disabilities Act) requires accessible digital experiences. The DOJ's 2024 rule specifies WCAG 2.1 AA. Over 4,000+ web accessibility lawsuits were filed in the US in 2023, and this number has increased every year. In the EU, the European Accessibility Act (EAA) mandates compliance by June 2025. Non-compliance means legal exposure, lost customers, and brand damage.

### 2.3 Current Tools and Their Fundamental Limitation

Three categories of accessibility testing tools exist today:

**Automated Code Scanners (what exists):**

- **Google Lighthouse** — Built into Chrome DevTools. Scores pages 0-100 across performance, SEO, best practices, and accessibility. Uses a subset of axe-core rules for accessibility checks. Free, ubiquitous, the most common first tool developers encounter.
- **axe-core** (by Deque Systems) — Open-source JavaScript library and browser extension. The industry-standard engine that powers Lighthouse's accessibility checks (Lighthouse uses a subset of axe's rules; the axe extension catches more). Every rule maps to specific WCAG criteria with pass/fail/incomplete states.
- **WAVE** (by WebAIM) — Browser extension that overlays visual icons directly on the page showing where problems are. More visual reporting than axe but same fundamental approach.
- **Pa11y, Tenon, SortSite, etc.** — Various other automated tools, all working the same way.

**How they all work:** They read the HTML/DOM and CSS, then check the code against a rulebook of patterns. "Does this `<img>` have an `alt` attribute?" "Is the contrast ratio between this text color and background color at least 4.5:1?" "Is this `<input>` associated with a `<label>`?" "Is this ARIA role valid per the spec?"

**The fundamental limitation:** These tools can ONLY test things that have a clear pass/fail answer based on code inspection. They cannot see the rendered page. They cannot make judgment calls about meaning, context, or visual presentation.

**The numbers that define our opportunity:**

- Only 13% of WCAG 2.2 AA success criteria can be RELIABLY flagged by automated scans (Source: accessible.org)
- ~45% are PARTIALLY detectable — the tool can flag something but a human must confirm whether it's actually a problem
- ~42% are FULLY UNDETECTABLE by automated tools — they require a human looking at the rendered page
- 70% of the 86 WCAG success criteria require human review (Source: UsableNet)
- A developer built a completely unusable website that scored 100/100 on Lighthouse (Manuel Matuzovic's famous demonstration)

**Manual Auditors (what's expensive):**

Professional WCAG auditors charge $100-200/hour. A full audit of a single website costs $5,000-$15,000. They look at the actual rendered pages, navigate with keyboard and screen readers, test with different zoom levels, evaluate meaning and context. The demand massively outstrips supply.

**User Testing (what's ideal but impractical at scale):**

Actual users with disabilities test the site. Most accurate but most expensive and least scalable.

### 2.4 The Gap We Fill

We are NOT replacing axe-core/Lighthouse. We are replacing the $150/hour human auditor who catches the 60-70% that automated code scanners structurally cannot detect. Our agent LOOKS at the rendered page with Gemini's visual reasoning and makes the judgment calls that code-level tools cannot.

**One-line pitch: "Lighthouse checks your code. We check your page. Because your users don't read HTML — they see pixels."**

### 2.5 Academic Validation

A 2024 paper published in Universal Access in the Information Society (Springer) tested LLMs on exactly this concept. They tested three WCAG criteria that require manual checks (1.1.1 Non-text Content, 2.4.4 Link Purpose, 3.1.2 Language of Parts) and found that LLM-based approaches showed promising results where automated evaluators failed. Their approach used text-based LLMs reading HTML. Our approach goes further — using Gemini's visual reasoning to look at the actual rendered page. This is a genuine research-grade contribution.

---

## 3. WCAG 2.2 Success Criteria — Complete Breakdown

WCAG is organized under 4 Principles, each containing Guidelines, each containing Success Criteria. Three conformance levels exist: A (minimum), AA (standard target), AAA (ideal). Legal requirements and most company policies target Level AA.

### 3.1 Principle 1: Perceivable

Information and UI components must be presentable in ways users can perceive.

#### Guideline 1.1 — Text Alternatives

**1.1.1 Non-text Content (Level A)**
All non-text content has a text alternative that serves the equivalent purpose.

- What axe-core checks: Does the `<img>` have an `alt` attribute? Is it empty on decorative images? Does `<input type="image">` have alt text?
- What axe-core CANNOT check: Is the alt text actually accurate? Does it describe what's in the image? Is a decorative image correctly marked as decorative, or is it informative but ignored? If alt text says "photo" but the image shows a critical diagram, axe passes but the user fails.
- **YOUR AGENT'S JOB:** Look at the image with Gemini vision. Read the alt text. Determine if the alt text meaningfully describes what the image actually shows. Flag cases where alt text is generic ("image", "photo", "banner"), misleading, or missing important information visible in the image.

#### Guideline 1.2 — Time-based Media

**1.2.1 Audio-only and Video-only (Level A)** — Alternatives provided for prerecorded audio/video.
**1.2.2 Captions (Prerecorded) (Level A)** — Captions for prerecorded audio in synchronized media.
**1.2.3 Audio Description or Media Alternative (Level A)** — Alternative for prerecorded video.
**1.2.4 Captions (Live) (Level AA)** — Captions for live audio.
**1.2.5 Audio Description (Level AA)** — Audio description for prerecorded video.

- What axe-core checks: Basically nothing meaningful here. It can detect `<video>` and `<audio>` elements but cannot evaluate caption quality or audio description accuracy.
- **YOUR AGENT'S JOB (stretch goal):** Detect presence of video/audio elements. Check if captions/transcripts exist. Could potentially use Gemini to evaluate if visible captions match spoken content in short clips. This is a stretch goal — deprioritize for hackathon.

#### Guideline 1.3 — Adaptable

Content can be presented in different ways without losing information or structure.

**1.3.1 Info and Relationships (Level A)**
Information, structure, and relationships conveyed through presentation are programmatically determinable or available in text.

- What axe-core checks: Are form labels present? Are table headers used? Are heading levels in order? Are lists using proper `<ul>`/`<ol>`/`<li>` markup?
- What axe-core CANNOT check: Does the VISUAL structure match the CODE structure? A developer might use CSS to visually position a sidebar above the main content, but in the DOM it comes after — a screen reader reads it in the wrong order. Visual groupings created purely through whitespace/color without structural markup.
- **YOUR AGENT'S JOB:** Compare the visual layout (from screenshot) against the DOM reading order. Detect visual groupings (sections, card layouts, sidebar/content relationships) that aren't reflected in the HTML structure. Identify cases where visual hierarchy (big bold text acting as a heading) doesn't use proper heading tags.

**1.3.2 Meaningful Sequence (Level A)**
When the sequence of content affects its meaning, a correct reading sequence is programmatically determinable.

- What axe-core checks: Very limited — mostly checks tab order on focusable elements.
- **YOUR AGENT'S JOB:** Visually scan the page and determine the intended reading order (left-to-right, top-to-bottom for LTR languages, with logical content groupings). Compare against DOM order. Flag cases where visual order and reading order diverge significantly.

**1.3.3 Sensory Characteristics (Level A)**
Instructions don't rely solely on sensory characteristics (shape, color, size, visual location, orientation, sound).

- What axe-core checks: Cannot check this at all.
- **YOUR AGENT'S JOB:** Look for instructional text that references visual properties only. Examples: "Click the round button", "See the sidebar on the right", "The red items are required." These assume the user can see shape, position, and color.

**1.3.4 Orientation (Level AA)** — Content not restricted to single orientation unless essential.
**1.3.5 Identify Input Purpose (Level AA)** — Input purpose can be programmatically determined for common fields.

#### Guideline 1.4 — Distinguishable

Make it easier for users to see and hear content.

**1.4.1 Use of Color (Level A)**
Color is not used as the only visual means of conveying information, indicating an action, prompting a response, or distinguishing a visual element.

- What axe-core checks: Cannot check this. It has no concept of "what does this color mean in context."
- **YOUR AGENT'S JOB (HIGH PRIORITY):** This is one of the highest-value visual checks. Look at the page for patterns where color alone conveys meaning: red/green for error/success states, colored dots for status indicators, link text that's only distinguished from body text by color (no underline), required fields marked only in red, graphs/charts using only color to differentiate data series. Simulate color-blind views if possible (Gemini can reason about what a deuteranopia user would see).

**1.4.2 Audio Control (Level A)** — Mechanism to pause/stop/control audio volume.

**1.4.3 Contrast (Minimum) (Level AA)**
Text has a contrast ratio of at least 4.5:1 (3:1 for large text).

- What axe-core checks: YES — this is one of axe's strongest checks. It computes contrast from declared CSS colors.
- What axe-core MISSES: Text over background images. Text over gradients. Text where the background color is set by a complex CSS stack. Text that overlaps other elements due to positioning. Dynamically colored text.
- **YOUR AGENT'S JOB:** Catch contrast failures that involve text rendered over images, gradients, or complex visual backgrounds where the CSS color values alone don't tell the full story. The screenshot reveals what the user actually sees.

**1.4.4 Resize Text (Level AA)** — Text can be resized up to 200% without loss of content or functionality.
**1.4.5 Images of Text (Level AA)** — If the same visual presentation can be made with text, actual text is used instead of images of text.

- What axe-core checks: Cannot reliably detect images that contain text vs. images that don't.
- **YOUR AGENT'S JOB:** Use Gemini vision to detect text rendered as images (banners, buttons using image backgrounds with text baked in, infographics with text). Flag these as potential WCAG violations.

**1.4.10 Reflow (Level AA)** — Content reflows at 320px width (400% zoom) without horizontal scrolling.
**1.4.11 Non-text Contrast (Level AA)** — UI components and graphical objects have at least 3:1 contrast.
**1.4.12 Text Spacing (Level AA)** — No loss of content when text spacing is adjusted.
**1.4.13 Content on Hover or Focus (Level AA)** — Additional content triggered by hover/focus is dismissible, hoverable, and persistent.

### 3.2 Principle 2: Operable

UI components and navigation must be operable.

#### Guideline 2.1 — Keyboard Accessible

**2.1.1 Keyboard (Level A)**
All functionality is operable through a keyboard.

- What axe-core checks: Some focusable element checks, tabindex validation.
- What axe-core CANNOT check: Whether ALL interactive elements are actually reachable and activatable via keyboard. This requires navigating the page.
- **YOUR AGENT'S JOB:** Use Computer Use to TAB through the page. Track focus movement. Identify interactive elements (buttons, links, dropdowns, modals) that are visually present but not reachable via keyboard. Detect keyboard traps (places where focus gets stuck and Tab doesn't advance).

**2.1.2 No Keyboard Trap (Level A)** — Focus can always be moved away from any component using keyboard.

- **YOUR AGENT'S JOB (HIGH PRIORITY):** Tab through the page and detect if focus gets trapped in any component (modal with no escape, custom widget that captures keyboard input). This is one of the most severe accessibility barriers.

**2.1.4 Character Key Shortcuts (Level A)** — Character-only keyboard shortcuts can be turned off or remapped.

#### Guideline 2.2 — Enough Time

**2.2.1 Timing Adjustable (Level A)** — Time limits can be adjusted.
**2.2.2 Pause, Stop, Hide (Level A)** — Moving, blinking, scrolling, or auto-updating content can be paused/stopped/hidden.

#### Guideline 2.3 — Seizures and Physical Reactions

**2.3.1 Three Flashes or Below Threshold (Level A)** — No content flashes more than 3 times per second.

#### Guideline 2.4 — Navigable

**2.4.1 Bypass Blocks (Level A)** — Mechanism to bypass repeated navigation blocks (skip links).

- What axe-core checks: Checks for skip-link presence.
- **YOUR AGENT'S JOB:** Verify the skip link actually works — does activating it move focus to the main content? Is it visible on focus?

**2.4.2 Page Titled (Level A)** — Pages have descriptive titles.

- What axe-core checks: Checks if `<title>` exists.
- What axe-core CANNOT check: Is the title actually descriptive of the page content?
- **YOUR AGENT'S JOB:** Read the page title. Look at the page content. Determine if the title meaningfully describes what the page is about. Flag generic titles like "Home", "Page 1", "Untitled".

**2.4.3 Focus Order (Level A)** — Focusable components receive focus in a meaningful sequence.

- **YOUR AGENT'S JOB:** Tab through the page and verify that focus moves in a logical visual order (not jumping randomly across the page). Compare visual position of focused elements against the sequence.

**2.4.4 Link Purpose (In Context) (Level A)**
The purpose of each link can be determined from the link text alone or from the link together with its context.

- What axe-core checks: Flags completely empty links. Can check for some generic link text patterns.
- What axe-core CANNOT check: Whether "Learn More" makes sense in its visual context. Whether 15 "Learn More" links on the same page create confusion.
- **YOUR AGENT'S JOB (HIGH PRIORITY):** Identify all links on the page. Flag generic link text ("Click Here", "Learn More", "Read More", "Here") that appears multiple times without distinguishing context. Evaluate whether each link's purpose is clear from its text and immediate visual surroundings.

**2.4.5 Multiple Ways (Level AA)** — More than one way to locate a page within a set of pages (navigation, search, site map).
**2.4.6 Headings and Labels (Level AA)** — Headings and labels describe topic or purpose.

- What axe-core checks: Checks that headings exist and are in order.
- What axe-core CANNOT check: Whether the heading TEXT actually describes the content below it.
- **YOUR AGENT'S JOB:** Read each heading, look at the content under it, and determine if the heading is descriptive. Flag vague headings like "Section 1", "More Info", "Details".

**2.4.7 Focus Visible (Level AA)** — Keyboard focus indicator is visible.

- What axe-core checks: Limited CSS checks for `outline: none`.
- **YOUR AGENT'S JOB (HIGH PRIORITY):** Tab through the page via Computer Use and visually verify that EVERY focused element has a visible focus indicator. Take screenshots of focused states. Flag elements where focus is invisible or nearly invisible (low-contrast focus rings, focus hidden by `outline: none` with no replacement).

**2.4.11 Focus Not Obscured (Minimum) (Level AA) [WCAG 2.2 new]** — Focused component is not entirely hidden by other content.

- **YOUR AGENT'S JOB:** While tabbing, detect if any focused element is hidden behind a sticky header, cookie banner, chat widget, or other overlapping content.

#### Guideline 2.5 — Input Modalities

**2.5.5 Target Size (Minimum) (Level AA) [WCAG 2.2 new]** — Touch targets are at least 24x24 CSS pixels.

- What axe-core checks: Some partial checks on target size.
- **YOUR AGENT'S JOB:** Visually identify interactive elements (buttons, links, checkboxes) that appear too small to comfortably tap/click. Measure approximate visual size from screenshots.

**2.5.7 Dragging Movements (Level AA) [WCAG 2.2 new]** — Functionality using dragging can be operated with a single pointer without dragging.
**2.5.8 Target Size (Minimum) (Level AA) [WCAG 2.2 new]** — Pointer targets at least 24x24px with exceptions.

### 3.3 Principle 3: Understandable

Information and UI operation must be understandable.

#### Guideline 3.1 — Readable

**3.1.1 Language of Page (Level A)** — Default language of page is programmatically determinable.

- What axe-core checks: YES — checks for `lang` attribute on `<html>`.

**3.1.2 Language of Parts (Level AA)** — Language of passages/phrases is programmatically determinable.

- What axe-core checks: Cannot detect unmarked foreign-language passages.
- **YOUR AGENT'S JOB:** Visually scan page text. Detect passages in a language different from the page's declared language that lack a `lang` attribute.

#### Guideline 3.2 — Predictable

**3.2.1 On Focus (Level A)** — No unexpected context change when component receives focus.
**3.2.2 On Input (Level A)** — No unexpected context change when user changes a setting.

- **YOUR AGENT'S JOB:** Interact with form elements and detect if focusing or changing values causes unexpected navigation, popup, or layout shifts.

**3.2.6 Consistent Help (Level A) [WCAG 2.2 new]** — Help mechanisms appear in same relative order across pages.
**3.2.7 Visible Controls (Level AA)** — User interface controls needed to advance are visible.

#### Guideline 3.3 — Input Assistance

**3.3.1 Error Identification (Level A)** — Input errors are automatically detected and described in text.

- What axe-core checks: Cannot check this — it requires triggering errors and evaluating responses.
- **YOUR AGENT'S JOB:** Submit empty forms or invalid data via Computer Use. Observe the error messages. Check: Are errors identified in text (not just color)? Are error messages near the fields they relate to? Are they specific ("Enter a valid email" vs. "Error")?

**3.3.2 Labels or Instructions (Level A)** — Labels or instructions are provided for user input.

- What axe-core checks: Checks for `<label>` elements associated with inputs.
- What axe-core CANNOT check: Whether the label text is clear and helpful. Whether placeholder text is being used as the only label (disappears on focus).
- **YOUR AGENT'S JOB:** Look at forms. Flag inputs where placeholder text is the only visible "label" (since it disappears when the user starts typing). Evaluate whether label text is clear or ambiguous.

**3.3.3 Error Suggestion (Level AA)** — When an error is detected and suggestions are known, they're provided.
**3.3.7 Redundant Entry (Level A) [WCAG 2.2 new]** — Information previously entered is auto-populated or available for selection.
**3.3.8 Accessible Authentication (Minimum) (Level AA) [WCAG 2.2 new]** — Cognitive function tests not required for authentication unless alternative provided.

### 3.4 Principle 4: Robust

Content must be robust enough to be interpreted by a wide variety of user agents, including assistive technologies.

**4.1.2 Name, Role, Value (Level A)** — For all UI components, name and role are programmatically determinable.

- What axe-core checks: YES — strong checks for ARIA roles, names, states.
- What axe-core CANNOT check: Whether the programmatic name matches the visual label. A button might have `aria-label="Submit"` but visually displays "Send" — confusing for users who see one thing but whose assistive tech announces another.
- **YOUR AGENT'S JOB:** Compare what's visually displayed on interactive elements against their programmatic names (from DOM). Flag mismatches.

**4.1.3 Status Messages (Level AA)** — Status messages can be programmatically determined without receiving focus.

---

## 4. Architecture — The Hybrid Approach

### 4.1 Design Principle

We do NOT rebuild what axe-core already does well. We run axe-core as a programmatic baseline for code-level checks (the reliable 13%), then deploy Gemini visual agents for the judgment-dependent checks (the remaining 60-70% that require "eyes").

### 4.2 System Components

**Component 1: Navigator Agent**
Uses Gemini Computer Use model (`gemini-2.5-computer-use-preview`) via ADK with Playwright. Navigates the target website like a real user — visits pages, clicks links, fills forms, tabs through elements. Captures screenshots at each state. Drives the entire audit flow.

**Component 2: axe-core Scanner**
Runs axe-core programmatically in the Playwright browser context at each page state. Returns structured JSON of all code-level violations with WCAG criteria mapping, severity, and affected elements. This is the fast, cheap, proven baseline.

**Component 3: Visual Audit Agents (Gemini Vision)**
A set of specialized agents, each mapped to specific WCAG criteria that require visual judgment. Each agent receives a screenshot + DOM context and evaluates specific visual-contextual accessibility properties. These agents use Gemini's multimodal reasoning (screenshot + text prompt describing the criterion).

**Component 4: Report Generator**
Combines axe-core results and visual agent findings into a unified report. Uses Nano Banana (Gemini image generation) to create annotated screenshots highlighting issues. Generates a structured report with WCAG criterion references, severity ratings, and remediation guidance.

### 4.3 Agent Skill Definitions (Priority Order)

These are the visual audit skills, ordered by impact and feasibility for the hackathon. Each skill is a focused prompt/instruction set for a Gemini visual reasoning call.

**P0 — Must have for hackathon demo:**

1. **Alt Text Quality (1.1.1)** — Look at images, read their alt text, evaluate accuracy
2. **Color-Only Information (1.4.1)** — Detect patterns where color alone conveys meaning
3. **Focus Visibility (2.4.7)** — Tab through and verify visible focus indicators
4. **Keyboard Traps (2.1.2)** — Tab through and detect focus traps
5. **Link Purpose (2.4.4)** — Identify generic/repetitive link text
6. **Visual Label Matching (4.1.2)** — Compare visible labels vs. programmatic names
7. **Contrast Over Images (1.4.3)** — Catch text-over-image contrast failures axe misses
8. **Form Error Handling (3.3.1)** — Submit forms with invalid data, evaluate error messages

**P1 — Should have:**

9. **Images of Text (1.4.5)** — Detect text baked into images
10. **Heading Quality (2.4.6)** — Evaluate if heading text describes content
11. **Reading Order (1.3.2)** — Compare visual flow vs. DOM order
12. **Sensory Instructions (1.3.3)** — Detect instructions relying on shape/color/position
13. **Page Title Quality (2.4.2)** — Evaluate if title describes page content
14. **Focus Obscured (2.4.11)** — Detect focused elements hidden by overlays
15. **Target Size (2.5.8)** — Identify too-small interactive targets

**P2 — Nice to have:**

16. **Visual Structure Match (1.3.1)** — Compare visual layout vs. HTML structure
17. **Language of Parts (3.1.2)** — Detect unmarked foreign-language text
18. **Placeholder Labels (3.3.2)** — Flag placeholder-only form labels
19. **Focus Order Logic (2.4.3)** — Evaluate if tab order matches visual layout
20. **Context Change (3.2.1/3.2.2)** — Detect unexpected changes on focus/input

### 4.4 Data Flow

```
Input: Target URL
  │
  ├─→ Navigator Agent (Computer Use + Playwright)
  │     │
  │     ├─→ Visits page
  │     ├─→ Captures screenshot
  │     ├─→ Runs axe-core in-page → Code-level violations (JSON)
  │     ├─→ Sends screenshot + context to Visual Audit Agents
  │     │     ├─→ Alt Text Quality Agent
  │     │     ├─→ Color-Only Information Agent
  │     │     ├─→ Contrast Over Images Agent
  │     │     ├─→ ... (parallel where possible)
  │     │     └─→ Returns visual findings per criterion
  │     │
  │     ├─→ Tabs through interactive elements (keyboard audit)
  │     │     ├─→ Focus Visibility Agent (screenshots of each focus state)
  │     │     ├─→ Keyboard Trap Agent
  │     │     ├─→ Focus Order Agent
  │     │     └─→ Focus Obscured Agent
  │     │
  │     ├─→ Fills and submits forms (form audit)
  │     │     ├─→ Error Handling Agent
  │     │     ├─→ Placeholder Label Agent
  │     │     └─→ Context Change Agent
  │     │
  │     └─→ Follows links to additional pages (crawl scope configurable)
  │
  └─→ Report Generator
        ├─→ Merges axe-core results + visual agent findings
        ├─→ Deduplicates (if axe caught it, don't double-report)
        ├─→ Assigns severity (Critical / Serious / Moderate / Minor)
        ├─→ Generates annotated screenshots via Nano Banana
        └─→ Outputs final report (HTML/JSON)
```

### 4.5 Tech Stack

- **Agent Framework:** Google ADK (Agent Development Kit) with Python
- **Browser Automation:** Playwright (required for Computer Use model)
- **Computer Use Model:** `gemini-2.5-computer-use-preview-10-2025` via ADK ComputerUseToolset
- **Visual Reasoning:** `gemini-2.5-flash` or `gemini-3-pro` for screenshot analysis
- **Image Generation:** Nano Banana (`gemini-2.5-flash-image` or `gemini-3.1-flash-image-preview`) for annotated report screenshots
- **Code Scanner:** axe-core npm package, injected via Playwright `page.evaluate()`
- **Backend:** Python FastAPI on Google Cloud Run
- **Storage:** Google Cloud Storage for screenshots and reports
- **Optional Voice (stretch):** Gemini Live API for voice narration of report
- **IaC (bonus points):** Terraform or Cloud Build scripts for automated deployment

### 4.6 ADK Agent Hierarchy

```
Root Agent (Orchestrator)
  ├─→ NavigatorAgent (Computer Use model)
  │     Uses: ComputerUseToolset with Playwright
  │     Responsibility: Navigate site, capture states, drive interaction
  │
  ├─→ CodeAuditAgent (tool-based, not LLM)
  │     Uses: Custom tool that runs axe-core via Playwright
  │     Responsibility: Return structured axe-core results
  │
  ├─→ VisualAuditAgent (Gemini vision model)
  │     Uses: Screenshot analysis with specific WCAG criterion prompts
  │     Responsibility: Evaluate visual-contextual accessibility issues
  │     Sub-skills loaded based on page content (has images? run alt text check, etc.)
  │
  └─→ ReportAgent (Gemini + Nano Banana)
        Uses: Text generation + image generation
        Responsibility: Synthesize findings into report with annotated screenshots
```

---

## 5. Key Technical Details

### 5.1 Running axe-core via Playwright

axe-core can be injected into any page via Playwright's `page.evaluate()`. The npm package `@axe-core/playwright` provides a clean API:

```javascript
// Conceptual — inject axe and run
const { AxeBuilder } = require('@axe-core/playwright');
const results = await new AxeBuilder({ page })
  .withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
  .analyze();
// results.violations = array of violations with WCAG mapping
```

Each violation includes: rule ID, WCAG criteria tags, impact (critical/serious/moderate/minor), affected HTML elements with selectors, and remediation help text.

### 5.2 Computer Use Model Integration

The Gemini Computer Use model works via a perception-action loop:

1. You provide a goal and initial screenshot
2. Model returns an action (click, type, scroll, keypress) with coordinates
3. Your code executes the action via Playwright
4. You capture a new screenshot and send it back
5. Repeat until goal is complete

ADK abstracts this via `ComputerUseToolset` with Playwright integration. The model supports 13 predefined actions: click, type, scroll, keypress, navigate, wait, drag, screenshot, etc.

### 5.3 Visual Audit Prompt Structure

Each visual audit skill should follow this pattern:

```
You are a WCAG 2.2 accessibility auditor. You are looking at a screenshot of a web page.

WCAG Criterion: [specific criterion number and name]
Requirement: [plain-language description of what this criterion requires]

Analyze this screenshot and identify any violations of this criterion.

For each violation found, provide:
- Description of the issue
- Location on the page (describe where visually)
- Severity (Critical / Serious / Moderate / Minor)
- WCAG criterion reference
- Suggested remediation

If no violations are found, state that the page passes this criterion.

[Additional context: DOM snippet of relevant elements, axe-core results for cross-reference]
```

### 5.4 Annotated Screenshot Generation

Use Nano Banana to generate annotated versions of page screenshots. The prompt would describe where to draw highlights, circles, or arrows pointing to problem areas, with text labels explaining each issue. This creates visually compelling report artifacts.

Alternative approach if image editing proves unreliable: use Playwright to inject CSS overlays (colored borders, labels) onto the actual page before screenshotting. This is more deterministic.

---

## 6. Scope Control for Hackathon

### 6.1 MVP (Must ship)

- Single-page audit (user provides one URL)
- axe-core baseline scan
- 4-5 visual audit skills (P0 items: alt text, color-only, focus visibility, link purpose, contrast over images)
- Unified report with findings from both layers
- Deployed on Cloud Run
- Working demo in under 4-minute video

### 6.2 Nice to Have

- Multi-page crawl (follow links, audit N pages)
- Full P0 + P1 skill set
- Annotated screenshots via Nano Banana
- Voice narration of report via Live API
- Terraform deployment scripts (bonus points)
- Comparison mode: show Lighthouse score vs. our findings

### 6.3 Out of Scope

- Real-time / live auditing (we generate a report, not a live dashboard)
- Mobile app testing (browser-only)
- PDF accessibility testing
- Full AAA conformance checking

---

## 7. Demo Video Strategy

The 4-minute demo video is worth 30% of the score. Script it.

**Structure:**

1. (0:00-0:30) THE PROBLEM — "Automated accessibility tools like Lighthouse only catch 30-40% of WCAG issues. The rest requires a human auditor at $150/hour. We're closing that gap."
2. (0:30-1:00) THE SOLUTION — "AccessVision is an AI agent that actually LOOKS at your website the way a user does, and catches the accessibility problems that code scanners structurally cannot."
3. (1:00-3:00) THE DEMO — Show the agent navigating a real website with known accessibility issues. Show it catching things Lighthouse missed. Show the annotated report. Side-by-side: Lighthouse says 95/100, our agent finds 12 additional issues.
4. (3:00-3:30) ARCHITECTURE — Quick flash of the architecture diagram.
5. (3:30-4:00) IMPACT — "1 billion people with disabilities. 4,000+ lawsuits per year. 70% of WCAG criteria require human judgment. Until now."

---

## 8. Reference Links

- WCAG 2.2 Specification: https://www.w3.org/TR/WCAG22/
- WCAG 2.2 Quick Reference (filterable checklist): https://www.w3.org/WAI/WCAG22/quickref/
- ACT Rules (machine-testable rules): https://www.w3.org/WAI/standards-guidelines/act/rules/
- Understanding WCAG 2.2: https://www.w3.org/WAI/WCAG22/Understanding/
- axe-core GitHub: https://github.com/dequelabs/axe-core
- axe-core Rule Descriptions: https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md
- ADK Documentation: https://google.github.io/adk-docs/
- ADK Computer Use Integration: https://google.github.io/adk-docs/integrations/computer-use/
- ADK Streaming (Live API): https://google.github.io/adk-docs/streaming/dev-guide/part1/
- Nano Banana Image Generation: https://ai.google.dev/gemini-api/docs/image-generation
- Gemini Computer Use Model: https://ai.google.dev/gemini-api/docs/computer-use
- Gemini Live API: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/live-api
- Springer Paper (LLM accessibility testing): https://link.springer.com/article/10.1007/s10209-024-01108-z
- Manuel Matuzovic's "Perfect Lighthouse Score" experiment: https://www.matuzo.at/blog/building-the-most-inaccessible-site-possible-with-a-perfect-lighthouse-score/
- Accessible.org scan coverage analysis: https://accessible.org/automated-scans-wcag/
- Hackathon page: https://geminiliveagentchallenge.devpost.com/
- Hackathon resources: https://geminiliveagentchallenge.devpost.com/resources
