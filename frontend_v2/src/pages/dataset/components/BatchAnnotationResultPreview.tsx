import React from 'react';
import { Empty, Spin } from 'antd';
import { previewSample } from '../../../api/dataset';
import { AnnotationShape, getClassColor, type AiPipelineBatchRunItem, type Annotation } from '../../../types';
import type { InferenceDetectionResult } from '../../../types/deploy';
import { getRecordLabelText } from '../../../utils/annotationRecordContent';
import { parseYoloAnnotations } from '../../../utils/yolo';

interface BatchAnnotationResultPreviewProps {
  datasetId: number;
  item: AiPipelineBatchRunItem;
  classNames: string[];
}

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

const toPercent = (value: number, total: number) => `${(clamp(value, 0, total) / Math.max(total, 1)) * 100}%`;

const isRecord = (value: unknown): value is Record<string, unknown> => (
  typeof value === 'object' && value !== null && !Array.isArray(value)
);

const getYoloLabelText = (item: AiPipelineBatchRunItem): string => {
  const content = item.result?.content;
  return isRecord(content) ? getRecordLabelText(content) : '';
};

const toInferenceResult = (annotation: Annotation, classNames: string[]): InferenceDetectionResult => {
  const common = {
    class_id: annotation.classId,
    class_name: classNames[annotation.classId] || `class_${annotation.classId}`,
    confidence: 1,
  };
  if (annotation.shape === AnnotationShape.BBox) {
    return {
      ...common,
      type: 'bbox',
      box: {
        x1: annotation.x,
        y1: annotation.y,
        x2: annotation.x + annotation.width,
        y2: annotation.y + annotation.height,
      },
    };
  }
  if (annotation.shape === AnnotationShape.OBB) {
    return {
      ...common,
      type: 'obb',
      obb: {
        cx: annotation.cx,
        cy: annotation.cy,
        w: annotation.width,
        h: annotation.height,
        angle: annotation.angle,
      },
    };
  }
  if (annotation.shape === AnnotationShape.Polygon) {
    return { ...common, type: 'polygon', points: annotation.points };
  }
  return { ...common, type: 'classification' };
};

const getLabelAnchor = (item: InferenceDetectionResult, imageWidth: number, imageHeight: number) => {
  if (item.box) {
    return {
      x: clamp(item.box.x1, 0, imageWidth),
      y: clamp(item.box.y1 <= 28 ? item.box.y1 : item.box.y1 - 26, 0, imageHeight),
    };
  }
  if (item.obb) {
    const y = item.obb.cy - item.obb.h / 2;
    return {
      x: clamp(item.obb.cx - item.obb.w / 2, 0, imageWidth),
      y: clamp(y <= 28 ? y : y - 26, 0, imageHeight),
    };
  }
  if (item.points && item.points.length > 0) {
    const xs = item.points.map((point) => point.x);
    const ys = item.points.map((point) => point.y);
    const minY = Math.min(...ys);
    return {
      x: clamp(Math.min(...xs), 0, imageWidth),
      y: clamp(minY <= 28 ? minY : minY - 26, 0, imageHeight),
    };
  }
  return { x: 0, y: 0 };
};

const formatGeometry = (item: InferenceDetectionResult) => {
  if (item.box) return `[${item.box.x1.toFixed(1)}, ${item.box.y1.toFixed(1)}, ${item.box.x2.toFixed(1)}, ${item.box.y2.toFixed(1)}]`;
  if (item.obb) return `cx=${item.obb.cx.toFixed(1)}, cy=${item.obb.cy.toFixed(1)}, w=${item.obb.w.toFixed(1)}, h=${item.obb.h.toFixed(1)}`;
  if (item.points?.length) return `${item.points.length} pts`;
  return '整图分类';
};

const renderOverlayShape = (item: InferenceDetectionResult, index: number) => {
  const color = getClassColor(item.class_id);
  const fill = `${color}22`;
  if (item.points && item.points.length > 1) {
    return <polygon key={`polygon-${index}`} points={item.points.map((point) => `${point.x},${point.y}`).join(' ')} fill={fill} stroke={color} strokeWidth={2} vectorEffect="non-scaling-stroke" />;
  }
  if (item.obb) {
    const angle = (item.obb.angle * 180) / Math.PI;
    return <rect key={`obb-${index}`} x={item.obb.cx - item.obb.w / 2} y={item.obb.cy - item.obb.h / 2} width={item.obb.w} height={item.obb.h} fill={fill} stroke={color} strokeWidth={2} vectorEffect="non-scaling-stroke" transform={`rotate(${angle} ${item.obb.cx} ${item.obb.cy})`} />;
  }
  if (item.box) {
    return <rect key={`bbox-${index}`} x={item.box.x1} y={item.box.y1} width={Math.max(0, item.box.x2 - item.box.x1)} height={Math.max(0, item.box.y2 - item.box.y1)} fill={fill} stroke={color} strokeWidth={2} vectorEffect="non-scaling-stroke" />;
  }
  return null;
};

