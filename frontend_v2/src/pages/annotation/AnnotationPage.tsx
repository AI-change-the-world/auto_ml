import React, { useEffect } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { Spin, Typography, message } from 'antd';
import { useDatasetStore } from '../../stores/datasetStore';
import { useAnnotationStore } from '../../stores/annotationStore';
import { useAnnotationCollaborationStore } from '../../stores/annotationCollaborationStore';
import { useAnnotationCollaborationDocument } from '../../hooks/useAnnotationCollaborationDocument';
import {
  useAnnotationCollaborationPresence,
  type AnnotationSampleEditor,
} from '../../hooks/useAnnotationCollaborationPresence';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { useUnsavedChangesGuard } from '../../hooks/useUnsavedChangesGuard';
import ImageCanvas from './components/ImageCanvas';
import AnnotationList from './components/AnnotationList';
import FileList from './components/FileList';
import Toolbar from './components/Toolbar';

const { Title } = Typography;

const AnnotationPage: React.FC = () => {
  const { annotationId } = useParams<{ annotationId: string }>();
  const location = useLocation();
  const {
    loadAnnotationProject,
    annotationProject,
    currentSampleIndex,
    loading,
    sampleItems,
  } = useDatasetStore();
  const initializeCollaboration = useAnnotationCollaborationStore((s) => s.initialize);
  const resetCollaboration = useAnnotationCollaborationStore((s) => s.reset);
  const collaborator = useAnnotationCollaborationStore((s) => s.collaborator);
  const collaborationLoading = useAnnotationCollaborationStore((s) => s.loading);
  const reset = useAnnotationStore((s) => s.reset);
  const modified = useAnnotationStore((s) => s.modified);
  const collaborationMode = location.pathname.endsWith('/label/collab-detection');

  // 快捷键
  useKeyboardShortcuts();
  useUnsavedChangesGuard(modified);

  const annotationNumericId = annotationId ? Number(annotationId) : NaN;
  const currentSample = currentSampleIndex >= 0 ? sampleItems[currentSampleIndex] : null;

  useAnnotationCollaborationDocument({
    enabled: collaborationMode && Number.isFinite(annotationNumericId) && Boolean(collaborator),
    annotationId: annotationNumericId,
    sampleItemId: currentSample?.id,
    collaboratorToken: collaborator?.token,
    collaboratorName: collaborator?.display_name,
  });
  const activeEditors = useAnnotationCollaborationPresence({
    enabled: collaborationMode && Number.isFinite(annotationNumericId) && Boolean(collaborator),
    annotationId: annotationNumericId,
    sampleItemId: currentSample?.id,
    collaborator,
  });
  const editorsBySampleId = React.useMemo(() => {
    return activeEditors.reduce<Record<number, AnnotationSampleEditor[]>>((acc, editor) => {
      if (!acc[editor.sampleItemId]) acc[editor.sampleItemId] = [];
      acc[editor.sampleItemId].push(editor);
      return acc;
    }, {});
  }, [activeEditors]);
  const onlineEditors = React.useMemo(() => {
    const editorMap = new Map<string, AnnotationSampleEditor>();
    for (const editor of activeEditors) {
      if (editor.local) continue;
      editorMap.set(editor.id, editor);
    }
    return Array.from(editorMap.values());
  }, [activeEditors]);

  // 加载标注项目
  useEffect(() => {
    let cancelled = false;
    if (annotationId) {
      const id = parseInt(annotationId, 10);
      if (!isNaN(id)) {
        if (collaborationMode) {
          initializeCollaboration(id);
          loadAnnotationProject(id).then((restored) => {
            if (!cancelled && restored?.sampleName) {
              message.info(`已恢复到上次位置：${restored.sampleName}`);
            }
          });
        } else {
          loadAnnotationProject(id).then((restored) => {
            if (!cancelled && restored?.sampleName) {
              message.info(`已恢复到上次位置：${restored.sampleName}`);
            }
          });
        }
      }
    }
    return () => {
      cancelled = true;
      if (collaborationMode) resetCollaboration();
      reset();
    };
  }, [annotationId, collaborationMode, initializeCollaboration, loadAnnotationProject, reset, resetCollaboration]);

  if (!annotationId) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Title level={4} type="secondary">请指定标注项目 ID</Title>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#fff' }}>
      {/* 工具栏 */}
      <Toolbar />

      {/* 主体区域 */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左侧: 文件列表 */}
        <div style={{ borderRight: '1px solid #f0f0f0' }}>
          <FileList editorsBySampleId={editorsBySampleId} />
        </div>

        {/* 中间: 画布 */}
        <div style={{ flex: 1, display: 'flex', position: 'relative' }}>
          {loading || collaborationLoading ? (
            <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <Spin size="large" tip="加载中..." />
            </div>
          ) : (
            <ImageCanvas />
          )}
        </div>

        {/* 右侧: 标注列表 */}
        <div style={{ borderLeft: '1px solid #f0f0f0' }}>
          <AnnotationList />
        </div>
      </div>

      {/* 底部状态栏 */}
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
          {collaborationMode && collaborator && (
            <span style={{ marginLeft: 16, color: '#64748b' }}>
              协作: {collaborator.display_name}
            </span>
          )}
          {collaborationMode && (
            <span style={{ marginLeft: 16, color: '#64748b' }}>
              在线: {onlineEditors.length > 0 ? onlineEditors.map((editor) => editor.name).join('、') : '仅我'}
            </span>
          )}
        </span>
        <span>
          快捷键: W 切换模式 | Q/E 翻页 | Ctrl+S 保存 | D 删除 | H 隐藏 | Esc 取消选中
        </span>
      </div>
    </div>
  );
};

export default AnnotationPage;
