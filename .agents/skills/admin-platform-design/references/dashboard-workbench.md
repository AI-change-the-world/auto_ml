# Dashboard And Workbench

Use this reference for home dashboards, review queues, operations workbenches, analytics landing pages, and role-based overview pages.

## Structure

Design the dashboard around decisions and next actions, matching the supplied reference style without copying its business domain:

- Greeting/context block only if the role benefits from it; otherwise use the space for real work.
- Primary KPI row with 3-5 compact metric tiles.
- Main work queue or recent table in the largest central area.
- Right rail for risk overview, pending tasks, alerts, or activity.
- Secondary row for trends, shortcuts, and process statistics.

The reference pattern is: light sidebar, restrained topbar, soft welcome block, compact KPI cards, central table, right-side status/risk panels, and lower trend/shortcut panels. Use that hierarchy only for dashboard/workbench pages. Do not add empty/filler cards, fake operational indicators, or explanatory modules to imitate the screenshot.

## Metric Tiles

- Show label, value, comparison, and icon/status.
- Keep values large enough to scan but not hero-sized.
- Keep metric labels around body/meta size and values below or proportional to the page title unless the dashboard is explicitly KPI-led.
- Use semantic trend colors: green for good increase, red for bad increase, amber for watch states.
- Make every metric explain its unit and period.
- Avoid filling an entire tile with saturated color unless it is an alert.
- Use colored circular icon wells sparingly, like the reference, and keep them secondary to the number.
- If a page already has enough task content, skip decorative metric tiles instead of inventing metrics.

## Work Queues

- Put the most actionable table/list high on the page.
- Include tabs or segmented filters only when they map to real workflow states in the product.
- Show the fields users need to decide the next action: owner, status, priority/risk, due time, or other domain-relevant metadata.
- Keep row actions predictable and derived from the product's real permissions and workflow.
- Prefer a real table or compact list over repeated title/subtitle cards when users compare records.

## Risk And Status Panels

- Risk overview can be a donut, stacked bar, or compact list. Do not use a chart when a list is clearer.
- Always pair chart colors with labels and counts.
- Use red only for genuinely high risk. Use amber for medium, green for low/normal.
- Put severe items near the top of the panel.

## Shortcuts

- Use compact icon+label buttons for frequent actions.
- Keep shortcuts task-oriented, but derive labels from the app's actual routes, permissions, and user jobs. Do not invent domain-specific shortcuts from a reference image.
- Do not add shortcut cards merely to fill space.
- If there are no real frequent actions, omit the shortcuts section.

## Redundancy Rules

- Remove page-summary cards that repeat the page title and subtitle already shown in the app header.
- Remove decorative assistant/promo/help cards unless the current app already provides that feature and data.
- Remove status pills that are not actual backend/frontend state.
- Remove decorative topbar controls that do not perform a real action in the current app.
- Do not add module cards just to name a module; use section headers, tabs, or direct content.

## Empty And Loading

- Skeleton metric tiles and table rows should preserve the dashboard grid.
- Empty queues should show the next action or explain that no work is pending.
- Chart loading should reserve final dimensions to prevent layout jump.

## Responsive

- Desktop: main content plus optional right rail.
- Tablet: KPI grid collapses to two columns; right rail moves below the main table.
- Mobile: single column, compact topbar, sidebar becomes drawer or bottom navigation if the app supports it.
