import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Spin, Typography, message } from 'antd';
import { useDatasetStore } from '../../stores/datasetStore';
import { useAnnotationStore } from '../../stores/annotationStore';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { useUnsavedChangesGuard } from '../../hooks/useUnsavedChangesGuard';
import ImageCanvas from './components/ImageCanvas';
import AnnotationList from './components/AnnotationList';
import FileList from './components/FileList';
import Toolbar from './components/Toolbar';

const { Title } = Typography;

const AnnotationPage: React.FC = () => {
  const { annotationId } = useParams<{ annotationId: string }>();
  const { loadAnnotationProject, annotationProject, loading } = useDatasetStore();
  const reset = useAnnotationStore((s) => s.reset);
  const modified = useAnnotationStore((s) => s.modified);

  // 快捷键
  useKeyboardShortcuts();
  useUnsavedChangesGuard(modified);

  // 加载标注项目
  useEffect(() => {
    let cancelled = false;
    if (annotationId) {
      const id = parseInt(annotationId, 10);
      if (!isNaN(id)) {
        loadAnnotationProject(id).then((restored) => {
          if (!cancelled && restored?.sampleName) {
            message.info(`已恢复到上次位置：${restored.sampleName}`);
          }
        });
      }
    }
    return () => {
      cancelled = true;
      reset();
    };
  }, [annotationId]);

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
          <FileList />
        </div>

        {/* 中间: 画布 */}
        <div style={{ flex: 1, display: 'flex', position: 'relative' }}>
          {loading ? (
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
        </span>
        <span>
          快捷键: W 切换模式 | Q/E 翻页 | Ctrl+S 保存 | D 删除 | H 隐藏 | Esc 取消选中
        </span>
      </div>
    </div>
  );
};

export default AnnotationPage;
