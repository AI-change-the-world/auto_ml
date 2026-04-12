import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Stage, Layer, Rect, Image as KonvaImage, Text, Group, Transformer } from 'react-konva';
import type Konva from 'konva';
import { useAnnotationStore } from '../../../stores/annotationStore';
import { useDatasetStore } from '../../../stores/datasetStore';
import { LabelMode, createBBoxAnnotation, getClassColor } from '../../../types';
import { parseYoloAnnotations } from '../../../utils/yolo';

const MIN_BOX_SIZE = 5;

const ImageCanvas: React.FC = () => {
  const stageRef = useRef<Konva.Stage>(null);
  const transformerRef = useRef<Konva.Transformer>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [stageSize, setStageSize] = useState({ width: 800, height: 600 });
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  // 绘制临时矩形
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState<{ x: number; y: number } | null>(null);
  const [drawRect, setDrawRect] = useState<{ x: number; y: number; w: number; h: number } | null>(null);

  const {
    annotations, mode, selectedUuid, classes,
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

      // 自适应缩放
      const scaleX = stageSize.width / img.naturalWidth;
      const scaleY = stageSize.height / img.naturalHeight;
      const newScale = Math.min(scaleX, scaleY, 1);
      setScale(newScale);
      setPosition({
        x: (stageSize.width - img.naturalWidth * newScale) / 2,
        y: (stageSize.height - img.naturalHeight * newScale) / 2,
      });

      // 解析标注
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

  // Transformer 绑定到选中节点
  useEffect(() => {
    const stage = stageRef.current;
    const transformer = transformerRef.current;
    if (!stage || !transformer) return;

    if (selectedUuid && mode === LabelMode.Edit) {
      const node = stage.findOne(`#bbox-${selectedUuid}`);
      if (node) {
        transformer.nodes([node]);
        transformer.getLayer()?.batchDraw();
        return;
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

  // 鼠标按下
  const handleMouseDown = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (mode !== LabelMode.Add) return;
    // 只响应左键
    if (e.evt.button !== 0) return;

    const pos = getImagePos(e);
    if (!pos) return;

    setIsDrawing(true);
    setDrawStart(pos);
    setDrawRect({ x: pos.x, y: pos.y, w: 0, h: 0 });
  }, [mode, getImagePos]);

  // 鼠标移动
  const handleMouseMove = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (!isDrawing || !drawStart) return;

    const pos = getImagePos(e);
    if (!pos) return;

    setDrawRect({
      x: Math.min(drawStart.x, pos.x),
      y: Math.min(drawStart.y, pos.y),
      w: Math.abs(pos.x - drawStart.x),
      h: Math.abs(pos.y - drawStart.y),
    });
  }, [isDrawing, drawStart, getImagePos]);

  // 鼠标松开
  const handleMouseUp = useCallback(() => {
    if (!isDrawing || !drawRect) {
      setIsDrawing(false);
      return;
    }

    setIsDrawing(false);
    setDrawStart(null);

    if (drawRect.w > MIN_BOX_SIZE && drawRect.h > MIN_BOX_SIZE) {
      const newAnnotation = createBBoxAnnotation(drawRect.x, drawRect.y, drawRect.w, drawRect.h, 0);
      addAnnotation(newAnnotation);
    }

    setDrawRect(null);
  }, [isDrawing, drawRect, addAnnotation]);

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

  // 点击空白区域取消选中
  const handleStageClick = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (e.target === e.target.getStage() || e.target.name() === 'background-image') {
      clearSelection();
    }
  }, [clearSelection]);

  // 标注框拖拽结束
  const handleDragEnd = useCallback((uuid: string, e: Konva.KonvaEventObject<DragEvent>) => {
    const node = e.target;
    updateAnnotation(uuid, {
      x: node.x(),
      y: node.y(),
    });
  }, [updateAnnotation]);

  // Transformer 变换结束
  const handleTransformEnd = useCallback((uuid: string, e: Konva.KonvaEventObject<Event>) => {
    const node = e.target as Konva.Rect;
    const scaleX = node.scaleX();
    const scaleY = node.scaleY();

    // 重置 scale，更新宽高
    node.scaleX(1);
    node.scaleY(1);

    updateAnnotation(uuid, {
      x: node.x(),
      y: node.y(),
      width: Math.max(MIN_BOX_SIZE, node.width() * scaleX),
      height: Math.max(MIN_BOX_SIZE, node.height() * scaleY),
    });
  }, [updateAnnotation]);

  // 适应窗口
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

  // 暴露 fitToWindow 给外部
  useEffect(() => {
    (window as unknown as Record<string, unknown>).__canvasFitToWindow = fitToWindow;
    return () => { delete (window as unknown as Record<string, unknown>).__canvasFitToWindow; };
  }, [fitToWindow]);

  return (
    <div
      ref={containerRef}
      style={{
        flex: 1,
        overflow: 'hidden',
        background: '#f0f0f0',
        cursor: mode === LabelMode.Add ? 'crosshair' : 'default',
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
      >
        <Layer x={position.x} y={position.y} scaleX={scale} scaleY={scale}>
          {/* 图像 */}
          {image && (
            <KonvaImage
              image={image}
              name="background-image"
            />
          )}

          {/* 标注框 */}
          {annotations.filter((a) => a.visible).map((annotation) => {
            const color = getClassColor(annotation.classId);
            const isSelected = annotation.uuid === selectedUuid;
            const label = annotation.classId >= 0 && annotation.classId < classes.length
              ? classes[annotation.classId]
              : `class_${annotation.classId}`;

            return (
              <Group key={annotation.uuid}>
                <Rect
                  id={`bbox-${annotation.uuid}`}
                  x={annotation.x}
                  y={annotation.y}
                  width={annotation.width}
                  height={annotation.height}
                  stroke={color}
                  strokeWidth={isSelected ? 3 / scale : 2 / scale}
                  fill={isSelected ? `${color}22` : 'transparent'}
                  draggable={mode === LabelMode.Edit}
                  onClick={(e) => {
                    e.cancelBubble = true;
                    selectAnnotation(annotation.uuid);
                  }}
                  onDragEnd={(e) => handleDragEnd(annotation.uuid, e)}
                  onTransformEnd={(e) => handleTransformEnd(annotation.uuid, e)}
                />
                {/* 类别标签 */}
                <Rect
                  x={annotation.x}
                  y={annotation.y - 18 / scale}
                  width={label.length * 8 / scale + 8 / scale}
                  height={18 / scale}
                  fill={color}
                  cornerRadius={2 / scale}
                  listening={false}
                />
                <Text
                  x={annotation.x + 4 / scale}
                  y={annotation.y - 16 / scale}
                  text={label}
                  fontSize={12 / scale}
                  fill="white"
                  listening={false}
                />
              </Group>
            );
          })}

          {/* 绘制中的临时矩形 */}
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

          {/* Transformer */}
          <Transformer
            ref={transformerRef}
            boundBoxFunc={(oldBox, newBox) => {
              if (newBox.width < MIN_BOX_SIZE || newBox.height < MIN_BOX_SIZE) {
                return oldBox;
              }
              return newBox;
            }}
            rotateEnabled={false}
            borderStroke="#1890ff"
            anchorStroke="#1890ff"
            anchorSize={8 / scale}
          />
        </Layer>
      </Stage>

      {/* 缩放比例显示 */}
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
