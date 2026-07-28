# Visual System

Use this reference when establishing or revising the admin platform's shared look.

## Product Feel

Aim for restrained, durable, tool-first software with the visual feel of the supplied reference:

- Light platform shell: near-white canvas, white work surfaces, hairline dividers, and almost-flat elevation.
- Compact working density: direct page headers, 14px body text, short metadata, line icons, and 32-36px controls.
- Deliberate interaction: quiet hover fills, clear active states, icon buttons for secondary commands, and no motion that shifts layout.
- Enterprise utility: predictable controls, fast scanning, dense tables or media grids, and state colors used only for meaningful data.

## Layout Tokens

- App background: warm-neutral or cool-neutral near-white such as `#fafafa`, `#f8fafc`, or the existing neutral canvas.
- Sidebar/topbar background: white. Separate both with `1px` low-contrast borders; avoid dark global chrome unless the existing brand requires it.
- Surface: white. Use `1px solid #e5e7eb`-like borders for ordinary separation. Use `box-shadow: 0 1px 2px rgb(0 0 0 / 0.06)` only for raised panels, menus, and overlays.
- Border: neutral gray such as `#e5e7eb`, `#e6e8eb`, or local equivalent. Do not use blue-tinted borders on every surface.
- Text: near-black/charcoal for primary, mid-gray for metadata, and muted gray for placeholders. Preserve readable contrast for labels and data.
- Radius: 4-6px for cards, panels, inputs, buttons, menu rows, and tabs. Use circles only for avatars, counters, and icon wells.
- Spacing: base on 4px increments. Use 24px desktop page padding where available, 16px on compact desktop/tablet, and 12px on mobile.
- Density: use 32px compact and 36px default controls. Keep icon buttons square with the same dimension. Avoid oversized hero typography and cards that only describe the page.

## Color

Use a neutral base with a small set of semantic accents:

- Primary/action: use the product's existing blue, indigo, or black action color sparingly.
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
- Keep ordinary navigation, panels, tables, and controls neutral. Do not color every border, header, or icon with the brand accent.

## Typography

- Use the existing app font unless it is clearly broken. Prefer a system sans stack with reliable Chinese glyph coverage for Chinese enterprise applications.
- Use a fixed type scale: shell/nav/body/table text `14px`; metadata, helper text, badge text, and counts `12-13px`; panel title `14-16px`; section title `16-18px`; page title `20-24px` with `600-700` weight. Use `16px` body text only for prose that users must read closely.
- Keep page title line-height around `28-32px`; body/table line-height around `20px`; metadata around `18px`. Do not scale text with viewport width or use negative tracking.
- KPI numbers may be `24-32px` only on true dashboard/workbench pages where the metric is the primary content. On ordinary management/list/detail pages, numbers inside cards should usually be `18-24px` and must not visually exceed the page title.
- Card labels should be smaller than card numbers, and card titles should not be larger than the page title.
- Section headings must step down from the page title. A section title should never compete with the page title unless it is the only title on the page.
- Keep labels short. In Chinese UI, prefer concise nouns and verbs over explanatory sentences.

## Page Hierarchy

- Give each page one primary title area. It may include breadcrumb, title, concise subtitle/context, and real actions.
- Keep the app title bar single-line. It can have breadcrumb plus one title, but it must not become a stacked title/subtitle tile.
- If breadcrumb or module context is already present in the shell header, table/list pages should usually omit an in-page title entirely.
- Do not stack a shell header title, then a duplicate page title, then a large intro card title, then card titles before useful content.
- If two adjacent text blocks communicate the same page identity, merge them or delete the lower-value one.
- On ordinary management pages, prefer direct content after the page header: toolbar, filters, table, form, or grouped panels.
- Keep page-header actions compact and aligned. Use one primary text button; group secondary commands into familiar icon buttons.
- KPI/stat cards belong only when they help the user make a decision on that page. Otherwise remove them or fold the count into the header/filter area.
- Preserve visual calm: fewer modules with sharper purpose beats more cards with explanatory copy.

## Shell

