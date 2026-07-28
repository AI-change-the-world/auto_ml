# Component Strategy

Use this reference when the app has, or can reasonably add, both utility-first styling and a mature enterprise component library. The goal is not Tailwind versus Ant Design; it is choosing the right layer for each job. Do not add shadcn or another UI dependency solely for aesthetics if local Tailwind/components can express the same primitive cleanly.

## Principle

Use Tailwind/shadcn-style primitives for the visual experience. Use Ant Design for complex business interaction.

This usually means:

- Outer page structure, spacing, surfaces, typography, state chips, and simple controls use Tailwind classes or local shadcn-style primitives.
- Complex data components stay on Ant Design when Ant already solves hard behavior: table mechanics, form validation, hierarchical data, uploads, date picking, transfers, and multi-step flows.
- Visual wrappers can be custom while inner Ant components remain functional.

Example pattern:

```tsx
<section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
  <header className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
    <h2 className="text-sm font-semibold text-slate-950">Records</h2>
  </header>
  <Table />
</section>
```

## Prefer Tailwind Or Shadcn-Style Primitives For

- App shell: sidebar, topbar, page frame, scroll containers.
- Page header: breadcrumb, title, subtitle, real actions.
- Cards and panels: KPI cards, dashboard sections, overview blocks, empty states.
- Buttons and icon buttons when the behavior is simple.
- Badges/status chips when they only display state.
- Tabs and segmented controls when they do not need complex Ant behavior.
- Dialogs/drawers for simple create/edit flows if the app already has accessible primitives.
- Empty, loading, and error states.

## Prefer Ant Design For

- Table: fixed columns, expansion, row selection, sorting, filtering, pagination, virtual scroll.
- Form: validation, dependencies, dynamic lists, complex field layout.
- Tree and tree-select: folders, permissions, organizations, category hierarchies.
- Upload: file lists, progress, drag/drop, validation.
- DatePicker and RangePicker.
- Cascader: regional or hierarchical choices.
- Transfer: permission and membership assignment.
- Steps: mature multi-step processes.
- Select with large option sets if Ant already handles search, virtualization, or async behavior.

## Integration Rules

- Do not rewrite a working Ant table/form/tree/upload only to make it look custom. Wrap it and tune tokens/classes first.
- Do not install or migrate to shadcn only because this guide mentions it. Treat "shadcn-style" as a visual/component architecture pattern unless the project already uses it or the user approves adding it.
- Do not place Ant Cards around every Ant component if the visual system already provides a panel primitive.
- Use one visual source of truth for radius, borders, shadows, text color, focus rings, and spacing.
- Normalize Ant components through theme tokens or scoped CSS so they fit the Tailwind/shadcn-style shell.
- Avoid mixing two button styles in the same toolbar. Pick one button primitive per local area.
- Keep accessibility and keyboard behavior from the mature component when replacing it would be risky.

## Migration Guidance

- Existing Ant Design app: first restyle shell, page headers, panels, metrics, badges, and empty states; keep Ant Table/Form/Tree/Upload/DatePicker.
- Existing Tailwind app: add Ant only for high-complexity components that would be expensive or fragile to rebuild.
- Existing mixed app: identify which layer owns each primitive before editing. Do not duplicate modal, button, badge, or tab systems unless there is a clear reason.
