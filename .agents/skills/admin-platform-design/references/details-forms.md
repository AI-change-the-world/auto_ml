# Details, Forms, Drawers, And Modals

Use this reference for entity detail pages, create/edit forms, approval dialogs, settings pages, drawers, and modals.

## Detail Pages

Use detail pages for entities that require reading, audit, history, or multiple related datasets.

Recommended structure:

- Header with back link, entity title, status/risk badge, and primary actions.
- Summary strip with 3-6 key fields.
- Main content organized into sections based on the entity model, such as overview, attributes, attachments, history, audit trail, and related records.
- Right rail for status timeline, owner, task state, or risk explanation when useful.
- Tabs only when each tab has enough content to justify navigation.
- Do not create overview tiles that repeat labels already present in the header or section title.

## Forms

- Group fields by user mental model, not database table order.
- Use one or two columns on desktop; one column on mobile.
- Keep required indicators visible.
- Put helper text under the field only when it prevents mistakes.
- Do not add explanatory subtitles to every field group. Use concise group titles and rely on labels.
- Validate inline and summarize blocking errors near submit for long forms.
- Use input types that match data: date picker, money input, percentage input, select, cascader, upload, textarea.
- Preserve unsaved changes if a drawer/modal closes accidentally when feasible.

## Drawers

Use drawers for create/edit flows, quick detail preview, and side-by-side review:

- Width: 480-640px for simple forms, 720-960px for complex review.
- Header: clear title, optional status.
- Body: scrollable.
- Footer: sticky with primary and secondary actions.
- Avoid putting a full dashboard or deeply nested workflow inside a drawer.

## Modals

Use modals for confirmations, short forms, and focused decisions:

- Keep destructive confirmation copy precise.
- Primary action label should describe the actual outcome in the product's domain.
- Do not use modals for long tables or multi-step forms unless there is no better route.

## Review And Approval

- Show the evidence needed for the decision near the action controls.
- Separate system-generated analysis from user-entered comments.
- For approve/reject flows, require a reason only when policy or audit value justifies it.
- Use status timelines for multi-step workflows.

## Settings Pages

- Prefer grouped settings panels with clear save behavior.
- Make dangerous settings visually separate.
- For integrations, show connection status, last sync, error, credentials state, and test action.
