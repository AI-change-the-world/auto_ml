import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Space, Tooltip, Tag, Divider, Segmented, message } from 'antd';
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
  UndoOutlined,
  RedoOutlined,
  DeleteOutlined,
  ArrowLeftOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { assistCurrentAnnotation } from '../../../api/annotation';
import { useAnnotationStore } from '../../../stores/annotationStore';
import { useDatasetStore } from '../../../stores/datasetStore';
import { LabelMode, AnnotationShape, AnnotationType } from '../../../types';
import { createBBoxAnnotation } from '../../../types';

const Toolbar: React.FC = () => {
  const navigate = useNavigate();
  const {
    mode, toggleMode, modified, annotationShape, setAnnotationShape,
    selectedUuid, deleteSelected, undo, redo, _history, _future,
    classes, setAnnotations, addAnnotation, addOrGetClassId,
  } = useAnnotationStore();
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

  const handleAssist = async () => {
    if (!annotationProject?.id) {
      message.warning('未加载标注项目');
      return;
    }
    if (currentFileIndex < 0 || currentFileIndex >= datasetFiles.length) {
      message.warning('未选择图片');
      return;
    }
    if ((classes || []).length === 0) {
      message.warning('请先为标注项目配置类别');
      return;
    }

    const currentFile = datasetFiles[currentFileIndex];
    try {
      const result = await assistCurrentAnnotation(annotationProject.id, {
        file_name: currentFile.file_name,
        replace_existing: false,
      });

      const nextAnnotations = result.annotations
        .filter((item) => item.label && item.bbox)
        .map((item) => {
          const classId = addOrGetClassId(item.label);
          return createBBoxAnnotation(
            item.bbox.x1,
            item.bbox.y1,
            Math.max(0, item.bbox.x2 - item.bbox.x1),
            Math.max(0, item.bbox.y2 - item.bbox.y1),
            classId,
          );
        });

      if (result.replace_existing) {
        setAnnotations(nextAnnotations);
      } else {
        nextAnnotations.forEach((item) => addAnnotation(item));
      }

      message.success(`辅助标注完成，返回 ${nextAnnotations.length} 个框`);
    } catch (error) {
      console.error('assist annotation failed', error);
      message.error('辅助标注失败');
    }
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
        {/* 返回主页面 */}
        <Tooltip title="返回标注列表">
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/annotations')}
            size="small"
          />
        </Tooltip>

        <Divider type="vertical" />

        {/* 模式切换 */}
        <Tooltip title={`切换模式 (W) - 当前: ${mode === LabelMode.Edit ? '编辑' : '添加'}`}>
          <Button
            type={mode === LabelMode.Add ? 'primary' : 'default'}
            icon={mode === LabelMode.Add ? <PlusSquareOutlined /> : <EditOutlined />}
            onClick={toggleMode}
            size="small"
          />
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
            size="small"
          >
            保存
          </Button>
        </Tooltip>

        {modified && <Tag color="warning">未保存</Tag>}

        <Divider type="vertical" />

        <Tooltip title="辅助标注当前图片">
          <Button
            icon={<RobotOutlined />}
            onClick={handleAssist}
            disabled={loading || !annotationProject || annotationType !== AnnotationType.Detection}
            size="small"
          >
            辅助标注
          </Button>
        </Tooltip>

        <Divider type="vertical" />

        {/* 撤销 / 重做 */}
        <Tooltip title="撤销 (Ctrl+Z)">
          <Button
            icon={<UndoOutlined />}
            onClick={undo}
            disabled={_history.length === 0}
            size="small"
          />
        </Tooltip>
        <Tooltip title="重做 (Ctrl+Shift+Z)">
          <Button
            icon={<RedoOutlined />}
            onClick={redo}
            disabled={_future.length === 0}
            size="small"
          />
        </Tooltip>

        <Divider type="vertical" />

        {/* 删除选中 */}
        <Tooltip title="删除选中 (D)">
          <Button
            icon={<DeleteOutlined />}
            onClick={deleteSelected}
            disabled={!selectedUuid}
            size="small"
            danger
          />
        </Tooltip>
      </Space>

      <Space size="small">
        {/* 当前工具提示 */}
        <Tag color="blue" style={{ margin: 0 }}>
          {mode === LabelMode.Edit ? '编辑' : '添加'}
          {' · '}
          {annotationShape === AnnotationShape.BBox && '矩形框'}
          {annotationShape === AnnotationShape.OBB && '旋转框'}
          {annotationShape === AnnotationShape.Polygon && '多边形'}
        </Tag>

        <Divider type="vertical" />

        {/* 缩放 */}
        <Tooltip title="适应窗口">
          <Button icon={<ExpandOutlined />} onClick={handleFitToWindow} size="small" />
        </Tooltip>

        <Divider type="vertical" />

        {/* 导航 */}
        <Tooltip title="上一张 (Q)">
          <Button
            icon={<LeftOutlined />}
            onClick={prevFile}
            disabled={currentFileIndex <= 0 || loading}
            size="small"
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
            size="small"
          />
        </Tooltip>
      </Space>
    </div>
  );
};

export default Toolbar;
