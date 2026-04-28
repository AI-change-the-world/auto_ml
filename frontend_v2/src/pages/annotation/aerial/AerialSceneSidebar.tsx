import React, { useMemo, useState } from 'react';
import { Badge, Empty } from 'antd';
import {
  AppstoreOutlined,
  CaretDownOutlined,
  CaretRightOutlined,
  FolderOpenOutlined,
  PictureOutlined,
} from '@ant-design/icons';
import { useDatasetStore } from '../../../stores/datasetStore';
import { buildAerialScenes, findSceneByFileName } from './utils';
import { getSampleItemName } from '../../../utils/sampleItem';

interface Props {
  activeSceneKey: string | null;
  onSelectScene: (sceneKey: string) => void;
  onOpenMosaic: (sceneKey: string, firstFileName?: string) => void;
}

const AerialSceneSidebar: React.FC<Props> = ({ activeSceneKey, onSelectScene, onOpenMosaic }) => {
  const { sampleItems, currentSampleIndex, loadSampleAtIndex, loading } = useDatasetStore();
  const [expandedKeys, setExpandedKeys] = useState<Record<string, boolean>>({});

  const currentSample = currentSampleIndex >= 0 ? sampleItems[currentSampleIndex] : undefined;
  const currentFileName = currentSample ? getSampleItemName(currentSample) : undefined;
  const scenes = useMemo(() => buildAerialScenes(sampleItems), [sampleItems]);
  const currentScene = useMemo(() => findSceneByFileName(scenes, currentFileName), [scenes, currentFileName]);

  React.useEffect(() => {
    if (currentScene?.key) {
      setExpandedKeys((prev) => ({ ...prev, [currentScene.key]: true }));
    }
  }, [currentScene?.key]);

  const toggleExpanded = (sceneKey: string) => {
    setExpandedKeys((prev) => ({ ...prev, [sceneKey]: !prev[sceneKey] }));
  };

  if (sampleItems.length === 0 && !loading) {
    return (
      <div style={{ width: 280, borderRight: '1px solid #f0f0f0', height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '10px 14px', borderBottom: '1px solid #f0f0f0', fontWeight: 600 }}>航拍场景</div>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Empty description="暂无可用子图" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        </div>
      </div>
    );
  }

  return (
    <div style={{ width: 280, borderRight: '1px solid #f0f0f0', height: '100%', display: 'flex', flexDirection: 'column', background: '#fcfcfd' }}>
      <div style={{ padding: '10px 14px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontWeight: 600 }}>航拍场景</span>
        <Badge count={sampleItems.length} showZero style={{ backgroundColor: '#667eea' }} />
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 8 }}>
        {scenes.map((scene) => {
          const expanded = expandedKeys[scene.key] ?? scene.key === activeSceneKey;
          const isSceneActive = scene.key === activeSceneKey;

          return (
            <div key={scene.key} style={{ marginBottom: 8, border: '1px solid #eef0f5', borderRadius: 10, background: '#fff', overflow: 'hidden' }}>
              <button
                type="button"
                onClick={() => {
                  onSelectScene(scene.key);
                  toggleExpanded(scene.key);
                }}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '10px 12px',
                  border: 'none',
                  background: isSceneActive ? '#eef2ff' : '#fff',
                  color: isSceneActive ? '#4f46e5' : '#111827',
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                {expanded ? <CaretDownOutlined style={{ fontSize: 12 }} /> : <CaretRightOutlined style={{ fontSize: 12 }} />}
                <FolderOpenOutlined />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{scene.label}</div>
                  <div style={{ fontSize: 11, color: '#94a3b8' }}>
                    {scene.rows} x {scene.cols} · {scene.tiles.length} 张
                  </div>
                </div>
              </button>

              {expanded && (
                <div style={{ borderTop: '1px solid #f6f7fb', padding: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <button
                    type="button"
                    onClick={() => onOpenMosaic(scene.key, scene.tiles[0] ? getSampleItemName(scene.tiles[0].sample) : undefined)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '8px 10px',
                      border: 'none',
                      borderRadius: 8,
                      background: isSceneActive ? '#f8fafc' : 'transparent',
                      color: '#475569',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    <AppstoreOutlined />
                    <span style={{ fontSize: 12 }}>完整图导航</span>
                  </button>

                  {scene.tiles.map((tile) => {
                    const sampleName = getSampleItemName(tile.sample);
                    const isTileActive = tile.index === currentSampleIndex;
                    return (
                      <button
                        key={tile.key}
                        type="button"
                        onClick={() => loadSampleAtIndex(tile.index)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          padding: '8px 10px',
                          border: 'none',
                          borderRadius: 8,
                          background: isTileActive ? '#e0f2fe' : 'transparent',
                          color: isTileActive ? '#0369a1' : '#475569',
                          cursor: 'pointer',
                          textAlign: 'left',
                        }}
                      >
                        <PictureOutlined />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 12, fontWeight: isTileActive ? 600 : 500 }}>
                            r{String(tile.row).padStart(2, '0')} c{String(tile.col).padStart(2, '0')}
                          </div>
                          <div style={{ fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', opacity: 0.8 }}>
                            {sampleName}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AerialSceneSidebar;
