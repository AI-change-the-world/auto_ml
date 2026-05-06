import React, { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Modal, Spin, Typography } from 'antd';
import { AppstoreOutlined } from '@ant-design/icons';
import Toolbar from '../components/Toolbar';
import ImageCanvas from '../components/ImageCanvas';
import AnnotationList from '../components/AnnotationList';
import { useDatasetStore } from '../../../stores/datasetStore';
import { useAnnotationStore } from '../../../stores/annotationStore';
import { useUnsavedChangesGuard } from '../../../hooks/useUnsavedChangesGuard';
import AerialSceneSidebar from './AerialSceneSidebar';
import AerialMosaicNavigator from './AerialMosaicNavigator';
import { buildAerialScenes, findSceneByFileName } from './utils';
import { getSampleItemName } from '../../../utils/sampleItem';

const { Title } = Typography;

const AerialAnnotationPage: React.FC = () => {
  const { annotationId } = useParams<{ annotationId: string }>();
  const {
    loadAnnotationProject,
    annotationProject,
    dataset,
    sampleItems,
    annotationRecords,
    currentSampleIndex,
    loading,
    loadSampleByName,
  } = useDatasetStore();
  const reset = useAnnotationStore((s) => s.reset);
  const modified = useAnnotationStore((s) => s.modified);
  const [activeSceneKey, setActiveSceneKey] = useState<string | null>(null);
  const [mosaicOpen, setMosaicOpen] = useState(false);

  useUnsavedChangesGuard(modified);

  useEffect(() => {
    if (annotationId) {
      const id = parseInt(annotationId, 10);
      if (!Number.isNaN(id)) {
        loadAnnotationProject(id);
      }
    }
    return () => {
      reset();
    };
  }, [annotationId, loadAnnotationProject, reset]);

  const currentSample = currentSampleIndex >= 0 ? sampleItems[currentSampleIndex] : undefined;
  const currentFileName = currentSample ? getSampleItemName(currentSample) : undefined;
  const scenes = useMemo(() => buildAerialScenes(sampleItems), [sampleItems]);
  const detectedScene = useMemo(() => findSceneByFileName(scenes, currentFileName), [scenes, currentFileName]);
  const activeScene = useMemo(
    () => scenes.find((scene) => scene.key === activeSceneKey) ?? detectedScene,
    [scenes, activeSceneKey, detectedScene],
  );

  useEffect(() => {
    if (!activeSceneKey && detectedScene?.key) {
      setActiveSceneKey(detectedScene.key);
    }
  }, [activeSceneKey, detectedScene?.key]);

  if (!annotationId) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Title level={4} type="secondary">请指定标注项目 ID</Title>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#fff' }}>
      <Toolbar />

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <AerialSceneSidebar
          activeSceneKey={activeScene?.key ?? null}
          onSelectScene={(sceneKey) => {
            setActiveSceneKey(sceneKey);
          }}
          onOpenMosaic={(sceneKey, firstFileName) => {
            setActiveSceneKey(sceneKey);
            setMosaicOpen(true);
            if (firstFileName && firstFileName !== currentFileName) {
              loadSampleByName(firstFileName);
            }
          }}
        />

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          <div style={{ padding: '10px 14px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#fff' }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>
                {activeScene ? `场景总览 · ${activeScene.label}` : '场景总览'}
              </div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
                使用大尺寸完整图查看器浏览场景，点击图块切换当前标注子图。
              </div>
            </div>
            <Button
              type="default"
              icon={<AppstoreOutlined />}
              onClick={() => setMosaicOpen(true)}
              disabled={!activeScene}
            >
              打开完整图
            </Button>
          </div>

          <div style={{ flex: 1, display: 'flex', position: 'relative', minHeight: 0 }}>
            {loading ? (
              <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <Spin size="large" tip="加载航拍标注中..." />
              </div>
            ) : (
              <ImageCanvas />
            )}
          </div>
        </div>

        <div style={{ borderLeft: '1px solid #f0f0f0' }}>
          <AnnotationList />
        </div>
      </div>

      <Modal
        title={activeScene ? `完整图导航 · ${activeScene.label}` : '完整图导航'}
        open={mosaicOpen}
        onCancel={() => setMosaicOpen(false)}
        footer={null}
        width="90vw"
        centered
        styles={{
          body: {
            padding: '0 0 8px',
            background: '#f8fafc',
            height: '78vh',
          },
        }}
      >
        <AerialMosaicNavigator
          scene={activeScene}
          datasetId={dataset?.id}
          overlapRatio={dataset?.scenario_config?.stitching?.default_overlap_ratio}
          currentFileName={currentFileName}
          onSelectFileName={async (fileName) => {
            await loadSampleByName(fileName);
            setMosaicOpen(false);
          }}
          annotationRecords={annotationRecords}
          height="100%"
        />
      </Modal>

      <div
        style={{
          padding: '4px 16px',
          borderTop: '1px solid #f0f0f0',
          fontSize: 12,
          color: '#999',
          display: 'flex',
          justifyContent: 'space-between',
        }}
      >
        <span>
          {annotationProject ? `项目: ${annotationProject.name}` : ''}
          {activeScene ? ` · 场景: ${activeScene.label}` : ''}
        </span>
        <span>
          航拍工作台: 左侧场景树 | 大尺寸完整图查看器 | 中间子图标注
        </span>
      </div>
    </div>
  );
};

export default AerialAnnotationPage;
