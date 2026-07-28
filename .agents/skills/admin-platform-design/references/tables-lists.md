# Tables And Lists

Use this reference for data management pages, search results, catalog pages, media/data-browser grids, approval lists, entity tables, logs, audit records, and their tabs.

## Page Anatomy

A strong admin list page usually has:

- Page title and short context/count in the shell/header. Do not duplicate the same title in a large intro card below.
- Primary action in the header, such as "新增", "导入", "同步", or "导出".
- Filter toolbar with search, status/type/date filters, and reset.
- Optional tabs or saved views for high-level slices.
- Dense table or stable visual-asset grid with meaningful widths.
- Pagination, bulk selection, and batch actions when relevant.
- Counts in tabs, filters, header metadata, or compact summary chips. Do not add a full KPI card row above a list unless those metrics directly drive filtering or prioritization.

## Default Rule

- Unless the user gives an explicit design reason, reduce every table/list page to two functional blocks: filter controls and the primary table/list.
- Do not add intro cards, summary cards, page-level KPI rows, helper banners, promo blocks, or duplicated section titles above the table.
- Keep the page title to a single line. If supporting context is needed, move it into breadcrumb, placeholder text, filter labels, table empty state, or compact toolbar hint instead of a second title line.
- If the shell breadcrumb already identifies the current module/page, remove the in-page title entirely instead of repeating it above the filters.

## Toolbar

- Keep search first when search is the dominant entry point.
- Put the primary action on the right or in the page header.
- Collapse rarely used filters into "更多筛选" on narrow screens.
- Show active filters as removable chips when filters can become complex.
- Use consistent widths for Select/Input controls to avoid jitter.
- Do not add a global search box or toolbar action unless it is wired to existing route/state behavior or the user asked for it.
- Use 32-36px controls with 8px gaps. Keep a primary text action at the end of the toolbar and group related secondary commands as bordered icon buttons with tooltips.
- Keep refresh time, sort selector, view-mode toggle, and other utility controls visually subordinate to the primary action. Only show them when their behavior exists.
- Keep the toolbar to one line on desktop where possible. On narrow layouts, preserve the primary action and move less frequent controls into an existing menu/overflow pattern before allowing a loose multi-row wrap.

## Tabs And Views

Use tabs only for real content sections or workflow slices. Do not use a tab bar as a decorative substitute for headings.

- For entity/detail navigation, use compact raised tabs: `32-36px` high, icon plus concise label where helpful, muted inactive text, and an active white/neutral surface with a thin border or quiet shadow. Keep the bar on one line.
- For workflow/count slices, use an underline tab row: compact labels, optional actual count or status dot, and a `2-3px` active underline in the semantic category color. Keep inactive tabs visually quiet.
- For mutually exclusive display modes such as grid/table/list, use square icon buttons with accessible labels and tooltips. Show the active mode with a neutral fill/border rather than a large colored pill.
- Pick one of these patterns in a local navigation context. Do not put raised tabs inside a rounded background and then add underlines to the active item.
- Keep tabs horizontally scrollable on narrow screens when necessary; do not wrap a tab bar into multiple rows or truncate the active label without an accessible alternative.
- Preserve the active tab and its filters in the route or existing local state pattern when users move between list and detail, if the application already supports that behavior.

## Floating Labels

- Ant Design does not provide a production-ready Material 3 floating-label field for ordinary admin filters out of the box. Treat this as a custom visual enhancement, not a default pattern.
- Use floating labels selectively, usually only for the primary search input in a dense filter bar when the field meaning would otherwise disappear after entry.
- Do not force floating-label treatment onto every Select, DatePicker, or filter control in a table toolbar. Standard compact Ant Design placeholders are usually cleaner.
- A floating-label field must remain the same visual height as neighboring controls. If the treatment makes the toolbar taller, heavier, or harder to scan, remove it.
- The resting state may resemble placeholder text, but once focused or once a value exists, shrink and pin the label quietly to the top-left inside the control.
- Keep the label inside the field boundary. Do not let it overlap borders, icons, clear buttons, suffix arrows, or neighboring controls.
- Do not combine a floating label with a second visible label above the field.
- Use a muted label in the filled state and reserve stronger accent color for focus only.
- If a compact placeholder communicates the field clearly, prefer the normal compact field over a custom floating-label implementation.

Example implementation:

