import React from 'react';
import { SettingOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';

const modules = [
  { name: '数据集管理', enabled: true },
  { name: '标注管理', enabled: true },
  { name: '训练任务', enabled: true },
  { name: '模型部署', enabled: true },
  { name: '用户管理', enabled: false },
  { name: '预测服务', enabled: false },
];

const SettingsPage: React.FC = () => {
  return (
    <div className="page-container" style={{ maxWidth: 700 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 24 }}>
        <SettingOutlined /> 设置
      </h1>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24, marginBottom: 20 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: '#111', marginBottom: 16 }}>系统信息</h3>
        {[
          { label: '平台名称', value: 'AutoML Platform' },
          { label: '版本', value: 'v0.1.0' },
          { label: 'API 地址', value: `${window.location.origin}/api`, mono: true },
          { label: '后端代理', value: 'http://localhost:8000', mono: true },
        ].map((item, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: i < 3 ? '1px solid #f8f8f8' : 'none' }}>
            <span style={{ fontSize: 13, color: '#888' }}>{item.label}</span>
            <span style={{ fontSize: 13, color: '#111', fontFamily: item.mono ? 'monospace' : 'inherit', background: item.mono ? '#f7f7f8' : 'none', padding: item.mono ? '2px 8px' : 0, borderRadius: 4 }}>{item.value}</span>
          </div>
        ))}
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: '#111', marginBottom: 16 }}>功能模块</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {modules.map((m, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#fafafa', borderRadius: 8 }}>
              <span style={{ fontSize: 13, color: '#555' }}>{m.name}</span>
              {m.enabled
                ? <span style={{ fontSize: 12, color: '#16a34a', display: 'flex', alignItems: 'center', gap: 4 }}><CheckCircleOutlined /> 已启用</span>
                : <span style={{ fontSize: 12, color: '#bbb', display: 'flex', alignItems: 'center', gap: 4 }}><ClockCircleOutlined /> 待开发</span>
              }
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
