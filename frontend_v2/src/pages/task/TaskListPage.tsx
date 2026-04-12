import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { message, Spin, Modal, Select } from 'antd';
import { PlusOutlined, ExperimentOutlined, ReloadOutlined, ClockCircleOutlined, RightOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { listTasks, createTrainTask, getBaseModels } from '../../api/task';
import { listDatasets } from '../../api/dataset';
import { listAnnotations } from '../../api/annotation';
import type { TaskResponse, TaskCreate, BaseModelResponse } from '../../types/task';
import type { Dataset } from '../../types/dataset';
import type { AnnotationProject } from '../../types/annotation';
import { TaskStatusLabels, TaskStatusColors } from '../../types/task';

const statusStyles: Record<string, { bg: string; fg: string }> = {
  default: { bg: '#f5f5f5', fg: '#888' },
  processing: { bg: '#eef2ff', fg: '#4f6ef7' },
  error: { bg: '#fef2f2', fg: '#dc2626' },
  success: { bg: '#f0fdf4', fg: '#16a34a' },
};

const TaskListPage: React.FC = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [annotations, setAnnotations] = useState<AnnotationProject[]>([]);
  const [_bm, setBm] = useState<BaseModelResponse[]>([]);
  const [form, setForm] = useState<{ task_type: number; dataset_id?: number; annotation_id?: number }>({ task_type: 0 });

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const st = statusFilter === 'all' ? undefined : Number(statusFilter);
      const r = await listTasks(page, 20, st);
      if (r) { setTasks(r.items); setTotal(r.total); }
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  }, [page, statusFilter]);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  const openCreate = async () => {
    setCreateOpen(true);
    try {
      const [d, a, b] = await Promise.all([listDatasets(1, 100), listAnnotations(1, 100), getBaseModels()]);
      if (d) setDatasets(d.items);
      if (a) setAnnotations(a.items);
      if (b) setBm(Array.isArray(b) ? b : []);
    } catch {}
  };

  const handleCreate = async () => {
    if (!form.dataset_id) { message.warning('请选择数据集'); return; }
    setCreating(true);
    try {
      const data: TaskCreate = { task_type: form.task_type, dataset_id: form.dataset_id, annotation_id: form.annotation_id };
      await createTrainTask(data);
      message.success('创建成功');
      setCreateOpen(false);
      setForm({ task_type: 0 });
      fetchTasks();
    } catch { message.error('创建失败'); }
    finally { setCreating(false); }
  };

  const tabs = [
    { key: 'all', label: '全部' }, { key: '0', label: '排队中' },
    { key: '1', label: '运行中' }, { key: '3', label: '已完成' }, { key: '2', label: '失败' },
  ];
  const typeLabels: Record<number, string> = { 0: '检测', 1: '分类', 2: '分割' };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}><ExperimentOutlined /> 训练任务</h1>
          <p style={{ color: '#888', fontSize: 13, marginTop: 4 }}>管理模型训练任务</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={fetchTasks} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '8px 14px', border: '1px solid #e5e5e5', borderRadius: 8, fontSize: 13, background: '#fff', color: '#666', cursor: 'pointer' }}><ReloadOutlined /> 刷新</button>
          <button onClick={openCreate} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '8px 16px', background: '#4f6ef7', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer' }}><PlusOutlined /> 创建训练</button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #eee', marginBottom: 20 }}>
        {tabs.map((t) => (
          <button key={t.key} onClick={() => { setStatusFilter(t.key); setPage(1); }} style={{
            padding: '10px 16px', fontSize: 13, fontWeight: 500, cursor: 'pointer', border: 'none', background: 'none',
            borderBottom: statusFilter === t.key ? '2px solid #4f6ef7' : '2px solid transparent',
            color: statusFilter === t.key ? '#4f6ef7' : '#888', marginBottom: -1,
          }}>{t.label}</button>
        ))}
      </div>

      {loading ? <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
      : tasks.length === 0 ? <div style={{ textAlign: 'center', padding: 80, color: '#ccc' }}><ExperimentOutlined style={{ fontSize: 48, marginBottom: 12 }} /><p>暂无任务</p></div>
      : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {tasks.map((task) => {
            const ck = TaskStatusColors[task.status] || 'default';
            const s = statusStyles[ck] || statusStyles.default;
            return (
              <div key={task.id} onClick={() => navigate(`/tasks/${task.id}`)} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: '14px 18px', cursor: 'pointer', transition: 'box-shadow 0.2s',
              }} onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)'} onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  <div style={{ width: 36, height: 36, borderRadius: 8, background: '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#4f6ef7', fontWeight: 600, fontSize: 13 }}>#{task.id}</div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 500, color: '#111' }}>{typeLabels[task.task_type] ?? `类型${task.task_type}`} 训练</span>
                      <span style={{ padding: '1px 8px', fontSize: 11, borderRadius: 999, background: s.bg, color: s.fg }}>{TaskStatusLabels[task.status] || '未知'}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, color: '#999', marginTop: 2 }}>
                      <span>数据集 #{task.dataset_id ?? '-'}</span>
                      {task.annotation_id && <span>标注 #{task.annotation_id}</span>}
                      <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}><ClockCircleOutlined /> {dayjs(task.created_at).format('MM-DD HH:mm')}</span>
                    </div>
                  </div>
                </div>
                <RightOutlined style={{ color: '#ddd' }} />
              </div>
            );
          })}
        </div>
      )}

      <div style={{ marginTop: 16, fontSize: 13, color: '#bbb' }}>共 {total} 条</div>

      <Modal title="创建训练任务" open={createOpen} onOk={handleCreate} onCancel={() => setCreateOpen(false)} confirmLoading={creating} okText="创建" cancelText="取消">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 16 }}>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>任务类型</label>
            <div style={{ display: 'flex', gap: 8 }}>
              {Object.entries(typeLabels).map(([k, v]) => (
                <button key={k} onClick={() => setForm({ ...form, task_type: Number(k) })} style={{
                  padding: '5px 14px', fontSize: 13, borderRadius: 8, cursor: 'pointer',
                  border: form.task_type === Number(k) ? '1px solid #4f6ef7' : '1px solid #e5e5e5',
                  background: form.task_type === Number(k) ? '#eef2ff' : '#fff',
                  color: form.task_type === Number(k) ? '#4f6ef7' : '#666',
                }}>{v}</button>
              ))}
            </div>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>数据集</label>
            <Select style={{ width: '100%' }} placeholder="选择数据集" value={form.dataset_id} onChange={(v) => setForm({ ...form, dataset_id: v })} options={datasets.map((d) => ({ label: d.name, value: d.id }))} showSearch optionFilterProp="label" />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>标注项目（可选）</label>
            <Select style={{ width: '100%' }} placeholder="选择标注项目" allowClear value={form.annotation_id} onChange={(v) => setForm({ ...form, annotation_id: v })} options={annotations.map((a) => ({ label: a.name, value: a.id }))} showSearch optionFilterProp="label" />
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default TaskListPage;
