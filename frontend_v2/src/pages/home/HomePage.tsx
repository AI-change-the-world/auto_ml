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
  CloudDownloadOutlined,
  PlusOutlined,
  ArrowRightOutlined,
  SyncOutlined,
  LockOutlined,
} from '@ant-design/icons';
import { getHomeStats } from '../../api/home';
import type { HomeStats } from '../../types/home';

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
    { icon: <DatabaseOutlined style={{ fontSize: 16 }} />, value: stats?.datasets ?? 1, label: 'Datasets' },
    { icon: <PictureOutlined style={{ fontSize: 16 }} />, value: 8, label: 'Images' },
    { icon: <TagsOutlined style={{ fontSize: 16 }} />, value: stats?.annotations ?? 30, label: 'Annotations' },
    { icon: <FolderOutlined style={{ fontSize: 16 }} />, value: 1, label: 'Projects' },
    { icon: <ExperimentOutlined style={{ fontSize: 16 }} />, value: stats?.models?.total ?? 1, label: 'Models' },
    { icon: <CloudServerOutlined style={{ fontSize: 16 }} />, value: stats?.models?.deployed ?? 0, label: 'Deployments' },
  ];

  const storageUsed = 5.3;
  const storageTotal = 100;
  const storagePercent = ((storageUsed / storageTotal) * 100).toFixed(1);

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
          <HomeOutlined /> Home
        </h1>
        <p style={{ color: '#666', marginTop: 6, fontSize: 14, lineHeight: 1.5 }}>
          Welcome to AutoML Platform. Annotate, train, and deploy your computer vision models.
        </p>
      </div>

      {/* ─── Welcome Card ─── */}
      <Card style={{ padding: '24px 24px 0', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}>
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: 16,
              background: 'linear-gradient(135deg, #f97316, #ef4444)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: 22,
              fontWeight: 700,
              flexShrink: 0,
            }}
          >
            A
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h2 style={{ fontSize: 20, fontWeight: 600, color: '#111', margin: 0 }}>Welcome back, Admin</h2>
              <span
                style={{
                  fontSize: 11,
                  padding: '2px 10px',
                  background: '#f5f5f5',
                  color: '#888',
                  borderRadius: 999,
                  fontWeight: 500,
                }}
              >
                Free
              </span>
            </div>
            <p style={{ fontSize: 13, color: '#999', margin: '2px 0 0' }}>admin · admin@automl.local</p>
          </div>
        </div>

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
              <DatabaseOutlined style={{ color: '#f59e0b' }} /> Datasets
            </h3>
            <PrimaryBtn onClick={() => navigate('/datasets')}>
              <PlusOutlined /> New Dataset
            </PrimaryBtn>
          </div>
          <p style={{ fontSize: 13, color: '#888', margin: '0 0 16px' }}>Upload images, videos, and datasets</p>

          {/* Drop zone */}
          <div
            style={{
              border: '2px dashed #e5e5e5',
              borderRadius: 12,
              padding: '32px 16px',
              textAlign: 'center',
              marginBottom: 16,
              cursor: 'pointer',
              transition: 'border-color 0.2s',
            }}
            onClick={() => navigate('/datasets')}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#bbb';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#e5e5e5';
            }}
          >
            <CloudUploadOutlined style={{ fontSize: 28, color: '#ccc', display: 'block', marginBottom: 8 }} />
            <p style={{ fontSize: 13, color: '#888', margin: 0 }}>Drop images, videos or datasets</p>
            <p style={{ fontSize: 11, color: '#bbb', margin: '6px 0 0' }}>
              Images &lt;50 MB · Videos &lt;1 GB · Datasets &lt;10 GB — ZIP, TAR, NDJSON
            </p>
          </div>

          {/* Example dataset card */}
          <div
            style={{
              borderRadius: 12,
              overflow: 'hidden',
              cursor: 'pointer',
              position: 'relative',
              background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 50%, #f97316 100%)',
              display: 'flex',
              gap: 4,
              minHeight: 80,
            }}
            onClick={() => navigate('/example-dataset')}
          >
            {[1, 2, 3, 4].map((n) => (
              <div
                key={n}
                style={{
                  flex: 1,
                  background: `linear-gradient(${45 + n * 30}deg, rgba(255,255,255,0.15), rgba(0,0,0,0.1))`,
                  minHeight: 80,
                }}
              />
            ))}
            {/* Overlay info */}
            <div
              style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                padding: '24px 14px 10px',
                background: 'linear-gradient(transparent, rgba(0,0,0,0.6))',
                color: '#fff',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600, fontSize: 14 }}>
                Example Dataset <LockOutlined style={{ fontSize: 12 }} />
              </div>
              <div style={{ fontSize: 12, opacity: 0.85, marginTop: 2, display: 'flex', gap: 8, alignItems: 'center' }}>
                <span>8 imgs</span>
                <span>80 cls</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80' }} />4
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#60a5fa' }} />4
                </span>
              </div>
            </div>
          </div>

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
            View all <ArrowRightOutlined style={{ fontSize: 11 }} />
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
              <FolderOutlined style={{ color: '#f59e0b' }} /> Projects
            </h3>
            <PrimaryBtn onClick={() => navigate('/annotations')}>
              <PlusOutlined /> New Project
            </PrimaryBtn>
          </div>
          <p style={{ fontSize: 13, color: '#888', margin: '0 0 16px' }}>Create a project to organize models</p>

          {/* Drop zone */}
          <div
            style={{
              border: '2px dashed #e5e5e5',
              borderRadius: 12,
              padding: '32px 16px',
              textAlign: 'center',
              marginBottom: 16,
              cursor: 'pointer',
              transition: 'border-color 0.2s',
            }}
            onClick={() => navigate('/annotations')}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#bbb';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#e5e5e5';
            }}
          >
            <CloudUploadOutlined style={{ fontSize: 28, color: '#ccc', display: 'block', marginBottom: 8 }} />
            <p style={{ fontSize: 13, color: '#888', margin: 0 }}>Drop .pt model files</p>
            <p style={{ fontSize: 11, color: '#bbb', margin: '6px 0 0' }}>PyTorch models up to 1 GB</p>
          </div>

          {/* Example project card */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              padding: '14px 16px',
              border: '1px solid #eee',
              borderRadius: 12,
              cursor: 'pointer',
              transition: 'box-shadow 0.2s',
            }}
            onClick={() => navigate('/annotations')}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 10,
                background: '#ef4444',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontWeight: 700,
                fontSize: 16,
                flexShrink: 0,
              }}
            >
              E
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 14, fontWeight: 600, color: '#111' }}>Example Project</span>
                <LockOutlined style={{ fontSize: 12, color: '#ccc' }} />
              </div>
              <div style={{ fontSize: 12, color: '#999', display: 'flex', gap: 10, marginTop: 2 }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <ExperimentOutlined style={{ fontSize: 11 }} /> 1 model
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <DatabaseOutlined style={{ fontSize: 11 }} /> 5.3 MB
                </span>
              </div>
            </div>
          </div>

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
            View all <ArrowRightOutlined style={{ fontSize: 11 }} />
          </div>
        </Card>

        {/* ── Storage ── */}
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
              <CloudServerOutlined /> Storage
            </h3>
            <SyncOutlined style={{ fontSize: 14, color: '#ccc', cursor: 'pointer' }} />
          </div>
          <p style={{ fontSize: 13, color: '#666', margin: '0 0 10px' }}>
            {storageUsed} MB / {storageTotal} GB ({storagePercent}%)
          </p>

          {/* Progress bar */}
          <div style={{ width: '100%', background: '#f0f0f0', borderRadius: 999, height: 6, marginBottom: 24 }}>
            <div
              style={{
                width: `${Math.max(Number(storagePercent), 1)}%`,
                background: 'linear-gradient(90deg, #a855f7, #7c3aed)',
                borderRadius: 999,
                height: 6,
                transition: 'width 0.3s',
              }}
            />
          </div>

          {/* By category */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, color: '#999', fontWeight: 600, marginBottom: 8, letterSpacing: 0.3 }}>
              By category
            </div>
            {/* Category bar */}
            <div style={{ width: '100%', background: '#f0f0f0', borderRadius: 999, height: 8, marginBottom: 8, overflow: 'hidden' }}>
              <div style={{ width: '100%', background: '#f59e0b', height: 8 }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#555' }}>
              <span style={{ width: 8, height: 8, borderRadius: 999, background: '#f59e0b', flexShrink: 0 }} />
              Models (5.3 MB)
            </div>
          </div>

          {/* Resources */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 12, color: '#999', fontWeight: 600, marginBottom: 10, letterSpacing: 0.3 }}>
              Resources
            </div>
            {[
              { icon: <FolderOutlined />, label: 'Projects', value: '1' },
              { icon: <DatabaseOutlined />, label: 'Datasets', value: String(stats?.datasets ?? 1) },
              { icon: <ExperimentOutlined />, label: 'Models', value: `${stats?.models?.total ?? 1} / 100` },
              { icon: <PictureOutlined />, label: 'Images', value: '8' },
              { icon: <CloudServerOutlined />, label: 'Deployments', value: `${stats?.models?.deployed ?? 0} / 3` },
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

          {/* Largest items */}
          <div>
            <div style={{ fontSize: 12, color: '#999', fontWeight: 600, marginBottom: 8, letterSpacing: 0.3 }}>
              Largest items
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: 13,
                padding: '4px 0',
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#666' }}>
                <ExperimentOutlined style={{ color: '#bbb', fontSize: 13 }} />
                yolo26n
              </span>
              <span style={{ fontWeight: 500, color: '#111' }}>5.3 MB</span>
            </div>
          </div>
        </Card>
      </div>

      {/* ─── Recent Activity ─── */}
      <Card style={{ padding: 24, marginTop: 24 }}>
        <h3 style={{ fontSize: 18, fontWeight: 700, color: '#111', margin: '0 0 6px' }}>Recent Activity</h3>
        <p style={{ fontSize: 13, color: '#888', margin: '0 0 20px' }}>
          Your latest datasets, models, and training runs
        </p>
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#e5e5e5' }}>
          <CloudDownloadOutlined style={{ fontSize: 40, marginBottom: 10, display: 'block' }} />
          <p style={{ fontSize: 13, color: '#bbb', margin: 0 }}>No recent activity</p>
        </div>
      </Card>
    </div>
  );
};

export default HomePage;
