import React, { useEffect, useState, useCallback } from 'react';
import { message, Spin, Modal, Select } from 'antd';
import { ThunderboltOutlined, ReloadOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { getAugmentCapabilities, processAugment } from '../../api/augment';
import { listDatasets } from '../../api/dataset';
import type { AugmentCapability } from '../../types/augment';
import type { Dataset } from '../../types/dataset';
import { AugmentTypeColors } from '../../types/augment';

const AugmentPage: React.FC = () => {
    const [capabilities, setCapabilities] = useState<AugmentCapability[]>([]);
    const [datasets, setDatasets] = useState<Dataset[]>([]);
    const [loading, setLoading] = useState(false);
    const [processOpen, setProcessOpen] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [selectedType, setSelectedType] = useState<string | null>(null);
    const [form, setForm] = useState<{ dataset_id?: number; augment_type: string }>({ augment_type: '' });

    const fetchCapabilities = useCallback(async () => {
        setLoading(true);
        try {
            const r = await getAugmentCapabilities();
            if (r) setCapabilities(r);
        } catch { message.error('加载失败'); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { fetchCapabilities(); }, [fetchCapabilities]);

    const openProcess = async (augType: string) => {
        setSelectedType(augType);
        setForm({ dataset_id: undefined, augment_type: augType });
        setProcessOpen(true);
        try {
            const r = await listDatasets(1, 100);
            if (r) setDatasets(r.items);
        } catch { }
    };

    const handleProcess = async () => {
        if (!form.dataset_id) { message.warning('请选择数据集'); return; }
        setProcessing(true);
        try {
            await processAugment({ dataset_id: form.dataset_id, augment_type: form.augment_type });
            message.success('增强任务已提交');
            setProcessOpen(false);
        } catch { message.error('提交失败'); }
        finally { setProcessing(false); }
    };

    const typeIcons: Record<string, string> = { cv: '🔄', gan: '🧠', sd: '🎨' };

    return (
        <div className="page-container">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <div>
                    <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
                        <ThunderboltOutlined /> 数据增强
                    </h1>
                    <p style={{ color: '#888', fontSize: 13, marginTop: 4 }}>使用多种增强策略扩充训练数据</p>
                </div>
                <button onClick={fetchCapabilities} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '8px 14px', border: '1px solid #e5e5e5', borderRadius: 8, fontSize: 13, background: '#fff', color: '#666', cursor: 'pointer' }}>
                    <ReloadOutlined /> 刷新
                </button>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
            ) : capabilities.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 80, color: '#ccc' }}>
                    <ThunderboltOutlined style={{ fontSize: 48, marginBottom: 12 }} />
                    <p>暂无可用增强能力</p>
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
                    {capabilities.map((cap) => {
                        const color = AugmentTypeColors[cap.id] || '#4f6ef7';
                        return (
                            <div key={cap.id} style={{
                                background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24,
                                display: 'flex', flexDirection: 'column', gap: 12, transition: 'box-shadow 0.2s',
                            }} onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.06)'}
                                onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <div style={{
                                        width: 48, height: 48, borderRadius: 12, background: `${color}15`,
                                        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24,
                                    }}>
                                        {typeIcons[cap.id] || '⚡'}
                                    </div>
                                    <div>
                                        <div style={{ fontSize: 16, fontWeight: 600, color: '#111' }}>{cap.name}</div>
                                        <span style={{ padding: '1px 8px', fontSize: 11, borderRadius: 999, background: `${color}15`, color }}>
                                            {cap.id.toUpperCase()}
                                        </span>
                                    </div>
                                </div>
                                <p style={{ fontSize: 13, color: '#666', margin: 0, lineHeight: 1.6 }}>{cap.description}</p>
                                <button onClick={() => openProcess(cap.id)} style={{
                                    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                                    padding: '8px 16px', background: color, color: '#fff', border: 'none', borderRadius: 8,
                                    fontSize: 13, fontWeight: 500, cursor: 'pointer', marginTop: 'auto',
                                }}>
                                    <PlayCircleOutlined /> 开始增强
                                </button>
                            </div>
                        );
                    })}
                </div>
            )}

            <Modal title={`数据增强 - ${selectedType?.toUpperCase() || ''}`} open={processOpen} onOk={handleProcess}
                onCancel={() => setProcessOpen(false)} confirmLoading={processing} okText="提交" cancelText="取消">
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 16 }}>
                    <div>
                        <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>选择数据集</label>
                        <Select style={{ width: '100%' }} placeholder="选择要增强的数据集" value={form.dataset_id}
                            onChange={(v) => setForm({ ...form, dataset_id: v })}
                            options={datasets.map((d) => ({ label: d.name, value: d.id }))} showSearch optionFilterProp="label" />
                    </div>
                </div>
            </Modal>
        </div>
    );
};

export default AugmentPage;
