---
name: admin-platform-design
description: Design and refactor compact, tool-first backend/admin platform frontends for SaaS, enterprise tools, data-management systems, review workflows, operations consoles, and AI/data platforms. Use when Codex needs to improve or build an app shell, expandable sidebar, topbar, dashboard/workbench, table/list or media grid, detail page, settings, forms, drawers/modals, navigation, tabs, filters, metrics, status indicators, or shared visual system while preserving existing interactions and applying a restrained Ultralytics-like reference style.
---

# Admin Platform Design

## Core Goal

Create admin interfaces that feel like real production software: compact, precise, scannable, and task-first. Apply the supplied reference's light shell, narrow topbar, white work surfaces, icon-led commands, compact metadata, and practical table/media-grid patterns. Transfer hierarchy and interaction behavior, not its product copy, product-specific modules, or bright accent colors.

## Workflow

1. Audit the existing app before changing UI:
   - Identify framework, component library, routing, layout primitives, CSS/token system, icon library, chart library, and current data states.
   - Find the key surfaces: login, shell/navigation, dashboard/workbench, list/table/grid, detail page, form/drawer/modal, empty/loading/error states.
   - Keep domain language and workflows. Replace weak visual structure, not the product model.

2. Preserve behavior and prune noise:
   - Do not change API contracts, route semantics, query parameters, form submission flows, permissions, or backend interaction behavior unless the user explicitly asks.
   - Remove redundant visual components when they only explain what the page is, duplicate navigation labels, or add fake status/context.
   - Collapse repeated title/subtitle/title-card chains into one clear page header plus direct content.
   - Treat table/list pages as strict utility surfaces by default: keep only filter controls and the primary table/list unless the user provides an explicit design reason for additional modules.
   - If the app shell already shows breadcrumb/module context, do not repeat the same page title inside the page body on table/list pages.
   - Do not add new business concepts, workflow states, promotional/help cards, readiness badges, shortcuts, search boxes, settings buttons, user menus, or text labels that are not already represented by the app's data, routes, auth model, or product requirements.

3. Establish a restrained platform language:
   - Use [visual-system.md](references/visual-system.md) for color, spacing, radius, shadows, typography, states, sidebar behavior, buttons, and density.
   - Use [component-strategy.md](references/component-strategy.md) to choose Tailwind/shadcn-style visual primitives versus Ant Design business components by scenario.
   - Match the reference's compact tool feel: 14px working text, 20-24px page title, clear icon actions, low-contrast chrome, and direct content.
   - Use the shell's expanded/collapsed sidebar states as one shared responsive component. Do not create a different navigation model per page.
   - Avoid making the UI one-note blue, purple, beige, dark slate, or gradient-heavy.
   - Treat style as system-level infrastructure: tokens first, local component patterns second, one-off styling last.

4. Redesign by surface:
   - Login/auth: read [login-auth.md](references/login-auth.md).
   - Dashboard/workbench: read [dashboard-workbench.md](references/dashboard-workbench.md).
   - Tables, filters, list pages, media grids, and tabs: read [tables-lists.md](references/tables-lists.md).
   - Details, forms, drawers, modals, and settings: read [details-forms.md](references/details-forms.md).
   - For filter-field label behavior, especially Material 3 style floating labels, read [tables-lists.md](references/tables-lists.md) before inventing new placeholder patterns.

5. Implement in the existing stack:
   - Reuse the app's component library where it works, but override defaults deliberately with shared classes/tokens.
   - Create or update layout primitives before touching every page individually.
   - Keep repeated primitives stable: app shell, page header, toolbar, panel, metric tile, status badge, tab bar, table action, and drawer footer.
   - Use familiar icons from the existing icon library for navigation and command buttons.
   - Keep the app title bar single-line. Do not render the app-level title area as a tile with stacked title and subtitle.
   - Keep the breadcrumb/header bar single-line as well. Left side is breadcrumb or module name; right side is real user/session actions only. Do not wrap it into multiple rows unless the user explicitly asks.
   - Preserve navigation hierarchy visually: parent/first-level items must start farther left than child/second-level items, never the reverse.
   - Keep sidebar expansion state at the shell level and preserve it during route changes. In collapsed desktop mode, show icons, retain the active-route indication, and provide accessible tooltips or a flyout for labels and child routes.
   - Enforce independent scroll containers: the browser body/root should not scroll; the sidebar navigation and main content should each own their own vertical scrolling area when content overflows.
   - Do not add topbar controls unless they are functional in the current app. A decorative global search, settings icon, avatar, or environment pill should be removed.

