import React, { useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Spin, Typography } from 'antd';
import { useAnnotationCollaborationDocument } from '../../hooks/useAnnotationCollaborationDocument';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { useUnsavedChangesGuard } from '../../hooks/useUnsavedChangesGuard';
import { useAnnotationCollaborationStore } from '../../stores/annotationCollaborationStore';
import { useAnnotationStore } from '../../stores/annotationStore';
import { useDatasetStore } from '../../stores/datasetStore';
import AnnotationList from './components/AnnotationList';
import CollaborationFileList from './components/CollaborationFileList';
import ImageCanvas from './components/ImageCanvas';
import Toolbar from './components/Toolbar';

const { Title } = Typography;

const CollaborativeDetectionAnnotationPage: React.FC = () => {
  const { annotationId } = useParams<{ annotationId: string }>();
  const {
    collaborator,
    initialize,
    loading: collaborationLoading,
    refreshStats,
    reset: resetCollaboration,
  } = useAnnotationCollaborationStore();
  const {
    annotationProject,
    collaboratorToken,
    currentSampleIndex,
    loading,
    sampleItems,
  } = useDatasetStore();
  const resetAnnotation = useAnnotationStore((state) => state.reset);
  const modified = useAnnotationStore((state) => state.modified);
  const wasModifiedRef = useRef(false);

  useKeyboardShortcuts();
  useUnsavedChangesGuard(modified);

  const annotationNumericId = annotationId ? Number(annotationId) : NaN;
  const currentSample = currentSampleIndex >= 0 ? sampleItems[currentSampleIndex] : null;

  useAnnotationCollaborationDocument({
    enabled: Number.isFinite(annotationNumericId),
    annotationId: annotationNumericId,
    sampleItemId: currentSample?.id,
    collaboratorToken,
    collaboratorName: collaborator?.display_name,
  });

  useEffect(() => {
    if (!annotationId || !Number.isFinite(annotationNumericId)) return undefined;
    void initialize(annotationNumericId);
    return () => {
      resetCollaboration();
      resetAnnotation();
    };
  }, [annotationId, annotationNumericId, initialize, resetAnnotation, resetCollaboration]);

  useEffect(() => {
    if (wasModifiedRef.current && !modified) {
      void refreshStats();
    }
    wasModifiedRef.current = modified;
  }, [modified, refreshStats]);

  if (!annotationId) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Title level={4} type="secondary">请指定标注项目 ID</Title>
      </div>
    );
  }

  const isLoading = loading || collaborationLoading;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#fff' }}>
      <Toolbar />

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <div style={{ borderRight: '1px solid #f0f0f0' }}>
          <CollaborationFileList />
        </div>

        <div style={{ flex: 1, display: 'flex', position: 'relative' }}>
          {isLoading ? (
            <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <Spin size="large" tip="加载中..." />
            </div>
          ) : (
            <ImageCanvas />
          )}
        </div>

        <div style={{ borderLeft: '1px solid #f0f0f0' }}>
          <AnnotationList />
        </div>
      </div>

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
          {collaborator ? ` · ${collaborator.display_name}` : ''}
        </span>
        <span>协作模式: 样本独占领取 | 快捷键: W 切换模式 | Q/E 翻页 | Ctrl+S 保存</span>
      </div>
    </div>
  );
};

export default CollaborativeDetectionAnnotationPage;
