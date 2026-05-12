import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Space, Tooltip, Tag, Divider, Segmented, message, Select } from 'antd';
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
  PictureOutlined,
} from '@ant-design/icons';
import { assistCurrentAnnotation, listAnnotationAssistPipelines, updateAnnotation } from '../../../api/annotation';
import { useAnnotationStore } from '../../../stores/annotationStore';
import { useDatasetStore } from '../../../stores/datasetStore';
import { LabelMode, AnnotationShape, AnnotationType } from '../../../types';
import { createBBoxAnnotation } from '../../../types';
import type { AnnotationAssistPipeline } from '../../../types';
import { useCapability } from '../../../hooks/useCapability';
import { showApiError } from '../../../utils/apiError';

const Toolbar: React.FC = () => {
  const navigate = useNavigate();
  const {
    mode, toggleMode, modified, annotationShape, setAnnotationShape,
    selectedUuid, deleteSelected, undo, redo, _history, _future,
    classes, setAnnotations, addAnnotation, addOrGetClassId,
  } = useAnnotationStore();
  const {
    nextSample,
    prevSample,
    saveCurrentAnnotation,
    currentSampleIndex,
    sampleItems,
    loading,
    annotationProject,
    samplePage,
    samplePageSize,
    totalSamples,
  } = useDatasetStore();
  const setDatasetState = useDatasetStore.setState;
  const [assistPipelines, setAssistPipelines] = React.useState<AnnotationAssistPipeline[]>([]);
  const [assistPipelineId, setAssistPipelineId] = React.useState<string | undefined>(undefined);
  const [assistPipelineLoading, setAssistPipelineLoading] = React.useState(false);
  const { getActionCapability } = useCapability();
  const assistCapability = getActionCapability('annotation', 'assist_label');

  const annotationType = annotationProject?.annotation_type ?? AnnotationType.Detection;
  const isClassification = annotationType === AnnotationType.Classification;
  const isPose = annotationType === AnnotationType.Pose;
  const currentShape = annotationShape === AnnotationShape.OBB ? 'obb'
    : annotationShape === AnnotationShape.Polygon ? 'polygon'
      : annotationShape === AnnotationShape.Classification ? 'classification'
        : 'bbox';
  const currentGlobalIndex = currentSampleIndex >= 0
    ? (samplePage - 1) * samplePageSize + currentSampleIndex + 1
    : 0;
  const hasPreviousSample = currentGlobalIndex > 1;
  const hasNextSample = currentGlobalIndex > 0 && currentGlobalIndex < totalSamples;
  const isAddMode = mode === LabelMode.Add;

  const handleFitToWindow = () => {
    const fn = (window as unknown as Record<string, unknown>).__canvasFitToWindow;
    if (typeof fn === 'function') fn();
  };

  const handleToggleMode = () => {
    const nextMode = mode === LabelMode.Edit ? LabelMode.Add : LabelMode.Edit;
    toggleMode();
    message.success(nextMode === LabelMode.Add ? '已切换到标注模式' : '已切换到修改模式');
  };

  // 根据 annotation_type 确定可用的标注工具
  const shapeOptions = React.useMemo(() => {
    if (annotationType === AnnotationType.Classification) {
      return [];
    }
    if (annotationType === AnnotationType.Segmentation) {
      return [
        { label: <Tooltip title="多边形"><GatewayOutlined /></Tooltip>, value: AnnotationShape.Polygon },
      ];
    }
    if (annotationType === AnnotationType.Pose) {
      return [];
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

  React.useEffect(() => {
    let cancelled = false;
    if (!annotationProject?.id || isClassification || isPose) {
      setAssistPipelines([]);
      setAssistPipelineId(undefined);
      return;
    }

    setAssistPipelineLoading(true);
    listAnnotationAssistPipelines(annotationProject.id, currentShape)
      .then((items) => {
        if (cancelled) return;
        setAssistPipelines(items || []);
        const current = annotationProject.assist_pipeline || undefined;
        const next = (items || []).some((item) => item.id === current)
          ? current
          : items?.[0]?.id;
        setAssistPipelineId(next);
      })
      .catch(() => {
        if (!cancelled) {
          setAssistPipelines([]);
          setAssistPipelineId(undefined);
        }
      })
      .finally(() => {
        if (!cancelled) setAssistPipelineLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [annotationProject?.id, annotationProject?.assist_pipeline, currentShape, isClassification, isPose]);

  const handleAssistPipelineChange = async (value: string) => {
    setAssistPipelineId(value);
    if (!annotationProject?.id) return;
    try {
      const updated = await updateAnnotation(annotationProject.id, { assist_pipeline: value });
      setDatasetState({ annotationProject: updated });
    } catch (error) {
      showApiError(error, '保存辅助标注链路失败');
    }
  };

  const handleAssist = async () => {
    if (!assistCapability.allowed) {
      message.warning(assistCapability.reason || '辅助标注服务不可用');
      return;
    }
    if (!annotationProject?.id) {
      message.warning('未加载标注项目');
      return;
    }
    if (currentSampleIndex < 0 || currentSampleIndex >= sampleItems.length) {
      message.warning('未选择图片');
      return;
    }
    if ((classes || []).length === 0) {
      message.warning('请先为标注项目配置类别');
      return;
    }
    if (!assistPipelineId) {
      message.warning('请先选择辅助标注 Pipeline');
      return;
    }

    const currentSample = sampleItems[currentSampleIndex];
    try {
      const result = await assistCurrentAnnotation(annotationProject.id, {
        sample_item_id: currentSample.id,
        pipeline_id: assistPipelineId,
        shape: currentShape,
        target_classes: classes,
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
      showApiError(error, '辅助标注失败');
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
        {!isClassification && !isPose && (
          <>
            <Tooltip title={`切换模式 (W) - 当前: ${mode === LabelMode.Edit ? '编辑' : '添加'}`}>
              <Button
                type={mode === LabelMode.Add ? 'primary' : 'default'}
                icon={mode === LabelMode.Add ? <PlusSquareOutlined /> : <EditOutlined />}
                onClick={handleToggleMode}
                size="small"
              />
            </Tooltip>

            <Divider type="vertical" />
          </>
        )}

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

        {!isClassification && !isPose && (
          <>
            <Select
              size="small"
              placeholder="选择辅助 Pipeline"
              value={assistPipelineId}
              loading={assistPipelineLoading}
              disabled={loading || !annotationProject || assistPipelines.length === 0 || !assistCapability.allowed}
              onChange={handleAssistPipelineChange}
              style={{ width: 190 }}
              options={assistPipelines.map((item) => ({
                label: item.name,
                value: item.id,
              }))}
            />
            <Tooltip title={!assistCapability.allowed ? (assistCapability.reason || '辅助标注服务不可用') : '辅助标注当前图片'}>
              <Button
                icon={<RobotOutlined />}
                onClick={handleAssist}
                disabled={loading || !annotationProject || !assistPipelineId || currentShape !== 'bbox' || !assistCapability.allowed}
                size="small"
              >
                辅助标注
              </Button>
            </Tooltip>
          </>
        )}

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
          {isClassification && <><PictureOutlined /> 整图分类</>}
          {isPose && '姿态标注（占位）'}
          {!isClassification && !isPose && (
            <>
              {isAddMode ? '标注' : '修改'}
              {' · '}
              {annotationShape === AnnotationShape.BBox && '矩形框'}
              {annotationShape === AnnotationShape.OBB && '旋转框'}
              {annotationShape === AnnotationShape.Polygon && '多边形'}
            </>
          )}
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
            onClick={prevSample}
            disabled={!hasPreviousSample || loading}
            size="small"
          />
        </Tooltip>

        <span style={{ fontSize: 13, minWidth: 60, textAlign: 'center', display: 'inline-block' }}>
          {totalSamples > 0 ? `${currentGlobalIndex} / ${totalSamples}` : '-'}
        </span>

        <Tooltip title="下一张 (E)">
          <Button
            icon={<RightOutlined />}
            onClick={nextSample}
            disabled={!hasNextSample || loading}
            size="small"
          />
        </Tooltip>
      </Space>
    </div>
  );
};

export default Toolbar;
