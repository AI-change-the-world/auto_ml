import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { message, Spin } from 'antd';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloudServerOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { getDeploymentOverview, getModelActivity } from '../../api/deploy';
import type { DeploymentOverviewItem, ModelInferenceActivityResponse } from '../../types/deploy';
import { useTranslation } from 'react-i18next';

const formatDateTime = (value: string | null | undefined) => (value ? dayjs(value).format('YYYY-MM-DD HH:mm:ss') : '-');

const cardStyle: React.CSSProperties = {
  background: '#fff',
  border: '1px solid #e5e7eb',
  borderRadius: 18,
};

const metricStyle: React.CSSProperties = {
  ...cardStyle,
  padding: 18,
  background: '#f8fafc',
};

const DeployDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const modelId = Number(id);
  const navigate = useNavigate();
  const { t } = useTranslation('deploy');
  const tc = useTranslation('common').t;
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [model, setModel] = useState<DeploymentOverviewItem | null>(null);
  const [activity, setActivity] = useState<ModelInferenceActivityResponse | null>(null);

  const fetchDetail = useCallback(async (silent = false) => {
    if (!Number.isFinite(modelId)) return;
    if (silent) setRefreshing(true);
    else setLoading(true);
    try {
      const [overviewRes, activityRes] = await Promise.all([
        getDeploymentOverview(false),
        getModelActivity(modelId, 20).catch(() => null),
      ]);
      setModel(overviewRes?.items.find((item) => item.model_id === modelId) || null);
      setActivity(activityRes || null);
    } catch {
      message.error(tc('msg.fetchFailed'));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [modelId, tc]);

  useEffect(() => {
    void fetchDetail(false);
  }, [fetchDetail]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!model) {
    return (
      <div style={{ padding: 24 }} className="page-container">
        <button
          onClick={() => navigate('/deploy')}
          style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', color: '#666', cursor: 'pointer', fontSize: 14 }}
        >
          <ArrowLeftOutlined /> {tc('action.back')}
        </button>
        <div style={{ textAlign: 'center', marginTop: 80, color: '#ccc' }}>{t('instanceNotFound', { defaultValue: '部署实例不存在' })}</div>
      </div>
    );
  }

  return (
    <div style={{ padding: 24, maxWidth: 1180, margin: '0 auto' }} className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            onClick={() => navigate('/deploy')}
            style={{ width: 32, height: 32, borderRadius: 8, border: '1px solid #eee', background: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888' }}
          >
            <ArrowLeftOutlined />
          </button>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
            <CloudServerOutlined /> {model.model_name || `Model #${model.model_id}`}
          </h1>
          {model.is_deployed ? (
            <span style={{ padding: '2px 10px', fontSize: 12, borderRadius: 999, background: '#f0fdf4', color: '#16a34a', fontWeight: 600 }}>
              {tc('status.deployed')}
            </span>
          ) : (
            <span style={{ padding: '2px 10px', fontSize: 12, borderRadius: 999, background: '#f5f5f5', color: '#999', fontWeight: 600 }}>
              {tc('status.notDeployed')}
            </span>
          )}
          <span
            style={{
              padding: '2px 10px',
              fontSize: 12,
              borderRadius: 999,
              background: model.runtime_status.healthy ? '#ecfdf5' : '#fff7ed',
              color: model.runtime_status.healthy ? '#15803d' : '#c2410c',
              fontWeight: 600,
            }}
          >
            {model.runtime_status.healthy
              ? t('runtimeHealthy', { defaultValue: '运行时正常' })
              : t('runtimeOffline', { defaultValue: '运行时离线' })}
          </span>
        </div>
        <button
          onClick={() => void fetchDetail(true)}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '8px 14px', border: '1px solid #e5e5e5', borderRadius: 8, fontSize: 13, background: '#fff', color: '#666', cursor: 'pointer' }}
        >
          <ReloadOutlined spin={refreshing} /> {tc('action.refresh')}
        </button>
      </div>

      <div style={{ ...cardStyle, padding: 24, marginBottom: 20 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 18 }}>
          {[
            { label: t('taskKind', { defaultValue: '任务类型' }), value: model.runtime_status.task_kind || model.model_type || '-' },
            { label: t('runtimeStatus', { defaultValue: '运行时状态' }), value: model.runtime_status.status || '-' },
            { label: t('device'), value: model.deployment_device || '-' },
            { label: t('port'), value: model.deployment_port != null ? String(model.deployment_port) : '-' },
            { label: t('versionLabel', { defaultValue: '版本' }), value: model.deployment_version || '-' },
            { label: t('deployedAt', { defaultValue: '部署时间' }), value: formatDateTime(model.deployed_at) },
            { label: t('lastCallAt', { defaultValue: '最近调用时间' }), value: formatDateTime(activity?.metrics.last_inference_at ?? model.last_inference_at) },
            { label: tc('label.createdAt'), value: formatDateTime(model.created_at) },
            { label: tc('label.updatedAt'), value: formatDateTime(model.updated_at) },
          ].map((item) => (
            <div key={item.label}>
              <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>{item.label}</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#111' }}>{item.value}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 16, marginBottom: 20 }}>
        {[
          {
            label: t('callCount', { defaultValue: '累计调用次数' }),
            value: activity?.metrics.inference_count ?? model.inference_count ?? 0,
            icon: <CloudServerOutlined style={{ color: '#2563eb' }} />,
          },
          {
            label: t('successCount', { defaultValue: '成功调用' }),
            value: activity?.metrics.success_count ?? 0,
            icon: <CheckCircleOutlined style={{ color: '#15803d' }} />,
          },
          {
            label: t('failureCount', { defaultValue: '失败调用' }),
            value: activity?.metrics.failure_count ?? 0,
            icon: <ExclamationCircleOutlined style={{ color: '#c2410c' }} />,
          },
          {
            label: t('avgDuration', { defaultValue: '平均耗时(ms)' }),
            value: activity?.metrics.avg_duration_ms != null ? Math.round(activity.metrics.avg_duration_ms) : '-',
            icon: <ClockCircleOutlined style={{ color: '#7c3aed' }} />,
          },
        ].map((item) => (
          <div key={item.label} style={metricStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <div style={{ fontSize: 12, color: '#64748b' }}>{item.label}</div>
              {item.icon}
            </div>
            <div style={{ fontSize: 28, fontWeight: 800, color: '#0f172a' }}>{item.value}</div>
          </div>
        ))}
      </div>

      <div style={{ ...cardStyle, overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', borderBottom: '1px solid #f3f4f6' }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: '#111827' }}>{t('activityLogsTitle', { defaultValue: '最近调用记录' })}</div>
            <div style={{ marginTop: 4, fontSize: 12, color: '#64748b' }}>{t('activityLogsDesc', { defaultValue: '当前部署实例最近 20 条推理调用。' })}</div>
          </div>
          <span style={{ fontSize: 12, color: '#94a3b8' }}>
            {t('last24hCount', { defaultValue: '近24h调用' })}: {activity?.metrics.last_24h_count ?? 0}
          </span>
        </div>

        {activity?.logs.length ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 18 }}>
            {activity.logs.map((log) => (
              <div
                key={log.id}
                style={{
                  padding: 14,
                  borderRadius: 14,
                  border: '1px solid #e5e7eb',
                  background: log.success ? '#fff' : '#fff7ed',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: 999,
                        fontSize: 11,
                        fontWeight: 700,
                        color: log.success ? '#15803d' : '#b91c1c',
                        background: log.success ? '#dcfce7' : '#fee2e2',
                      }}
                    >
                      {log.success ? t('requestSuccess', { defaultValue: '成功' }) : t('requestFailed', { defaultValue: '失败' })}
                    </span>
                    <span style={{ padding: '3px 8px', borderRadius: 999, fontSize: 11, fontWeight: 700, color: '#1d4ed8', background: '#dbeafe' }}>
                      {log.request_type || '-'}
                    </span>
                    {log.client_ip && (
                      <span style={{ padding: '3px 8px', borderRadius: 999, fontSize: 11, color: '#475569', background: '#f1f5f9' }}>
                        {log.client_ip}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 12, color: '#64748b' }}>{formatDateTime(log.created_at)}</div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap', marginTop: 10, fontSize: 12, color: '#475569' }}>
                  <span>{t('resultCount', { defaultValue: '结果数量' })}: <strong style={{ color: '#111827' }}>{log.result_count}</strong></span>
                  <span>{t('durationMs', { defaultValue: '耗时(ms)' })}: <strong style={{ color: '#111827' }}>{log.duration_ms ?? '-'}</strong></span>
                  <span>{t('imageSize', { defaultValue: '图像尺寸' })}: <strong style={{ color: '#111827' }}>{log.image_width && log.image_height ? `${log.image_width} × ${log.image_height}` : '-'}</strong></span>
                </div>

                {!log.success && log.error_message && (
                  <div style={{ marginTop: 10, padding: '10px 12px', borderRadius: 10, background: '#fff', color: '#9a3412', fontSize: 12, border: '1px solid #fed7aa' }}>
                    {log.error_message}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: 48, color: '#94a3b8', fontSize: 13 }}>
            {t('activityLogsEmpty', { defaultValue: '当前实例还没有调用记录' })}
          </div>
        )}
      </div>
    </div>
  );
};

export default DeployDetailPage;
