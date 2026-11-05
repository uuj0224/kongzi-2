---
name: 孔子问答
description: 现代东方文化展览中的经典问答与原文阅读
colors:
  primary: "#963f30"
  primary-deep: "#773023"
  primary-soft: "#f2e7e2"
  paper: "#f8f9f6"
  surface: "#ffffff"
  ink: "#24352d"
  muted: "#606b62"
  line: "#dfe4dc"
  hover: "#e6e7dc"
  success: "#526343"
  warning: "#895020"
  chapter-surface: "#eef1eb"
typography:
  display:
    fontFamily: "'Exhibit Serif', 'Songti SC', STSong, SimSun, serif"
    fontSize: "56px"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "3px"
  headline:
    fontFamily: "'Exhibit Serif', 'Songti SC', STSong, SimSun, serif"
    fontSize: "36px"
    fontWeight: 500
    lineHeight: 1.5
  question:
    fontFamily: "system-ui, 'PingFang SC', sans-serif"
    fontSize: "19px"
    fontWeight: 500
    lineHeight: 1.8
  answer:
    fontFamily: "'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: "16px"
    lineHeight: 2
  original:
    fontFamily: "'Exhibit Serif', 'Songti SC', STSong, SimSun, serif"
    fontSize: "21px"
    lineHeight: 2.05
  label:
    fontFamily: "'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: "12px"
rounded:
  base: "6px"
  composer: "8px"
  hero-composer: "5px"
  compact: "4px"
  citation: "3px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.base}"
    height: "36px"
    padding: "0 16px"
  button-text:
    textColor: "{colors.primary}"
    padding: "5px 0"
  answer-status:
    textColor: "{colors.success}"
    backgroundColor: "#e9ecdf"
    rounded: "{rounded.compact}"
    padding: "4px 8px"
  reader:
    backgroundColor: "{colors.surface}"
  search:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    height: "40px"
    padding: "0 13px"
    rounded: "{rounded.base}"
---

# Design System: 孔子问答

## Overview

**Creative North Star: "现代东方文化展览"**

The confirmed visual world pairs a continuous ink-and-color handscroll with precise contemporary Chinese typography. Cool paper, green-black ink and a restrained cinnabar accent connect the exhibition entrance to the quieter reading surfaces.

The presentation is spacious at the entrance and denser around answers and source passages. Cultural character comes from the complete artwork and typography. The user explicitly rejected the former permanent application sidebar and isolated floating character portrait; the chapter directory remains a reading aid within the library. AI imagery and modern interpretations carry visible labels.

**Key Characteristics:**
- Complete artwork with an integrated question form.
- Serif display and original passages; system sans for controls and answers.
- Flat reading surfaces, thin dividers and restrained accent states.
- Desktop layout with visible keyboard focus and reduced-motion support.

## Colors

The palette combines cool paper and green-black text with one cinnabar action accent. Hex values in the frontmatter record the effective stylesheet tokens after the exhibition overrides.

### Primary
- **Cinnabar — primary:** submission, links, active navigation underline, selected chapter text and inline citations.
- **Deep cinnabar — primary-deep:** the darker text-button hover treatment and Element Plus primary dark token.
- **Pale cinnabar — primary-soft:** small inline citation backgrounds.

### Neutral
- **Cool paper — paper:** the application canvas and drawer background.
- **White surface — surface:** header, footer and reading container.
- **Green-black ink — ink:** primary text and active top navigation.
- **Muted green-gray — muted:** metadata, guidance and inactive controls.
- **Pale green-gray — line:** section rules, passage dividers and reading-container border.
- **Soft olive — hover:** existing history-row hover treatment.
- **Pale chapter ground — chapter-surface:** chapter navigation within the reader.

### Status
- **Muted olive — success:** ready indicator and supported-answer status text.
- **Warm umber — warning:** insufficient-evidence or citation-warning status text.

## Typography

**Display Font:** self-hosted Noto Serif SC subset, registered as `Exhibit Serif` at weight (500), served from `/fonts/exhibit-serif.ttf` using `format('truetype')`, with Songti SC, STSong, SimSun and serif fallbacks. The font face uses `font-display: swap`.

**Body Font:** PingFang SC, Microsoft YaHei, system-ui and sans-serif. Questions explicitly begin with system-ui. There is no separate monospace system; keyboard hints inherit the surrounding font.

**Character:** serif headlines and source text provide a literary register; plain sans-serif controls and generated answers support scanning and extended reading.

### Hierarchy
- **Display:** the frontmatter display role is used on the entrance heading. At viewport widths of at least (1600px), it becomes (64px).
- **Headline:** the library heading uses the headline role; discovery headings use (27px), weight (500), line height (1.5).
- **Question:** the question role distinguishes the user's prompt above the answer.
- **Answer:** the answer role preserves whitespace, wraps long content and limits text to (75ch).
- **Original:** the original role applies within the library reader. Source-dialog originals retain the base (20px) size and line height (1.95).
- **Label:** metadata typically uses (11–13px); the label role records the common middle step. Numerals in counts, timings and pagination use tabular figures.

## Layout

Desktop only: the body has a minimum width of (1100px). There is no mobile layout in the implemented system.

The white header is (88px) high with horizontal padding of (4%). It contains the brand, two top-level destinations, service status and the history trigger. History opens in a (360px) drawer. The application's main area has no permanent navigation rail.

The entrance container is (94%) wide and capped at (1600px). Its handscroll artwork fills a hero of at least (588px), using `object-fit: cover` and an object position of (60% center). The copy and composer occupy (49%) width with a cap of (650px). At widths of at least (1600px), the hero minimum height becomes (650px). Discovery uses two columns in a (1 : 1.3) ratio with a (70px) gap.