6. Verify the result:
   - Run the app and capture desktop plus mobile/tablet screenshots when possible.
   - Check that text does not overflow controls, tables remain usable, media tiles keep stable dimensions, charts render, and drawers/modals fit smaller viewports.
   - Check type hierarchy: page title is visually dominant, section headings are smaller, card labels and table text are smaller again, and ordinary card numbers do not overpower the page title unless the page is a true KPI dashboard.
   - Check reference density: ordinary text is 14px, metadata is 12-13px, page titles are 20-24px, and controls stay 32-36px high unless touch/mobile requirements need more room.
   - Check sidebar hierarchy: first-level labels/icons align to a smaller x-position than second-level labels/icons; selected backgrounds and accent lines do not make child items look like parents.
   - Check sidebar states: expanded mode exposes groups and labels; collapsed mode is usable by icon, focus, tooltip, and flyout without clipping or changing the active route.
   - Check scroll behavior: wheel/trackpad inside the sidebar scrolls only navigation; wheel/trackpad inside the main content scrolls only the page content; no nested accidental page/body scrollbars.
   - Check hover/focus/selected/active/disabled/loading/empty/error states on at least one example of each important primitive, including panel links, rows, icon buttons, tabs, and sidebar items.

## Design Direction

Prefer this product feel:

- Light shell, white or near-white surfaces, thin neutral borders, near-flat elevation, crisp 14px working type, and clear hierarchy.
- Sidebar with compact line icons and readable labels. Use a 240-256px expanded width and a 56-64px collapsed width on desktop when the existing layout permits it.
- Selected navigation with a quiet neutral fill and stronger text/icon color. Use an accent line only when it adds clarity; do not combine a saturated fill, thick accent, and heavy shadow.
- Single-line 48-56px topbar with shell toggle and context on the left; only real global/session actions on the right.
- Page headers with a small breadcrumb or module context, concise title, compact metadata, and real actions. Do not turn a page header into an intro card.
- Dashboards that prioritize decisions: compact metrics, queues, status summaries, media previews, and real shortcuts. Limit dashboard composition to pages that benefit from overview.
- Tables and media grids that feel dense and direct: filter/action bar first, useful column widths or fixed image tiles, compact status chips, and icon-led secondary actions.
- Tabs that use one pattern per intent: compact raised navigation tabs for content sections, or underline/count tabs for workflow slices. Do not mix tab patterns in one bar.
- Forms that reduce cognitive load: grouped sections, clear required states, readable helper/error text, persistent footer actions, and settings tabs only when the content warrants them.

Avoid these failure modes:

- Copying the old project's deep-blue gradient sidebar/topbar as the dominant visual identity.
- Building a marketing landing page instead of the actual tool surface.
- Using giant hero cards, floating nested cards, decorative blobs/orbs, glassmorphism, or stock-like illustrations for core admin screens.
- Leaving raw Ant Design/Table defaults with no hierarchy, no empty states, no spacing system, and no product-specific affordances.
- Using oversized 16px body text, 48px controls, or rounded 12-16px pills throughout a working admin surface.
- Treating every white block as a clickable card. Keep static panels still; make only genuine navigation/action surfaces interactive.
- Allowing sidebar collapse to hide the active state, remove keyboard labels, or cause page content to jump unpredictably.
- Wrapping tabs onto multiple rows or mixing filled pills, underlines, and segmented buttons in the same navigation context.
- Replacing dense workflows with oversized tiles that reduce the amount of useful information visible.
- Stacking page title, page subtitle, repeated content title, repeated explanatory subtitle, and metric cards before the real work.
- Adding any summary/KPI/intro/promo module above a table/list page without explicit design justification.
- Adding list-tile explanation blocks where a normal section header, table caption, tab, or empty state would be enough.
- Adding fake environment, readiness, automation, or assistant-like labels unless the product already has that state in data.
- Creating dashboard-only chrome on simple list/detail pages.

## Implementation Notes

- For React + Ant Design, keep Ant's behavior and accessibility but standardize shells, tables, form layout, badges, tabs, and buttons through CSS tokens/classes.
- For mixed stacks, prefer Tailwind/shadcn-style primitives for visual shell components and keep Ant Design for complex data-entry/data-display components where functionality matters.
- For Tailwind projects, define semantic tokens/classes for surfaces, border, muted text, accent, success, warning, danger, and focus rings before styling pages.
- For chart-heavy dashboards, use restrained categorical colors and direct labels/legends; avoid rainbow palettes.
- For Chinese enterprise systems, keep Chinese labels concise, use tighter vertical rhythm, and avoid English SaaS filler copy.

## Output Expectations

When using this skill, produce implementation-ready changes, not just aesthetic advice. If the user asks for a design pass on an existing app, update shared styling and at least one representative page per affected surface so the pattern is obvious and reusable. Include shell-state and interaction-state verification whenever the change touches navigation, tabs, panels, rows, or buttons.
