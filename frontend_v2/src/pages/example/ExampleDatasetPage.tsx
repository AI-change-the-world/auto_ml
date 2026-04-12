import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeftOutlined,
  TagOutlined,
  PictureOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  BulbOutlined,
  DeleteOutlined,
  UndoOutlined,
  EditOutlined,
  DragOutlined,
} from '@ant-design/icons';

/* ─── Static example data (no API calls) ─── */

const CLASSES = [
  { id: 45, name: 'bowl', color: '#ef4444' },
  { id: 49, name: 'orange', color: '#f59e0b' },
  { id: 50, name: 'broccoli', color: '#22c55e' },
];

const classMap = Object.fromEntries(CLASSES.map((c) => [c.id, c]));

interface YoloBox {
  classId: number;
  cx: number;
  cy: number;
  w: number;
  h: number;
}

interface UserBox {
  classId: number;
  x1: number; // normalized 0-1
  y1: number;
  x2: number;
  y2: number;
}

// YOLO labels from 000000000009.txt (normalized xywh)
const EXAMPLE_IMAGE = {
  src: '/example_dataset/000000000009.jpg',
  name: '000000000009.jpg',
  width: 640,
  height: 480,
  boxes: [
    { classId: 45, cx: 0.479492, cy: 0.688771, w: 0.955609, h: 0.5955 },
    { classId: 45, cx: 0.736516, cy: 0.247188, w: 0.498875, h: 0.476417 },
    { classId: 50, cx: 0.637063, cy: 0.732938, w: 0.494125, h: 0.510583 },
    { classId: 45, cx: 0.339438, cy: 0.418896, w: 0.678875, h: 0.7815 },
    { classId: 49, cx: 0.646836, cy: 0.132552, w: 0.118047, h: 0.0969375 },
    { classId: 49, cx: 0.773148, cy: 0.129802, w: 0.0907344, h: 0.0972292 },
    { classId: 49, cx: 0.668297, cy: 0.226906, w: 0.131281, h: 0.146896 },
    { classId: 49, cx: 0.642859, cy: 0.0792187, w: 0.148063, h: 0.148062 },
  ] as YoloBox[],
};

/* ─── Steps guide ─── */
const STEPS = [
  { num: 1, title: '创建数据集', desc: '在"数据集"页面上传你的图片或拖放压缩包。' },
  { num: 2, title: '创建标注项目', desc: '在"标注"页面创建项目，选择标注类型并关联数据集。' },
  { num: 3, title: '开始标注', desc: '进入标注工具，在图片上拖拽矩形框并指定类别。' },
  { num: 4, title: '训练模型', desc: '标注完成后创建训练任务，开始 YOLO 模型训练。' },
  { num: 5, title: '部署上线', desc: '训练结束后一键部署模型，通过 API 调用推理。' },
];

