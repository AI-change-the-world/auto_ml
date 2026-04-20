# Aerial Stitch Dataset Extension TODO

## Goal

Add a dataset-level extension for drone/aerial image groups where multiple overlapping sub-images belong to one larger scene. The system should support ordinary datasets unchanged, while aerial stitch datasets can later support automatic grouping, optional mosaic generation, global/tile annotation mapping, and view-specific training.

The core design principle is:

- Dataset import establishes scene identity and spatial relationship.
- Annotation consumes the scene relationship and stores global defect identity.
- Training chooses the view: tile, mosaic, or mixed.
- Inference maps all predictions back into global scene coordinates.

## Current Stage

This checkpoint only introduces the dataset scenario entry point and persistence fields. It does not yet generate mosaics, parse filenames into scenes, or sync tile/global annotations.

## Data Model

### Dataset

- `scenario_type`
  - `0`: normal dataset
  - `1`: drone/aerial stitch dataset
- `scenario_config`
  - JSON configuration for filename grouping, stitching defaults, annotation behavior, and training view defaults.

### Recommended Future Tables

- `facade_scene` or generic `aerial_scene`
  - one logical stitched scene, such as one facade, roof, bridge span, road section, or other aerial target.
- `aerial_scene_tile`
  - one original drone sub-image in a scene.
  - stores row/column, filename, grid size, overlap estimate, and transform to global coordinates.
- `aerial_scene_mosaic`
  - optional generated or manually uploaded full-scene image.
- `defect_instance`
  - one unique global defect or target instance in scene coordinates.
- `annotation_observation`
  - one local observation on a tile or mosaic, mapped to a global `defect_instance`.

## Filename Strategy

Recommended primary format:

```text
{scene}_{rows}x{cols}_r{row}_c{col}.jpg
buildingA_3x4_r01_c01.jpg
buildingA_3x4_r01_c02.jpg
```

Supported later as fallback:

```text
{scene}_{rows}x{cols}_{index}.jpg
buildingA_3x4_001.jpg
```

For sequence-only filenames, default order should be row-major: left to right, top to bottom.

## Implementation Checklist

### Phase 1: Dataset Entry And Persistence

- [x] Add backend dataset scenario enum constant.
- [x] Add `dataset.scenario_type` SQLAlchemy model field.
- [x] Add `dataset.scenario_config` SQLAlchemy model field.
- [x] Add MySQL init schema columns.
- [x] Add lightweight compatibility migration for existing MySQL dev databases.
- [x] Extend dataset create/update/response schemas.
- [x] Store default aerial stitch configuration as JSON.
- [x] Return `scenario_config` as an object in dataset APIs.
- [x] Extend frontend dataset types.
- [x] Add scenario dropdown in dataset creation modal.
- [x] Show aerial scenario guidance in dataset detail page.
- [x] Run backend compile validation.
- [x] Run frontend production build validation.

### Phase 2: Aerial Import Preprocessing

- [ ] Add filename parser for `{scene}_{rows}x{cols}_r{row}_c{col}`.
- [ ] Add fallback parser for `{scene}_{rows}x{cols}_{index}`.
- [ ] Group uploaded files by scene prefix.
- [ ] Detect missing tiles, duplicate row/column positions, invalid grid sizes, and unsupported names.
- [ ] Produce an import report instead of silently skipping bad files.
- [ ] Allow invalid files to be skipped when `scenario_config.stitching.skip_invalid_files` is true.
- [ ] Add API to run/re-run aerial preprocessing for one dataset.
- [ ] Add frontend import report panel in dataset detail page.

### Phase 3: Scene And Tile Storage

- [ ] Add `aerial_scene` table.
- [ ] Add `aerial_scene_tile` table.
- [ ] Persist tile row, column, rows, cols, original file id, and local-to-global transform.
- [ ] Support incomplete grids when `allow_missing_tiles` is true.
- [ ] Store estimated overlap ratio per scene and allow manual override.
- [ ] Add APIs to list scenes and tiles under an aerial dataset.
- [ ] Add frontend scene list and tile grid view.

### Phase 4: Mosaic Generation And Manual Correction

- [ ] Generate a provisional mosaic canvas from grid layout and overlap ratio.
- [ ] Allow uploaded full-scene mosaic as an alternative to generated mosaic.
- [ ] Store mosaic file path and size.
- [ ] Add manual tile alignment UI placeholder.
- [ ] Persist corrected tile transforms.
- [ ] Add error state when mosaic generation fails but tile annotation can continue.

### Phase 5: Annotation Mapping

- [ ] Add global scene coordinate utilities.
- [ ] Add tile-local to global coordinate conversion.
- [ ] Add global to tile-local projection.
- [ ] Add polygon clipping for labels crossing tile boundaries.
- [ ] Add global defect instance model.
- [ ] Add local annotation observation model.
- [ ] Support annotating on tile view.
- [ ] Support annotating on mosaic view.
- [ ] Sync tile and mosaic annotation through global defect instances.
- [ ] Add duplicate handling for the same defect observed in overlapping tiles.

### Phase 6: Training View Configuration

- [ ] Extend task creation for aerial datasets with training view selection: tile, mosaic, mixed.
- [ ] Allow tile and mosaic views to use different base models by creating linked subtasks.
- [ ] Add tile export from global annotations.
- [ ] Add mosaic export from global annotations.
- [ ] Add mixed export with configurable sample ratio.
- [ ] Preserve existing ordinary dataset training flow unchanged.

### Phase 7: Inference And Result Fusion

- [ ] Support tile inference on large mosaics.
- [ ] Map tile predictions back to global scene coordinates.
- [ ] Fuse overlapping predictions with NMS or polygon IoU.
- [ ] Optionally combine small-target tile model results with large-context mosaic model results.
- [ ] Display final global prediction layer on mosaic and per-tile views.

## Notes

- The MVP should not require a complete stitched full image at upload time.
- The source of truth should be the global scene coordinate system, not any single tile.
- Raw drone homography can be added later; the first version can use grid + overlap + manual correction.
- One training task should still produce one model. If tile and mosaic use different base models, create linked subtasks under one higher-level aerial training group.