- Use a light sidebar like the reference: product mark/title at the top, grouped navigation below, compact utility actions at the bottom, and selected item with a quiet neutral fill plus stronger text/icon color.
- Use a CSS variable or shared layout state for sidebar width. Default desktop sizes are `240-256px` expanded and `56-64px` collapsed. Avoid per-page width overrides.
- Use a `48-56px` topbar. Keep it single-line and align the sidebar toggle with the breadcrumb/module context.
- Keep the header bar single-line: breadcrumb or module name on the left, real actions or user/session controls on the right.
- Do not allow breadcrumb, module name, or user area to wrap into a second line unless the user explicitly asks for a multi-line header.
- Use 32-36px navigation rows with 8-12px vertical gap between unrelated groups. Keep group labels small and muted; do not use large all-caps section labels.
- Navigation selected state should use a subtle filled row and strong text/icon color. Add a thin accent line only if it improves wayfinding; avoid heavy gradients, saturated fills, and large shadows.
- On hover, add a light neutral fill or slightly stronger icon/text color. Do not translate items, widen borders, or shift neighboring rows.
- Navigation indentation must follow hierarchy from left to right. First-level nav items must have the smallest left inset; second-level items must be indented farther right; third-level items, if present, must be farther right again.
- Never let parent items appear more indented than their children. This includes icon x-position, text x-position, selected background start, hover background start, and left accent position.
- In common expanded sidebars, use a stable pattern such as parent item `padding-left: 12px` and child item `padding-left: 32px`; adjust to the component library, but preserve ordering and icon alignment.
- Parent section labels should use stronger weight or section spacing, not extra right indentation. Child items may be smaller or lighter, but their indentation must remain visually subordinate.
- Persist the user's desktop expansion preference using the existing layout/store mechanism. Do not reset it on route changes or normal refreshes when persistence is already available.
- In collapsed mode, center first-level icons in a stable square hit area, retain a visible active indicator, and expose a tooltip with the label. Hide section labels, child rows, and chevrons from the rail; open an anchored flyout for child routes only when the current component library already supports it accessibly.
- Do not animate width if it causes unreadable reflow. When animation is suitable, keep it brief (`150-200ms`), respect reduced-motion preferences, and reserve the final layout width throughout the transition.
- The shell must use independent scroll containers: root/body fixed to viewport height, sidebar navigation scrolls within the sidebar, and main content scrolls within its own content area.
- Do not allow both the browser body and the main content to scroll at the same time.
- Implement the shell as a fixed-height flex/grid system: root `height: 100vh; overflow: hidden`; sidebar `height: 100vh; display: flex; flex-direction: column`; sidebar nav `min-height: 0; overflow-y: auto`; main column `min-height: 0; overflow: hidden`; main content `min-height: 0; overflow-y: auto`.
- Avoid nested vertical scroll regions inside ordinary page panels unless the user is interacting with a table body, drawer, modal, code block, or virtualized list.

## Panels And Cards

- Use panels for grouped work areas, repeated cards for repeated entities, and metric tiles for KPIs.
- Do not nest card inside card. If a panel needs substructure, use sections, dividers, grids, or definition rows.
- Use 4-6px corners, 16-20px panel padding, and 12-16px compact card padding. Reduce to 12-16px page-local padding when information density matters.
- Panel headers should contain title, optional count/status, and right-aligned actions. Keep header controls on the same baseline and use a divider only when it improves scanability.
- Shadows should be subtle: a small ambient shadow or none. Let borders do most separation. Do not use a larger shadow simply to imply clickability.
- Keep static panels static. Give navigation cards, entity previews, and actionable metric tiles a hover fill/border treatment plus pointer cursor; do not make a visual lift or translate effect the default.
- Preserve panel dimensions during loading. Use skeletons that match the final title, value, and row/image proportions instead of replacing the panel with spinner-only space.
- Avoid using a large intro card on every page. If the page title already explains the surface, remove redundant title/subtitle tiles.
- Do not render list-tile rows solely to explain a module. Use actual data rows, compact cards with real controls, or an empty state.
- Ordinary management pages should usually be: shell header, optional toolbar, content panel/table. Do not force the dashboard's KPI/right-rail composition onto them.
- When a page begins with repeated titles plus stat cards, first try to merge the title/subtitle into the shell header and delete the intro card; then keep only stats that affect filtering, prioritization, or action.
- For table/list pages, the default layout is: single-line page title, filter area, table/list. Add anything else only with explicit design justification from the user or product requirements.

## Buttons And Commands

- Use a dark or brand-primary filled button only for the local primary command. Keep its label concise and pair an icon only when it improves recognition.
- Use bordered or text buttons for secondary actions. Use square icon buttons for familiar, secondary commands such as refresh, export, settings, display mode, favorite, or delete.
- Give every icon-only control an accessible name and tooltip. Group related icon actions with consistent gap and sizing; do not replace a destructive action label with an ambiguous icon when consequence is unclear.
- Keep command bars single-line on desktop. On narrow layouts, preserve the primary action and move secondary actions into an existing overflow/menu pattern rather than wrapping each control to a new row.

## States

Every primitive should have:

- Hover state that changes fill, border tone, or foreground without shifting layout.
- Focus-visible ring with an offset or high-contrast outline that remains visible against white surfaces.
- Active/selected state that remains distinguishable from hover after pointer exit.
- Disabled state with clear opacity, disabled cursor, and no active hover affordance.
- Loading state that preserves dimensions and prevents duplicate command submission.
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
- A collapsed sidebar that exposes unlabeled controls, clips an active state, or changes navigation hierarchy.
