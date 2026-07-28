# Visual System

Use this reference when establishing or revising the admin platform's shared look.

## Product Feel

Aim for restrained, durable software with the visual feel of the supplied dashboard reference:

- Light, polished SaaS clarity: pale app background, white cards, subtle dividers, readable density, visible focus and selected states.
- Modern dashboard polish: soft but minimal shadows, calm accent colors, clean iconography, rich states.
- Enterprise utility: compact spacing, predictable controls, fast scanning, strong tables and forms.

## Layout Tokens

- App background: near-white or cool gray, for example `#f6f8fb`, `#f7f8fa`, or `#f8fafc`.
- Sidebar/topbar background: white or very pale blue-gray. Avoid dark global chrome unless the existing brand requires it.
- Surface: white with a 1px border and a soft shadow. Use stronger shadows only on raised dashboard cards.
- Border: low-contrast neutral such as `#d9e2ef`, `#e5e7eb`, or `#e6ebf1`.
- Text: strong neutral navy/charcoal for primary, muted gray-blue for secondary.
- Radius: 10-14px for dashboard cards/panels to match the reference; 8-10px for buttons, inputs, table controls, and nav items.
- Spacing: base on 4px increments. Typical page padding is 20-24px desktop, 12-16px mobile.
- Density: compact controls are valid for admin workflows. Avoid oversized hero typography inside panels and avoid cards that exist only to describe the page.

## Color

Use a neutral base with a small set of semantic accents:

- Primary/action: blue or indigo, but not everywhere.
- Success: green.
- Warning: amber/orange.
- Danger/risk: red.
- Info/processing: blue/cyan.
- Neutral/draft/disabled: gray.

Rules:

- Do not let one hue family dominate the entire interface.
- Use color to encode status, priority, or action. Use layout and typography for structure.
- Pair colored fills with text and icons so status remains understandable without color alone.
- Use tinted backgrounds for badges and alerts, not large saturated blocks.

## Typography

- Use the existing app font unless it is clearly broken.
- Use a fixed type scale. Recommended desktop scale: page title 22-24px, page subtitle 13-14px, section title 16-18px, panel/card title 14-16px, body/table text 13-14px, metadata 12-13px, badge text 12px.
- KPI numbers may be 28-36px only on true dashboard/workbench pages where the metric is the primary content. On ordinary management/list/detail pages, numbers inside cards should usually be 20-28px and must not visually exceed the page title.
- Card labels should be smaller than card numbers, and card titles should not be larger than the page title.
- Section headings must step down from the page title. A section title should never compete with the page title unless it is the only title on the page.
- Avoid negative letter spacing and viewport-scaled type.
- Keep labels short. In Chinese UI, prefer concise nouns and verbs over explanatory sentences.

## Page Hierarchy

- Each page should have one primary title area. It may include breadcrumb, title, concise subtitle/context, and real actions.
- The app title bar must be single-line at the title level. It can have breadcrumb plus one title, but it must not become a stacked title/subtitle tile.
- If breadcrumb or module context is already present in the shell header, table/list pages should usually omit an in-page title entirely.
- Do not stack a shell header title, then a duplicate page title, then a large intro card title, then card titles before useful content.
- If two adjacent text blocks communicate the same page identity, merge them or delete the lower-value one.
- On ordinary management pages, prefer direct content after the page header: toolbar, filters, table, form, or grouped panels.
- KPI/stat cards belong only when they help the user make a decision on that page. Otherwise remove them or fold the count into the header/filter area.
- Preserve visual calm: fewer modules with sharper purpose beats more cards with explanatory copy.

## Shell

- Use a light sidebar like the reference: product mark/title at the top, grouped navigation below, selected item with pale blue fill plus left accent.
- Sidebar width usually lands between 220-260px desktop.
- Topbar height usually lands between 56-72px.
- Keep the header bar single-line: breadcrumb or module name on the left, real actions or user/session controls on the right.
- Do not allow breadcrumb, module name, or user area to wrap into a second line unless the user explicitly asks for a multi-line header.
- Navigation selected state should be a subtle filled row, left accent, and strong text/icon color; avoid heavy gradients.
- Navigation indentation must follow hierarchy from left to right. First-level nav items must have the smallest left inset; second-level items must be indented farther right; third-level items, if present, must be farther right again.
- Never let parent items appear more indented than their children. This includes icon x-position, text x-position, selected background start, hover background start, and left accent position.
- In common 220-260px sidebars, use a stable pattern such as parent item `padding-left: 24px` and child item `padding-left: 48px`; adjust values to the component library, but preserve the ordering.
- Parent section labels should use stronger weight or section spacing, not extra right indentation. Child items may be smaller or lighter, but their indentation must remain visually subordinate.
- The shell must use independent scroll containers: root/body fixed to viewport height, sidebar navigation scrolls within the sidebar, and main content scrolls within its own content area.
- Do not allow both the browser body and the main content to scroll at the same time.
- Implement the shell as a fixed-height flex/grid system: root `height: 100vh; overflow: hidden`; sidebar `height: 100vh; display: flex; flex-direction: column`; sidebar nav `min-height: 0; overflow-y: auto`; main column `min-height: 0; overflow: hidden`; main content `min-height: 0; overflow-y: auto`.
- Avoid nested vertical scroll regions inside ordinary page panels unless the user is interacting with a table body, drawer, modal, code block, or virtualized list.

## Panels And Cards

- Use panels for grouped work areas, repeated cards for repeated entities, and metric tiles for KPIs.
- Do not nest card inside card. If a panel needs substructure, use sections, dividers, grids, or definition rows.
- Panel headers should contain title, optional count/status, and right-aligned actions.
- Shadows should be subtle: a small ambient shadow or none. Let borders do most separation.
- Avoid using a large "intro card" on every page. If the page title already explains the surface, remove redundant title/subtitle tiles.
- Do not render list-tile rows solely to explain a module. Use actual data rows, compact cards with real controls, or an empty state.
- Ordinary management pages should usually be: shell header, optional toolbar, content panel/table. Do not force the dashboard's KPI/right-rail composition onto them.
- When a page begins with repeated titles plus stat cards, first try to merge the title/subtitle into the shell header and delete the intro card; then keep only stats that affect filtering, prioritization, or action.
- For table/list pages, the default layout is: single-line page title, filter area, table/list. Add anything else only with explicit design justification from the user or product requirements.

## States

Every primitive should have:

- Hover state that does not shift layout.
- Focus-visible ring for keyboard navigation.
- Active/selected state.
- Disabled state with clear opacity and cursor.
- Loading state that preserves dimensions.
- Empty state with one clear next action when applicable.
- Error state with actionable recovery text.

## Anti-Patterns

- Full-screen gradients for ordinary admin pages.
- Decorative blobs/orbs, glass cards, large background illustrations, or marketing sections.
- Raw component-library defaults with inconsistent radius, color, and typography.
- Thin gray text for important data.
- Oversized metric cards that push tables and tasks below the fold.
- Decorative or fake operational labels unless backed by actual data.
- Repeating title/subtitle pairs inside every card when the content itself is already labeled.
- Card numbers or labels that are larger than the page title on non-dashboard pages.
