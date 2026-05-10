import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Drawer, message, Spin, Modal, Select, Upload, Input, InputNumber, Switch } from 'antd';
import {
  CloudServerOutlined,
  ReloadOutlined,
  CloudUploadOutlined,
  CloudDownloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ExperimentOutlined,
  EyeOutlined,
  ApiOutlined,
  CopyOutlined,
  EditOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { getDeploymentOverview, deployModel, undeployModel, predictModel, getDeployStatus, renameModel } from '../../api/deploy';
import { getClassColor } from '../../types';
import type { DeploymentOverviewItem, InferenceDetectionResult, InferenceParams, InferencePredictResponse } from '../../types/deploy';
import { useTranslation } from 'react-i18next';
import { getDeployConfirmEnabled } from '../../utils/localSettings';

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

const DEPLOYMENTS_CHANGED_EVENT = 'automl:deployments-changed';

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

const getItemBounds = (item: InferenceDetectionResult) => {
  if (item.box) {
    return item.box;
  }
  if (item.obb) {
    return {
      x1: item.obb.cx - item.obb.w / 2,
      y1: item.obb.cy - item.obb.h / 2,
      x2: item.obb.cx + item.obb.w / 2,
      y2: item.obb.cy + item.obb.h / 2,
    };
  }
  if (item.points && item.points.length > 0) {
    const xs = item.points.map((point) => point.x);
    const ys = item.points.map((point) => point.y);
    return {
      x1: Math.min(...xs),
      y1: Math.min(...ys),
      x2: Math.max(...xs),
      y2: Math.max(...ys),
    };
  }
  return null;
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
  const navigate = useNavigate();
  const { t } = useTranslation('deploy');
  const tc = useTranslation('common').t;
  const [models, setModels] = useState<DeploymentOverviewItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [deployingId, setDeployingId] = useState<number | null>(null);
  const [testingId, setTestingId] = useState<number | null>(null);
  const [deviceMap, setDeviceMap] = useState<Record<number, string>>({});
  const [previewMap, setPreviewMap] = useState<Record<number, InferencePreviewEntry | null>>({});
  const [activePreviewModelId, setActivePreviewModelId] = useState<number | null>(null);
  const [activeApiModelId, setActiveApiModelId] = useState<number | null>(null);
  const [renamingModel, setRenamingModel] = useState<DeploymentOverviewItem | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [renameSubmitting, setRenameSubmitting] = useState(false);
  const [testingModel, setTestingModel] = useState<DeploymentOverviewItem | null>(null);
  const [testingFile, setTestingFile] = useState<File | null>(null);
  const [inferenceMode, setInferenceMode] = useState<'direct' | 'tile'>('direct');
  const [tileSize, setTileSize] = useState(1280);
  const [tileOverlap, setTileOverlap] = useState(0.2);
  const [mergeIou, setMergeIou] = useState(0.45);
  const [edgeFilter, setEdgeFilter] = useState(true);
  const [previewZoom, setPreviewZoom] = useState(1);
  const [focusedResultIndex, setFocusedResultIndex] = useState<number | null>(null);
  const previewMapRef = useRef<Record<number, InferencePreviewEntry | null>>({});
  const previewViewportRef = useRef<HTMLDivElement | null>(null);

  const activePreview = useMemo(
    () => (activePreviewModelId != null ? previewMap[activePreviewModelId] ?? null : null),
    [activePreviewModelId, previewMap],
  );
  const activeApiModel = useMemo(
    () => (activeApiModelId != null ? models.find((item) => item.model_id === activeApiModelId) ?? null : null),
    [activeApiModelId, models],
  );

  useEffect(() => {
    previewMapRef.current = previewMap;
  }, [previewMap]);

  useEffect(() => {
    if (activePreview) {
      setPreviewZoom(1);
      setFocusedResultIndex(null);
    }
  }, [activePreview]);

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
      const r = await getDeploymentOverview(false);
      if (r) {
        setModels(r.items);
        setTotal(r.items.length);
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
      window.dispatchEvent(new Event(DEPLOYMENTS_CHANGED_EVENT));
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
    const onUndeploy = async () => {
      setDeployingId(id);
      try {
        await undeployModel(id);
        const undeployed = await waitForDeployState(id, false);
        await fetchModels();
        window.dispatchEvent(new Event(DEPLOYMENTS_CHANGED_EVENT));
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
    };
    if (!getDeployConfirmEnabled()) {
      void onUndeploy();
      return;
    }
    Modal.confirm({
      title: t('confirmUndeploy'),
      content: t('confirmUndeployMsg'),
      onOk: onUndeploy,
    });
  };

  const handleTestInference = async (
    model: DeploymentOverviewItem,
    file: File,
    inferenceParams: InferenceParams,
  ) => {
    setTestingId(model.model_id);
    const imageUrl = URL.createObjectURL(file);

    try {
      const result = await predictModel(model.model_id, file, inferenceParams);
      savePreviewEntry({
        modelId: model.model_id,
        modelName: model.model_name || `Model #${model.model_id}`,
        fileName: file.name,
        imageUrl,
        result,
        testedAt: Date.now(),
      });
      message.success(t('testSuccess'));
    } catch (error) {
      savePreviewEntry({
        modelId: model.model_id,
        modelName: model.model_name || `Model #${model.model_id}`,
        fileName: file.name,
        imageUrl,
        result: {
          success: false,
          model_id: model.model_id,
          model_name: model.model_name,
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

  const buildInferenceParams = useCallback<() => InferenceParams>(() => {
    if (inferenceMode === 'tile') {
      return {
        inference_mode: 'tile',
        tile_size: tileSize,
        tile_overlap: tileOverlap,
        merge_iou: mergeIou,
        edge_filter: edgeFilter,
        merge_strategy: 'nms',
      };
    }

    return {
      inference_mode: 'direct',
    };
  }, [edgeFilter, inferenceMode, mergeIou, tileOverlap, tileSize]);

  const handleOpenTestModal = (model: DeploymentOverviewItem) => {
    setTestingModel(model);
    setTestingFile(null);
  };

  const handleInferenceRequestSubmit = async () => {
    if (!testingModel) return;
    if (!testingFile) {
      message.warning(t('selectImageRequired'));
      return;
    }

    const model = testingModel;
    const file = testingFile;
    const inferenceParams = buildInferenceParams();

    await handleTestInference(model, file, inferenceParams);
    setTestingModel(null);
    setTestingFile(null);
  };

  const handleRenameSubmit = async () => {
    if (!renamingModel) return;
    const name = renameValue.trim();
    if (!name) {
      message.warning(tc('msg.pleaseInputName'));
      return;
    }

    setRenameSubmitting(true);
    try {
      await renameModel(renamingModel.model_id, { name });
      await fetchModels();
      setRenamingModel(null);
      setRenameValue('');
      message.success(t('renameSuccess'));
    } catch {
      message.error(t('renameFailed'));
    } finally {
      setRenameSubmitting(false);
    }
  };

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
  const previewZoomPercent = Math.round(previewZoom * 100);
  const apiBaseUrl = useMemo(() => getApiBaseUrl(), []);
  const apiEndpoints = useMemo<ApiEndpointInfo[]>(() => {
    if (!activeApiModel) {
      return [];
    }
    const predictUrl = `${apiBaseUrl}/inference/models/${activeApiModel.model_id}/predict`;
    const predictBase64Url = `${apiBaseUrl}/inference/models/${activeApiModel.model_id}/predict/base64`;
    const healthUrl = `${apiBaseUrl}/inference/models/${activeApiModel.model_id}/health`;
    return [
      {
        title: t('apiBinaryTitle'),
        method: 'POST',
        url: predictUrl,
        contentType: 'multipart/form-data',
        body: 'form-data\nfile: <binary image file>\ninference_params: {"inference_mode":"tile","tile_size":1280,"tile_overlap":0.2,"merge_iou":0.45,"edge_filter":true}',
        curl: `curl -X POST "${predictUrl}" \\\n  -F "file=@/path/to/image.jpg" \\\n  -F 'inference_params={"inference_mode":"tile","tile_size":1280,"tile_overlap":0.2,"merge_iou":0.45,"edge_filter":true}'`,
      },
      {
        title: t('apiBase64Title'),
        method: 'POST',
        url: predictBase64Url,
        contentType: 'application/json',
        body: '{\n  "image": "<base64 string or data URL>",\n  "inference_params": {\n    "inference_mode": "tile",\n    "tile_size": 1280,\n    "tile_overlap": 0.2,\n    "merge_iou": 0.45,\n    "edge_filter": true\n  }\n}',
        curl: `curl -X POST "${predictBase64Url}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"image":"<base64 string or data URL>","inference_params":{"inference_mode":"tile","tile_size":1280,"tile_overlap":0.2,"merge_iou":0.45,"edge_filter":true}}'`,
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
  const focusPreviewResult = useCallback((item: InferenceDetectionResult, index: number) => {
    setFocusedResultIndex(index);
    setPreviewZoom((prev) => Math.max(prev, 2.5));

    const bounds = getItemBounds(item);
    const viewport = previewViewportRef.current;
    if (!bounds || !viewport || imageWidth <= 0 || imageHeight <= 0) {
      return;
    }

    requestAnimationFrame(() => {
      const targetZoom = Math.max(previewZoom, 2.5);
      const scaledWidth = imageWidth * targetZoom;
      const scaledHeight = imageHeight * targetZoom;
      const centerX = ((bounds.x1 + bounds.x2) / 2 / imageWidth) * scaledWidth;
      const centerY = ((bounds.y1 + bounds.y2) / 2 / imageHeight) * scaledHeight;
      const nextLeft = Math.max(0, centerX - viewport.clientWidth / 2);
      const nextTop = Math.max(0, centerY - viewport.clientHeight / 2);
      viewport.scrollTo({
        left: nextLeft,
        top: nextTop,
        behavior: 'smooth',
      });
    });
  }, [imageHeight, imageWidth, previewZoom]);

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-title-block">
          <div className="page-title-icon">
            <CloudServerOutlined />
          </div>
          <div>
            <h1 className="page-title">{t('title')}</h1>
            <p className="page-subtitle">{t('subtitle')}</p>
          </div>
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
            background: '#fff',
            color: '#666',
            cursor: 'pointer',
          }}
          className="button-text"
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {models.map((m) => {
            const runtimeReady = m.is_deployed && m.runtime_status.healthy;
            const runtimeOffline = !runtimeReady && m.runtime_status.status !== 'offline';
            return (
            <div
              key={m.model_id}
              style={{
                background: '#fff',
                border: '1px solid #eee',
                borderRadius: 12,
                padding: '16px 20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: 12,
                transition: 'border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease',
              }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  <div style={{ width: 36, height: 36, borderRadius: 8, background: 'linear-gradient(135deg, #faf5ff, #eef2ff)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8b5cf6' }}>
                    <CloudServerOutlined />
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span className="body-text" style={{ fontWeight: 500, color: '#111' }}>{m.model_name || `Model #${m.model_id}`}</span>
                    <button
                      onClick={() => {
                        setRenamingModel(m);
                        setRenameValue(m.model_name || '');
                      }}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '4px 8px',
                        border: '1px solid #e5e7eb',
                        borderRadius: 999,
                        background: '#fff',
                        color: '#4b5563',
                        cursor: 'pointer',
                      }}
                      className="tag-text"
                    >
                      <EditOutlined /> {t('rename')}
                    </button>
                    {m.model_type && <span className="tag-text" style={{ padding: '1px 8px', background: '#f5f5f5', color: '#888', borderRadius: 999 }}>{m.model_type}</span>}
                    {m.is_deployed ? (
                      <span className="tag-text" style={{ padding: '1px 8px', background: '#f0fdf4', color: '#16a34a', borderRadius: 999, display: 'flex', alignItems: 'center', gap: 3 }}>
                        <CheckCircleOutlined style={{ fontSize: 10 }} /> {tc('status.deployed')}
                      </span>
                    ) : (
                      <span className="tag-text" style={{ padding: '1px 8px', background: '#f5f5f5', color: '#999', borderRadius: 999 }}>
                        {tc('status.notDeployed')}
                      </span>
                    )}
                    {previewMap[m.model_id] && (
                      <span className="tag-text" style={{ padding: '1px 8px', background: '#fff7ed', color: '#c2410c', borderRadius: 999 }}>
                        {t('lastTest')}: {dayjs(previewMap[m.model_id]?.testedAt).format('HH:mm:ss')}
                      </span>
                    )}
                    {runtimeOffline && (
                      <span className="tag-text" style={{ padding: '1px 8px', background: '#fff7ed', color: '#c2410c', borderRadius: 999, display: 'flex', alignItems: 'center', gap: 3 }}>
                        <ExclamationCircleOutlined style={{ fontSize: 10 }} /> {t('runtimeOffline', { defaultValue: '运行时离线' })}
                      </span>
                    )}
                  </div>
                  <div className="caption-text" style={{ display: 'flex', alignItems: 'center', gap: 12, color: '#999', marginTop: 2, flexWrap: 'wrap' }}>
                    {m.deployment_device && <span>{t('device')}: {m.deployment_device}</span>}
                    {m.deployment_port != null && <span>{t('port')}: {m.deployment_port}</span>}
                    {runtimeOffline && <span>{t('runtimeStatus', { defaultValue: '运行时状态' })}: {m.runtime_status.status || 'offline'}</span>}
                    <span>{dayjs(m.created_at).format('YYYY-MM-DD')}</span>
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                {previewMap[m.model_id] && (
                  <button
                    onClick={() => {
                      setActiveApiModelId(null);
                      setActivePreviewModelId(m.model_id);
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
                      onClick={() => navigate(`/deploy/${m.model_id}`)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '6px 14px',
                        border: '1px solid #e5e7eb',
                        borderRadius: 8,
                        fontSize: 13,
                        background: '#fff',
                        color: '#334155',
                        cursor: 'pointer',
                      }}
                    >
                      {t('viewActivity', { defaultValue: '实例详情' })}
                    </button>
                    <button
                      onClick={() => {
                        setActivePreviewModelId(null);
                        setActiveApiModelId(m.model_id);
                      }}
                      disabled={!runtimeReady}
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
                        cursor: runtimeReady ? 'pointer' : 'not-allowed',
                        opacity: runtimeReady ? 1 : 0.5,
                      }}
                    >
                      <ApiOutlined /> {t('viewApi')}
                    </button>
                    <button
                      onClick={() => handleOpenTestModal(m)}
                      disabled={!runtimeReady || testingId === m.model_id}
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
                        cursor: runtimeReady ? 'pointer' : 'not-allowed',
                        opacity: runtimeReady ? 1 : 0.5,
                      }}
                    >
                      <ExperimentOutlined /> {testingId === m.model_id ? t('testing') : t('testInference')}
                    </button>
                    <button
                      onClick={() => handleUndeploy(m.model_id)}
                      disabled={deployingId === m.model_id}
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
                      value={deviceMap[m.model_id] || 'cpu'}
                      onChange={(v) => setDeviceMap((p) => ({ ...p, [m.model_id]: v }))}
                      style={{ width: 80 }}
                      options={[
                        { label: 'CPU', value: 'cpu' },
                        { label: 'CUDA', value: 'cuda' },
                      ]}
                    />
                    <button
                      onClick={() => void handleDeploy(m.model_id)}
                      disabled={deployingId === m.model_id}
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
          );
          })}
        </div>
      )}

      <div className="body-text-sm" style={{ marginTop: 16, color: '#bbb', textAlign: 'center' }}>{t('totalModels', { count: total })}</div>

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
              {hasPreviewGeometry && (
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <button
                    type="button"
                    onClick={() => setPreviewZoom((prev) => Math.max(1, Number((prev - 0.25).toFixed(2))))}
                    style={{
                      padding: '4px 10px',
                      borderRadius: 999,
                      border: '1px solid #d1d5db',
                      background: '#fff',
                      color: '#374151',
                      cursor: 'pointer',
                    }}
                  >
                    -
                  </button>
                  <span style={{ padding: '4px 10px', borderRadius: 999, background: '#f8fafc', color: '#475569', fontSize: 12 }}>
                    {t('previewZoom')}: {previewZoomPercent}%
                  </span>
                  <button
                    type="button"
                    onClick={() => setPreviewZoom((prev) => Math.min(6, Number((prev + 0.25).toFixed(2))))}
                    style={{
                      padding: '4px 10px',
                      borderRadius: 999,
                      border: '1px solid #d1d5db',
                      background: '#fff',
                      color: '#374151',
                      cursor: 'pointer',
                    }}
                  >
                    +
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setPreviewZoom(1);
                      setFocusedResultIndex(null);
                      previewViewportRef.current?.scrollTo({ left: 0, top: 0, behavior: 'smooth' });
                    }}
                    style={{
                      padding: '4px 10px',
                      borderRadius: 999,
                      border: '1px solid #d1d5db',
                      background: '#fff',
                      color: '#374151',
                      cursor: 'pointer',
                    }}
                  >
                    {t('resetView')}
                  </button>
                </div>
              )}
            </div>

            <div style={{ border: '1px solid #e5e7eb', borderRadius: 16, overflow: 'hidden', background: '#0f172a' }}>
              {hasPreviewGeometry ? (
                <div
                  ref={previewViewportRef}
                  style={{
                    position: 'relative',
                    width: '100%',
                    maxHeight: '72vh',
                    overflow: 'auto',
                    background: '#020617',
                  }}
                >
                  <div
                    style={{
                      position: 'relative',
                      width: imageWidth * previewZoom,
                      height: imageHeight * previewZoom,
                      transformOrigin: 'top left',
                    }}
                  >
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
                            background: focusedResultIndex === index ? '#111827' : color,
                            color: '#fff',
                            fontSize: Math.max(12, 12 * previewZoom),
                            lineHeight: 1.2,
                            padding: `${Math.max(4, 4 * previewZoom)}px ${Math.max(8, 8 * previewZoom)}px`,
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
                        onClick={() => focusPreviewResult(item, index)}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          gap: 16,
                          padding: '12px 14px',
                          borderRadius: 12,
                          border: focusedResultIndex === index ? '1px solid #93c5fd' : '1px solid #eef2f7',
                          background: focusedResultIndex === index ? '#eff6ff' : '#fafcff',
                          fontSize: 13,
                          cursor: 'pointer',
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

      <Modal
        open={!!testingModel}
        onCancel={() => {
          if (testingModel && testingId === testingModel.model_id) return;
          setTestingModel(null);
          setTestingFile(null);
        }}
        onOk={() => void handleInferenceRequestSubmit()}
        confirmLoading={!!testingModel && testingId === testingModel.model_id}
        okText={testingModel && testingId === testingModel.model_id ? t('testing') : t('testInference')}
        cancelButtonProps={{ disabled: !!testingModel && testingId === testingModel.model_id }}
        title={testingModel ? `${t('testConfigTitle')} · ${testingModel.model_name || `Model #${testingModel.model_id}`}` : t('testConfigTitle')}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ color: '#6b7280', fontSize: 13 }}>{t('inferenceParamsDesc')}</div>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12, color: '#4b5563' }}>
            <span>{t('inferenceMode')}</span>
            <Select
              value={inferenceMode}
              onChange={(value) => setInferenceMode(value)}
              options={[
                { label: t('directInference'), value: 'direct' },
                { label: t('tileInference'), value: 'tile' },
              ]}
            />
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12 }}>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12, color: '#4b5563' }}>
              <span>{t('tileSize')}</span>
              <InputNumber
                min={256}
                max={4096}
                step={64}
                value={tileSize}
                onChange={(value) => setTileSize(Number(value || 1280))}
                style={{ width: '100%' }}
                disabled={inferenceMode !== 'tile'}
              />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12, color: '#4b5563' }}>
              <span>{t('tileOverlap')}</span>
              <InputNumber
                min={0}
                max={0.9}
                step={0.05}
                value={tileOverlap}
                onChange={(value) => setTileOverlap(Number(value ?? 0.2))}
                style={{ width: '100%' }}
                disabled={inferenceMode !== 'tile'}
              />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12, color: '#4b5563' }}>
              <span>{t('mergeIou')}</span>
              <InputNumber
                min={0}
                max={1}
                step={0.05}
                value={mergeIou}
                onChange={(value) => setMergeIou(Number(value ?? 0.45))}
                style={{ width: '100%' }}
                disabled={inferenceMode !== 'tile'}
              />
            </label>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
                fontSize: 12,
                color: '#4b5563',
                alignSelf: 'end',
              }}
            >
              <span>{t('edgeFilter')}</span>
              <div style={{ display: 'inline-flex', width: 'fit-content' }}>
                <Switch checked={edgeFilter} onChange={setEdgeFilter} disabled={inferenceMode !== 'tile'} />
              </div>
            </label>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 12, color: '#4b5563' }}>{t('selectImage')}</div>
            <Upload
              accept="image/*"
              showUploadList={false}
              beforeUpload={(file) => {
                setTestingFile(file);
                return false;
              }}
            >
              <button
                type="button"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '8px 14px',
                  border: '1px solid #d1d5db',
                  borderRadius: 8,
                  background: '#fff',
                  color: '#374151',
                  cursor: 'pointer',
                }}
              >
                {t('selectImage')}
              </button>
            </Upload>
            <div style={{ minHeight: 20, fontSize: 12, color: testingFile ? '#111827' : '#9ca3af' }}>
              {testingFile ? `${t('fileName')}: ${testingFile.name}` : t('selectImageRequired')}
            </div>
          </div>
        </div>
      </Modal>

      <Modal
        open={!!renamingModel}
        onCancel={() => {
          if (renameSubmitting) return;
          setRenamingModel(null);
          setRenameValue('');
        }}
        onOk={() => void handleRenameSubmit()}
        confirmLoading={renameSubmitting}
        title={t('renameTitle')}
      >
        <Input
          value={renameValue}
          onChange={(event) => setRenameValue(event.target.value)}
          placeholder={t('renamePlaceholder')}
          maxLength={255}
        />
      </Modal>

      <Drawer
        open={!!activeApiModel}
        onClose={() => setActiveApiModelId(null)}
        width={860}
        title={activeApiModel ? `${t('apiDrawerTitle')} · ${activeApiModel.model_name || `Model #${activeApiModel.model_id}`}` : t('apiDrawerTitle')}
      >
        {activeApiModel && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              <span style={{ padding: '4px 10px', borderRadius: 999, background: '#eff6ff', color: '#2563eb', fontSize: 12 }}>
                {t('apiModelId')}: {activeApiModel.model_id}
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
