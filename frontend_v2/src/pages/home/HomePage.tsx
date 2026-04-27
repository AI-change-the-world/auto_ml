import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Spin } from 'antd';
import {
  HomeOutlined,
  DatabaseOutlined,
  PictureOutlined,
  TagsOutlined,
  FolderOutlined,
  ExperimentOutlined,
  CloudServerOutlined,
  CloudUploadOutlined,
  PlusOutlined,
  ArrowRightOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { getHomeStats } from '../../api/home';
import type { HomeStats } from '../../types/home';
import { AnnotationTypeLabels } from '../../types';
import { useTranslation } from 'react-i18next';

/* ─── Reusable Card ─── */
const Card: React.FC<{ children: React.ReactNode; style?: React.CSSProperties; className?: string }> = ({
  children,
  style,
  className,
}) => (
  <div
    className={className}
    style={{
      background: '#fff',
      borderRadius: 12,
      border: '1px solid #eee',
      ...style,
    }}
  >
    {children}
  </div>
);

/* ─── Primary Button ─── */
const PrimaryBtn: React.FC<{
  children: React.ReactNode;
  onClick?: () => void;
  style?: React.CSSProperties;
}> = ({ children, onClick, style }) => (
  <button
    onClick={onClick}
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      padding: '8px 16px',
      borderRadius: 8,
      fontSize: 13,
      fontWeight: 600,
      border: 'none',
      background: '#111',
      color: '#fff',
      cursor: 'pointer',
      whiteSpace: 'nowrap',
      lineHeight: 1.5,
      ...style,
    }}
  >
    {children}
  </button>
);

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation('home');
  const [stats, setStats] = useState<HomeStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await getHomeStats();
        if (res) setStats(res);
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Spin size="large" />
      </div>
    );
  }

  const statItems = [
    { icon: <DatabaseOutlined style={{ fontSize: 16 }} />, value: stats?.datasets ?? 0, label: t('datasets') },
    { icon: <PictureOutlined style={{ fontSize: 16 }} />, value: stats?.images ?? 0, label: t('images') },
    { icon: <TagsOutlined style={{ fontSize: 16 }} />, value: stats?.annotations ?? 0, label: t('annotations') },
    { icon: <FolderOutlined style={{ fontSize: 16 }} />, value: stats?.tasks?.total ?? 0, label: t('projects') },
    { icon: <ExperimentOutlined style={{ fontSize: 16 }} />, value: stats?.models?.total ?? 0, label: t('models') },
    { icon: <CloudServerOutlined style={{ fontSize: 16 }} />, value: stats?.models?.deployed ?? 0, label: t('deployments') },
  ];

  const recentDatasets = stats?.recent_datasets ?? [];
  const recentAnnotations = stats?.recent_annotations ?? [];
  return (
    <div className="page-container">
      {/* ─── Page Header ─── */}
      <div style={{ marginBottom: 24 }}>
        <h1
          style={{
            fontSize: 24,
            fontWeight: 700,
            color: '#111',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            margin: 0,
          }}
        >
          <HomeOutlined /> {t('title')}
        </h1>
        <p style={{ color: '#666', marginTop: 6, fontSize: 14, lineHeight: 1.5 }}>
          {t('subtitle')}
        </p>
      </div>

      {/* ─── Stats Card ─── */}
      <Card style={{ padding: '24px 24px 0', marginBottom: 24 }}>

        {/* Stats row with dividers via CSS class */}
        <div className="stats-grid" style={{ borderTop: '1px solid #f0f0f0' }}>
          {statItems.map((item, i) => (
            <div key={i}>
              <div style={{ color: '#999', fontSize: 13, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 5 }}>
                {item.icon}
              </div>
              <div style={{ fontSize: 26, fontWeight: 700, color: '#111', lineHeight: 1.2 }}>{item.value}</div>
              <div style={{ fontSize: 12, color: '#888', marginTop: 2 }}>{item.label}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* ─── 3-column layout ─── */}
      <div className="home-main-grid">
        {/* ── Datasets ── */}
        <Card style={{ padding: 20, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <h3
              style={{
                fontSize: 16,
                fontWeight: 600,
                color: '#111',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                margin: 0,
              }}
            >
              <DatabaseOutlined style={{ color: '#f59e0b' }} /> {t('datasets')}
            </h3>
            <PrimaryBtn onClick={() => navigate('/datasets')}>
              <PlusOutlined /> {t('newDataset')}
            </PrimaryBtn>
          </div>
          <p style={{ fontSize: 13, color: '#888', margin: '0 0 16px' }}>{t('uploadDesc')}</p>

          {recentDatasets.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 16px', border: '2px dashed #e5e5e5', borderRadius: 12, cursor: 'pointer' }} onClick={() => navigate('/datasets')}>
              <CloudUploadOutlined style={{ fontSize: 28, color: '#ccc', display: 'block', marginBottom: 8 }} />
              <p style={{ fontSize: 13, color: '#888', margin: 0 }}>{t('dropFiles')}</p>
              <p style={{ fontSize: 11, color: '#bbb', margin: '6px 0 0' }}>{t('dropLimit')}</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {recentDatasets.map((ds) => (
                <div key={ds.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', border: '1px solid #eee', borderRadius: 10, cursor: 'pointer', transition: 'box-shadow 0.2s' }}
                  onClick={() => navigate(`/datasets/${ds.id}`)}
                  onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; }}
                >
                  <DatabaseOutlined style={{ fontSize: 18, color: '#f59e0b' }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#111', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ds.name}</div>
                    <div style={{ fontSize: 11, color: '#999' }}>{ds.count} {t('images')}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div style={{ flex: 1 }} />
          <div
            style={{
              marginTop: 14,
              fontSize: 13,
              color: '#888',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
            onClick={() => navigate('/datasets')}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = '#4f6ef7';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = '#888';
            }}
          >
            {t('action:viewAll', { defaultValue: t('common:action.viewAll') })} <ArrowRightOutlined style={{ fontSize: 11 }} />
          </div>
        </Card>

        {/* ── Projects ── */}
        <Card style={{ padding: 20, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <h3
              style={{
                fontSize: 16,
                fontWeight: 600,
                color: '#111',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                margin: 0,
              }}
            >
              <FolderOutlined style={{ color: '#f59e0b' }} /> {t('projects')}
            </h3>
            <PrimaryBtn onClick={() => navigate('/annotations')}>
              <PlusOutlined /> {t('newProject')}
            </PrimaryBtn>
          </div>
          <p style={{ fontSize: 13, color: '#888', margin: '0 0 16px' }}>{t('projectDesc')}</p>

          {recentAnnotations.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 16px', border: '2px dashed #e5e5e5', borderRadius: 12, cursor: 'pointer' }} onClick={() => navigate('/annotations')}>
              <CloudUploadOutlined style={{ fontSize: 28, color: '#ccc', display: 'block', marginBottom: 8 }} />
              <p style={{ fontSize: 13, color: '#888', margin: 0 }}>{t('dropModel')}</p>
              <p style={{ fontSize: 11, color: '#bbb', margin: '6px 0 0' }}>{t('dropModelLimit')}</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {recentAnnotations.map((ann) => (
                <div key={ann.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', border: '1px solid #eee', borderRadius: 10, cursor: 'pointer', transition: 'box-shadow 0.2s' }}
                  onClick={() => navigate(`/annotations/${ann.id}/label`)}
                  onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; }}
                >
                  <div style={{ width: 36, height: 36, borderRadius: 8, background: '#8b5cf6', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: 14, flexShrink: 0 }}>
                    {ann.name?.charAt(0)?.toUpperCase() || 'P'}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#111', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ann.name}</div>
                    <div style={{ fontSize: 11, color: '#999' }}>{AnnotationTypeLabels[ann.annotation_type] ?? '检测'}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div style={{ flex: 1 }} />
          <div
            style={{
              marginTop: 14,
              fontSize: 13,
              color: '#888',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
            onClick={() => navigate('/annotations')}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = '#4f6ef7';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = '#888';
            }}
          >
            {t('common:action.viewAll')} <ArrowRightOutlined style={{ fontSize: 11 }} />
          </div>
        </Card>

        {/* ── 统计概览 ── */}
        <Card style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <h3
              style={{
                fontSize: 16,
                fontWeight: 600,
                color: '#111',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                margin: 0,
              }}
            >
              <CloudServerOutlined /> {t('storage')}
            </h3>
            <SyncOutlined style={{ fontSize: 14, color: '#ccc', cursor: 'pointer' }} />
          </div>
          <p style={{ fontSize: 13, color: '#666', margin: '0 0 10px' }}>
            {stats?.datasets ?? 0} {t('datasets')} · {stats?.images ?? 0} {t('images')} · {stats?.annotations ?? 0} {t('annotations')}
          </p>

          {/* Progress bar */}
          <div style={{ width: '100%', background: '#f0f0f0', borderRadius: 999, height: 6, marginBottom: 24 }} />

          {/* Resources */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 12, color: '#999', fontWeight: 600, marginBottom: 10, letterSpacing: 0.3 }}>
              {t('resources')}
            </div>
            {[
              { icon: <FolderOutlined />, label: t('projects'), value: String(stats?.annotations ?? 0) },
              { icon: <DatabaseOutlined />, label: t('datasets'), value: String(stats?.datasets ?? 0) },
              { icon: <ExperimentOutlined />, label: t('models'), value: String(stats?.models?.total ?? 0) },
              { icon: <PictureOutlined />, label: t('images'), value: String(stats?.images ?? 0) },
              { icon: <CloudServerOutlined />, label: t('deployments'), value: String(stats?.models?.deployed ?? 0) },
            ].map((r, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: 13,
                  padding: '6px 0',
                }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#666' }}>
                  <span style={{ color: '#bbb', fontSize: 13, display: 'flex' }}>{r.icon}</span>
                  {r.label}
                </span>
                <span style={{ fontWeight: 600, color: '#111' }}>{r.value}</span>
              </div>
            ))}
          </div>

          {/* Largest datasets */}
          {recentDatasets.length > 0 && (
            <div>
              <div style={{ fontSize: 12, color: '#999', fontWeight: 600, marginBottom: 8, letterSpacing: 0.3 }}>
                {t('largestItems')}
              </div>
              {recentDatasets.slice(0, 3).map((ds) => (
                <div key={ds.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13, padding: '4px 0' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#666' }}>
                    <DatabaseOutlined style={{ color: '#bbb', fontSize: 13 }} />
                    {ds.name}
                  </span>
                  <span style={{ fontWeight: 500, color: '#111' }}>{ds.count} {t('images')}</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default HomePage;
