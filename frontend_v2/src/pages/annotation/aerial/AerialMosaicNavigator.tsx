import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  AppstoreOutlined,
} from '@ant-design/icons';
import { previewSample } from '../../../api/dataset';
import type { AerialScene } from './utils';
import type { AnnotationRecord } from '../../../types';
import { getRecordLabelText } from '../../../utils/annotationRecordContent';
import { getSampleItemName } from '../../../utils/sampleItem';

interface Props {
  scene: AerialScene | null;
  datasetId?: number | null;
  overlapRatio?: number;
  currentFileName?: string;
  onSelectFileName: (fileName: string) => void;
  height?: number | string;
  annotationRecords?: AnnotationRecord[];
}

const AerialMosaicNavigator: React.FC<Props> = ({
  scene,
  datasetId,
  overlapRatio = 0.2,
  currentFileName,
  onSelectFileName,
  height = 420,
  annotationRecords = [],
}) => {
  const [previewUrls, setPreviewUrls] = useState<Record<string, string>>({});
  const [tileAspectRatio, setTileAspectRatio] = useState(1);
  const [viewportSize, setViewportSize] = useState({ width: 0, height: 0 });
  const viewportRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadScenePreviews = async () => {
      if (!scene || !datasetId) return;
      const missingTiles = scene.tiles.filter((tile) => !previewUrls[getSampleItemName(tile.sample)]);
      if (missingTiles.length === 0) return;

      const results = await Promise.all(
        missingTiles.map(async (tile) => {
          const sampleName = getSampleItemName(tile.sample);
          try {
            const response = await previewSample(datasetId, tile.sample.id);
            return [sampleName, response.presigned_url] as const;
          } catch (error) {
            console.error('Failed to load aerial tile preview', sampleName, error);
            return [sampleName, ''] as const;
          }
        }),
      );

      if (!cancelled) {
        setPreviewUrls((prev) => {
          const next = { ...prev };
          results.forEach(([fileName, url]) => {
            if (url) next[fileName] = url;
          });
          return next;
        });
      }
    };

    loadScenePreviews();
    return () => {
      cancelled = true;
    };
  }, [scene, datasetId, previewUrls]);

  useEffect(() => {
    const element = viewportRef.current;
    if (!element) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width, height } = entry.contentRect;
      setViewportSize({ width, height });
    });

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!scene) return;
    const firstPreviewUrl = scene.tiles
      .map((tile) => previewUrls[getSampleItemName(tile.sample)])
      .find(Boolean);
    if (!firstPreviewUrl) return;

    let cancelled = false;
    const image = new window.Image();
    image.onload = () => {
      if (cancelled) return;
      if (image.naturalWidth > 0 && image.naturalHeight > 0) {
        setTileAspectRatio(image.naturalWidth / image.naturalHeight);
      }
    };
    image.src = firstPreviewUrl;

    return () => {
      cancelled = true;
    };
  }, [scene, previewUrls]);

  const tileMap = new Map((scene?.tiles || []).map((tile) => [`${tile.row}-${tile.col}`, tile]));
  const cells = [];
  for (let row = 1; row <= Math.max(scene?.rows || 1, 1); row += 1) {
    for (let col = 1; col <= Math.max(scene?.cols || 1, 1); col += 1) {
      cells.push({ row, col, tile: tileMap.get(`${row}-${col}`) });
    }
  }

  const normalizedOverlap = Math.min(Math.max(overlapRatio, 0), 0.6);
  const stepX = 1 - normalizedOverlap;
  const stepY = 1 - normalizedOverlap;
  const totalWidthUnits = 1 + Math.max((scene?.cols || 1) - 1, 0) * stepX;
  const totalHeightUnits = 1 + Math.max((scene?.rows || 1) - 1, 0) * stepY;
  const tileWidthPercent = 100 / totalWidthUnits;
  const tileHeightPercent = 100 / totalHeightUnits;
  const sceneAspectRatio = tileAspectRatio * totalWidthUnits / totalHeightUnits;
  const tileAnnotationCount = new Map(
    annotationRecords.map((record) => {
      const normalized = getRecordLabelText(record.content).trim();
      const count = normalized ? normalized.split(/\n+/).filter(Boolean).length : 0;
      return [record.sample_item_id, count];
    }),
  );

  const fittedSize = useMemo(() => {
    const availableWidth = Math.max(0, viewportSize.width);
    const availableHeight = Math.max(0, viewportSize.height);
    if (!availableWidth || !availableHeight || !Number.isFinite(sceneAspectRatio) || sceneAspectRatio <= 0) {
      return null;
    }

    if (availableWidth / availableHeight > sceneAspectRatio) {
      const heightPx = availableHeight;
      return {
        width: heightPx * sceneAspectRatio,
        height: heightPx,
      };
    }

    const widthPx = availableWidth;
    return {
      width: widthPx,
      height: widthPx / sceneAspectRatio,
    };
  }, [viewportSize, sceneAspectRatio]);

  if (!scene) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
        暂无场景可预览
      </div>
    );
  }

  return (
    <div style={{ height, background: 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 700, color: '#0f172a' }}>
            <AppstoreOutlined style={{ color: '#4f46e5' }} />
            完整图导航
          </div>
          <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
            基于子图缩略图按行列和重叠率生成伪拼接总览。比例保持与原始子图一致，点击不同图块切换当前标注子图。
          </div>
        </div>
        <div style={{ fontSize: 12, color: '#64748b' }}>
          {scene.label} · {scene.rows} x {scene.cols} · 重叠 {Math.round(normalizedOverlap * 100)}%
        </div>
      </div>

      <div
        ref={viewportRef}
        style={{ flex: 1, minHeight: 0, borderRadius: 12, border: '1px solid #e2e8f0', background: 'linear-gradient(135deg, #f8fafc, #ffffff)', padding: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}
      >
        <div
          style={{
            position: 'relative',
            width: fittedSize ? `${fittedSize.width}px` : '100%',
            height: fittedSize ? `${fittedSize.height}px` : '100%',
            borderRadius: 12,
            overflow: 'hidden',
            background: 'radial-gradient(circle at top left, rgba(79, 70, 229, 0.06), transparent 35%), linear-gradient(135deg, #f8fafc, #eef2ff)',
            border: '1px solid rgba(148, 163, 184, 0.18)',
            boxShadow: '0 12px 36px rgba(15, 23, 42, 0.08)',
          }}
        >
          {cells.map(({ row, col, tile }) => {
            const sampleName = tile ? getSampleItemName(tile.sample) : '';
            const isActive = sampleName === currentFileName;
            const isEmpty = !tile;
            const left = (((col - 1) * stepX) / totalWidthUnits) * 100;
            const top = (((row - 1) * stepY) / totalHeightUnits) * 100;
            const previewUrl = tile ? previewUrls[sampleName] : undefined;
            const annotatedCount = tile ? (tileAnnotationCount.get(tile.sample.id) ?? 0) : 0;

            return (
              <button
                key={`${row}-${col}`}
                type="button"
                disabled={!tile}
                onClick={() => tile && onSelectFileName(sampleName)}
                style={{
                  position: 'absolute',
                  left: `${left}%`,
                  top: `${top}%`,
                  width: `${tileWidthPercent}%`,
                  height: `${tileHeightPercent}%`,
                  borderRadius: 10,
                  border: isActive ? '2px solid #4f46e5' : '1px dashed #cbd5e1',
                  background: isEmpty
                    ? 'repeating-linear-gradient(135deg, #f8fafc, #f8fafc 8px, #f1f5f9 8px, #f1f5f9 16px)'
                    : '#fff',
                  color: isEmpty ? '#94a3b8' : isActive ? '#3730a3' : '#334155',
                  cursor: tile ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  padding: 0,
                  textAlign: 'left',
                  minHeight: 0,
                  overflow: 'hidden',
                  boxShadow: isActive
                    ? '0 0 0 3px rgba(99, 102, 241, 0.15), 0 8px 20px rgba(79, 70, 229, 0.18)'
                    : '0 4px 12px rgba(15, 23, 42, 0.10)',
                  zIndex: isActive ? 3 : 1,
                }}
              >
                {previewUrl && tile ? (
                  <img
                    src={previewUrl}
                    alt={sampleName}
                    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block', filter: isActive ? 'none' : 'saturate(0.92)' }}
                  />
                ) : (
                  <div
                    style={{
                      width: '100%',
                      height: '100%',
                      background: isEmpty
                        ? 'repeating-linear-gradient(135deg, #f8fafc, #f8fafc 8px, #f1f5f9 8px, #f1f5f9 16px)'
                        : 'linear-gradient(135deg, #dbeafe, #eef2ff)',
                    }}
                  />
                )}

                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    background: isEmpty
                      ? 'transparent'
                      : isActive
                        ? 'linear-gradient(180deg, rgba(79, 70, 229, 0.10), rgba(15, 23, 42, 0.12))'
                        : 'linear-gradient(180deg, transparent, rgba(15, 23, 42, 0.18))',
                  }}
                />

                <div
                  style={{
                    position: 'absolute',
                    left: 8,
                    top: 8,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 4,
                    alignItems: 'flex-start',
                  }}
                >
                  <span
                    style={{
                      padding: '2px 6px',
                      borderRadius: 999,
                      background: isEmpty ? 'rgba(255,255,255,0.9)' : 'rgba(15, 23, 42, 0.68)',
                      color: isEmpty ? '#64748b' : '#fff',
                      fontSize: 10,
                      fontWeight: 700,
                      backdropFilter: 'blur(6px)',
                    }}
                  >
                    r{String(row).padStart(2, '0')} c{String(col).padStart(2, '0')}
                  </span>
                  {!isEmpty && (
                    <span
                      style={{
                        padding: '2px 6px',
                        borderRadius: 999,
                        background: annotatedCount > 0 ? 'rgba(34, 197, 94, 0.88)' : 'rgba(255, 255, 255, 0.90)',
                        color: annotatedCount > 0 ? '#f8fafc' : '#475569',
                        fontSize: 10,
                        fontWeight: 700,
                        backdropFilter: 'blur(6px)',
                      }}
                    >
                      {annotatedCount} 个标注
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default AerialMosaicNavigator;
