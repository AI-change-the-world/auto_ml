import React, { useEffect, useState, useCallback } from 'react';
import {
  Typography, Button, Table, Tag, Space, Modal, Form, Select, InputNumber, message, Tabs,
} from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { listTasks, createTrainTask, getBaseModels } from '../../api/task';
import { listDatasets } from '../../api/dataset';
import { listAnnotations } from '../../api/annotation';
import type { TaskResponse, TaskCreate, BaseModelResponse } from '../../types/task';
import type { Dataset } from '../../types/dataset';
import type { AnnotationProject } from '../../types/annotation';
import { TaskStatusLabels, TaskStatusColors } from '../../types/task';

const { Title } = Typography;

const TaskListPage: React.FC = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form] = Form.useForm();

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [annotations, setAnnotations] = useState<AnnotationProject[]>([]);
  const [baseModels, setBaseModels] = useState<BaseModelResponse[]>([]);

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const status = statusFilter === 'all' ? undefined : Number(statusFilter);
      const res = await listTasks(page, 10, status);
      if (res) {
        setTasks(res.items);
        setTotal(res.total);
      }
    } catch {
      message.error('获取任务列表失败');
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const loadFormData = async () => {
    try {
      const [dsRes, annRes, bmRes] = await Promise.all([
        listDatasets(1, 100),
        listAnnotations(1, 100),
        getBaseModels(),
      ]);
      if (dsRes) setDatasets(dsRes.items);
      if (annRes) setAnnotations(annRes.items);
      if (bmRes) setBaseModels(Array.isArray(bmRes) ? bmRes : []);
    } catch {
      /* ignore */
    }
  };

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      setCreating(true);
      const data: TaskCreate = {
        task_type: values.task_type,
        dataset_id: values.dataset_id,
        annotation_id: values.annotation_id,
        config: values.config ? JSON.stringify(values.config) : undefined,
      };
      await createTrainTask(data);
      message.success('任务创建成功');
      setCreateOpen(false);
      form.resetFields();
      fetchTasks();
    } catch {
      message.error('创建失败');
    } finally {
      setCreating(false);
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
    },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      width: 120,
      render: (v: number) => {
        const labels: Record<number, string> = { 0: '检测', 1: '分类', 2: '分割' };
        return labels[v] ?? `类型${v}`;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (v: number) => (
        <Tag color={TaskStatusColors[v] || 'default'}>{TaskStatusLabels[v] || '未知'}</Tag>
      ),
    },
    {
      title: '数据集 ID',
      dataIndex: 'dataset_id',
      width: 100,
      render: (v: number | null) => v ?? '-',
    },
    {
      title: '标注 ID',
      dataIndex: 'annotation_id',
      width: 100,
      render: (v: number | null) => v ?? '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      width: 100,
      render: (_: unknown, record: TaskResponse) => (
        <Button type="link" size="small" onClick={() => navigate(`/tasks/${record.id}`)}>
          详情
        </Button>
      ),
    },
  ];

  const tabItems = [
    { key: 'all', label: '全部' },
    { key: '0', label: '排队中' },
    { key: '1', label: '运行中' },
    { key: '3', label: '已完成' },
    { key: '2', label: '失败' },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>训练任务</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchTasks}>刷新</Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => { setCreateOpen(true); loadFormData(); }}
          >
            创建训练
          </Button>
        </Space>
      </div>

      <Tabs
        activeKey={statusFilter}
        onChange={(key) => { setStatusFilter(key); setPage(1); }}
        items={tabItems}
        style={{ marginBottom: 16 }}
      />

      <Table
        rowKey="id"
        columns={columns}
        dataSource={tasks}
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 10,
          onChange: setPage,
          showTotal: (t) => `共 ${t} 条`,
        }}
      />

      <Modal
        title="创建训练任务"
        open={createOpen}
        onOk={handleCreate}
        onCancel={() => { setCreateOpen(false); form.resetFields(); }}
        confirmLoading={creating}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="task_type" label="任务类型" rules={[{ required: true, message: '请选择任务类型' }]}>
            <Select placeholder="选择任务类型">
              <Select.Option value={0}>检测</Select.Option>
              <Select.Option value={1}>分类</Select.Option>
              <Select.Option value={2}>分割</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="dataset_id" label="数据集" rules={[{ required: true, message: '请选择数据集' }]}>
            <Select placeholder="选择数据集" showSearch optionFilterProp="label">
              {datasets.map((ds) => (
                <Select.Option key={ds.id} value={ds.id} label={ds.name}>{ds.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="annotation_id" label="标注项目">
            <Select placeholder="选择标注项目（可选）" allowClear showSearch optionFilterProp="label">
              {annotations.map((a) => (
                <Select.Option key={a.id} value={a.id} label={a.name}>{a.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="base_model_id" label="基础模型">
            <Select placeholder="选择基础模型（可选）" allowClear>
              {baseModels.map((m) => (
                <Select.Option key={m.id} value={m.id}>{m.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="epochs" label="训练轮次">
            <InputNumber min={1} max={1000} placeholder="默认值" style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TaskListPage;
