import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Stage, Layer, Rect, Image as KonvaImage, Text, Group, Line, Circle } from 'react-konva';
import type Konva from 'konva';
import { useAnnotationStore } from '../../../stores/annotationStore';
import { useDatasetStore } from '../../../stores/datasetStore';
import {
  LabelMode, AnnotationShape, AnnotationType,
  createBBoxAnnotation, createPolygonAnnotation, createOBBAnnotation,
  getClassColor, getOBBVertices, getPolygonCenter,
} from '../../../types';
import type { Annotation, BBoxAnnotation, PolygonAnnotation, OBBAnnotation, Point } from '../../../types';
import { parseYoloAnnotations } from '../../../utils/yolo';

const MIN_BOX_SIZE = 5;
const VERTEX_RADIUS = 4;
const HANDLE_RADIUS = 4;

type OBBResizeHandle = `vertex-${0 | 1 | 2 | 3}` | `edge-${0 | 1 | 2 | 3}`;

type ResizeState =
  | {
    kind: 'bbox';
    uuid: string;
    handle: string;
    startMouse: Point;
    origRect: { x: number; y: number; w: number; h: number };
  }
  | {
    kind: 'obb';
    uuid: string;
    handle: OBBResizeHandle;
    origBox: Pick<OBBAnnotation, 'cx' | 'cy' | 'width' | 'height' | 'angle'>;
  };

const rotatePoint = (point: Point, angle: number): Point => {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  return {
    x: point.x * cos - point.y * sin,
    y: point.x * sin + point.y * cos,
  };
};

const toObbLocalPoint = (
  point: Point,
  obb: Pick<OBBAnnotation, 'cx' | 'cy' | 'angle'>,
): Point => {
  const dx = point.x - obb.cx;
  const dy = point.y - obb.cy;
  const cos = Math.cos(obb.angle);
  const sin = Math.sin(obb.angle);
  return {
    x: dx * cos + dy * sin,
    y: -dx * sin + dy * cos,
  };
};

const resizeOBB = (
  obb: Pick<OBBAnnotation, 'cx' | 'cy' | 'width' | 'height' | 'angle'>,
  handle: OBBResizeHandle,
  pointer: Point,
): Partial<OBBAnnotation> => {
  const local = toObbLocalPoint(pointer, obb);
  let left = -obb.width / 2;
  let right = obb.width / 2;
  let top = -obb.height / 2;
  let bottom = obb.height / 2;

  switch (handle) {
    case 'vertex-0':
      left = Math.min(local.x, right - MIN_BOX_SIZE);
      top = Math.min(local.y, bottom - MIN_BOX_SIZE);
      break;
    case 'vertex-1':
      right = Math.max(local.x, left + MIN_BOX_SIZE);
      top = Math.min(local.y, bottom - MIN_BOX_SIZE);
      break;
    case 'vertex-2':
      right = Math.max(local.x, left + MIN_BOX_SIZE);
      bottom = Math.max(local.y, top + MIN_BOX_SIZE);
      break;
    case 'vertex-3':
      left = Math.min(local.x, right - MIN_BOX_SIZE);
      bottom = Math.max(local.y, top + MIN_BOX_SIZE);
      break;
    case 'edge-0':
      top = Math.min(local.y, bottom - MIN_BOX_SIZE);
      break;
    case 'edge-1':
      right = Math.max(local.x, left + MIN_BOX_SIZE);
      break;
    case 'edge-2':
      bottom = Math.max(local.y, top + MIN_BOX_SIZE);
      break;
    case 'edge-3':
      left = Math.min(local.x, right - MIN_BOX_SIZE);
      break;
  }

  const centerOffset = rotatePoint(
    { x: (left + right) / 2, y: (top + bottom) / 2 },
    obb.angle,
  );

  return {
    cx: obb.cx + centerOffset.x,
    cy: obb.cy + centerOffset.y,
    width: right - left,
    height: bottom - top,
  };
};