/* ─── Component ─── */
const ExampleDatasetPage: React.FC = () => {
  const navigate = useNavigate();

  // Display state
  const [showPreset, setShowPreset] = useState(true);
  const [hoveredClass, setHoveredClass] = useState<number | null>(null);
  const [imgSize, setImgSize] = useState({ w: 0, h: 0 });
  const imgRef = useRef<HTMLImageElement>(null);
  const canvasRef = useRef<HTMLDivElement>(null);

  // Interactive annotation state
  const [mode, setMode] = useState<'view' | 'draw'>('view');
  const [activeClassId, setActiveClassId] = useState(CLASSES[0].id);
  const [userBoxes, setUserBoxes] = useState<UserBox[]>([]);
  const [drawing, setDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState({ x: 0, y: 0 });
  const [drawCurrent, setDrawCurrent] = useState({ x: 0, y: 0 });
  const [selectedUserBox, setSelectedUserBox] = useState<number | null>(null);

  // Image size tracking
  useEffect(() => {
    const updateSize = () => {
      if (imgRef.current) {
        setImgSize({ w: imgRef.current.clientWidth, h: imgRef.current.clientHeight });
      }
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  const handleImageLoad = () => {
    if (imgRef.current) {
      setImgSize({ w: imgRef.current.clientWidth, h: imgRef.current.clientHeight });
    }
  };

  // Get mouse position relative to image (normalized 0-1)
  const getRelPos = useCallback(
    (e: React.MouseEvent) => {
      if (!imgRef.current) return { x: 0, y: 0 };
      const rect = imgRef.current.getBoundingClientRect();
      return {
        x: Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width)),
        y: Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height)),
      };
    },
    [],
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (mode !== 'draw') return;
      e.preventDefault();
      const pos = getRelPos(e);
      setDrawing(true);
      setDrawStart(pos);
      setDrawCurrent(pos);
      setSelectedUserBox(null);
    },
    [mode, getRelPos],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!drawing) return;
      setDrawCurrent(getRelPos(e));
    },
    [drawing, getRelPos],
  );

  const handleMouseUp = useCallback(() => {
    if (!drawing) return;
    setDrawing(false);
    const x1 = Math.min(drawStart.x, drawCurrent.x);
    const y1 = Math.min(drawStart.y, drawCurrent.y);
    const x2 = Math.max(drawStart.x, drawCurrent.x);
    const y2 = Math.max(drawStart.y, drawCurrent.y);
    // Ignore tiny boxes (accidental clicks)
    if (x2 - x1 > 0.01 && y2 - y1 > 0.01) {
      setUserBoxes((prev) => [...prev, { classId: activeClassId, x1, y1, x2, y2 }]);
    }
  }, [drawing, drawStart, drawCurrent, activeClassId]);

  const deleteUserBox = (idx: number) => {
    setUserBoxes((prev) => prev.filter((_, i) => i !== idx));
    if (selectedUserBox === idx) setSelectedUserBox(null);
  };

  const clearUserBoxes = () => {
    setUserBoxes([]);
    setSelectedUserBox(null);
  };

  // Convert preset YOLO box to pixel coords
  const yoloToPixel = (box: YoloBox) => ({
    x: (box.cx - box.w / 2) * imgSize.w,
    y: (box.cy - box.h / 2) * imgSize.h,
    w: box.w * imgSize.w,
    h: box.h * imgSize.h,
  });

  return (
    <div className="page-container">
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#999', marginBottom: 16 }}>
        <span
          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
          onClick={() => navigate('/')}
        >
          <ArrowLeftOutlined style={{ fontSize: 12 }} /> 首页
        </span>
        <span>/</span>
        <span style={{ color: '#111', fontWeight: 500 }}>Example Dataset</span>
      </div>

      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8, flexWrap: 'wrap' }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#111', margin: 0 }}>Example Dataset</h1>
          <span style={{ padding: '3px 12px', background: '#eef2ff', color: '#4f6ef7', fontSize: 12, borderRadius: 999, fontWeight: 500 }}>
            目标检测
          </span>
          <span style={{ padding: '3px 12px', background: '#fef3c7', color: '#d97706', fontSize: 12, borderRadius: 999, fontWeight: 500 }}>
            交互演示
          </span>
        </div>
        <p style={{ fontSize: 14, color: '#666', margin: 0, lineHeight: 1.6 }}>
          在下方图片上试试拖拽画框标注！切换到<strong>「标注模式」</strong>后，选择类别，在图片上拖动鼠标即可创建标注框。这里的操作不会保存，仅用于体验标注流程。
        </p>
      </div>

      {/* Main content */}
      <div style={{ display: 'flex', gap: 20, marginBottom: 32, flexWrap: 'wrap' }}>
        {/* ─── Image canvas area ─── */}
        <div style={{ flex: '1 1 600px', minWidth: 0 }}>
          {/* Toolbar */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '10px 16px',
              background: '#1a1a2e',
              borderRadius: '12px 12px 0 0',
              flexWrap: 'wrap',
              gap: 8,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <PictureOutlined style={{ color: '#8b5cf6', fontSize: 14 }} />
              <span style={{ color: '#ddd', fontSize: 13, fontWeight: 500 }}>{EXAMPLE_IMAGE.name}</span>
              <span style={{ color: '#666', fontSize: 12 }}>{EXAMPLE_IMAGE.width}×{EXAMPLE_IMAGE.height}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {/* Mode toggle */}
              <button
                onClick={() => setMode(mode === 'view' ? 'draw' : 'view')}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6, padding: '5px 14px',
                  background: mode === 'draw' ? 'rgba(79,110,247,0.3)' : 'rgba(255,255,255,0.1)',
                  border: mode === 'draw' ? '1px solid #4f6ef7' : '1px solid rgba(255,255,255,0.15)',
                  borderRadius: 6, color: mode === 'draw' ? '#93b4ff' : '#999', fontSize: 12, cursor: 'pointer',
                  fontWeight: mode === 'draw' ? 600 : 400,
                }}
              >
                {mode === 'draw' ? <EditOutlined /> : <DragOutlined />}
                {mode === 'draw' ? '标注模式' : '查看模式'}
              </button>
              {/* Toggle preset */}
              <button
                onClick={() => setShowPreset(!showPreset)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6, padding: '5px 12px',
                  background: showPreset ? 'rgba(139,92,246,0.2)' : 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.15)', borderRadius: 6,
                  color: showPreset ? '#a78bfa' : '#999', fontSize: 12, cursor: 'pointer',
                }}
              >
                {showPreset ? <EyeOutlined /> : <EyeInvisibleOutlined />}
                预设标注
              </button>
            </div>
          </div>

          {/* Canvas */}
          <div
            ref={canvasRef}
            style={{
              position: 'relative',
              display: 'flex',
              justifyContent: 'center',
              background: '#111',
              borderRadius: '0 0 12px 12px',
              overflow: 'hidden',
              cursor: mode === 'draw' ? 'crosshair' : 'default',
              userSelect: 'none',
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={() => { if (drawing) handleMouseUp(); }}
          >
            <img
              ref={imgRef}
              src={EXAMPLE_IMAGE.src}
              alt={EXAMPLE_IMAGE.name}
              onLoad={handleImageLoad}
              draggable={false}
              style={{ maxWidth: '100%', maxHeight: 520, objectFit: 'contain', display: 'block' }}
            />

            {/* SVG overlay */}
            {imgSize.w > 0 && (
              <svg
                style={{
                  position: 'absolute', top: 0, left: '50%', transform: 'translateX(-50%)',
                  width: imgSize.w, height: imgSize.h, pointerEvents: 'none',
                }}
                viewBox={`0 0 ${imgSize.w} ${imgSize.h}`}
              >
                {/* Preset boxes */}
                {showPreset && EXAMPLE_IMAGE.boxes.map((box, idx) => {
                  const cls = classMap[box.classId];
                  if (!cls) return null;
                  const p = yoloToPixel(box);
                  const highlighted = hoveredClass === box.classId;
                  return (
                    <g key={`preset-${idx}`} opacity={highlighted ? 1 : 0.7}>
                      <rect x={p.x} y={p.y} width={p.w} height={p.h}
                        fill={highlighted ? `${cls.color}15` : 'none'}
                        stroke={cls.color} strokeWidth={highlighted ? 2.5 : 1.5}
                        strokeDasharray={highlighted ? 'none' : '4 2'} rx={2} />
                      <rect x={p.x} y={Math.max(0, p.y - 18)} width={cls.name.length * 7 + 12} height={18}
                        fill={cls.color} rx={3} opacity={0.85} />
                      <text x={p.x + 6} y={Math.max(0, p.y - 18) + 13} fill="#fff" fontSize={10}
                        fontWeight={600} fontFamily="monospace">{cls.name}</text>
                    </g>
                  );
                })}

                {/* User-drawn boxes */}
                {userBoxes.map((box, idx) => {
                  const cls = classMap[box.classId] || CLASSES[0];
                  const x = box.x1 * imgSize.w;
                  const y = box.y1 * imgSize.h;
                  const w = (box.x2 - box.x1) * imgSize.w;
                  const h = (box.y2 - box.y1) * imgSize.h;
                  const selected = selectedUserBox === idx;
                  return (
                    <g key={`user-${idx}`} style={{ pointerEvents: 'auto', cursor: 'pointer' }}
                      onClick={(e) => { e.stopPropagation(); setSelectedUserBox(idx); }}>
                      <rect x={x} y={y} width={w} height={h}
                        fill={selected ? `${cls.color}20` : `${cls.color}10`}
                        stroke={cls.color} strokeWidth={selected ? 3 : 2} rx={2} />
                      {/* Label */}
                      <rect x={x} y={Math.max(0, y - 20)} width={cls.name.length * 8 + 30} height={20}
                        fill={cls.color} rx={3} />
                      <text x={x + 6} y={Math.max(0, y - 20) + 14} fill="#fff" fontSize={11}
                        fontWeight={600} fontFamily="monospace">
                        {cls.name} ✎
                      </text>
                      {/* Corner handles when selected */}
                      {selected && <>
                        {[[x, y], [x + w, y], [x, y + h], [x + w, y + h]].map(([cx, cy], hi) => (
                          <circle key={hi} cx={cx} cy={cy} r={4} fill="#fff" stroke={cls.color} strokeWidth={2} />
                        ))}
                      </>}
                    </g>
                  );
                })}

                {/* Drawing preview */}
                {drawing && (() => {
                  const cls = classMap[activeClassId] || CLASSES[0];
                  const x = Math.min(drawStart.x, drawCurrent.x) * imgSize.w;
                  const y = Math.min(drawStart.y, drawCurrent.y) * imgSize.h;
                  const w = Math.abs(drawCurrent.x - drawStart.x) * imgSize.w;
                  const h = Math.abs(drawCurrent.y - drawStart.y) * imgSize.h;
                  return (
                    <rect x={x} y={y} width={w} height={h}
                      fill={`${cls.color}15`} stroke={cls.color} strokeWidth={2}
                      strokeDasharray="6 3" rx={2} />
                  );
                })()}
              </svg>
            )}

            {/* Mode hint overlay */}
            {mode === 'draw' && userBoxes.length === 0 && !drawing && (
              <div style={{
                position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                background: 'rgba(0,0,0,0.6)', color: '#fff', padding: '12px 24px', borderRadius: 10,
                fontSize: 14, pointerEvents: 'none', textAlign: 'center', whiteSpace: 'nowrap',
              }}>
                🖱️ 在图片上拖拽鼠标画框
              </div>
            )}
          </div>

          {/* User action bar */}
          {userBoxes.length > 0 && (
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              marginTop: 10, padding: '8px 14px', background: '#fff', border: '1px solid #eee', borderRadius: 10,
              flexWrap: 'wrap', gap: 8,
            }}>
              <span style={{ fontSize: 13, color: '#666' }}>
                你画了 <strong style={{ color: '#4f6ef7' }}>{userBoxes.length}</strong> 个标注框
                {selectedUserBox !== null && (
                  <span style={{ marginLeft: 8 }}>
                    — 已选中 #{selectedUserBox + 1} ({classMap[userBoxes[selectedUserBox].classId]?.name})
                  </span>
                )}
              </span>
              <div style={{ display: 'flex', gap: 6 }}>
                {selectedUserBox !== null && (
                  <button onClick={() => deleteUserBox(selectedUserBox)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 4, padding: '4px 12px',
                      background: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca',
                      borderRadius: 6, fontSize: 12, cursor: 'pointer',
                    }}>
                    <DeleteOutlined /> 删除选中
                  </button>
                )}
                <button onClick={clearUserBoxes}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 4, padding: '4px 12px',
                    background: '#f5f5f5', color: '#666', border: '1px solid #e5e5e5',
                    borderRadius: 6, fontSize: 12, cursor: 'pointer',
                  }}>
                  <UndoOutlined /> 清除全部
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ─── Sidebar ─── */}
        <div style={{ flex: '0 0 280px', minWidth: 250 }}>
          {/* Class selector (for drawing) */}
          <div style={{
            background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 20, marginBottom: 16,
          }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: '#111', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: 6 }}>
              <TagOutlined style={{ color: '#22c55e' }} /> 标注类别
            </h3>
            <p style={{ fontSize: 12, color: '#999', margin: '0 0 12px' }}>
              {mode === 'draw' ? '选择类别后在图片上画框' : '悬浮查看各类别标注'}
            </p>
            {CLASSES.map((cls) => {
              const presetCount = EXAMPLE_IMAGE.boxes.filter((b) => b.classId === cls.id).length;
              const userCount = userBoxes.filter((b) => b.classId === cls.id).length;
              const isActive = activeClassId === cls.id;
              return (
                <div
                  key={cls.id}
                  onClick={() => setActiveClassId(cls.id)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10, padding: '9px 12px',
                    borderRadius: 8, marginBottom: 4, cursor: 'pointer', transition: 'all 0.15s',
                    background: isActive && mode === 'draw' ? `${cls.color}10` : '#fafafa',
                    border: isActive && mode === 'draw' ? `2px solid ${cls.color}` : '2px solid transparent',
                  }}
                  onMouseEnter={() => setHoveredClass(cls.id)}
                  onMouseLeave={() => setHoveredClass(null)}
                >
                  <div style={{ width: 16, height: 16, borderRadius: 4, background: cls.color, flexShrink: 0 }} />
                  <span style={{ flex: 1, fontSize: 13, fontWeight: 500, color: '#333' }}>{cls.name}</span>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <span style={{
                      fontSize: 11, padding: '1px 6px', background: '#f5f5f5', borderRadius: 999, color: '#999',
                    }}>{presetCount}</span>
                    {userCount > 0 && (
                      <span style={{
                        fontSize: 11, padding: '1px 6px', background: `${cls.color}15`, borderRadius: 999,
                        color: cls.color, fontWeight: 600,
                      }}>+{userCount}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Dataset info */}
          <div style={{
            background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 20, marginBottom: 16,
          }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: '#111', margin: '0 0 12px', display: 'flex', alignItems: 'center', gap: 6 }}>
              <InfoCircleOutlined style={{ color: '#4f6ef7' }} /> 数据集信息
            </h3>
            {[
              { label: '标注格式', value: 'YOLO v8' },
              { label: '预设标注框', value: `${EXAMPLE_IMAGE.boxes.length} 个` },
              { label: '你的标注框', value: `${userBoxes.length} 个` },
              { label: '类别数', value: `${CLASSES.length} 个` },
              { label: '图片尺寸', value: `${EXAMPLE_IMAGE.width}×${EXAMPLE_IMAGE.height}` },
            ].map((item, i) => (
              <div key={i} style={{
                display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: 13,
                borderBottom: i < 4 ? '1px solid #f8f8f8' : 'none',
              }}>
                <span style={{ color: '#888' }}>{item.label}</span>
                <span style={{ color: '#111', fontWeight: 500 }}>{item.value}</span>
              </div>
            ))}
          </div>

          {/* YOLO preview */}
          <div style={{
            background: '#1a1a2e', borderRadius: 12, padding: 14,
            fontFamily: 'monospace', fontSize: 11, lineHeight: 1.8, color: '#a5b4fc',
            overflow: 'auto', maxHeight: 180,
          }}>
            <div style={{ color: '#666', marginBottom: 4, fontSize: 10, fontFamily: 'sans-serif' }}>
              YOLO 标注预览
            </div>
            {EXAMPLE_IMAGE.boxes.slice(0, 4).map((box, i) => (
              <div key={`p-${i}`} style={{ color: classMap[box.classId]?.color ?? '#888', opacity: 0.6 }}>
                {box.classId} {box.cx.toFixed(4)} {box.cy.toFixed(4)} {box.w.toFixed(4)} {box.h.toFixed(4)}
              </div>
            ))}
            {EXAMPLE_IMAGE.boxes.length > 4 && (
              <div style={{ color: '#555' }}>... +{EXAMPLE_IMAGE.boxes.length - 4} more</div>
            )}
            {userBoxes.length > 0 && (
              <>
                <div style={{ color: '#4f6ef7', marginTop: 6, fontSize: 10, fontFamily: 'sans-serif' }}>
                  — 你的标注 —
                </div>
                {userBoxes.map((box, i) => {
                  const cx = ((box.x1 + box.x2) / 2);
                  const cy = ((box.y1 + box.y2) / 2);
                  const w = box.x2 - box.x1;
                  const h = box.y2 - box.y1;
                  return (
                    <div key={`u-${i}`} style={{ color: classMap[box.classId]?.color ?? '#4f6ef7' }}>
                      {box.classId} {cx.toFixed(4)} {cy.toFixed(4)} {w.toFixed(4)} {h.toFixed(4)}
                    </div>
                  );
                })}
              </>
            )}
          </div>
        </div>
      </div>

      {/* ─── How-to Guide ─── */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{
          fontSize: 20, fontWeight: 700, color: '#111', margin: '0 0 6px',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <BulbOutlined style={{ color: '#f59e0b' }} /> 标注工作流
        </h2>
        <p style={{ fontSize: 14, color: '#888', margin: '0 0 20px' }}>从数据准备到模型部署</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 14 }}>
          {STEPS.map((step) => (
            <div key={step.num} style={{
              background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 18,
              transition: 'box-shadow 0.2s',
            }}
              onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.06)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; }}
            >
              <div style={{
                width: 32, height: 32, borderRadius: 8, background: '#eef2ff', color: '#4f6ef7',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 700, fontSize: 15, marginBottom: 10,
              }}>{step.num}</div>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: '#111', margin: '0 0 4px' }}>{step.title}</h3>
              <p style={{ fontSize: 12, color: '#666', margin: 0, lineHeight: 1.5 }}>{step.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div style={{
        background: 'linear-gradient(135deg, #4f6ef7 0%, #7c3aed 100%)', borderRadius: 16,
        padding: '28px 36px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexWrap: 'wrap', gap: 16,
      }}>
        <div>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: '#fff', margin: '0 0 4px' }}>准备好开始标注了吗？</h3>
          <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.8)', margin: 0 }}>创建你自己的数据集，上传图片开始标注</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={() => navigate('/datasets')} style={{
            padding: '10px 24px', background: '#fff', color: '#4f6ef7', border: 'none',
            borderRadius: 10, fontSize: 14, fontWeight: 600, cursor: 'pointer',
          }}>
            <CheckCircleOutlined /> 创建数据集
          </button>
          <button onClick={() => navigate('/annotations')} style={{
            padding: '10px 24px', background: 'rgba(255,255,255,0.15)', color: '#fff',
            border: '1px solid rgba(255,255,255,0.3)', borderRadius: 10, fontSize: 14, fontWeight: 500,
            cursor: 'pointer',
          }}>
            创建标注项目
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExampleDatasetPage;
