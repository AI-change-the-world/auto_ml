import type { DatasetFile } from '../../../types';

export interface AerialSceneTile {
  key: string;
  sceneKey: string;
  row: number;
  col: number;
  index: number;
  file: DatasetFile;
  parsed: boolean;
}

export interface AerialScene {
  key: string;
  label: string;
  rows: number;
  cols: number;
  tiles: AerialSceneTile[];
  parsed: boolean;
}

const STRUCTURED_TILE_PATTERN = /^(.*)_(\d+)x(\d+)_r(\d+)_c(\d+)\.[^.]+$/i;
const UNGROUPED_SCENE_KEY = '__ungrouped__';

export function parseAerialTileName(fileName: string) {
  const matched = STRUCTURED_TILE_PATTERN.exec(fileName);
  if (!matched) return null;

  const [, sceneLabel, rowsText, colsText, rowText, colText] = matched;
  const rows = Number(rowsText);
  const cols = Number(colsText);
  const row = Number(rowText);
  const col = Number(colText);

  if ([rows, cols, row, col].some((value) => Number.isNaN(value) || value <= 0)) {
    return null;
  }

  return {
    sceneKey: sceneLabel,
    sceneLabel,
    rows,
    cols,
    row,
    col,
  };
}

export function buildAerialScenes(datasetFiles: DatasetFile[]): AerialScene[] {
  const sceneMap = new Map<string, AerialScene>();

  datasetFiles.forEach((file, index) => {
    const parsed = parseAerialTileName(file.file_name);
    const sceneKey = parsed?.sceneKey ?? UNGROUPED_SCENE_KEY;
    const sceneLabel = parsed?.sceneLabel ?? '未分组文件';

    if (!sceneMap.has(sceneKey)) {
      sceneMap.set(sceneKey, {
        key: sceneKey,
        label: sceneLabel,
        rows: parsed?.rows ?? 0,
        cols: parsed?.cols ?? 1,
        tiles: [],
        parsed: Boolean(parsed),
      });
    }

    const scene = sceneMap.get(sceneKey)!;
    const fallbackRow = scene.tiles.length + 1;
    const tile: AerialSceneTile = {
      key: `${sceneKey}:${file.id}`,
      sceneKey,
      row: parsed?.row ?? fallbackRow,
      col: parsed?.col ?? 1,
      index,
      file,
      parsed: Boolean(parsed),
    };
    scene.tiles.push(tile);

    if (parsed) {
      scene.rows = Math.max(scene.rows, parsed.rows, tile.row);
      scene.cols = Math.max(scene.cols, parsed.cols, tile.col);
      scene.parsed = true;
    } else {
      scene.rows = scene.tiles.length;
    }
  });

  return Array.from(sceneMap.values())
    .map((scene) => ({
      ...scene,
      tiles: [...scene.tiles].sort((a, b) => {
        if (a.row !== b.row) return a.row - b.row;
        if (a.col !== b.col) return a.col - b.col;
        return a.file.file_name.localeCompare(b.file.file_name);
      }),
      rows: Math.max(scene.rows, 1),
      cols: Math.max(scene.cols, 1),
    }))
    .sort((a, b) => {
      if (a.key === UNGROUPED_SCENE_KEY) return 1;
      if (b.key === UNGROUPED_SCENE_KEY) return -1;
      return a.label.localeCompare(b.label);
    });
}

export function findSceneByFileName(
  scenes: AerialScene[],
  fileName?: string,
): AerialScene | null {
  if (!fileName) return scenes[0] ?? null;
  for (const scene of scenes) {
    if (scene.tiles.some((tile) => tile.file.file_name === fileName)) {
      return scene;
    }
  }
  return scenes[0] ?? null;
}

export function isStructuredAerialScene(scene: AerialScene): boolean {
  return scene.parsed && scene.tiles.some((tile) => tile.parsed);
}