const ImageCanvas: React.FC = () => {
  const stageRef = useRef<Konva.Stage>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [stageSize, setStageSize] = useState({ width: 800, height: 600 });
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  // BBox / OBB 绘制状态
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState<Point | null>(null);
  const [drawRect, setDrawRect] = useState<{ x: number; y: number; w: number; h: number } | null>(null);

  // Polygon 绘制状态
  const [polygonPoints, setPolygonPoints] = useState<Point[]>([]);
  const [polygonPreview, setPolygonPreview] = useState<Point | null>(null);

  // BBox/OBB 缩放/拖拽/旋转状态（统一用 Stage 鼠标事件驱动）
  const [resizing, setResizing] = useState<ResizeState | null>(null);
  const [draggingBox, setDraggingBox] = useState<{
    uuid: string; startMouse: Point; origX: number; origY: number;
  } | null>(null);
  const [draggingPolygon, setDraggingPolygon] = useState<{
    uuid: string; startMouse: Point; origPoints: Point[];
  } | null>(null);
  const [draggingPolygonVertex, setDraggingPolygonVertex] = useState<{
    uuid: string; vertexIndex: number;
  } | null>(null);
  const [rotating, setRotating] = useState<{
    uuid: string; cx: number; cy: number; startAngle: number; origAngle: number;
  } | null>(null);

  const {
    annotations, mode, selectedUuid, classes, annotationShape, defaultClassId,
    addAnnotation, selectAnnotation, clearSelection,
    updateAnnotation, setImageSize, changeMode,
  } = useAnnotationStore();

  const { currentImageUrl, annotationFiles, datasetFiles, currentFileIndex, annotationProject } = useDatasetStore();
  const setAnnotations = useAnnotationStore((s) => s.setAnnotations);
  const undo = useAnnotationStore((s) => s.undo);
  const redo = useAnnotationStore((s) => s.redo);
  const beginBatch = useAnnotationStore((s) => s.beginBatch);
  const endBatch = useAnnotationStore((s) => s.endBatch);
  const annotationType = annotationProject?.annotation_type ?? AnnotationType.Detection;
  const isClassification = annotationType === AnnotationType.Classification;
  const isPose = annotationType === AnnotationType.Pose;

  const fitImageToViewport = useCallback((img: HTMLImageElement) => {
    const scaleX = stageSize.width / img.naturalWidth;
    const scaleY = stageSize.height / img.naturalHeight;
    const newScale = Math.min(scaleX, scaleY, 1);
    setScale(newScale);
    setPosition({
      x: (stageSize.width - img.naturalWidth * newScale) / 2,
      y: (stageSize.height - img.naturalHeight * newScale) / 2,
    });
  }, [stageSize.height, stageSize.width]);

  // 容器尺寸响应
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        setStageSize({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight,
        });
      }
    };
    updateSize();
    const observer = new ResizeObserver(updateSize);
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // 加载图像
  useEffect(() => {
    if (!currentImageUrl) {
      setImage(null);
      return;
    }
    let cancelled = false;
    const img = new window.Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      if (cancelled) return;
      setImage(img);
      setImageSize(img.naturalWidth, img.naturalHeight);
    };
    img.src = currentImageUrl;
    return () => {
      cancelled = true;
    };
  }, [currentImageUrl, setImageSize]);

  useEffect(() => {
    if (!image) return;
    fitImageToViewport(image);
  }, [image, fitImageToViewport]);

  useEffect(() => {
    if (!image || isClassification || isPose) return;
    let hasExistingAnnotations = false;
    if (datasetFiles.length > 0 && currentFileIndex >= 0) {
      const file = datasetFiles[currentFileIndex];
      const labelFileName = file.file_name.replace(/\.[^.]+$/, '.txt');
      const annotationFile = annotationFiles.find((f) => f.file_name === labelFileName);
      if (annotationFile?.content) {
        const parsed = parseYoloAnnotations(annotationFile.content, image.naturalWidth, image.naturalHeight);
        setAnnotations(parsed);
        hasExistingAnnotations = parsed.length > 0;
      }
    }
    if (!hasExistingAnnotations) {
      changeMode(LabelMode.Add);
    }
  }, [
    image,
    annotationFiles,
    datasetFiles,
    currentFileIndex,
    isClassification,
    isPose,
    setAnnotations,
    changeMode,
  ]);

  // 获取鼠标在图像坐标系中的位置
  const getImagePos = useCallback((_e: Konva.KonvaEventObject<MouseEvent>) => {
    const stage = stageRef.current;
    if (!stage) return null;
    const pointer = stage.getPointerPosition();
    if (!pointer) return null;
    return {
      x: (pointer.x - position.x) / scale,
      y: (pointer.y - position.y) / scale,
    };
  }, [position, scale]);

  // ============ 鼠标事件 ============

  const handleMouseDown = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (mode !== LabelMode.Add) return;
    if (e.evt.button !== 0) return;
    const pos = getImagePos(e);
    if (!pos) return;

    if (annotationShape === AnnotationShape.Polygon) {
      return;
    }

    setIsDrawing(true);
    setDrawStart(pos);
    setDrawRect({ x: pos.x, y: pos.y, w: 0, h: 0 });
  }, [mode, getImagePos, annotationShape]);

  const handleMouseMove = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    const pos = getImagePos(e);

    // Polygon 顶点编辑
    if (draggingPolygonVertex && pos) {
      const ann = annotations.find((a) => a.uuid === draggingPolygonVertex.uuid);
      if (!ann || ann.shape !== AnnotationShape.Polygon) return;
      const newPoints = ann.points.map((point, index) => (
        index === draggingPolygonVertex.vertexIndex ? pos : point
      ));
      updateAnnotation(draggingPolygonVertex.uuid, { points: newPoints } as Partial<PolygonAnnotation>);
      return;
    }

    // Polygon 整体拖拽移动
    if (draggingPolygon && pos) {
      const dx = pos.x - draggingPolygon.startMouse.x;
      const dy = pos.y - draggingPolygon.startMouse.y;
      const newPoints = draggingPolygon.origPoints.map((point) => ({
        x: point.x + dx,
        y: point.y + dy,
      }));
      updateAnnotation(draggingPolygon.uuid, { points: newPoints } as Partial<PolygonAnnotation>);
      return;
    }

    // BBox 拖拽移动
    if (draggingBox && pos) {
      const dx = pos.x - draggingBox.startMouse.x;
      const dy = pos.y - draggingBox.startMouse.y;
      const ann = annotations.find((a) => a.uuid === draggingBox.uuid);
      if (ann?.shape === AnnotationShape.OBB) {
        updateAnnotation(draggingBox.uuid, {
          cx: draggingBox.origX + dx,
          cy: draggingBox.origY + dy,
        } as Partial<OBBAnnotation>);
      } else {
        updateAnnotation(draggingBox.uuid, {
          x: draggingBox.origX + dx,
          y: draggingBox.origY + dy,
        });
      }
      return;
    }

    // OBB 旋转
    if (rotating && pos) {
      const currentAngle = Math.atan2(pos.y - rotating.cy, pos.x - rotating.cx);
      let deltaAngle = currentAngle - rotating.startAngle;
      // 归一化到 [-π, π]，避免 atan2 跨 ±π 边界时跳变
      while (deltaAngle > Math.PI) deltaAngle -= 2 * Math.PI;
      while (deltaAngle < -Math.PI) deltaAngle += 2 * Math.PI;
      updateAnnotation(rotating.uuid, {
        angle: rotating.origAngle + deltaAngle,
      } as Partial<OBBAnnotation>);
      return;
    }

    // BBox / OBB 缩放
    if (resizing && pos) {
      if (resizing.kind === 'obb') {
        updateAnnotation(
          resizing.uuid,
          resizeOBB(resizing.origBox, resizing.handle, pos) as Partial<OBBAnnotation>,
        );
        return;
      }

      const dx = pos.x - resizing.startMouse.x;
      const dy = pos.y - resizing.startMouse.y;
      const { x: ox, y: oy, w: ow, h: oh } = resizing.origRect;
      let nx = ox, ny = oy, nw = ow, nh = oh;

      switch (resizing.handle) {
        case 'tl': nx = ox + dx; ny = oy + dy; nw = ow - dx; nh = oh - dy; break;
        case 'tc': ny = oy + dy; nh = oh - dy; break;
        case 'tr': ny = oy + dy; nw = ow + dx; nh = oh - dy; break;
        case 'ml': nx = ox + dx; nw = ow - dx; break;
        case 'mr': nw = ow + dx; break;
        case 'bl': nx = ox + dx; nw = ow - dx; nh = oh + dy; break;
        case 'bc': nh = oh + dy; break;
        case 'br': nw = ow + dx; nh = oh + dy; break;
      }

      if (nw < MIN_BOX_SIZE) { nw = MIN_BOX_SIZE; nx = ox; }
      if (nh < MIN_BOX_SIZE) { nh = MIN_BOX_SIZE; ny = oy; }

      updateAnnotation(resizing.uuid, { x: nx, y: ny, width: nw, height: nh });
      return;
    }

    // Polygon 预览线
    if (mode === LabelMode.Add && annotationShape === AnnotationShape.Polygon && polygonPoints.length > 0 && pos) {
      setPolygonPreview(pos);
      return;
    }

    // BBox / OBB 拖拽绘制
    if (!isDrawing || !drawStart || !pos) return;
    setDrawRect({
      x: Math.min(drawStart.x, pos.x),
      y: Math.min(drawStart.y, pos.y),
      w: Math.abs(pos.x - drawStart.x),
      h: Math.abs(pos.y - drawStart.y),
    });
  }, [
    isDrawing,
    drawStart,
    getImagePos,
    mode,
    annotationShape,
    polygonPoints,
    draggingBox,
    draggingPolygon,
    draggingPolygonVertex,
    resizing,
    rotating,
    updateAnnotation,
    annotations,
  ]);

  const handleMouseUp = useCallback(() => {
    // BBox 拖拽/缩放结束
    if (draggingPolygonVertex) { setDraggingPolygonVertex(null); endBatch(); return; }
    if (draggingPolygon) { setDraggingPolygon(null); endBatch(); return; }
    if (draggingBox) { setDraggingBox(null); endBatch(); return; }
    if (resizing) { setResizing(null); endBatch(); return; }
    if (rotating) { setRotating(null); endBatch(); return; }

    if (!isDrawing || !drawRect) {
      setIsDrawing(false);
      return;
    }

    setIsDrawing(false);
    setDrawStart(null);

    if (drawRect.w > MIN_BOX_SIZE && drawRect.h > MIN_BOX_SIZE) {
      if (annotationShape === AnnotationShape.BBox) {
        addAnnotation(createBBoxAnnotation(drawRect.x, drawRect.y, drawRect.w, drawRect.h, defaultClassId));
      } else if (annotationShape === AnnotationShape.OBB) {
        const cx = drawRect.x + drawRect.w / 2;
        const cy = drawRect.y + drawRect.h / 2;
        addAnnotation(createOBBAnnotation(cx, cy, drawRect.w, drawRect.h, 0, defaultClassId));
      }
    }

    setDrawRect(null);
  }, [
    isDrawing,
    drawRect,
    addAnnotation,
    annotationShape,
    draggingBox,
    draggingPolygon,
    draggingPolygonVertex,
    resizing,
    rotating,
    endBatch,
  ]);

  const handleStageClick = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (mode === LabelMode.Add && annotationShape === AnnotationShape.Polygon) {
      const pos = getImagePos(e);
      if (!pos) return;

      if (polygonPoints.length >= 3) {
        const first = polygonPoints[0];
        const dist = Math.sqrt((pos.x - first.x) ** 2 + (pos.y - first.y) ** 2);
        if (dist < 10 / scale) {
          addAnnotation(createPolygonAnnotation([...polygonPoints], defaultClassId));
          setPolygonPoints([]);
          setPolygonPreview(null);
          return;
        }
      }

      setPolygonPoints((prev) => [...prev, pos]);
      return;
    }

    if (e.target === e.target.getStage() || e.target.name() === 'background-image') {
      clearSelection();
    }
  }, [mode, annotationShape, getImagePos, polygonPoints, scale, addAnnotation, clearSelection]);

  const handleStageDblClick = useCallback(() => {
    if (mode === LabelMode.Add && annotationShape === AnnotationShape.Polygon && polygonPoints.length >= 3) {
      addAnnotation(createPolygonAnnotation([...polygonPoints], defaultClassId));
      setPolygonPoints([]);
      setPolygonPreview(null);
    }
  }, [mode, annotationShape, polygonPoints, addAnnotation]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && polygonPoints.length > 0) {
        setPolygonPoints([]);
        setPolygonPreview(null);
      }
      // Ctrl+Z / Cmd+Z 撤销
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        undo();
      }
      // Ctrl+Shift+Z / Cmd+Shift+Z 重做
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) {
        e.preventDefault();
        redo();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [polygonPoints, undo, redo]);

  const handleWheel = useCallback((e: Konva.KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault();
    const stage = stageRef.current;
    if (!stage) return;
    const pointer = stage.getPointerPosition();
    if (!pointer) return;

    const scaleBy = 1.1;
    const oldScale = scale;
    const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy;
    const clampedScale = Math.max(0.1, Math.min(5, newScale));

    const mousePointTo = {
      x: (pointer.x - position.x) / oldScale,
      y: (pointer.y - position.y) / oldScale,
    };

    setScale(clampedScale);
    setPosition({
      x: pointer.x - mousePointTo.x * clampedScale,
      y: pointer.y - mousePointTo.y * clampedScale,
    });
  }, [scale, position]);

  // ============ 标注交互 ============

  // BBox 缩放手柄拖拽结束 — 已由 Stage 鼠标事件替代

  const fitToWindow = useCallback(() => {
    if (!image) return;
    fitImageToViewport(image);
  }, [image, fitImageToViewport]);

  useEffect(() => {
    (window as unknown as Record<string, unknown>).__canvasFitToWindow = fitToWindow;
    return () => { delete (window as unknown as Record<string, unknown>).__canvasFitToWindow; };
  }, [fitToWindow]);

  // ============ 渲染标注 ============

  const renderAnnotation = (annotation: Annotation) => {
    const color = getClassColor(annotation.classId);
    const isSelected = annotation.uuid === selectedUuid;

    switch (annotation.shape) {
      case AnnotationShape.BBox:
        return renderBBox(annotation, color, isSelected);
      case AnnotationShape.Polygon:
        return renderPolygon(annotation, color, isSelected);
      case AnnotationShape.OBB:
        return renderOBB(annotation, color, isSelected);
      default:
        return null;
    }
  };

  const renderLabel = (x: number, y: number, classId: number, rotation: number = 0) => {
    const label = classId >= 0 && classId < classes.length
      ? classes[classId]
      : `class_${classId}`;
    const color = getClassColor(classId);
    const labelHeight = 18 / scale;
    const labelPaddingX = 4 / scale;
    const labelWidth = label.length * 8 / scale + 8 / scale;
    return (
      <Group
        x={x}
        y={y}
        rotation={rotation}
        listening={false}
      >
        <Rect
          x={0}
          y={-labelHeight}
          width={labelWidth}
          height={labelHeight}
          fill={color}
          cornerRadius={2 / scale}
        />
        <Text
          x={labelPaddingX}
          y={-labelHeight + 2 / scale}
          text={label}
          fontSize={12 / scale}
          fill="white"
        />
      </Group>
    );
  };

  // BBox: 一个 Group = 框 + 标签 + 手柄，通过 Stage 鼠标事件统一驱动
  const renderBBox = (a: BBoxAnnotation, color: string, isSelected: boolean) => {
    const r = HANDLE_RADIUS / scale;
    const editable = isSelected && mode === LabelMode.Edit;

    const handles = [
      { name: 'tl', x: a.x, y: a.y, cursor: 'nwse-resize' },
      { name: 'tc', x: a.x + a.width / 2, y: a.y, cursor: 'ns-resize' },
      { name: 'tr', x: a.x + a.width, y: a.y, cursor: 'nesw-resize' },
      { name: 'ml', x: a.x, y: a.y + a.height / 2, cursor: 'ew-resize' },
      { name: 'mr', x: a.x + a.width, y: a.y + a.height / 2, cursor: 'ew-resize' },
      { name: 'bl', x: a.x, y: a.y + a.height, cursor: 'nesw-resize' },
      { name: 'bc', x: a.x + a.width / 2, y: a.y + a.height, cursor: 'ns-resize' },
      { name: 'br', x: a.x + a.width, y: a.y + a.height, cursor: 'nwse-resize' },
    ];

    return (
      <Group key={a.uuid}>
        {/* 框体 —— 点击选中，mouseDown 开始拖拽 */}
        <Rect
          x={a.x}
          y={a.y}
          width={a.width}
          height={a.height}
          stroke={color}
          strokeWidth={isSelected ? 2.5 / scale : 2 / scale}
          fill={isSelected ? `${color}22` : 'transparent'}
          onClick={(e) => { e.cancelBubble = true; selectAnnotation(a.uuid); }}
          onMouseDown={(e) => {
            if (mode !== LabelMode.Edit || !isSelected) return;
            e.cancelBubble = true;
            const pos = getImagePos(e);
            if (!pos) return;
            setDraggingBox({ uuid: a.uuid, startMouse: pos, origX: a.x, origY: a.y });
            beginBatch();
          }}
        />
        {/* 标签 */}
        {renderLabel(a.x, a.y, a.classId)}
        {/* 缩放手柄 */}
        {editable && handles.map((h) => (
          <Circle
            key={h.name}
            x={h.x}
            y={h.y}
            radius={r}
            fill="#fff"
            stroke={color}
            strokeWidth={1.5 / scale}
            onMouseEnter={(e) => {
              const stage = e.target.getStage();
              if (stage) stage.container().style.cursor = h.cursor;
            }}
            onMouseLeave={(e) => {
              const stage = e.target.getStage();
              if (stage) stage.container().style.cursor = 'default';
            }}
            onMouseDown={(e) => {
              e.cancelBubble = true;
              const pos = getImagePos(e);
              if (!pos) return;
              setResizing({
                kind: 'bbox',
                uuid: a.uuid,
                handle: h.name,
                startMouse: pos,
                origRect: { x: a.x, y: a.y, w: a.width, h: a.height },
              });
              beginBatch();
            }}
          />
        ))}
      </Group>
    );
  };

  const renderPolygon = (a: PolygonAnnotation, color: string, isSelected: boolean) => {
    const flatPoints = a.points.flatMap((p) => [p.x, p.y]);
    const center = getPolygonCenter(a);
    const editable = isSelected && mode === LabelMode.Edit;
    return (
      <Group key={a.uuid}>
        <Line
          points={flatPoints}
          closed
          stroke={color}
          strokeWidth={isSelected ? 3 / scale : 2 / scale}
          fill={isSelected ? `${color}33` : `${color}11`}
          onClick={(e) => { e.cancelBubble = true; selectAnnotation(a.uuid); }}
          onMouseEnter={(e) => {
            const stage = e.target.getStage();
            if (stage) stage.container().style.cursor = editable ? 'grab' : 'pointer';
          }}
          onMouseLeave={(e) => {
            const stage = e.target.getStage();
            if (stage) stage.container().style.cursor = 'default';
          }}
          onMouseDown={(e) => {
            if (mode !== LabelMode.Edit || !isSelected) return;
            e.cancelBubble = true;
            const pos = getImagePos(e);
            if (!pos) return;
            setDraggingPolygon({
              uuid: a.uuid,
              startMouse: pos,
              origPoints: a.points.map((point) => ({ ...point })),
            });
            beginBatch();
          }}
        />
        {editable && a.points.map((p, i) => (
          <Circle
            key={`vertex-${a.uuid}-${i}`}
            x={p.x}
            y={p.y}
            radius={VERTEX_RADIUS / scale}
            fill="white"
            stroke={color}
            strokeWidth={2 / scale}
            onClick={(e) => { e.cancelBubble = true; }}
            onMouseEnter={(e) => {
              const stage = e.target.getStage();
              if (stage) stage.container().style.cursor = 'pointer';
            }}
            onMouseLeave={(e) => {
              const stage = e.target.getStage();
              if (stage) stage.container().style.cursor = 'default';
            }}
            onMouseDown={(e) => {
              e.cancelBubble = true;
              setDraggingPolygonVertex({ uuid: a.uuid, vertexIndex: i });
              beginBatch();
            }}
          />
        ))}
        {renderLabel(center.x, center.y, a.classId)}
      </Group>
    );
  };

  const renderOBB = (a: OBBAnnotation, color: string, isSelected: boolean) => {
    const vertices = getOBBVertices(a);
    const editable = isSelected && mode === LabelMode.Edit;
    const r = HANDLE_RADIUS / scale;

    // 四个顶点坐标
    const flatPoints = vertices.flatMap((v) => [v.x, v.y]);

    // 旋转手柄位置：顶边中点沿外法线方向延伸
    const topMidX = (vertices[0].x + vertices[1].x) / 2;
    const topMidY = (vertices[0].y + vertices[1].y) / 2;
    const rotHandleDist = 30 / scale;
    // 顶边外法线方向 = (sin(θ), -cos(θ))
    const rotX = topMidX + Math.sin(a.angle) * rotHandleDist;
    const rotY = topMidY - Math.cos(a.angle) * rotHandleDist;
    const edgeHandles = vertices.map((start, i) => {
      const end = vertices[(i + 1) % vertices.length];
      return {
        name: `edge-${i}` as OBBResizeHandle,
        points: [start.x, start.y, end.x, end.y],
        x: (start.x + end.x) / 2,
        y: (start.y + end.y) / 2,
      };
    });

    // 标签挂在 OBB 固定的局部左上角顶点，并随框体一起旋转
    const labelAnchor = vertices[0];

    return (
      <Group key={a.uuid}>
        {/* OBB 框体 */}
        <Line
          points={flatPoints}
          closed
          stroke={color}
          strokeWidth={isSelected ? 2.5 / scale : 2 / scale}
          fill={isSelected ? `${color}22` : 'transparent'}
          onClick={(e) => { e.cancelBubble = true; selectAnnotation(a.uuid); }}
          onMouseDown={(e) => {
            if (mode !== LabelMode.Edit || !isSelected) return;
            e.cancelBubble = true;
            const pos = getImagePos(e);
            if (!pos) return;
            setDraggingBox({ uuid: a.uuid, startMouse: pos, origX: a.cx, origY: a.cy });
            beginBatch();
          }}
        />
        {/* 标签 */}
        {renderLabel(labelAnchor.x, labelAnchor.y, a.classId, (a.angle * 180) / Math.PI)}
        {/* 4条边手柄 */}
        {editable && edgeHandles.map((edge) => (
          <React.Fragment key={edge.name}>
            <Line
              points={edge.points}
              stroke="rgba(0,0,0,0.01)"
              strokeWidth={12 / scale}
              lineCap="round"
              onMouseEnter={(e) => {
                const stage = e.target.getStage();
                if (stage) stage.container().style.cursor = 'pointer';
              }}
              onMouseLeave={(e) => {
                const stage = e.target.getStage();
                if (stage) stage.container().style.cursor = 'default';
              }}
              onMouseDown={(e) => {
                e.cancelBubble = true;
                const pos = getImagePos(e);
                if (!pos) return;
                setResizing({
                  kind: 'obb',
                  uuid: a.uuid,
                  handle: edge.name,
                  origBox: {
                    cx: a.cx,
                    cy: a.cy,
                    width: a.width,
                    height: a.height,
                    angle: a.angle,
                  },
                });
                beginBatch();
              }}
            />
            <Circle
              x={edge.x}
              y={edge.y}
              radius={r * 0.9}
              fill="#fff"
              stroke={color}
              strokeWidth={1.5 / scale}
              onMouseEnter={(e) => {
                const stage = e.target.getStage();
                if (stage) stage.container().style.cursor = 'pointer';
              }}
              onMouseLeave={(e) => {
                const stage = e.target.getStage();
                if (stage) stage.container().style.cursor = 'default';
              }}
              onMouseDown={(e) => {
                e.cancelBubble = true;
                const pos = getImagePos(e);
                if (!pos) return;
                setResizing({
                  kind: 'obb',
                  uuid: a.uuid,
                  handle: edge.name,
                  origBox: {
                    cx: a.cx,
                    cy: a.cy,
                    width: a.width,
                    height: a.height,
                    angle: a.angle,
                  },
                });
                beginBatch();
              }}
            />
          </React.Fragment>
        ))}
        {/* 4个顶点手柄 */}
        {editable && vertices.map((v, i) => (
          <Circle
            key={`v${i}`}
            x={v.x}
            y={v.y}
            radius={r}
            fill="#fff"
            stroke={color}
            strokeWidth={1.5 / scale}
            onMouseEnter={(e) => {
              const stage = e.target.getStage();
              if (stage) stage.container().style.cursor = 'pointer';
            }}
            onMouseLeave={(e) => {
              const stage = e.target.getStage();
              if (stage) stage.container().style.cursor = 'default';
            }}
            onMouseDown={(e) => {
              e.cancelBubble = true;
              const pos = getImagePos(e);
              if (!pos) return;
              setResizing({
                kind: 'obb',
                uuid: a.uuid,
                handle: `vertex-${i}` as OBBResizeHandle,
                origBox: {
                  cx: a.cx,
                  cy: a.cy,
                  width: a.width,
                  height: a.height,
                  angle: a.angle,
                },
              });
              beginBatch();
            }}
          />
        ))}
        {/* 旋转手柄 */}
        {editable && (
          <>
            <Line
              points={[topMidX, topMidY, rotX, rotY]}
              stroke={color}
              strokeWidth={1 / scale}
              dash={[4 / scale, 2 / scale]}
              listening={false}
            />
            <Circle
              x={rotX}
              y={rotY}
              radius={r * 1.2}
              fill="#fff"
              stroke={color}
              strokeWidth={1.5 / scale}
              onMouseEnter={(e) => {
                const stage = e.target.getStage();
                if (stage) stage.container().style.cursor = 'grab';
              }}
              onMouseLeave={(e) => {
                const stage = e.target.getStage();
                if (stage) stage.container().style.cursor = 'default';
              }}
              onMouseDown={(e) => {
                e.cancelBubble = true;
                const pos = getImagePos(e);
                if (!pos) return;
                setRotating({
                  uuid: a.uuid,
                  cx: a.cx,
                  cy: a.cy,
                  startAngle: Math.atan2(pos.y - a.cy, pos.x - a.cx),
                  origAngle: a.angle,
                });
                beginBatch();
              }}
            />
          </>
        )}
      </Group>
    );
  };

  // ============ 光标样式 ============

  const getCursor = () => {
    if (isClassification || isPose) return 'default';
    if (mode !== LabelMode.Add) return 'default';
    return 'crosshair';
  };

  const classificationAnnotation = annotations[0];
  const classificationLabel = classificationAnnotation && classificationAnnotation.classId >= 0 && classificationAnnotation.classId < classes.length
    ? classes[classificationAnnotation.classId]
    : null;

  return (
    <div
      ref={containerRef}
      style={{
        flex: 1,
        overflow: 'hidden',
        background: '#f0f0f0',
        cursor: getCursor(),
        position: 'relative',
      }}
    >
      <Stage
        ref={stageRef}
        width={stageSize.width}
        height={stageSize.height}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        onClick={handleStageClick}
        onDblClick={handleStageDblClick}
      >
        <Layer x={position.x} y={position.y} scaleX={scale} scaleY={scale}>
          {image && (
            <KonvaImage
              image={image}
              name="background-image"
            />
          )}

          {annotations.filter((a) => a.visible).map((a) => renderAnnotation(a))}

          {drawRect && (
            <Rect
              x={drawRect.x}
              y={drawRect.y}
              width={drawRect.w}
              height={drawRect.h}
              stroke="#1890ff"
              strokeWidth={2 / scale}
              dash={[6 / scale, 3 / scale]}
              fill="rgba(24,144,255,0.1)"
            />
          )}

          {polygonPoints.length > 0 && (
            <>
              <Line
                points={[
                  ...polygonPoints.flatMap((p) => [p.x, p.y]),
                  ...(polygonPreview ? [polygonPreview.x, polygonPreview.y] : []),
                ]}
                stroke="#1890ff"
                strokeWidth={2 / scale}
                dash={[6 / scale, 3 / scale]}
                fill="rgba(24,144,255,0.1)"
                closed={false}
              />
              {polygonPoints.map((p, i) => (
                <Circle
                  key={`draw-vertex-${i}`}
                  x={p.x}
                  y={p.y}
                  radius={(i === 0 ? VERTEX_RADIUS + 2 : VERTEX_RADIUS) / scale}
                  fill={i === 0 ? '#1890ff' : 'white'}
                  stroke="#1890ff"
                  strokeWidth={2 / scale}
                />
              ))}
            </>
          )}

          {isClassification && classificationLabel && (
            <Group listening={false}>
              <Rect
                x={12 / scale}
                y={12 / scale}
                width={(classificationLabel.length * 8 + 24) / scale}
                height={24 / scale}
                fill={getClassColor(classificationAnnotation.classId)}
                cornerRadius={6 / scale}
              />
              <Text
                x={20 / scale}
                y={17 / scale}
                text={`Class: ${classificationLabel}`}
                fontSize={13 / scale}
                fill="#fff"
              />
            </Group>
          )}

        </Layer>
      </Stage>

      {(isClassification || isPose) && (
        <div
          style={{
            position: 'absolute',
            top: 16,
            left: 16,
            background: 'rgba(255,255,255,0.92)',
            border: '1px solid #e5e7eb',
            borderRadius: 10,
            padding: '10px 12px',
            fontSize: 13,
            color: '#475569',
            maxWidth: 320,
          }}
        >
          {isClassification
            ? '当前项目为整图分类，请在右侧标注列表选择或编辑类别。'
            : '姿态标注暂未支持，当前仅保留占位类型。'}
        </div>
      )}

      <div
        style={{
          position: 'absolute',
          bottom: 8,
          right: 8,
          background: 'rgba(0,0,0,0.5)',
          color: 'white',
          padding: '2px 8px',
          borderRadius: 4,
          fontSize: 12,
        }}
      >
        {Math.round(scale * 100)}%
      </div>
    </div>
  );
};

export default ImageCanvas;
