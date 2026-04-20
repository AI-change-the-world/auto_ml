# Multi-Dataset Training TODO

## Goal

Support training with multiple `(dataset, annotation)` sources while keeping annotation editing bound to a single dataset.

The design principle is:

- Annotation stays simple: one annotation project belongs to one dataset.
- Training becomes composable: one task can consume multiple labeled sources.

## Current Constraints

- `annotation.dataset_id` is single-valued.
- `task` currently stores only one `dataset_id` and one `annotation_id`.
- Training API only accepts one `dataset_path` and one `annotation_path`.
- Trainer downloads one dataset folder and one annotation folder, then matches image and label by filename.
- Multi-source merge would currently break on duplicate filenames and mixed class systems.

## Target Design

### Data model

- Keep `annotation.dataset_id` unchanged.
- Keep `task.dataset_id` and `task.annotation_id` for backward compatibility as the primary source.
- Add a new table `task_source` to store all training inputs for a task.
- Each `task_source` row represents one labeled training source:
  - `task_id`
  - `dataset_id`
  - `annotation_id`
  - `source_order`
  - `source_name` optional snapshot name for display

### API behavior

- Extend task creation payload to accept `sources`.
- Preserve compatibility with old clients:
  - If only `dataset_id` and `annotation_id` are provided, create one source automatically.
  - If `sources` is provided, validate all sources and use them.
- Extend task response to include `sources`.

### Validation rules

- Require at least one source.
- All sources must exist and not be deleted.
- All annotations must have `save_path`.
- All datasets must have `save_path`.
- All sources in one task must have the same training-compatible type.
- For detection tasks:
  - annotation type must be detection.
- For classification tasks:
  - annotation type must be classification.
- All source class lists must be exactly the same after normalization.

### Trainer protocol

- Extend training message payload with `sources`.
- Keep `dataset_path` and `annotation_path` in payload for backward compatibility, using the first source.
- Trainer should prefer `sources` when present.

### Dataset preparation

- Add multi-source download helper that downloads each source into isolated subfolders.
- Add merge helper that:
  - prefixes filenames with source index or stable dataset/annotation identifiers
  - copies images and labels into one merged temp dataset
  - preserves one-to-one image/label pairing
- Reuse existing detection/classification preparation after merge when possible.

### Frontend

- Update task creation dialog from single dataset/annotation selection to source list editing.
- Allow adding multiple sources, removing sources, and picking dataset + annotation per source.
- Show source count and source summary on task list and task detail pages.
- Keep old fields in response display where useful, but prefer `sources`.

## Implementation Checklist

- [x] Create `task_source` SQL schema and SQLAlchemy model.
- [x] Export `TaskSource` from model package.
- [x] Add CRUD helpers for creating and reading task sources.
- [x] Extend task schemas with `TaskSourceItem`, `TaskSourceResponse`, and `sources`.
- [x] Update task service creation flow to validate and persist multiple sources.
- [x] Update task service serialization to include sources.
- [x] Update trainer request payload to include `sources`.
- [x] Extend model_trainer request schema to accept `sources`.
- [x] Implement multi-source download and merge helpers in trainer dataset module.
- [x] Update detection training to use merged sources.
- [x] Update classification training to use merged sources.
- [x] Update frontend task types and API typings for `sources`.
- [x] Update task creation UI to edit multiple sources.
- [x] Update task list UI to display multi-source summary.
- [x] Update task detail UI to display all sources.
- [x] Run backend and frontend validation.
- [x] Mark completed items in this file.

## Notes

- This implementation intentionally does not change annotation ownership.
- This implementation intentionally does not add class mapping across sources.
- This implementation intentionally requires exact class compatibility to keep behavior predictable.
