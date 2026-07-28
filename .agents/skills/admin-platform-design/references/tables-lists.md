# Tables And Lists

Use this reference for data management pages, search results, catalog pages, approval lists, entity tables, logs, and audit records.

## Page Anatomy

A strong admin list page usually has:

- Page title and short context/count in the shell/header. Do not duplicate the same title in a large intro card below.
- Primary action in the header, such as "新增", "导入", "同步", or "导出".
- Filter toolbar with search, status/type/date filters, and reset.
- Optional tabs or saved views for high-level slices.
- Dense table with meaningful column widths.
- Pagination, bulk selection, and batch actions when relevant.
- Counts can appear in tabs, filters, header metadata, or compact summary chips. Do not add a full KPI card row above a list unless those metrics directly drive filtering or prioritization.

## Default Rule

- Unless the user gives an explicit design reason, every table/list page should be reduced to two functional blocks only: filter controls and the primary table/list.
- Do not add intro cards, summary cards, page-level KPI rows, helper banners, promo blocks, or duplicated section titles above the table.
- Keep the page title to a single line. If supporting context is needed, move it into breadcrumb, placeholder text, filter labels, table empty state, or compact toolbar hint instead of a second title line.
- If the shell breadcrumb already identifies the current module/page, remove the in-page title entirely instead of repeating it above the filters.

## Toolbar

- Keep search first when search is the dominant entry point.
- Put primary action on the right or in the page header.
- Collapse rarely used filters into "更多筛选" on narrow screens.
- Show active filters as removable chips when filters can become complex.
- Use consistent widths for Select/Input controls to avoid jitter.
- Do not add a global search box or toolbar action unless it is wired to existing route/state behavior or the user asked for it.

## Floating Labels

- Ant Design does not provide a production-ready Material 3 floating-label field for ordinary admin filters out of the box. Treat this as a custom visual enhancement, not a default pattern.
- Use floating labels selectively, usually only for the primary search input in a dense filter bar when the field meaning would otherwise disappear after entry.
- Do not force floating-label treatment onto every Select, DatePicker, or filter control in a table toolbar. Standard compact Ant Design placeholders are usually cleaner.
- A floating-label field must remain the same visual height as neighboring controls. If the treatment makes the toolbar taller, heavier, or harder to scan, remove it.
- The resting state may resemble placeholder text, but once focused or once a value exists, the label should shrink and pin quietly to the top-left inside the control.
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
    <label className={`relative block min-w-0 h-[38px]${className ? ` ${className}` : ''}`}>
      <input
        {...props}
        value={value}
        placeholder=" "
        className={[
          'peer box-border block h-full w-full rounded-[8px] border border-[#dbe2ea] bg-transparent',
          'px-3 pt-[11px] pb-[3px] text-[13px] leading-[1.25] text-[#0f172a] outline-none',
          'transition-[border-color,border-width] duration-200',
          'placeholder:text-transparent focus:border-2 focus:border-[#2563eb]',
        ].join(' ')}
        onChange={(event) => onValueChange(event.target.value)}
        onKeyDown={handleKeyDown}
      />
      <span
        className={[
          'pointer-events-none absolute left-3 top-0 z-[1] max-w-[calc(100%-24px)]',
          'origin-[0] -translate-y-1/2 scale-[0.85] whitespace-nowrap bg-white px-1',
          'text-[13px] leading-none text-[#2563eb] transition-all duration-200',
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

- Use 13px table text and compact row height when the data is operational.
- First column should identify the entity clearly and may include secondary metadata.
- Use ellipsis for long names, addresses, IDs, and organizations.
- Align numeric values by decimal or right edge when comparing amounts.
- Keep status/risk badges compact with tinted backgrounds.
- Use fixed right action column only when horizontal scroll is expected.
- Avoid putting too many buttons in every row. Prefer one primary inline action plus overflow menu.
- Remove list-tile wrappers around table/list sections when they do not add filtering, grouping, or an action.
- Keep the real list/table close to the top. Avoid forcing users past repeated titles, explanatory copy, and large stat cards before they reach the data.

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
