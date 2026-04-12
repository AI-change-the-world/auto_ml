import React from 'react';
import { Button, Space, Tooltip, Tag, Divider } from 'antd';
import {
  EditOutlined,
  PlusSquareOutlined,
  SaveOutlined,
  LeftOutlined,
  RightOutlined,
  ExpandOutlined,
} from '@ant-design/icons';
import { useAnnotationStore } from '../../../stores/annotationStore';
import { useDatasetStore } from '../../../stores/datasetStore';
import { LabelMode } from '../../../types';

const Toolbar: React.FC = () => {
  const { mode, toggleMode, modified } = useAnnotationStore();
  const { nextFile, prevFile, saveCurrentAnnotation, currentFileIndex, datasetFiles, loading } = useDatasetStore();

  const handleFitToWindow = () => {
    const fn = (window as unknown as Record<string, unknown>).__canvasFitToWindow;
    if (typeof fn === 'function') fn();
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '8px 16px',
        borderBottom: '1px solid #f0f0f0',
        background: '#fff',
      }}
    >
      <Space size="small">
        {/* 模式切换 */}
        <Tooltip title={`切换模式 (W) - 当前: ${mode === LabelMode.Edit ? '编辑' : '添加'}`}>
          <Button
            type={mode === LabelMode.Add ? 'primary' : 'default'}
            icon={mode === LabelMode.Add ? <PlusSquareOutlined /> : <EditOutlined />}
            onClick={toggleMode}
          >
            {mode === LabelMode.Edit ? '编辑模式' : '添加模式'}
          </Button>
        </Tooltip>

        <Divider type="vertical" />

        {/* 保存 */}
        <Tooltip title="保存 (Ctrl+S)">
          <Button
            icon={<SaveOutlined />}
            onClick={saveCurrentAnnotation}
            disabled={!modified}
            type={modified ? 'primary' : 'default'}
          >
            保存
          </Button>
        </Tooltip>

        {modified && <Tag color="warning">未保存</Tag>}
      </Space>

      <Space size="small">
        {/* 缩放 */}
        <Tooltip title="适应窗口">
          <Button icon={<ExpandOutlined />} onClick={handleFitToWindow} />
        </Tooltip>

        <Divider type="vertical" />

        {/* 导航 */}
        <Tooltip title="上一张 (Q)">
          <Button
            icon={<LeftOutlined />}
            onClick={prevFile}
            disabled={currentFileIndex <= 0 || loading}
          />
        </Tooltip>

        <span style={{ fontSize: 13, minWidth: 60, textAlign: 'center', display: 'inline-block' }}>
          {datasetFiles.length > 0 ? `${currentFileIndex + 1} / ${datasetFiles.length}` : '-'}
        </span>

        <Tooltip title="下一张 (E)">
          <Button
            icon={<RightOutlined />}
            onClick={nextFile}
            disabled={currentFileIndex >= datasetFiles.length - 1 || loading}
          />
        </Tooltip>
      </Space>
    </div>
  );
};

export default Toolbar;