```tsx
import type { InputHTMLAttributes, KeyboardEvent } from 'react';

interface OutlinedTextFieldProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'className' | 'value' | 'onChange'> {
  label: string;
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
  onEnter?: (value: string) => void;
}

export function OutlinedTextField({ label, value, onValueChange, className, onEnter, ...props }: OutlinedTextFieldProps) {
  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    props.onKeyDown?.(event);
    if (!event.defaultPrevented && event.key === 'Enter') {
      onEnter?.(event.currentTarget.value);
    }
  }

  return (
    <label className={`relative block min-w-0 h-[36px]${className ? ` ${className}` : ''}`}>
      <input
        {...props}
        value={value}
        placeholder=" "
        className={[
          'peer box-border block h-full w-full rounded-[6px] border border-[#dbe2ea] bg-transparent',
          'px-3 pt-[11px] pb-[3px] text-[13px] leading-[1.25] text-[#0f172a] outline-none',
          'transition-[border-color,box-shadow] duration-150',
          'placeholder:text-transparent focus:border-[#2563eb] focus:ring-2 focus:ring-[#2563eb]/15',
        ].join(' ')}
        onChange={(event) => onValueChange(event.target.value)}
        onKeyDown={handleKeyDown}
      />
      <span
        className={[
          'pointer-events-none absolute left-3 top-0 z-[1] max-w-[calc(100%-24px)]',
          'origin-[0] -translate-y-1/2 scale-[0.85] whitespace-nowrap bg-white px-1',
          'text-[13px] leading-none text-[#2563eb] transition-all duration-150',
          'peer-placeholder-shown:top-1/2 peer-placeholder-shown:scale-100 peer-placeholder-shown:text-[#8b9ab0]',
          'peer-focus:top-0 peer-focus:scale-[0.85] peer-focus:text-[#2563eb]',
        ].join(' ')}
      >
        {label}
      </span>
    </label>
  );
}
```

```tsx
<OutlinedTextField
  label="搜索资产名称、编号、地址"
  value={searchText}
  className="w-80"
  onValueChange={setSearchText}
  onEnter={(value) => setKeyword(value.trim())}
/>
```

## Table Design

- Use 13-14px table text and 44-48px compact row height when the data is operational. Use 32-36px table header height when the component library permits it.
- First column should identify the entity clearly and may include secondary metadata.
- Use ellipsis for long names, addresses, IDs, and organizations.
- Align numeric values by decimal or right edge when comparing amounts.
- Keep status/risk badges compact with tinted backgrounds.
- Use fixed right action column only when horizontal scroll is expected.
- Avoid putting too many buttons in every row. Prefer one primary inline action plus overflow menu.
- Remove list-tile wrappers around table/list sections when they do not add filtering, grouping, or an action.
- Keep the real list/table close to the top. Avoid forcing users past repeated titles, explanatory copy, and large stat cards before they reach the data.
- Use a neutral row hover fill and preserve column alignment. Do not add row elevation, scale, or a layout-shifting border on hover.
- Use an icon button or overflow menu for secondary row actions. Keep one text action only when it is the clear, frequent next step.

## Media And Entity Grids

Use a grid when users must inspect visual assets or compare visual entities. Do not force an image-heavy dataset into a table.

- Use stable aspect-ratio tiles, usually square or the source-media ratio, with consistent 4-6px corners and overflow hidden. Do not let labels or hover states resize a tile.
- Put selection, status, count, or annotation overlays in predictable corners with a solid/tinted backing when image contrast requires it.
- Keep image metadata compact below the tile or in a low-profile overlay. Use ellipsis for long names and preserve the primary click target for preview/detail.
- On hover, reveal genuine quick actions or a quiet selection affordance without covering the asset's most useful area. Maintain keyboard focus and selection states independently from hover.
- Use responsive fixed-column rules or `minmax()` grids that preserve useful tile size. Do not stretch a few assets across the entire content width.
- Keep grid/list/table mode in the same content context. Do not navigate to a differently structured page only to change view mode.

## Badges

Suggested mapping:

- Draft/unknown: neutral gray.
- Processing/reviewing: blue.
- Approved/success/active: green.
- Pending/medium risk/warning: amber.
- Rejected/high risk/failed: red.
- Archived/disabled: muted gray.

Badges should include text, not only color.

## Bulk Actions

- Show selected count and batch actions only after selection.
- Destructive actions require confirmation.
- Batch action bars should not push the table layout around; reserve space or use a sticky low-profile bar.

## Empty, Error, Loading

- Empty first-use state: explain what the user can create/import/sync next.
- Empty after filtering: say no results match current filters and offer reset.
- Loading: use table skeleton or preserve table header.
- Error: show retry and any safe fallback.
- Keep empty/error copy specific to the current feature. Do not use generic operational-health language.

## Detail Entry

- Entity names in the first column should link to detail pages.
- Row click is acceptable only if it does not conflict with selection, inline controls, or text copying.
- Preserve the user's list filters when returning from detail pages when feasible.
