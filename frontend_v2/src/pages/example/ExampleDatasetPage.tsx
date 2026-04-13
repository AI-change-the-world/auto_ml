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
import { useTranslation } from 'react-i18next';

/* ─── Static data ─── */
const DEFAULT_CLASSES = [
  { id: 45, name: 'bowl', color: '#ef4444' },
  { id: 49, name: 'orange', color: '#f59e0b' },
  { id: 50, name: 'broccoli', color: '#22c55e' },
];
const CLASS_COLORS = ['#ef4444', '#f59e0b', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];
// classMap will be derived from state

interface YoloBox { classId: number; cx: number; cy: number; w: number; h: number; }
interface UserBox { classId: number; x1: number; y1: number; x2: number; y2: number; }

const EXAMPLE_IMAGE = {
  src: '/example_dataset/000000000009.jpg',
  name: '000000000009.jpg',
  width: 640, height: 480,
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

const STEPS = [
  { num: 1, title: 'step1Title', desc: 'step1Desc' },
  { num: 2, title: 'step2Title', desc: 'step2Desc' },
  { num: 3, title: 'step3Title', desc: 'step3Desc' },
  { num: 4, title: 'step4Title', desc: 'step4Desc' },
  { num: 5, title: 'step5Title', desc: 'step5Desc' },
];

/* ─── Drag action types ─── */
type HandleId = 'tl' | 'tr' | 'bl' | 'br' | 'top' | 'bottom' | 'left' | 'right';
type DragAction =
  | { type: 'none' }
  | { type: 'draw'; startX: number; startY: number }
  | { type: 'move'; boxIdx: number; offsetX: number; offsetY: number }
  | { type: 'resize'; boxIdx: number; handle: HandleId; anchorX: number; anchorY: number };

const HANDLE_SIZE = 0.015; // normalized hit area

/* ─── Component ─── */
const ExampleDatasetPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation('example');
  const tc = useTranslation('common').t;

  const [showPreset, setShowPreset] = useState(true);
  const [hoveredClass, setHoveredClass] = useState<number | null>(null);
  const [imgSize, setImgSize] = useState({ w: 0, h: 0 });
  const imgRef = useRef<HTMLImageElement>(null);

  const [mode, setMode] = useState<'view' | 'draw'>('view');
  const [classes, setClasses] = useState(DEFAULT_CLASSES);
  const [activeClassId, setActiveClassId] = useState(DEFAULT_CLASSES[0].id);
  const classMap = Object.fromEntries(classes.map((c) => [c.id, c]));
  const [userBoxes, setUserBoxes] = useState<UserBox[]>([]);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [dragAction, setDragAction] = useState<DragAction>({ type: 'none' });
  const [dragCurrent, setDragCurrent] = useState({ x: 0, y: 0 });

  // Image size tracking
  useEffect(() => {
    const update = () => {
      if (imgRef.current) setImgSize({ w: imgRef.current.clientWidth, h: imgRef.current.clientHeight });
    };
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  const handleImageLoad = () => {
    if (imgRef.current) setImgSize({ w: imgRef.current.clientWidth, h: imgRef.current.clientHeight });
  };

  // Normalized position relative to image
  const getRelPos = useCallback((e: React.MouseEvent | MouseEvent) => {
    if (!imgRef.current) return { x: 0, y: 0 };
    const rect = imgRef.current.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width)),
      y: Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height)),
    };
  }, []);

  // Hit-test: which handle or box body is under the cursor?
  const hitTest = useCallback((pos: { x: number; y: number }): { boxIdx: number; part: 'body' | HandleId } | null => {
    // Check from top (newest) to bottom
    for (let i = userBoxes.length - 1; i >= 0; i--) {
      const b = userBoxes[i];
      const hs = HANDLE_SIZE;
      // Corner handles (check first, they're smaller targets on top)
      const corners: { id: HandleId; cx: number; cy: number }[] = [
        { id: 'tl', cx: b.x1, cy: b.y1 },
        { id: 'tr', cx: b.x2, cy: b.y1 },
        { id: 'bl', cx: b.x1, cy: b.y2 },
        { id: 'br', cx: b.x2, cy: b.y2 },
      ];
      for (const c of corners) {
        if (Math.abs(pos.x - c.cx) < hs && Math.abs(pos.y - c.cy) < hs) {
          return { boxIdx: i, part: c.id };
        }
      }
      // Edge handles (midpoints)
      const edges: { id: HandleId; cx: number; cy: number }[] = [
        { id: 'top', cx: (b.x1 + b.x2) / 2, cy: b.y1 },
        { id: 'bottom', cx: (b.x1 + b.x2) / 2, cy: b.y2 },
        { id: 'left', cx: b.x1, cy: (b.y1 + b.y2) / 2 },
        { id: 'right', cx: b.x2, cy: (b.y1 + b.y2) / 2 },
      ];
      for (const e of edges) {
        if (Math.abs(pos.x - e.cx) < hs && Math.abs(pos.y - e.cy) < hs) {
          return { boxIdx: i, part: e.id };
        }
      }
      // Body
      if (pos.x >= b.x1 && pos.x <= b.x2 && pos.y >= b.y1 && pos.y <= b.y2) {
        return { boxIdx: i, part: 'body' };
      }
    }
    return null;
  }, [userBoxes]);

  // ─── Mouse handlers ───
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (mode !== 'draw') return;
    e.preventDefault();
    const pos = getRelPos(e);

    // First, check if clicking on existing box
    const hit = hitTest(pos);
    if (hit) {
      const b = userBoxes[hit.boxIdx];
      setSelectedIdx(hit.boxIdx);
      if (hit.part === 'body') {
        setDragAction({ type: 'move', boxIdx: hit.boxIdx, offsetX: pos.x - b.x1, offsetY: pos.y - b.y1 });
      } else {
        // Resize: anchor is the opposite corner/edge
        let ax: number, ay: number;
        switch (hit.part) {
          case 'tl': ax = b.x2; ay = b.y2; break;
          case 'tr': ax = b.x1; ay = b.y2; break;
          case 'bl': ax = b.x2; ay = b.y1; break;
          case 'br': ax = b.x1; ay = b.y1; break;
          case 'top': ax = (b.x1 + b.x2) / 2; ay = b.y2; break;
          case 'bottom': ax = (b.x1 + b.x2) / 2; ay = b.y1; break;
          case 'left': ax = b.x2; ay = (b.y1 + b.y2) / 2; break;
          case 'right': ax = b.x1; ay = (b.y1 + b.y2) / 2; break;
        }
        setDragAction({ type: 'resize', boxIdx: hit.boxIdx, handle: hit.part, anchorX: ax!, anchorY: ay! });
      }
    } else {
      // Draw new box
      setSelectedIdx(null);
      setDragAction({ type: 'draw', startX: pos.x, startY: pos.y });
    }
    setDragCurrent(pos);
  }, [mode, getRelPos, hitTest, userBoxes]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (dragAction.type === 'none') return;
    const pos = getRelPos(e);
    setDragCurrent(pos);

    if (dragAction.type === 'move') {
      const b = userBoxes[dragAction.boxIdx];
      const bw = b.x2 - b.x1;
      const bh = b.y2 - b.y1;
      let nx1 = pos.x - dragAction.offsetX;
      let ny1 = pos.y - dragAction.offsetY;
      // Clamp to image bounds
      nx1 = Math.max(0, Math.min(1 - bw, nx1));
      ny1 = Math.max(0, Math.min(1 - bh, ny1));
      setUserBoxes((prev) => prev.map((box, i) =>
        i === dragAction.boxIdx ? { ...box, x1: nx1, y1: ny1, x2: nx1 + bw, y2: ny1 + bh } : box
      ));
    } else if (dragAction.type === 'resize') {
      const { handle, anchorX, anchorY, boxIdx } = dragAction;
      const b = userBoxes[boxIdx];
      let nx1: number, ny1: number, nx2: number, ny2: number;
      switch (handle) {
        case 'tl': case 'tr': case 'bl': case 'br':
          nx1 = Math.min(pos.x, anchorX); ny1 = Math.min(pos.y, anchorY);
          nx2 = Math.max(pos.x, anchorX); ny2 = Math.max(pos.y, anchorY);
          break;
        case 'top':
          nx1 = b.x1; nx2 = b.x2; ny1 = Math.min(pos.y, anchorY); ny2 = Math.max(pos.y, anchorY);
          break;
        case 'bottom':
          nx1 = b.x1; nx2 = b.x2; ny1 = Math.min(pos.y, anchorY); ny2 = Math.max(pos.y, anchorY);
          break;
        case 'left':
          ny1 = b.y1; ny2 = b.y2; nx1 = Math.min(pos.x, anchorX); nx2 = Math.max(pos.x, anchorX);
          break;
        case 'right':
          ny1 = b.y1; ny2 = b.y2; nx1 = Math.min(pos.x, anchorX); nx2 = Math.max(pos.x, anchorX);
          break;
        default: return;
      }
      // Min size
      if (nx2 - nx1 > 0.01 && ny2 - ny1 > 0.01) {
        setUserBoxes((prev) => prev.map((box, i) =>
          i === boxIdx ? { ...box, x1: nx1, y1: ny1, x2: nx2, y2: ny2 } : box
        ));
      }
    }
  }, [dragAction, getRelPos, userBoxes]);

  const handleMouseUp = useCallback(() => {
    if (dragAction.type === 'draw') {
      const x1 = Math.min(dragAction.startX, dragCurrent.x);
      const y1 = Math.min(dragAction.startY, dragCurrent.y);
      const x2 = Math.max(dragAction.startX, dragCurrent.x);
      const y2 = Math.max(dragAction.startY, dragCurrent.y);
      if (x2 - x1 > 0.01 && y2 - y1 > 0.01) {
        const newIdx = userBoxes.length;
        setUserBoxes((prev) => [...prev, { classId: activeClassId, x1, y1, x2, y2 }]);
        setSelectedIdx(newIdx);
      }
    }
    setDragAction({ type: 'none' });
  }, [dragAction, dragCurrent, activeClassId, userBoxes.length]);

  // Global mouseup to handle drag release outside canvas
  useEffect(() => {
    const onUp = () => { if (dragAction.type !== 'none') setDragAction({ type: 'none' }); };
    window.addEventListener('mouseup', onUp);
    return () => window.removeEventListener('mouseup', onUp);
  }, [dragAction]);

  const deleteUserBox = (idx: number) => {
    setUserBoxes((prev) => prev.filter((_, i) => i !== idx));
    setSelectedIdx(null);
  };

  const changeBoxClass = (idx: number, classId: number) => {
    setUserBoxes((prev) => prev.map((b, i) => i === idx ? { ...b, classId } : b));
  };

  const clearUserBoxes = () => { setUserBoxes([]); setSelectedIdx(null); };

  const yoloToPixel = (box: YoloBox) => ({
    x: (box.cx - box.w / 2) * imgSize.w, y: (box.cy - box.h / 2) * imgSize.h,
    w: box.w * imgSize.w, h: box.h * imgSize.h,
  });

  // Cursor based on hover target
  const getCursor = useCallback((e: React.MouseEvent) => {
    if (mode !== 'draw') return 'default';
    if (dragAction.type === 'move') return 'grabbing';
    if (dragAction.type === 'resize') return 'nwse-resize';
    if (dragAction.type === 'draw') return 'crosshair';
    const pos = getRelPos(e);
    const hit = hitTest(pos);
    if (!hit) return 'crosshair';
    if (hit.part === 'body') return 'grab';
    if (hit.part === 'tl' || hit.part === 'br') return 'nwse-resize';
    if (hit.part === 'tr' || hit.part === 'bl') return 'nesw-resize';
    if (hit.part === 'top' || hit.part === 'bottom') return 'ns-resize';
    return 'ew-resize';
  }, [mode, dragAction, getRelPos, hitTest]);

  const [cursorStyle, setCursorStyle] = useState('crosshair');

  // Render handle circles for selected box
  const renderHandles = (b: UserBox, color: string) => {
    const handles: { id: string; x: number; y: number }[] = [
      { id: 'tl', x: b.x1, y: b.y1 }, { id: 'tr', x: b.x2, y: b.y1 },
      { id: 'bl', x: b.x1, y: b.y2 }, { id: 'br', x: b.x2, y: b.y2 },
      { id: 'top', x: (b.x1 + b.x2) / 2, y: b.y1 },
      { id: 'bottom', x: (b.x1 + b.x2) / 2, y: b.y2 },
      { id: 'left', x: b.x1, y: (b.y1 + b.y2) / 2 },
      { id: 'right', x: b.x2, y: (b.y1 + b.y2) / 2 },
    ];
    return handles.map((h) => {
      const isCorner = ['tl', 'tr', 'bl', 'br'].includes(h.id);
      return (
        <rect
          key={h.id}
          x={h.x * imgSize.w - (isCorner ? 5 : 4)}
          y={h.y * imgSize.h - (isCorner ? 5 : 4)}
          width={isCorner ? 10 : 8}
          height={isCorner ? 10 : 8}
          rx={isCorner ? 2 : 1}
          fill="#fff"
          stroke={color}
          strokeWidth={2}
        />
      );
    });
  };

  return (
    <div className="page-container">
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#999', marginBottom: 16 }}>
        <span style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }} onClick={() => navigate('/')}>
          <ArrowLeftOutlined style={{ fontSize: 12 }} /> 首页
        </span>
        <span>/</span>
        <span style={{ color: '#111', fontWeight: 500 }}>Example Dataset</span>
      </div>

      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8, flexWrap: 'wrap' }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#111', margin: 0 }}>Example Dataset</h1>
          <span style={{ padding: '3px 12px', background: '#eef2ff', color: '#4f6ef7', fontSize: 12, borderRadius: 999, fontWeight: 500 }}>{t('objectDetection')}</span>
          <span style={{ padding: '3px 12px', background: '#fef3c7', color: '#d97706', fontSize: 12, borderRadius: 999, fontWeight: 500 }}>{t('interactiveDemo')}</span>
        </div>
        <p style={{ fontSize: 14, color: '#666', margin: 0, lineHeight: 1.6 }} dangerouslySetInnerHTML={{ __html: t('demoDesc') }} />
      </div>

      <div style={{ display: 'flex', gap: 20, marginBottom: 32, flexWrap: 'wrap' }}>
        {/* ─── Canvas ─── */}
        <div style={{ flex: '1 1 600px', minWidth: 0 }}>
          {/* Toolbar */}
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '10px 16px', background: '#1a1a2e', borderRadius: '12px 12px 0 0', flexWrap: 'wrap', gap: 8,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <PictureOutlined style={{ color: '#8b5cf6', fontSize: 14 }} />
              <span style={{ color: '#ddd', fontSize: 13, fontWeight: 500 }}>{EXAMPLE_IMAGE.name}</span>
              <span style={{ color: '#666', fontSize: 12 }}>{EXAMPLE_IMAGE.width}×{EXAMPLE_IMAGE.height}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <button onClick={() => { setMode(mode === 'view' ? 'draw' : 'view'); setSelectedIdx(null); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6, padding: '5px 14px',
                  background: mode === 'draw' ? 'rgba(79,110,247,0.3)' : 'rgba(255,255,255,0.1)',
                  border: mode === 'draw' ? '1px solid #4f6ef7' : '1px solid rgba(255,255,255,0.15)',
                  borderRadius: 6, color: mode === 'draw' ? '#93b4ff' : '#999', fontSize: 12, cursor: 'pointer',
                  fontWeight: mode === 'draw' ? 600 : 400,
                }}>
                {mode === 'draw' ? <EditOutlined /> : <DragOutlined />}
                {mode === 'draw' ? t('annotateMode') : t('viewMode')}
              </button>
              <button onClick={() => setShowPreset(!showPreset)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6, padding: '5px 12px',
                  background: showPreset ? 'rgba(139,92,246,0.2)' : 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.15)', borderRadius: 6,
                  color: showPreset ? '#a78bfa' : '#999', fontSize: 12, cursor: 'pointer',
                }}>
                {showPreset ? <EyeOutlined /> : <EyeInvisibleOutlined />}
                {t('presetAnnotation')}
              </button>
            </div>
          </div>

          {/* Image + overlay */}
          <div
            style={{
              position: 'relative', display: 'flex', justifyContent: 'center', background: '#111',
              borderRadius: '0 0 12px 12px', overflow: 'hidden', userSelect: 'none',
              cursor: mode === 'draw' ? cursorStyle : 'default',
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={(e) => { handleMouseMove(e); if (mode === 'draw') setCursorStyle(getCursor(e)); }}
            onMouseUp={handleMouseUp}
            onMouseLeave={() => { if (dragAction.type !== 'none') { handleMouseUp(); } }}
          >
            <img ref={imgRef} src={EXAMPLE_IMAGE.src} alt={EXAMPLE_IMAGE.name} onLoad={handleImageLoad}
              draggable={false} style={{ maxWidth: '100%', maxHeight: 520, objectFit: 'contain', display: 'block' }} />

            {imgSize.w > 0 && (
              <svg style={{
                position: 'absolute', top: 0, left: '50%', transform: 'translateX(-50%)',
                width: imgSize.w, height: imgSize.h, pointerEvents: 'none',
              }} viewBox={`0 0 ${imgSize.w} ${imgSize.h}`}>
                {/* Preset */}
                {showPreset && EXAMPLE_IMAGE.boxes.map((box, idx) => {
                  const cls = classMap[box.classId]; if (!cls) return null;
                  const p = yoloToPixel(box);
                  const hl = hoveredClass === box.classId;
                  return (
                    <g key={`p-${idx}`} opacity={hl ? 1 : 0.6}>
                      <rect x={p.x} y={p.y} width={p.w} height={p.h} fill={hl ? `${cls.color}15` : 'none'}
                        stroke={cls.color} strokeWidth={hl ? 2.5 : 1.5} strokeDasharray={hl ? 'none' : '4 2'} rx={2} />
                      <rect x={p.x} y={Math.max(0, p.y - 18)} width={cls.name.length * 7 + 12} height={18}
                        fill={cls.color} rx={3} opacity={0.8} />
                      <text x={p.x + 6} y={Math.max(0, p.y - 18) + 13} fill="#fff" fontSize={10}
                        fontWeight={600} fontFamily="monospace">{cls.name}</text>
                    </g>
                  );
                })}

                {/* User boxes */}
                {userBoxes.map((box, idx) => {
                  const cls = classMap[box.classId] || classes[0];
                  const x = box.x1 * imgSize.w, y = box.y1 * imgSize.h;
                  const w = (box.x2 - box.x1) * imgSize.w, h = (box.y2 - box.y1) * imgSize.h;
                  const sel = selectedIdx === idx;
                  return (
                    <g key={`u-${idx}`}>
                      <rect x={x} y={y} width={w} height={h}
                        fill={sel ? `${cls.color}18` : `${cls.color}08`}
                        stroke={cls.color} strokeWidth={sel ? 3 : 2} rx={2} />
                      {/* Label tag */}
                      <rect x={x} y={Math.max(0, y - 22)} width={cls.name.length * 8 + (sel ? 40 : 16)} height={22}
                        fill={cls.color} rx={4} />
                      <text x={x + 8} y={Math.max(0, y - 22) + 15} fill="#fff" fontSize={11}
                        fontWeight={600} fontFamily="monospace">
                        {cls.name}{sel ? ' ✎' : ''}
                      </text>
                      {/* Handles */}
                      {sel && renderHandles(box, cls.color)}
                    </g>
                  );
                })}

                {/* Drawing preview */}
                {dragAction.type === 'draw' && (() => {
                  const cls = classMap[activeClassId] || classes[0];
                  const x1 = Math.min(dragAction.startX, dragCurrent.x), y1 = Math.min(dragAction.startY, dragCurrent.y);
                  const x2 = Math.max(dragAction.startX, dragCurrent.x), y2 = Math.max(dragAction.startY, dragCurrent.y);
                  const px = x1 * imgSize.w, py = y1 * imgSize.h;
                  const pw = (x2 - x1) * imgSize.w, ph = (y2 - y1) * imgSize.h;
                  if (pw < 2 && ph < 2) return null;
                  return (
                    <rect x={px} y={py} width={pw} height={ph}
                      fill={`${cls.color}12`} stroke={cls.color} strokeWidth={2} strokeDasharray="6 3" rx={2} />
                  );
                })()}
              </svg>
            )}

            {/* Hint */}
            {mode === 'draw' && userBoxes.length === 0 && dragAction.type === 'none' && (
              <div style={{
                position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                background: 'rgba(0,0,0,0.6)', color: '#fff', padding: '12px 24px', borderRadius: 10,
                fontSize: 14, pointerEvents: 'none', textAlign: 'center',
              }}>
                🖱️ {t('dragHint').replace('🖱️ ', '')}
              </div>
            )}
          </div>

          {/* Action bar */}
          {(userBoxes.length > 0 || selectedIdx !== null) && (
            <div style={{
              marginTop: 10, padding: '10px 14px', background: '#fff', border: '1px solid #eee',
              borderRadius: 10,
            }}>
              {/* Top row: info + actions */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                <span style={{ fontSize: 13, color: '#666' }}>
                  {t('boxCount', { count: userBoxes.length })}
                  {selectedIdx !== null && userBoxes[selectedIdx] && (
                    <span style={{ marginLeft: 6, color: classMap[userBoxes[selectedIdx].classId]?.color || '#4f6ef7' }}>
                      — {t('selected', { idx: selectedIdx + 1 })}
                    </span>
                  )}
                </span>
                <div style={{ display: 'flex', gap: 6 }}>
                  {selectedIdx !== null && (
                    <button onClick={() => deleteUserBox(selectedIdx)} style={{
                      display: 'flex', alignItems: 'center', gap: 4, padding: '4px 12px',
                      background: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca',
                      borderRadius: 6, fontSize: 12, cursor: 'pointer',
                    }}><DeleteOutlined /> {tc('action.delete', { ns: 'common' })}</button>
                  )}
                  <button onClick={clearUserBoxes} style={{
                    display: 'flex', alignItems: 'center', gap: 4, padding: '4px 12px',
                    background: '#f5f5f5', color: '#666', border: '1px solid #e5e5e5',
                    borderRadius: 6, fontSize: 12, cursor: 'pointer',
                  }}><UndoOutlined /> {tc('action.clearAll', { ns: 'common' })}</button>
                </div>
              </div>

              {/* Class editor row - shown when a box is selected */}
              {selectedIdx !== null && userBoxes[selectedIdx] && (() => {
                const selBox = userBoxes[selectedIdx];
                const selCls = classMap[selBox.classId];
                return (
                  <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid #f0f0f0' }}>
                    <div style={{ fontSize: 12, color: '#888', marginBottom: 6 }}>{t('changeClassLabel')}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                      {/* Existing class quick-select */}
                      {classes.map((cls) => (
                        <button key={cls.id} onClick={() => changeBoxClass(selectedIdx, cls.id)}
                          style={{
                            display: 'flex', alignItems: 'center', gap: 5, padding: '4px 10px',
                            borderRadius: 6, fontSize: 12, cursor: 'pointer', transition: 'all 0.15s',
                            background: selBox.classId === cls.id ? `${cls.color}15` : '#f5f5f5',
                            border: selBox.classId === cls.id ? `2px solid ${cls.color}` : '2px solid transparent',
                            color: selBox.classId === cls.id ? cls.color : '#666',
                            fontWeight: selBox.classId === cls.id ? 600 : 400,
                          }}>
                          <span style={{ width: 10, height: 10, borderRadius: 3, background: cls.color, flexShrink: 0 }} />
                          {cls.name}
                        </button>
                      ))}
                      {/* Add new class */}
                      <form onSubmit={(e) => {
                        e.preventDefault();
                        const input = (e.target as HTMLFormElement).elements.namedItem('newClass') as HTMLInputElement;
                        const name = input.value.trim();
                        if (!name) return;
                        // Check if already exists
                        const existing = classes.find((c) => c.name === name);
                        if (existing) {
                          changeBoxClass(selectedIdx, existing.id);
                        } else {
                          const newId = Math.max(...classes.map((c) => c.id)) + 1;
                          const color = CLASS_COLORS[classes.length % CLASS_COLORS.length];
                          const newCls = { id: newId, name, color };
                          setClasses((prev) => [...prev, newCls]);
                          changeBoxClass(selectedIdx, newId);
                        }
                        input.value = '';
                      }} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <input name="newClass" placeholder={t('inputNewClass')}
                          style={{
                            width: 110, padding: '4px 8px', border: '1px solid #e5e5e5',
                            borderRadius: 6, fontSize: 12, outline: 'none',
                          }}
                          onFocus={(e) => { e.currentTarget.style.borderColor = '#4f6ef7'; }}
                          onBlur={(e) => { e.currentTarget.style.borderColor = '#e5e5e5'; }}
                        />
                        <button type="submit" style={{
                          padding: '4px 10px', background: '#4f6ef7', color: '#fff',
                          border: 'none', borderRadius: 6, fontSize: 12, cursor: 'pointer', whiteSpace: 'nowrap',
                        }}>+ {tc('action.add', { ns: 'common' })}</button>
                      </form>
                    </div>
                    {selCls && (
                      <div style={{ marginTop: 6, fontSize: 11, color: '#999' }}>
                        当前: <span style={{ color: selCls.color, fontWeight: 600 }}>{selCls.name}</span> (id: {selBox.classId})
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}
        </div>

        {/* ─── Sidebar ─── */}
        <div style={{ flex: '0 0 280px', minWidth: 250 }}>
          {/* Class selector */}
          <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 20, marginBottom: 16 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: '#111', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: 6 }}>
              <TagOutlined style={{ color: '#22c55e' }} /> {t('annotationClasses')}
            </h3>
            <p style={{ fontSize: 12, color: '#999', margin: '0 0 10px' }}>
              {selectedIdx !== null ? t('classHintSelected') : mode === 'draw' ? t('classHintDraw') : t('classHintView')}
            </p>
            {classes.map((cls) => {
              const presetCount = EXAMPLE_IMAGE.boxes.filter((b) => b.classId === cls.id).length;
              const userCount = userBoxes.filter((b) => b.classId === cls.id).length;
              const isActive = activeClassId === cls.id;
              const isSelectedClass = selectedIdx !== null && userBoxes[selectedIdx]?.classId === cls.id;
              return (
                <div key={cls.id}
                  onClick={() => {
                    setActiveClassId(cls.id);
                    // If a box is selected, change its class
                    if (selectedIdx !== null) changeBoxClass(selectedIdx, cls.id);
                  }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10, padding: '9px 12px',
                    borderRadius: 8, marginBottom: 4, cursor: 'pointer', transition: 'all 0.15s',
                    background: isSelectedClass ? `${cls.color}12` : isActive && mode === 'draw' ? `${cls.color}08` : '#fafafa',
                    border: isSelectedClass ? `2px solid ${cls.color}` : isActive && mode === 'draw' ? `2px solid ${cls.color}40` : '2px solid transparent',
                  }}
                  onMouseEnter={() => setHoveredClass(cls.id)}
                  onMouseLeave={() => setHoveredClass(null)}
                >
                  <div style={{ width: 16, height: 16, borderRadius: 4, background: cls.color, flexShrink: 0 }} />
                  <span style={{ flex: 1, fontSize: 13, fontWeight: 500, color: '#333' }}>{cls.name}</span>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <span style={{ fontSize: 11, padding: '1px 6px', background: '#f5f5f5', borderRadius: 999, color: '#999' }}>{presetCount}</span>
                    {userCount > 0 && (
                      <span style={{ fontSize: 11, padding: '1px 6px', background: `${cls.color}15`, borderRadius: 999, color: cls.color, fontWeight: 600 }}>+{userCount}</span>
                    )}
                  </div>
                </div>
              );
            })}
            {selectedIdx !== null && (
              <div style={{ marginTop: 8, padding: '8px 10px', background: '#f0f7ff', borderRadius: 8, fontSize: 12, color: '#4f6ef7' }}>
                {t('clickToChangeClass')}
              </div>
            )}
          </div>

          {/* Info */}
          <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 20, marginBottom: 16 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: '#111', margin: '0 0 12px', display: 'flex', alignItems: 'center', gap: 6 }}>
              <InfoCircleOutlined style={{ color: '#4f6ef7' }} /> {t('datasetInfo')}
            </h3>
            {[
              { label: t('annotationFormat'), value: 'YOLO v8' },
              { label: t('presetCount'), value: t('countUnit', { count: EXAMPLE_IMAGE.boxes.length }) },
              { label: t('yourAnnotations'), value: t('countUnit', { count: userBoxes.length }) },
              { label: t('classCount'), value: t('countUnit', { count: classes.length }) },
            ].map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', fontSize: 13, borderBottom: i < 3 ? '1px solid #f8f8f8' : 'none' }}>
                <span style={{ color: '#888' }}>{item.label}</span>
                <span style={{ color: '#111', fontWeight: 500 }}>{item.value}</span>
              </div>
            ))}
          </div>

          {/* YOLO preview */}
          <div style={{
            background: '#1a1a2e', borderRadius: 12, padding: 14,
            fontFamily: 'monospace', fontSize: 11, lineHeight: 1.8, color: '#a5b4fc', overflow: 'auto', maxHeight: 160,
          }}>
            <div style={{ color: '#666', marginBottom: 4, fontSize: 10, fontFamily: 'sans-serif' }}>{t('yoloPreview')}</div>
            {userBoxes.length > 0 ? userBoxes.map((box, i) => {
              const cx = (box.x1 + box.x2) / 2, cy = (box.y1 + box.y2) / 2;
              const w = box.x2 - box.x1, h = box.y2 - box.y1;
              const sel = selectedIdx === i;
              return (
                <div key={`u-${i}`} style={{
                  color: classMap[box.classId]?.color ?? '#4f6ef7',
                  background: sel ? 'rgba(79,110,247,0.15)' : 'transparent',
                  padding: '0 4px', borderRadius: 3, cursor: 'pointer',
                }} onClick={() => setSelectedIdx(i)}>
                  {box.classId} {cx.toFixed(4)} {cy.toFixed(4)} {w.toFixed(4)} {h.toFixed(4)}
                </div>
              );
            }) : (
              <div style={{ color: '#555', fontFamily: 'sans-serif' }}>{t('yoloHint')}</div>
            )}
          </div>
        </div>
      </div>

      {/* ─── Steps ─── */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: '#111', margin: '0 0 6px', display: 'flex', alignItems: 'center', gap: 8 }}>
          <BulbOutlined style={{ color: '#f59e0b' }} /> {t('workflow')}
        </h2>
        <p style={{ fontSize: 14, color: '#888', margin: '0 0 20px' }}>{t('workflowDesc')}</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 14 }}>
          {STEPS.map((s) => (
            <div key={s.num} style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 16, transition: 'box-shadow 0.2s' }}
              onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.06)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; }}>
              <div style={{ width: 30, height: 30, borderRadius: 8, background: '#eef2ff', color: '#4f6ef7', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 14, marginBottom: 8 }}>{s.num}</div>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: '#111', margin: '0 0 4px' }}>{t(s.title)}</h3>
              <p style={{ fontSize: 12, color: '#666', margin: 0, lineHeight: 1.5 }}>{t(s.desc)}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div style={{
        background: 'linear-gradient(135deg, #4f6ef7 0%, #7c3aed 100%)', borderRadius: 16,
        padding: '28px 36px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16,
      }}>
        <div>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: '#fff', margin: '0 0 4px' }}>{t('readyToStart')}</h3>
          <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.8)', margin: 0 }}>{t('readyDesc')}</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={() => navigate('/datasets')} style={{
            padding: '10px 24px', background: '#fff', color: '#4f6ef7', border: 'none',
            borderRadius: 10, fontSize: 14, fontWeight: 600, cursor: 'pointer',
          }}><CheckCircleOutlined /> {t('createDataset')}</button>
          <button onClick={() => navigate('/annotations')} style={{
            padding: '10px 24px', background: 'rgba(255,255,255,0.15)', color: '#fff',
            border: '1px solid rgba(255,255,255,0.3)', borderRadius: 10, fontSize: 14, fontWeight: 500, cursor: 'pointer',
          }}>{t('createAnnotation')}</button>
        </div>
      </div>
    </div>
  );
};

export default ExampleDatasetPage;
