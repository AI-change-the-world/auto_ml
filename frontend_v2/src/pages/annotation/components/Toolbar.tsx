import React from 'react';
import { Button, Space, Tooltip, Tag, Divider, Segmented } from 'antd';
import {
  EditOutlined,
  PlusSquareOutlined,
  SaveOutlined,
  LeftOutlined,
  RightOutlined,
  ExpandOutlined,
  BorderOutlined,
  StarOutlined,
  GatewayOutlined,
} from '@ant-design/icons';
import { useAnnotationStore } from '../../../stores/annotationStore';
import { useDatasetStore } from '../../../stores/datasetStore';
import { LabelMode, AnnotationShape, AnnotationType } from '../../../types';

const Toolbar: React.FC = () => {
  const { mode, toggleMode, modified, annotationShape, setAnnotationShape } = useAnnotationStore();
  const { nextFile, prevFile, saveCurrentAnnotation, currentFileIndex, datasetFiles, loading, annotationProject } = useDatasetStore();

  const annotationType = annotationProject?.annotation_type ?? AnnotationType.Detection;

  const handleFitToWindow = () => {
    const fn = (window as unknown as Record<string, unknown>).__canvasFitToWindow;
    if (typeof fn === 'function') fn();
  };

  // 根据 annotation_type 确定可用的标注工具
  const shapeOptions = React.useMemo(() => {
    if (annotationType === AnnotationType.Segmentation) {
      return [
        { label: <Tooltip title="多边形"><GatewayOutlined /></Tooltip>, value: AnnotationShape.Polygon },
      ];
    }
    // 检测模式：BBox + OBB
    return [
      { label: <Tooltip title="矩形框"><BorderOutlined /></Tooltip>, value: AnnotationShape.BBox },
      { label: <Tooltip title="旋转框 OBB"><StarOutlined /></Tooltip>, value: AnnotationShape.OBB },
    ];
  }, [annotationType]);

  // 确保当前 shape 在可用选项中
  React.useEffect(() => {
    const validValues = shapeOptions.map((o) => o.value);
    if (!validValues.includes(annotationShape)) {
      setAnnotationShape(validValues[0]);
    }
  }, [shapeOptions, annotationShape, setAnnotationShape]);

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

        {/* 标注工具切换 */}
        {shapeOptions.length > 1 && (
          <>
            <Segmented
              size="small"
              options={shapeOptions}
              value={annotationShape}
              onChange={(val) => setAnnotationShape(val as AnnotationShape)}
            />
            <Divider type="vertical" />
          </>
        )}

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
        {/* 当前工具提示 */}
        <Tag color="blue" style={{ margin: 0 }}>
          {annotationShape === AnnotationShape.BBox && '矩形框'}
          {annotationShape === AnnotationShape.OBB && '旋转框'}
          {annotationShape === AnnotationShape.Polygon && '多边形'}
        </Tag>

        <Divider type="vertical" />

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
