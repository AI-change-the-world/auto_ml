---
name: admin-platform-design
description: Design and refactor polished backend/admin platform frontends for SaaS, enterprise tools, internal dashboards, data-management systems, review/approval workflows, and operations consoles. Use when Codex needs to improve or build login pages, app shells, dashboards/workbenches, table/list pages, detail pages, forms, drawers/modals, navigation, filters, metrics, status/risk indicators, or visual systems in a clean, modern, reference-dashboard-like admin UI while preserving existing frontend/backend interactions and removing redundant UI instead of inventing new business widgets.
---

# Admin Platform Design

## Core Goal

Create admin interfaces that feel like real production software: calm, precise, scannable, and polished. Prefer the supplied dashboard reference style: light sidebar, airy topbar, white work surfaces, soft shadows, compact metric cards, clear risk/status chips, and practical tables. Do not over-design ordinary management pages.

## Workflow

1. Audit the existing app before changing UI:
   - Identify framework, component library, routing, layout primitives, CSS/token system, icon library, chart library, and current data states.
   - Find the key surfaces: login, shell/navigation, dashboard/workbench, list/table, detail page, form/drawer/modal, empty/loading/error states.
   - Keep domain language and workflows. Replace weak visual structure, not the product model.

2. Preserve behavior and prune noise:
   - Do not change API contracts, route semantics, query parameters, form submission flows, permissions, or backend interaction behavior unless the user explicitly asks.
   - Remove redundant visual components when they only explain what the page is, duplicate navigation labels, or add fake status/context.
   - Collapse repeated title/subtitle/title-card chains into one clear page header plus direct content.
   - Treat table/list pages as strict utility surfaces by default: keep only filter controls and the primary table/list unless the user provides an explicit design reason for additional modules.
   - If the app shell already shows breadcrumb/module context, do not repeat the same page title inside the page body on table/list pages.
   - Do not add new business concepts, workflow states, promotional/help cards, readiness badges, shortcuts, search boxes, settings buttons, user menus, or text labels that are not already represented by the app's data, routes, auth model, or product requirements.

3. Establish a restrained platform language:
   - Use [visual-system.md](references/visual-system.md) for color, spacing, radius, shadows, typography, states, and density.
   - Use [component-strategy.md](references/component-strategy.md) to choose Tailwind/shadcn-style visual primitives versus Ant Design business components by scenario.
   - Match the reference dashboard's light, polished SaaS feel without copying its business copy or turning every page into a dashboard.
   - Avoid making the UI one-note blue, purple, beige, dark slate, or gradient-heavy.
   - Treat style as system-level infrastructure: tokens first, local component patterns second, one-off styling last.

4. Redesign by surface:
   - Login/auth: read [login-auth.md](references/login-auth.md).
   - Dashboard/workbench: read [dashboard-workbench.md](references/dashboard-workbench.md).
   - Tables, filters, and list pages: read [tables-lists.md](references/tables-lists.md).
   - Details, forms, drawers, and modals: read [details-forms.md](references/details-forms.md).
   - For filter-field label behavior, especially Material 3 style floating labels, read [tables-lists.md](references/tables-lists.md) before inventing new placeholder patterns.

5. Implement in the existing stack:
   - Reuse the app's component library where it works, but override defaults deliberately with shared classes/tokens.
   - Create or update layout primitives before touching every page individually.
   - Keep repeated primitives stable: app shell, page header, toolbar, panel, metric tile, status badge, table action, drawer footer.
   - Use familiar icons from the existing icon library for navigation and command buttons.
   - Keep the app title bar single-line. Do not render the app-level title area as a tile with stacked title and subtitle.
   - Keep the breadcrumb/header bar single-line as well. Left side is breadcrumb or module name; right side is real user/session actions only. Do not wrap it into multiple rows unless the user explicitly asks.
   - Preserve navigation hierarchy visually: parent/first-level items must start farther left than child/second-level items, never the reverse.
   - Enforce independent scroll containers: the browser body/root should not scroll; the sidebar navigation and main content should each own their own vertical scrolling area when content overflows.
   - Do not add topbar controls unless they are functional in the current app. A decorative global search, settings icon, avatar, or environment pill should be removed.

6. Verify the result:
   - Run the app and capture desktop plus mobile/tablet screenshots when possible.
   - Check that text does not overflow controls, tables remain usable, charts render, and drawers/modals fit smaller viewports.
   - Check type hierarchy: page title is visually dominant, section headings are smaller, card labels and table text are smaller again, and ordinary card numbers do not overpower the page title unless the page is a true KPI dashboard.
   - Check sidebar hierarchy: first-level labels/icons align to a smaller x-position than second-level labels/icons; selected backgrounds and accent lines do not make child items look like parents.
   - Check scroll behavior: wheel/trackpad inside the sidebar scrolls only navigation; wheel/trackpad inside the main content scrolls only the page content; no nested accidental page/body scrollbars.
   - Check hover/focus/selected/active/disabled/loading/empty/error states on at least one example of each important primitive.

## Design Direction

Prefer this product feel:

- Light shell, white or near-white surfaces, subtle borders, quiet shadows, crisp type, clear hierarchy.
- Left navigation with compact icons and readable labels; selected states should be obvious through pale fill, accent line, and text/icon color.
- Page headers that combine breadcrumb, title, short product-context line, and real actions only when these already exist or are useful.
- Dashboards that prioritize operational decisions: metrics, queues, risk/status summaries, recent activity, trend charts, and real shortcuts.
- Tables that feel dense and professional: clear filters, sticky action affordances, compact status chips, useful column widths.
- Forms that reduce cognitive load: grouped sections, clear required states, readable helper/error text, persistent footer actions.

Avoid these failure modes:

- Copying the old project's deep-blue gradient sidebar/topbar as the dominant visual identity.
- Building a marketing landing page instead of the actual tool surface.
- Using giant hero cards, floating nested cards, decorative blobs/orbs, glassmorphism, or stock-like illustrations for core admin screens.
- Leaving raw Ant Design/Table defaults with no hierarchy, no empty states, no spacing system, and no product-specific affordances.
- Replacing dense workflows with oversized tiles that reduce the amount of useful information visible.
- Stacking page title, page subtitle, repeated content title, repeated explanatory subtitle, and metric cards before the real work.
- Adding any summary/KPI/intro/promo module above a table/list page without explicit design justification.
- Adding list-tile explanation blocks where a normal section header, table caption, tab, or empty state would be enough.
- Adding fake environment, readiness, automation, or assistant-like labels unless the product already has that state in data.
- Creating dashboard-only chrome on simple list/detail pages.

## Implementation Notes

- For React + Ant Design, keep Ant's behavior and accessibility but standardize shells, tables, form layout, badges, and buttons through CSS tokens/classes.
- For mixed stacks, prefer Tailwind/shadcn-style primitives for visual shell components and keep Ant Design for complex data-entry/data-display components where functionality matters.
- For Tailwind projects, define semantic tokens/classes for surfaces, border, muted text, accent, success, warning, danger, and focus rings before styling pages.
- For chart-heavy dashboards, use restrained categorical colors and direct labels/legends; avoid rainbow palettes.
- For Chinese enterprise systems, keep Chinese labels concise, use tighter vertical rhythm, and avoid English SaaS filler copy.

## Output Expectations

When using this skill, produce implementation-ready changes, not just aesthetic advice. If the user asks for a design pass on an existing app, update the shared styling and at least one representative page per affected surface so the pattern is obvious and reusable.
