import React, { useEffect, useState, useCallback } from 'react';
import {
  Typography, Table, Tag, Button, Space, message, Popconfirm, Select,
} from 'antd';
import { ReloadOutlined, CloudUploadOutlined, CloudDownloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { listModels, deployModel, undeployModel } from '../../api/deploy';
import type { AvailableModelResponse } from '../../types/deploy';

const { Title } = Typography;

const DeployPage: React.FC = () => {
  const [models, setModels] = useState<AvailableModelResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [deployingId, setDeployingId] = useState<number | null>(null);
  const [deviceMap, setDeviceMap] = useState<Record<number, string>>({});

  const fetchModels = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listModels(page, 10);
      if (res) {
        setModels(res.items);
        setTotal(res.total);
      }
    } catch {
      message.error('获取模型列表失败');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const handleDeploy = async (modelId: number) => {
    const device = deviceMap[modelId] || 'cpu';
    setDeployingId(modelId);
    try {
      await deployModel(modelId, device);
      message.success('部署成功');
      fetchModels();
    } catch {
      message.error('部署失败');
    } finally {
      setDeployingId(null);
    }
  };

  const handleUndeploy = async (modelId: number) => {
    setDeployingId(modelId);
    try {
      await undeployModel(modelId);
      message.success('卸载成功');
      fetchModels();
    } catch {
      message.error('卸载失败');
    } finally {
      setDeployingId(null);
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
    },
    {
      title: '模型名称',
      dataIndex: 'name',
      width: 180,
      render: (v: string | null) => v || '-',
    },
    {
      title: '类型',
      dataIndex: 'model_type',
      width: 100,
      render: (v: string | null) => v || '-',
    },
    {
      title: 'Loss',
      dataIndex: 'loss',
      width: 100,
      render: (v: number | null) => (v !== null && v !== undefined ? v.toFixed(4) : '-'),
    },
    {
      title: '部署状态',
      dataIndex: 'is_deployed',
      width: 100,
      render: (v: boolean) => (
        <Tag color={v ? 'success' : 'default'}>{v ? '已部署' : '未部署'}</Tag>
      ),
    },
    {
      title: '端口',
      dataIndex: 'deployment_port',
      width: 80,
      render: (v: number | null) => v ?? '-',
    },
    {
      title: '设备',
      dataIndex: 'deployment_device',
      width: 80,
      render: (v: string | null) => v ?? '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 160,
      render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      width: 220,
      render: (_: unknown, record: AvailableModelResponse) => {
        if (record.is_deployed) {
          return (
            <Popconfirm
              title="确认卸载该模型？"
              onConfirm={() => handleUndeploy(record.id)}
              okText="确认"
              cancelText="取消"
            >
              <Button
                danger
                size="small"
                icon={<CloudDownloadOutlined />}
                loading={deployingId === record.id}
              >
                卸载
              </Button>
            </Popconfirm>
          );
        }
        return (
          <Space>
            <Select
              size="small"
              value={deviceMap[record.id] || 'cpu'}
              onChange={(v) => setDeviceMap((prev) => ({ ...prev, [record.id]: v }))}
              style={{ width: 90 }}
              options={[
                { label: 'CPU', value: 'cpu' },
                { label: 'CUDA', value: 'cuda' },
              ]}
            />
            <Popconfirm
              title="确认部署该模型？"
              onConfirm={() => handleDeploy(record.id)}
              okText="确认"
              cancelText="取消"
            >
              <Button
                type="primary"
                size="small"
                icon={<CloudUploadOutlined />}
                loading={deployingId === record.id}
              >
                部署
              </Button>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>模型部署</Title>
        <Button icon={<ReloadOutlined />} onClick={fetchModels}>刷新</Button>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={models}
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 10,
          onChange: setPage,
          showTotal: (t) => `共 ${t} 条`,
        }}
        scroll={{ x: 1000 }}
      />
    </div>
  );
};

export default DeployPage;
