import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Stage, Layer, Rect, Image as KonvaImage, Text, Group, Transformer, Line, Circle } from 'react-konva';
import type Konva from 'konva';
import { useAnnotationStore } from '../../../stores/annotationStore';
import { useDatasetStore } from '../../../stores/datasetStore';
import {
  LabelMode, AnnotationShape,
  createBBoxAnnotation, createPolygonAnnotation, createOBBAnnotation,
  getClassColor, getOBBVertices, getPolygonCenter,
} from '../../../types';
import type { Annotation, BBoxAnnotation, PolygonAnnotation, OBBAnnotation, Point } from '../../../types';
import { parseYoloAnnotations } from '../../../utils/yolo';

const MIN_BOX_SIZE = 5;
const VERTEX_RADIUS = 4;

const ImageCanvas: React.FC = () => {
  const stageRef = useRef<Konva.Stage>(null);
  const transformerRef = useRef<Konva.Transformer>(null);
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

  const {
    annotations, mode, selectedUuid, classes, annotationShape,
    addAnnotation, selectAnnotation, clearSelection,
    updateAnnotation, setImageSize,
  } = useAnnotationStore();

  const { currentImageUrl, annotationFiles, datasetFiles, currentFileIndex } = useDatasetStore();
  const setAnnotations = useAnnotationStore((s) => s.setAnnotations);

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
    const img = new window.Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      setImage(img);
      setImageSize(img.naturalWidth, img.naturalHeight);

      const scaleX = stageSize.width / img.naturalWidth;
      const scaleY = stageSize.height / img.naturalHeight;
      const newScale = Math.min(scaleX, scaleY, 1);
      setScale(newScale);
      setPosition({
        x: (stageSize.width - img.naturalWidth * newScale) / 2,
        y: (stageSize.height - img.naturalHeight * newScale) / 2,
      });

      if (datasetFiles.length > 0 && currentFileIndex >= 0) {
        const file = datasetFiles[currentFileIndex];
        const labelFileName = file.file_name.replace(/\.[^.]+$/, '.txt');
        const annotationFile = annotationFiles.find((f) => f.file_name === labelFileName);
        if (annotationFile?.content) {
          const parsed = parseYoloAnnotations(annotationFile.content, img.naturalWidth, img.naturalHeight);
          setAnnotations(parsed);
        }
      }
    };
    img.src = currentImageUrl;
  }, [currentImageUrl, stageSize.width, stageSize.height]);

  // Transformer 绑定
  useEffect(() => {
    const stage = stageRef.current;
    const transformer = transformerRef.current;
    if (!stage || !transformer) return;

    if (selectedUuid && mode === LabelMode.Edit) {
      const selected = annotations.find((a) => a.uuid === selectedUuid);
      // Transformer 只用于 BBox 和 OBB
      if (selected && (selected.shape === AnnotationShape.BBox || selected.shape === AnnotationShape.OBB)) {
        const node = stage.findOne(`#shape-${selectedUuid}`);
        if (node) {
          transformer.nodes([node]);
          transformer.getLayer()?.batchDraw();
          return;
        }
      }
    }
    transformer.nodes([]);
    transformer.getLayer()?.batchDraw();
  }, [selectedUuid, mode, annotations]);

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
      // Polygon: 不在 mouseDown 开始，用 click 添加点
      return;
    }

    // BBox / OBB: 拖拽绘制
    setIsDrawing(true);
    setDrawStart(pos);
    setDrawRect({ x: pos.x, y: pos.y, w: 0, h: 0 });
  }, [mode, getImagePos, annotationShape]);

  const handleMouseMove = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    const pos = getImagePos(e);

    // Polygon 预览线
    if (mode === LabelMode.Add && annotationShape === AnnotationShape.Polygon && polygonPoints.length > 0 && pos) {
      setPolygonPreview(pos);
      return;
    }

    // BBox / OBB 拖拽
    if (!isDrawing || !drawStart || !pos) return;
    setDrawRect({
      x: Math.min(drawStart.x, pos.x),
      y: Math.min(drawStart.y, pos.y),
      w: Math.abs(pos.x - drawStart.x),
      h: Math.abs(pos.y - drawStart.y),
    });
  }, [isDrawing, drawStart, getImagePos, mode, annotationShape, polygonPoints]);

  const handleMouseUp = useCallback(() => {
    if (!isDrawing || !drawRect) {
      setIsDrawing(false);
      return;
    }

    setIsDrawing(false);
    setDrawStart(null);

    if (drawRect.w > MIN_BOX_SIZE && drawRect.h > MIN_BOX_SIZE) {
      if (annotationShape === AnnotationShape.BBox) {
        addAnnotation(createBBoxAnnotation(drawRect.x, drawRect.y, drawRect.w, drawRect.h, 0));
      } else if (annotationShape === AnnotationShape.OBB) {
        const cx = drawRect.x + drawRect.w / 2;
        const cy = drawRect.y + drawRect.h / 2;
        addAnnotation(createOBBAnnotation(cx, cy, drawRect.w, drawRect.h, 0, 0));
      }
    }

    setDrawRect(null);
  }, [isDrawing, drawRect, addAnnotation, annotationShape]);

  // Stage click for polygon point adding and selection
  const handleStageClick = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    // Polygon 添加点
    if (mode === LabelMode.Add && annotationShape === AnnotationShape.Polygon) {
      const pos = getImagePos(e);
      if (!pos) return;

      // 如果靠近第一个点，闭合多边形
      if (polygonPoints.length >= 3) {
        const first = polygonPoints[0];
        const dist = Math.sqrt((pos.x - first.x) ** 2 + (pos.y - first.y) ** 2);
        if (dist < 10 / scale) {
          // 闭合
          addAnnotation(createPolygonAnnotation([...polygonPoints], 0));
          setPolygonPoints([]);
          setPolygonPreview(null);
          return;
        }
      }

      setPolygonPoints((prev) => [...prev, pos]);
      return;
    }

    // 点击空白取消选中
    if (e.target === e.target.getStage() || e.target.name() === 'background-image') {
      clearSelection();
    }
  }, [mode, annotationShape, getImagePos, polygonPoints, scale, addAnnotation, clearSelection]);

  // 双击闭合 polygon
  const handleStageDblClick = useCallback(() => {
    if (mode === LabelMode.Add && annotationShape === AnnotationShape.Polygon && polygonPoints.length >= 3) {
      addAnnotation(createPolygonAnnotation([...polygonPoints], 0));
      setPolygonPoints([]);
      setPolygonPreview(null);
    }
  }, [mode, annotationShape, polygonPoints, addAnnotation]);

  // Escape 取消 polygon 绘制
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && polygonPoints.length > 0) {
        setPolygonPoints([]);
        setPolygonPreview(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [polygonPoints]);

  // 滚轮缩放
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

  const handleDragEnd = useCallback((uuid: string, e: Konva.KonvaEventObject<DragEvent>) => {
    const node = e.target;
    const ann = annotations.find((a) => a.uuid === uuid);
    if (!ann) return;

    if (ann.shape === AnnotationShape.BBox) {
      updateAnnotation(uuid, { x: node.x(), y: node.y() });
    } else if (ann.shape === AnnotationShape.OBB) {
      updateAnnotation(uuid, { cx: node.x() + ann.width / 2, cy: node.y() + ann.height / 2 } as Partial<OBBAnnotation>);
    }
  }, [updateAnnotation, annotations]);

  const handleTransformEnd = useCallback((uuid: string, e: Konva.KonvaEventObject<Event>) => {
    const node = e.target as Konva.Rect;
    const ann = annotations.find((a) => a.uuid === uuid);
    if (!ann) return;

    const sx = node.scaleX();
    const sy = node.scaleY();
    node.scaleX(1);
    node.scaleY(1);

    if (ann.shape === AnnotationShape.BBox) {
      updateAnnotation(uuid, {
        x: node.x(),
        y: node.y(),
        width: Math.max(MIN_BOX_SIZE, node.width() * sx),
        height: Math.max(MIN_BOX_SIZE, node.height() * sy),
      });
    } else if (ann.shape === AnnotationShape.OBB) {
      const w = Math.max(MIN_BOX_SIZE, node.width() * sx);
      const h = Math.max(MIN_BOX_SIZE, node.height() * sy);
      const rotation = node.rotation() || 0;
      const angleRad = (rotation * Math.PI) / 180;
      updateAnnotation(uuid, {
        cx: node.x() + w / 2,
        cy: node.y() + h / 2,
        width: w,
        height: h,
        angle: ann.angle + angleRad,
      } as Partial<OBBAnnotation>);
      node.rotation(0);
    }
  }, [updateAnnotation, annotations]);

  // Polygon 顶点拖拽
  const handlePolygonVertexDrag = useCallback((uuid: string, vertexIndex: number, e: Konva.KonvaEventObject<DragEvent>) => {
    const node = e.target;
    const ann = annotations.find((a) => a.uuid === uuid);
    if (!ann || ann.shape !== AnnotationShape.Polygon) return;

    const newPoints = [...ann.points];
    newPoints[vertexIndex] = { x: node.x(), y: node.y() };
    updateAnnotation(uuid, { points: newPoints } as Partial<PolygonAnnotation>);
  }, [updateAnnotation, annotations]);

  const fitToWindow = useCallback(() => {
    if (!image) return;
    const scaleX = stageSize.width / image.naturalWidth;
    const scaleY = stageSize.height / image.naturalHeight;
    const newScale = Math.min(scaleX, scaleY, 1);
    setScale(newScale);
    setPosition({
      x: (stageSize.width - image.naturalWidth * newScale) / 2,
      y: (stageSize.height - image.naturalHeight * newScale) / 2,
    });
  }, [image, stageSize]);

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

  const renderLabel = (x: number, y: number, classId: number) => {
    const label = classId >= 0 && classId < classes.length
      ? classes[classId]
      : `class_${classId}`;
    const color = getClassColor(classId);
    return (
      <>
        <Rect
          x={x}
          y={y - 18 / scale}
          width={label.length * 8 / scale + 8 / scale}
          height={18 / scale}
          fill={color}
          cornerRadius={2 / scale}
          listening={false}
        />
        <Text
          x={x + 4 / scale}
          y={y - 16 / scale}
          text={label}
          fontSize={12 / scale}
          fill="white"
          listening={false}
        />
      </>
    );
  };

  const renderBBox = (a: BBoxAnnotation, color: string, isSelected: boolean) => (
    <Group key={a.uuid}>
      <Rect
        id={`shape-${a.uuid}`}
        x={a.x}
        y={a.y}
        width={a.width}
        height={a.height}
        stroke={color}
        strokeWidth={isSelected ? 3 / scale : 2 / scale}
        fill={isSelected ? `${color}22` : 'transparent'}
        draggable={mode === LabelMode.Edit}
        onClick={(e) => { e.cancelBubble = true; selectAnnotation(a.uuid); }}
        onDragEnd={(e) => handleDragEnd(a.uuid, e)}
        onTransformEnd={(e) => handleTransformEnd(a.uuid, e)}
      />
      {renderLabel(a.x, a.y, a.classId)}
    </Group>
  );

  const renderPolygon = (a: PolygonAnnotation, color: string, isSelected: boolean) => {
    const flatPoints = a.points.flatMap((p) => [p.x, p.y]);
    const center = getPolygonCenter(a);
    return (
      <Group key={a.uuid}>
        <Line
          points={flatPoints}
          closed
          stroke={color}
          strokeWidth={isSelected ? 3 / scale : 2 / scale}
          fill={isSelected ? `${color}33` : `${color}11`}
          onClick={(e) => { e.cancelBubble = true; selectAnnotation(a.uuid); }}
        />
        {/* 编辑模式显示顶点 */}
        {isSelected && mode === LabelMode.Edit && a.points.map((p, i) => (
          <Circle
            key={`vertex-${a.uuid}-${i}`}
            x={p.x}
            y={p.y}
            radius={VERTEX_RADIUS / scale}
            fill="white"
            stroke={color}
            strokeWidth={2 / scale}
            draggable
            onDragEnd={(e) => handlePolygonVertexDrag(a.uuid, i, e)}
          />
        ))}
        {renderLabel(center.x, center.y, a.classId)}
      </Group>
    );
  };

  const renderOBB = (a: OBBAnnotation, color: string, isSelected: boolean) => {
    const vertices = getOBBVertices(a);
    const flatPoints = vertices.flatMap((p) => [p.x, p.y]);
    const angleDeg = (a.angle * 180) / Math.PI;
    const topLeftX = a.cx - a.width / 2;
    const topLeftY = a.cy - a.height / 2;

    return (
      <Group key={a.uuid}>
        {/* 用于 Transformer 拖拽/变换的隐形 Rect */}
        <Rect
          id={`shape-${a.uuid}`}
          x={topLeftX}
          y={topLeftY}
          width={a.width}
          height={a.height}
          offsetX={0}
          offsetY={0}
          rotation={angleDeg}
          stroke={color}
          strokeWidth={isSelected ? 3 / scale : 2 / scale}
          fill={isSelected ? `${color}22` : 'transparent'}
          draggable={mode === LabelMode.Edit}
          onClick={(e) => { e.cancelBubble = true; selectAnnotation(a.uuid); }}
          onDragEnd={(e) => {
            const node = e.target;
            const newCx = node.x() + a.width / 2;
            const newCy = node.y() + a.height / 2;
            updateAnnotation(a.uuid, { cx: newCx, cy: newCy } as Partial<OBBAnnotation>);
          }}
          onTransformEnd={(e) => handleTransformEnd(a.uuid, e)}
        />
        {/* 方向指示线（从中心到顶边中点） */}
        {isSelected && (
          <Line
            points={[a.cx, a.cy, vertices[0].x + (vertices[1].x - vertices[0].x) / 2, vertices[0].y + (vertices[1].y - vertices[0].y) / 2]}
            stroke={color}
            strokeWidth={1 / scale}
            dash={[4 / scale, 2 / scale]}
            listening={false}
          />
        )}
        {renderLabel(vertices[0].x, vertices[0].y, a.classId)}
      </Group>
    );
  };

  // ============ 光标样式 ============

  const getCursor = () => {
    if (mode !== LabelMode.Add) return 'default';
    if (annotationShape === AnnotationShape.Polygon) return 'crosshair';
    return 'crosshair';
  };

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
          {/* 图像 */}
          {image && (
            <KonvaImage
              image={image}
              name="background-image"
            />
          )}

          {/* 已有标注 */}
          {annotations.filter((a) => a.visible).map((a) => renderAnnotation(a))}

          {/* BBox/OBB 绘制中的临时矩形 */}
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

          {/* Polygon 绘制中的临时线 */}
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
              {/* 顶点 */}
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

          {/* Transformer */}
          <Transformer
            ref={transformerRef}
            boundBoxFunc={(oldBox, newBox) => {
              if (newBox.width < MIN_BOX_SIZE || newBox.height < MIN_BOX_SIZE) {
                return oldBox;
              }
              return newBox;
            }}
            rotateEnabled={annotationShape === AnnotationShape.OBB || annotations.find((a) => a.uuid === selectedUuid)?.shape === AnnotationShape.OBB}
            borderStroke="#1890ff"
            anchorStroke="#1890ff"
            anchorSize={8 / scale}
          />
        </Layer>
      </Stage>

      {/* 缩放比例 */}
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