Answers occupy a centered container capped at (960px), including horizontal padding of (40px). The library container is capped at (1360px), with padding of (44px 48px). Its reader splits into a (180px) chapter directory and a flexible text column. The directory sticks at the viewport top with a maximum height of (90vh). Reader-body padding is (26px 36px 30px).

Spacing is specified per component; the code defines no shared spacing token scale. Dividers separate passages and conversation turns rather than enclosing every item in a card.

## Elevation & Depth

Application-defined surfaces are flat: the stylesheet declares no custom box-shadow tokens. Paper, white and pale chapter backgrounds, thin borders and whitespace establish layers. Element Plus provides the drawer and source-dialog overlay behavior; the application does not define a separate elevation scale for them.

## Shapes

Corners remain slight and functional. The frontmatter records the base control radius, the regular and entrance composer radii, compact status and chapter-control corners, and inline-citation corners. The handscroll and reading container have square outer silhouettes. The brand seal uses a compact corner and an inset outline rather than a shadow.

## Components

### Buttons

Compact solid submission and quiet text actions.

- **Primary:** the composer submit button uses the primary color, base radius, and the height and padding in the component token. Element Plus supplies loading, disabled and primary hover states.
- **Text:** transparent background, cinnabar text and a small inline icon gap of (7px). Hover darkens the text and adds an underline with offset (4px).
- **Focus:** keyboard focus uses a (2px) primary outline with offset (4px).

### Cards / Containers

The main reader is a white bordered container, split by tone between the chapter directory and passages. Passage items are flat rows with a bottom divider and vertical padding of (24px). Project-prepared interpretation appears in a pale olive note with padding of (14px 16px), compact corners and a visible label.

### Inputs / Fields

The regular composer is a lightly bordered paper surface with padding of (18px 20px 15px). The entrance version uses warmer near-white fill, the hero-composer radius and padding of (17px 18px 13px). Focus changes the enclosing border to primary. The textarea uses (15px) text at line height (1.8), permits vertical resizing and caps height at (240px); its normal minimum height is (68px), reduced to (56px) on the entrance.

The search field uses its component token, a thin muted green border and a gap of (10px). Focus adds the primary border and a (2px) outline with offset (2px). Busy or locked question input is disabled, and errors appear above the composer with an alert role. Enter submits; Shift+Enter inserts a newline. The question limit is (1200) characters.

### Navigation

Top navigation uses transparent buttons, a horizontal gap of (34px), and a primary underline of (3px) on the active destination. The active label gains weight (600). History is available from the header and renders as full-width divided rows in the drawer.

Library book selectors are horizontal, flat tabs with a selected bottom rule of (2px). The chapter directory uses compact text rows; its selected chapter has cinnabar text on a warm white background. This local directory supports reading and is distinct from application navigation.

### Answer Status and Citations

Answer status uses the success token on a pale olive fill; warning states use warning text on a pale warm fill. The text states the condition, so color is accompanied by meaning. Inline citation controls are small superscript numbers with a pale cinnabar background; they open the same source dialog as the citation list. The dialog is (680px) wide and separates original text, project interpretation and source attribution.

### Motion and Accessibility

Hover transitions use (160ms ease-out). Suggestion arrows move right by (3px). Pending-answer feedback pulses over (1.5s ease-in-out). Reduced-motion preference removes animation and transitions and switches conversation scrolling away from smooth behavior. Preserve visible focus, field labels, status text, source labels and the distinction between original text and modern interpretation.

### Reading and Retrieval Refinements

History rows include the full first-question title (visually limited to two lines, with the full title available through the native title), local date and time, question count, and a two-line preview of the latest answer. Search filters the question title and preview. The drawer stays (360px) wide, and refresh errors appear inside it with retry.

The library requests ten passages per page. Result range and page controls appear above the list as well as below it; changing page brings the results heading into view. Chapter search filters the local directory without replacing the selected reading scope. Project interpretations use native details/summary disclosure, initially closed, with an option to expand all interpretations. Original passages keep their existing type and measure.

Examples and passage invitations prepare an editable question before submission. Existing text is retained; content exceeding the question limit is rejected with a visible explanation. Drafts are held separately for each open conversation and the new-question surface during the current page session. They are not persisted across reloads. A “停止等待” control aborts the browser's wait and preserves the question; its status message states that backend generation may still complete and become available in history.

Answers render plain-text paragraphs and recognized section headings without rendering model HTML. New generation instructions request content-appropriate headings and adjacent citations. Existing answers retain their wording; explicit modern-interpretation and limitation labels may become section boundaries. Citation controls have descriptive source names. Current navigation and chapter controls expose current-state semantics, and connection changes have status semantics.

The shared composer has one compact explanation of independent questions and a native expandable guide for asking and checking sources. Source dialogs show retrieval progress and local retry while retaining the available passage. The source link is labelled “查看原始资料” with fixed-version detail beneath it. Element Plus uses the installed Chinese locale, including dialog and drawer close controls.

## Do's and Don'ts

### Do:
- **Do** use the effective exhibition palette and font stacks recorded in the frontmatter.
- **Do** keep generated answers readable within the established answer measure and label original passages separately from project interpretation.
- **Do** preserve keyboard focus and reduced-motion behavior.
- **Do** identify AI-created artwork and the simulated character interpretation.

### Don't:
- **Don't** restore the rejected permanent application sidebar or isolated floating portrait.
- **Don't** let character artwork overlap reading text.
- **Don't** treat the current desktop implementation as a mobile-responsive design.
- **Don't** add a spacing, shadow or color scale that is absent from the source and describe it as an existing token.