export const BatchAnnotationResultPreview: React.FC<BatchAnnotationResultPreviewProps> = ({ datasetId, item, classNames }) => {
  const [imageUrl, setImageUrl] = React.useState('');
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');
  const [imageSize, setImageSize] = React.useState<{ width: number; height: number } | null>(null);
  const [focusedResultIndex, setFocusedResultIndex] = React.useState<number | null>(null);
  const labelText = React.useMemo(() => getYoloLabelText(item), [item]);
  const results = React.useMemo(() => {
    if (!labelText || !imageSize) return [];
    return parseYoloAnnotations(labelText, imageSize.width, imageSize.height)
      .map((annotation) => toInferenceResult(annotation, classNames));
  }, [classNames, imageSize, labelText]);

  React.useEffect(() => {
    let disposed = false;
    setLoading(true);
    setError('');
    setImageUrl('');
    setImageSize(null);
    setFocusedResultIndex(null);
    void previewSample(datasetId, item.sample_item_id)
      .then((response) => {
        if (!disposed) setImageUrl(response.presigned_url);
      })
      .catch(() => {
        if (!disposed) setError('无法加载原始图像');
      })
      .finally(() => {
        if (!disposed) setLoading(false);
      });
    return () => {
      disposed = true;
    };
  }, [datasetId, item.sample_item_id]);

  return (
    <section className="mt-5 border-t border-gray-100 pt-5">
      <div className="mb-3 flex items-center justify-between text-sm">
        <span className="font-medium text-gray-800">标注预览</span>
        {imageSize ? <span className="text-gray-500">{results.length} 个标注</span> : null}
      </div>
      {loading ? <div className="flex h-56 items-center justify-center bg-gray-50"><Spin /></div> : null}
      {error ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={error} /> : null}
      {imageUrl ? (
        <div className="overflow-auto rounded-[6px] border border-gray-200 bg-gray-950">
          {imageSize ? (
            <div className="relative w-full" style={{ aspectRatio: `${imageSize.width} / ${imageSize.height}` }}>
              <img className="absolute inset-0 h-full w-full object-contain" src={imageUrl} alt={item.item_key} />
              <svg viewBox={`0 0 ${imageSize.width} ${imageSize.height}`} preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full">
                {results.map(renderOverlayShape)}
              </svg>
              {results.map((result, index) => {
                const anchor = getLabelAnchor(result, imageSize.width, imageSize.height);
                const color = getClassColor(result.class_id);
                return (
                  <div
                    key={`label-${index}`}
                    className="pointer-events-none absolute whitespace-nowrap rounded px-2 py-1 text-xs text-white shadow"
                    style={{
                      left: toPercent(anchor.x, imageSize.width),
                      top: toPercent(anchor.y, imageSize.height),
                      background: focusedResultIndex === index ? '#111827' : color,
                    }}
                  >
                    {result.class_name}
                  </div>
                );
              })}
            </div>
          ) : (
            <img
              className="block max-h-[60vh] w-full object-contain"
              src={imageUrl}
              alt={item.item_key}
              onLoad={(event) => setImageSize({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })}
              onError={() => setError('原始图像加载失败')}
            />
          )}
        </div>
      ) : null}
      {!loading && !error && imageUrl && !labelText ? <div className="mt-2 text-xs text-gray-500">本次结果不包含可渲染的 YOLO 标注。</div> : null}
      {results.length > 0 ? (
        <div className="mt-3 flex flex-col gap-2">
          {results.map((result, index) => (
            <button
              key={`result-${index}`}
              type="button"
              className={`flex items-center justify-between gap-3 rounded-[6px] border px-3 py-2 text-left text-xs ${focusedResultIndex === index ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-gray-50'}`}
              onClick={() => setFocusedResultIndex(index)}
            >
              <span className="flex min-w-0 items-center gap-2 font-medium text-gray-800">
                <i className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: getClassColor(result.class_id) }} />
                <span className="truncate">[{result.type}] {result.class_name}</span>
              </span>
              <span className="shrink-0 text-gray-500">{formatGeometry(result)}</span>
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
};
