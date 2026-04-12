import React, { useEffect, useState, useCallback } from 'react';
import { message, Spin, Modal, Select } from 'antd';
import { CloudServerOutlined, ReloadOutlined, CloudUploadOutlined, CloudDownloadOutlined, CheckCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { listModels, deployModel, undeployModel } from '../../api/deploy';
import type { AvailableModelResponse } from '../../types/deploy';

const DeployPage: React.FC = () => {
  const [models, setModels] = useState<AvailableModelResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [deployingId, setDeployingId] = useState<number | null>(null);
  const [deviceMap, setDeviceMap] = useState<Record<number, string>>({});

  const fetchModels = useCallback(async () => {
    setLoading(true);
    try { const r = await listModels(1, 20); if (r) { setModels(r.items); setTotal(r.total); } }
    catch { message.error('加载失败'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchModels(); }, [fetchModels]);

  const handleDeploy = async (id: number) => {
    setDeployingId(id);
    try { await deployModel(id, deviceMap[id] || 'cpu'); message.success('部署成功'); fetchModels(); }
    catch { message.error('部署失败'); }
    finally { setDeployingId(null); }
  };

  const handleUndeploy = async (id: number) => {
    Modal.confirm({ title: '确认卸载', content: '确定卸载？', onOk: async () => {
      setDeployingId(id);
      try { await undeployModel(id); message.success('卸载成功'); fetchModels(); }
      catch { message.error('卸载失败'); }
      finally { setDeployingId(null); }
    }});
  };

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}><CloudServerOutlined /> 模型部署</h1>
          <p style={{ color: '#888', fontSize: 13, marginTop: 4 }}>管理模型的部署与卸载</p>
        </div>
        <button onClick={fetchModels} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '8px 14px', border: '1px solid #e5e5e5', borderRadius: 8, fontSize: 13, background: '#fff', color: '#666', cursor: 'pointer' }}><ReloadOutlined /> 刷新</button>
      </div>

      {loading ? <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
      : models.length === 0 ? <div style={{ textAlign: 'center', padding: 80, color: '#ccc' }}><CloudServerOutlined style={{ fontSize: 48, marginBottom: 12 }} /><p>暂无可用模型</p></div>
      : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {models.map((m) => (
            <div key={m.id} style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ width: 36, height: 36, borderRadius: 8, background: 'linear-gradient(135deg, #faf5ff, #eef2ff)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8b5cf6' }}><CloudServerOutlined /></div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 14, fontWeight: 500, color: '#111' }}>{m.name || `Model #${m.id}`}</span>
                    {m.model_type && <span style={{ padding: '1px 8px', background: '#f5f5f5', color: '#888', fontSize: 11, borderRadius: 999 }}>{m.model_type}</span>}
                    {m.is_deployed
                      ? <span style={{ padding: '1px 8px', background: '#f0fdf4', color: '#16a34a', fontSize: 11, borderRadius: 999, display: 'flex', alignItems: 'center', gap: 3 }}><CheckCircleOutlined style={{ fontSize: 10 }} /> 已部署</span>
                      : <span style={{ padding: '1px 8px', background: '#f5f5f5', color: '#999', fontSize: 11, borderRadius: 999 }}>未部署</span>
                    }
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 12, color: '#999', marginTop: 2 }}>
                    {m.loss != null && <span>Loss: {m.loss.toFixed(4)}</span>}
                    {m.deployment_port && <span>端口: {m.deployment_port}</span>}
                    {m.deployment_device && <span>设备: {m.deployment_device}</span>}
                    <span>{dayjs(m.created_at).format('YYYY-MM-DD')}</span>
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                {m.is_deployed ? (
                  <button onClick={() => handleUndeploy(m.id)} disabled={deployingId === m.id} style={{
                    display: 'inline-flex', alignItems: 'center', gap: 4, padding: '6px 14px',
                    border: '1px solid #fecaca', borderRadius: 8, fontSize: 13, background: '#fff', color: '#dc2626', cursor: 'pointer',
                  }}><CloudDownloadOutlined /> 卸载</button>
                ) : (
                  <>
                    <Select size="small" value={deviceMap[m.id] || 'cpu'} onChange={(v) => setDeviceMap((p) => ({ ...p, [m.id]: v }))} style={{ width: 80 }} options={[{ label: 'CPU', value: 'cpu' }, { label: 'CUDA', value: 'cuda' }]} />
                    <button onClick={() => handleDeploy(m.id)} disabled={deployingId === m.id} style={{
                      display: 'inline-flex', alignItems: 'center', gap: 4, padding: '6px 14px',
                      background: '#4f6ef7', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, cursor: 'pointer',
                    }}><CloudUploadOutlined /> 部署</button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      <div style={{ marginTop: 16, fontSize: 13, color: '#bbb' }}>共 {total} 个模型</div>
    </div>
  );
};

export default DeployPage;
