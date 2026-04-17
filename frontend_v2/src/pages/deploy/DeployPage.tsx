import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import { Drawer, message, Spin, Modal, Select, Upload } from 'antd';
import type { UploadProps } from 'antd';
import {
  CloudServerOutlined,
  ReloadOutlined,
  CloudUploadOutlined,
  CloudDownloadOutlined,
  CheckCircleOutlined,
  ExperimentOutlined,
  EyeOutlined,
  ApiOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { listModels, deployModel, undeployModel, predictModel, getDeployStatus } from '../../api/deploy';
import { getClassColor } from '../../types';
import type { AvailableModelResponse, InferenceDetectionResult, InferencePredictResponse } from '../../types/deploy';
import { useTranslation } from 'react-i18next';

type InferencePreviewEntry = {
  modelId: number;
  modelName: string;
  fileName: string;
  imageUrl: string;
  result: InferencePredictResponse;
  testedAt: number;
};

type ApiEndpointInfo = {
  title: string;
  method: 'GET' | 'POST';
  url: string;
  contentType?: string;
  body: string;
  curl: string;
};

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

const toPercent = (value: number, total: number) => `${(clamp(value, 0, total) / Math.max(total, 1)) * 100}%`;

const formatConfidence = (confidence: number | null | undefined) => `${((confidence || 0) * 100).toFixed(1)}%`;

const getApiBaseUrl = () => {
  const base = import.meta.env.VITE_API_BASE_URL || '/api';
  if (/^https?:\/\//i.test(base)) {
    return base.replace(/\/+$/, '');
  }
  return new URL(base, window.location.origin).toString().replace(/\/+$/, '');
};

const codeBlockStyle: React.CSSProperties = {
  margin: 0,
  padding: '12px 14px',
  borderRadius: 10,
  background: '#0f172a',
  color: '#dbeafe',
  fontSize: 12,
  lineHeight: 1.6,
  overflowX: 'auto',
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
};

const methodBadgeStyle = (method: ApiEndpointInfo['method']): React.CSSProperties => ({
  padding: '2px 8px',
  borderRadius: 999,
  fontSize: 12,
  fontWeight: 700,
  color: method === 'GET' ? '#047857' : '#1d4ed8',
  background: method === 'GET' ? '#ecfdf5' : '#eff6ff',
});

const extractErrorMessage = (error: unknown, fallback: string) => {
  if (error && typeof error === 'object') {
    const maybeResponse = (error as { response?: { data?: { detail?: unknown; message?: unknown } } }).response;
    const detail = maybeResponse?.data?.detail;
    const message = maybeResponse?.data?.message;
    if (typeof detail === 'string' && detail) return detail;
    if (typeof message === 'string' && message) return message;
  }
  return error instanceof Error ? error.message : fallback;
};

const getLabelAnchor = (
  item: InferenceDetectionResult,
  imageWidth: number,
  imageHeight: number,
) => {
  if (item.box) {
    return {
      x: clamp(item.box.x1, 0, imageWidth),
      y: clamp(item.box.y1 <= 28 ? item.box.y1 : item.box.y1 - 26, 0, imageHeight),
    };
  }

  if (item.obb) {
    return {
      x: clamp(item.obb.cx - item.obb.w / 2, 0, imageWidth),
      y: clamp(item.obb.cy - item.obb.h / 2 <= 28 ? item.obb.cy - item.obb.h / 2 : item.obb.cy - item.obb.h / 2 - 26, 0, imageHeight),
    };
  }

  if (item.points && item.points.length > 0) {
    const xs = item.points.map((point) => point.x);
    const ys = item.points.map((point) => point.y);
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    return {
      x: clamp(minX, 0, imageWidth),
      y: clamp(minY <= 28 ? minY : minY - 26, 0, imageHeight),
    };
  }

  return { x: 0, y: 0 };
};

const formatResultGeometry = (item: InferenceDetectionResult) => {
  if (item.box) {
    return `[${item.box.x1.toFixed(1)}, ${item.box.y1.toFixed(1)}, ${item.box.x2.toFixed(1)}, ${item.box.y2.toFixed(1)}]`;
  }
  if (item.obb) {
    return `cx=${item.obb.cx.toFixed(1)}, cy=${item.obb.cy.toFixed(1)}, w=${item.obb.w.toFixed(1)}, h=${item.obb.h.toFixed(1)}, angle=${item.obb.angle.toFixed(2)}`;
  }
  if (item.points && item.points.length > 0) {
    return `${item.points.length} pts`;
  }
  return '-';
};

const renderOverlayShape = (
  item: InferenceDetectionResult,
  index: number,
) => {
  const color = getClassColor(item.class_id);
  const fill = `${color}22`;

  if (item.points && item.points.length > 1) {
    return (
      <polygon
        key={`poly-${index}`}
        points={item.points.map((point) => `${point.x},${point.y}`).join(' ')}
        fill={fill}
        stroke={color}
        strokeWidth={2}
        vectorEffect="non-scaling-stroke"
      />
    );
  }

  if (item.obb) {
    const angle = (item.obb.angle * 180) / Math.PI;
    return (
      <rect
        key={`obb-${index}`}
        x={item.obb.cx - item.obb.w / 2}
        y={item.obb.cy - item.obb.h / 2}
        width={item.obb.w}
        height={item.obb.h}
        fill={fill}
        stroke={color}
        strokeWidth={2}
        vectorEffect="non-scaling-stroke"
        transform={`rotate(${angle} ${item.obb.cx} ${item.obb.cy})`}
      />
    );
  }

  if (item.box) {
    return (
      <rect
        key={`bbox-${index}`}
        x={item.box.x1}
        y={item.box.y1}
        width={Math.max(0, item.box.x2 - item.box.x1)}
        height={Math.max(0, item.box.y2 - item.box.y1)}
        fill={fill}
        stroke={color}
        strokeWidth={2}
        strokeDasharray={item.type === 'obb' ? '8 4' : undefined}
        vectorEffect="non-scaling-stroke"
      />
    );
  }

  return null;
};

const DeployPage: React.FC = () => {
  const { t } = useTranslation('deploy');
  const tc = useTranslation('common').t;
  const [models, setModels] = useState<AvailableModelResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [deployingId, setDeployingId] = useState<number | null>(null);
  const [testingId, setTestingId] = useState<number | null>(null);
  const [deviceMap, setDeviceMap] = useState<Record<number, string>>({});
  const [previewMap, setPreviewMap] = useState<Record<number, InferencePreviewEntry | null>>({});
  const [activePreviewModelId, setActivePreviewModelId] = useState<number | null>(null);
  const [activeApiModelId, setActiveApiModelId] = useState<number | null>(null);
  const previewMapRef = useRef<Record<number, InferencePreviewEntry | null>>({});

  const activePreview = useMemo(
    () => (activePreviewModelId != null ? previewMap[activePreviewModelId] ?? null : null),
    [activePreviewModelId, previewMap],
  );
  const activeApiModel = useMemo(
    () => (activeApiModelId != null ? models.find((item) => item.id === activeApiModelId) ?? null : null),
    [activeApiModelId, models],
  );

  useEffect(() => {
    previewMapRef.current = previewMap;
  }, [previewMap]);

  useEffect(() => {
    return () => {
      Object.values(previewMapRef.current).forEach((entry) => {
        if (entry?.imageUrl) {
          URL.revokeObjectURL(entry.imageUrl);
        }
      });
    };
  }, []);

  const savePreviewEntry = useCallback((entry: InferencePreviewEntry) => {
    setPreviewMap((prev) => {
      const previous = prev[entry.modelId];
      if (previous?.imageUrl && previous.imageUrl !== entry.imageUrl) {
        URL.revokeObjectURL(previous.imageUrl);
      }
      return {
        ...prev,
        [entry.modelId]: entry,
      };
    });
    setActivePreviewModelId(entry.modelId);
  }, []);

  const fetchModels = useCallback(async () => {
    setLoading(true);
    try {
      const r = await listModels(1, 20);
      if (r) {
        setModels(r.items);
        setTotal(r.total);
      }
    } catch {
      message.error(tc('msg.loadFailed'));
    } finally {
      setLoading(false);
    }
  }, [tc]);

  const waitForDeployState = async (modelId: number, expected: boolean, timeoutMs = 12000) => {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const status = await getDeployStatus(modelId);
      if (status?.is_deployed === expected) {
        return status;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 1000));
    }
    return null;
  };

  useEffect(() => {
    void fetchModels();
  }, [fetchModels]);

  const handleDeploy = async (id: number) => {
    setDeployingId(id);
    try {
      await deployModel(id, deviceMap[id] || 'cpu');
      const deployed = await waitForDeployState(id, true);
      await fetchModels();
      if (deployed?.is_deployed) {
        message.success(t('deploySuccess'));
      } else {
        message.warning(t('deployPending'));
      }
    } catch {
      message.error(t('deployFailed'));
    } finally {
      setDeployingId(null);
    }
  };

  const handleUndeploy = async (id: number) => {
    Modal.confirm({
      title: t('confirmUndeploy'),
      content: t('confirmUndeployMsg'),
      onOk: async () => {
        setDeployingId(id);
        try {
          await undeployModel(id);
          const undeployed = await waitForDeployState(id, false);
          await fetchModels();
          if (undeployed?.is_deployed === false) {
            message.success(t('undeploySuccess'));
          } else {
            message.warning(t('undeployPending'));
          }
        } catch {
          message.error(t('undeployFailed'));
        } finally {
          setDeployingId(null);
        }
      },
    });
  };

  const handleTestInference = async (model: AvailableModelResponse, file: File) => {
    setTestingId(model.id);
    const imageUrl = URL.createObjectURL(file);

    try {
      const result = await predictModel(model.id, file);
      savePreviewEntry({
        modelId: model.id,
        modelName: model.name || `Model #${model.id}`,
        fileName: file.name,
        imageUrl,
        result,
        testedAt: Date.now(),
      });
      message.success(t('testSuccess'));
    } catch (error) {
      savePreviewEntry({
        modelId: model.id,
        modelName: model.name || `Model #${model.id}`,
        fileName: file.name,
        imageUrl,
        result: {
          success: false,
          model_id: model.id,
          model_name: model.name,
          task_kind: model.model_type,
          backend: 'onnxruntime',
          device: model.deployment_device,
          results: [],
          image_width: null,
          image_height: null,
          error: extractErrorMessage(error, t('testFailed')),
          raw: null,
        },
        testedAt: Date.now(),
      });
      message.error(t('testFailed'));
    } finally {
      setTestingId(null);
    }
  };

  const uploadProps = (model: AvailableModelResponse): UploadProps => ({
    accept: 'image/*',
    showUploadList: false,
    beforeUpload: (file) => {
      void handleTestInference(model, file);
      return false;
    },
  });

  const handleCopy = useCallback(async (content: string, successText: string) => {
    try {
      await navigator.clipboard.writeText(content);
      message.success(successText);
    } catch {
      message.error(t('copyFailed'));
    }
  }, [t]);

  const imageWidth = activePreview?.result.image_width || 0;
  const imageHeight = activePreview?.result.image_height || 0;
  const hasPreviewGeometry = imageWidth > 0 && imageHeight > 0;
  const previewResults = activePreview?.result.results || [];
  const apiBaseUrl = useMemo(() => getApiBaseUrl(), []);
  const apiEndpoints = useMemo<ApiEndpointInfo[]>(() => {
    if (!activeApiModel) {
      return [];
    }
    const predictUrl = `${apiBaseUrl}/inference/models/${activeApiModel.id}/predict`;
    const predictBase64Url = `${apiBaseUrl}/inference/models/${activeApiModel.id}/predict/base64`;
    const healthUrl = `${apiBaseUrl}/inference/models/${activeApiModel.id}/health`;
    return [
      {
        title: t('apiBinaryTitle'),
        method: 'POST',
        url: predictUrl,
        contentType: 'multipart/form-data',
        body: 'form-data\nfile: <binary image file>',
        curl: `curl -X POST "${predictUrl}" \\\n  -F "file=@/path/to/image.jpg"`,
      },
      {
        title: t('apiBase64Title'),
        method: 'POST',
        url: predictBase64Url,
        contentType: 'application/json',
        body: '{\n  "image": "<base64 string or data URL>"\n}',
        curl: `curl -X POST "${predictBase64Url}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"image":"<base64 string or data URL>"}'`,
      },
      {
        title: t('apiHealthTitle'),
        method: 'GET',
        url: healthUrl,
        body: '-',
        curl: `curl "${healthUrl}"`,
      },
    ];
  }, [activeApiModel, apiBaseUrl, t]);

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
            <CloudServerOutlined /> {t('title')}
          </h1>
          <p style={{ color: '#888', fontSize: 13, marginTop: 4 }}>{t('subtitle')}</p>
        </div>
        <button
          onClick={() => void fetchModels()}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            padding: '8px 14px',
            border: '1px solid #e5e5e5',
            borderRadius: 8,
            fontSize: 13,
            background: '#fff',
            color: '#666',
            cursor: 'pointer',
          }}
        >
          <ReloadOutlined /> {tc('action.refresh')}
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <Spin size="large" />
        </div>
      ) : models.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 80, color: '#ccc' }}>
          <CloudServerOutlined style={{ fontSize: 48, marginBottom: 12 }} />
          <p>{t('empty')}</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {models.map((m) => (
            <div key={m.id} style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ width: 36, height: 36, borderRadius: 8, background: 'linear-gradient(135deg, #faf5ff, #eef2ff)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8b5cf6' }}>
                  <CloudServerOutlined />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 14, fontWeight: 500, color: '#111' }}>{m.name || `Model #${m.id}`}</span>
                    {m.model_type && <span style={{ padding: '1px 8px', background: '#f5f5f5', color: '#888', fontSize: 11, borderRadius: 999 }}>{m.model_type}</span>}
                    {m.onnx_model_path && <span style={{ padding: '1px 8px', background: '#eff6ff', color: '#2563eb', fontSize: 11, borderRadius: 999 }}>ONNX</span>}
                    {m.is_deployed ? (
                      <span style={{ padding: '1px 8px', background: '#f0fdf4', color: '#16a34a', fontSize: 11, borderRadius: 999, display: 'flex', alignItems: 'center', gap: 3 }}>
                        <CheckCircleOutlined style={{ fontSize: 10 }} /> {tc('status.deployed')}
                      </span>
                    ) : (
                      <span style={{ padding: '1px 8px', background: '#f5f5f5', color: '#999', fontSize: 11, borderRadius: 999 }}>
                        {tc('status.notDeployed')}
                      </span>
                    )}
                    {previewMap[m.id] && (
                      <span style={{ padding: '1px 8px', background: '#fff7ed', color: '#c2410c', fontSize: 11, borderRadius: 999 }}>
                        {t('lastTest')}: {dayjs(previewMap[m.id]?.testedAt).format('HH:mm:ss')}
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 12, color: '#999', marginTop: 2, flexWrap: 'wrap' }}>
                    {m.loss != null && <span>Loss: {m.loss.toFixed(4)}</span>}
                    {m.deployment_device && <span>{t('device')}: {m.deployment_device}</span>}
                    <span>{dayjs(m.created_at).format('YYYY-MM-DD')}</span>
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                {previewMap[m.id] && (
                  <button
                    onClick={() => {
                      setActiveApiModelId(null);
                      setActivePreviewModelId(m.id);
                    }}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 4,
                      padding: '6px 14px',
                      border: '1px solid #e5e7eb',
                      borderRadius: 8,
                      fontSize: 13,
                      background: '#fff',
                      color: '#374151',
                      cursor: 'pointer',
                    }}
                  >
                    <EyeOutlined /> {t('viewResult')}
                  </button>
                )}
                {m.is_deployed ? (
                  <>
                    <button
                      onClick={() => {
                        setActivePreviewModelId(null);
                        setActiveApiModelId(m.id);
                      }}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '6px 14px',
                        border: '1px solid #ddd6fe',
                        borderRadius: 8,
                        fontSize: 13,
                        background: '#f5f3ff',
                        color: '#6d28d9',
                        cursor: 'pointer',
                      }}
                    >
                      <ApiOutlined /> {t('viewApi')}
                    </button>
                    <Upload {...uploadProps(m)}>
                      <button
                        disabled={testingId === m.id}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 4,
                          padding: '6px 14px',
                          border: '1px solid #dbeafe',
                          borderRadius: 8,
                          fontSize: 13,
                          background: '#eff6ff',
                          color: '#2563eb',
                          cursor: 'pointer',
                        }}
                      >
                        <ExperimentOutlined /> {testingId === m.id ? t('testing') : t('testInference')}
                      </button>
                    </Upload>
                    <button
                      onClick={() => handleUndeploy(m.id)}
                      disabled={deployingId === m.id}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '6px 14px',
                        border: '1px solid #fecaca',
                        borderRadius: 8,
                        fontSize: 13,
                        background: '#fff',
                        color: '#dc2626',
                        cursor: 'pointer',
                      }}
                    >
                      <CloudDownloadOutlined /> {t('undeploy')}
                    </button>
                  </>
                ) : (
                  <>
                    <Select
                      size="small"
                      value={deviceMap[m.id] || 'cpu'}
                      onChange={(v) => setDeviceMap((p) => ({ ...p, [m.id]: v }))}
                      style={{ width: 80 }}
                      options={[
                        { label: 'CPU', value: 'cpu' },
                        { label: 'CUDA', value: 'cuda' },
                      ]}
                    />
                    <button
                      onClick={() => void handleDeploy(m.id)}
                      disabled={deployingId === m.id}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '6px 14px',
                        background: '#4f6ef7',
                        color: '#fff',
                        border: 'none',
                        borderRadius: 8,
                        fontSize: 13,
                        cursor: 'pointer',
                      }}
                    >
                      <CloudUploadOutlined /> {t('deploy')}
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 16, fontSize: 13, color: '#bbb', textAlign: 'center' }}>{t('totalModels', { count: total })}</div>

      <Drawer
        open={!!activePreview}
        onClose={() => setActivePreviewModelId(null)}
        width={960}
        title={activePreview ? `${t('previewTitle')} · ${activePreview.modelName}` : t('previewTitle')}
      >
        {activePreview && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              <span style={{ padding: '4px 10px', borderRadius: 999, background: '#f3f4f6', color: '#374151', fontSize: 12 }}>
                {t('fileName')}: {activePreview.fileName}
              </span>
              <span style={{ padding: '4px 10px', borderRadius: 999, background: '#eff6ff', color: '#2563eb', fontSize: 12 }}>
                {activePreview.result.task_kind || 'unknown'}
              </span>
              <span style={{ padding: '4px 10px', borderRadius: 999, background: '#f5f3ff', color: '#7c3aed', fontSize: 12 }}>
                {activePreview.result.backend || 'onnxruntime'} · {activePreview.result.device || '-'}
              </span>
              {hasPreviewGeometry && (
                <span style={{ padding: '4px 10px', borderRadius: 999, background: '#ecfeff', color: '#0f766e', fontSize: 12 }}>
                  {t('imageSize')}: {imageWidth} × {imageHeight}
                </span>
              )}
            </div>

            <div style={{ border: '1px solid #e5e7eb', borderRadius: 16, overflow: 'hidden', background: '#0f172a' }}>
              {hasPreviewGeometry ? (
                <div style={{ position: 'relative', width: '100%', aspectRatio: `${imageWidth} / ${imageHeight}` }}>
                  <img
                    src={activePreview.imageUrl}
                    alt={activePreview.fileName}
                    style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'contain' }}
                  />
                  <svg
                    viewBox={`0 0 ${imageWidth} ${imageHeight}`}
                    preserveAspectRatio="none"
                    style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
                  >
                    {previewResults.map((item, index) => renderOverlayShape(item, index))}
                  </svg>
                  {previewResults.map((item, index) => {
                    const color = getClassColor(item.class_id);
                    const anchor = getLabelAnchor(item, imageWidth, imageHeight);
                    return (
                      <div
                        key={`label-${index}`}
                        style={{
                          position: 'absolute',
                          left: toPercent(anchor.x, imageWidth),
                          top: toPercent(anchor.y, imageHeight),
                          pointerEvents: 'none',
                          background: color,
                          color: '#fff',
                          fontSize: 12,
                          lineHeight: 1.2,
                          padding: '4px 8px',
                          borderRadius: 8,
                          boxShadow: '0 8px 24px rgba(15, 23, 42, 0.24)',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {item.class_name || `class_${item.class_id}`} · {formatConfidence(item.confidence)}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <img
                  src={activePreview.imageUrl}
                  alt={activePreview.fileName}
                  style={{ display: 'block', width: '100%', maxHeight: '70vh', objectFit: 'contain' }}
                />
              )}
            </div>

            {activePreview.result.success ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#111' }}>
                  {t('testResultTitle', { count: previewResults.length })}
                </div>
                {previewResults.length === 0 ? (
                  <div style={{ padding: '14px 16px', borderRadius: 12, background: '#f9fafb', color: '#6b7280', fontSize: 13 }}>
                    {t('noResults')}
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {previewResults.map((item, index) => (
                      <div
                        key={`result-${index}`}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          gap: 16,
                          padding: '12px 14px',
                          borderRadius: 12,
                          border: '1px solid #eef2f7',
                          background: '#fafcff',
                          fontSize: 13,
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
                          <span
                            style={{
                              width: 10,
                              height: 10,
                              borderRadius: '50%',
                              background: getClassColor(item.class_id),
                              flex: '0 0 auto',
                            }}
                          />
                          <span style={{ color: '#111', fontWeight: 600 }}>
                            [{item.type}] {item.class_name || `class_${item.class_id}`}
                          </span>
                        </div>
                        <div style={{ color: '#6b7280', textAlign: 'right' }}>
                          <div>{formatConfidence(item.confidence)}</div>
                          <div>{formatResultGeometry(item)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ padding: '14px 16px', borderRadius: 12, background: '#fef2f2', color: '#b91c1c', fontSize: 13 }}>
                {t('testResultError')}: {activePreview.result.error || t('testFailed')}
              </div>
            )}
          </div>
        )}
      </Drawer>

      <Drawer
        open={!!activeApiModel}
        onClose={() => setActiveApiModelId(null)}
        width={860}
        title={activeApiModel ? `${t('apiDrawerTitle')} · ${activeApiModel.name || `Model #${activeApiModel.id}`}` : t('apiDrawerTitle')}
      >
        {activeApiModel && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              <span style={{ padding: '4px 10px', borderRadius: 999, background: '#eff6ff', color: '#2563eb', fontSize: 12 }}>
                {t('apiModelId')}: {activeApiModel.id}
              </span>
              <span style={{ padding: '4px 10px', borderRadius: 999, background: '#f5f3ff', color: '#7c3aed', fontSize: 12 }}>
                {t('apiBaseUrlLabel')}: {apiBaseUrl}
              </span>
              <span style={{ padding: '4px 10px', borderRadius: 999, background: '#ecfdf5', color: '#047857', fontSize: 12 }}>
                {activeApiModel.model_type || 'unknown'}
              </span>
            </div>

            <div style={{ padding: '14px 16px', borderRadius: 12, background: '#f8fafc', border: '1px solid #e2e8f0', color: '#475569', fontSize: 13, lineHeight: 1.7 }}>
              <div style={{ fontWeight: 600, color: '#111827', marginBottom: 6 }}>{t('apiUsageTitle')}</div>
              <div>{t('apiUsageDesc')}</div>
            </div>

            {apiEndpoints.map((endpoint) => (
              <div
                key={`${endpoint.method}-${endpoint.url}`}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 10,
                  padding: '16px',
                  borderRadius: 14,
                  border: '1px solid #e5e7eb',
                  background: '#fff',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <span style={methodBadgeStyle(endpoint.method)}>{endpoint.method}</span>
                      <span style={{ fontSize: 14, fontWeight: 600, color: '#111827' }}>{endpoint.title}</span>
                    </div>
                    <div style={{ color: '#374151', fontSize: 13, wordBreak: 'break-all' }}>{endpoint.url}</div>
                    {endpoint.contentType && (
                      <div style={{ color: '#6b7280', fontSize: 12 }}>
                        Content-Type: {endpoint.contentType}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => void handleCopy(endpoint.curl, t('copySuccess'))}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 4,
                      padding: '6px 12px',
                      border: '1px solid #e5e7eb',
                      borderRadius: 8,
                      fontSize: 12,
                      background: '#fff',
                      color: '#374151',
                      cursor: 'pointer',
                      flex: '0 0 auto',
                    }}
                  >
                    <CopyOutlined /> {t('copyCurl')}
                  </button>
                </div>

                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 6 }}>
                    {t('requestBody')}
                  </div>
                  <pre style={codeBlockStyle}>{endpoint.body}</pre>
                </div>

                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 6 }}>
                    cURL
                  </div>
                  <pre style={codeBlockStyle}>{endpoint.curl}</pre>
                </div>
              </div>
            ))}
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default DeployPage;
