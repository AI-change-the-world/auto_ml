import React, { useEffect, useState, useCallback } from 'react';
import { Card, Row, Col, Button, Input, Modal, Form, Select, Typography, Spin, Empty, Tag, Popconfirm, message } from 'antd';
import { PlusOutlined, SearchOutlined, DeleteOutlined, PictureOutlined, FileTextOutlined, VideoCameraOutlined, AudioOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { listDatasets, createDataset, deleteDataset } from '../../api/dataset';
import type { Dataset, DatasetCreate } from '../../types';
import { DataTypeLabels } from '../../types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const dataTypeIconMap: Record<number, React.ReactNode> = {
  0: <PictureOutlined />,
  1: <FileTextOutlined />,
  2: <VideoCameraOutlined />,
  3: <AudioOutlined />,
};

const DatasetListPage: React.FC = () => {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [keyword, setKeyword] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form] = Form.useForm();

  const loadData = useCallback(async (search?: string) => {
    setLoading(true);
    try {
      const result = await listDatasets(1, 50, search || undefined);
      setDatasets(result.items || []);
      setTotal(result.total);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSearch = (value: string) => {
    setKeyword(value);
    loadData(value);
  };

  const handleCreate = async (values: DatasetCreate) => {
    setCreating(true);
    try {
      await createDataset(values);
      message.success('数据集创建成功');
      setModalOpen(false);
      form.resetFields();
      loadData(keyword);
    } catch {
      message.error('创建失败');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteDataset(id);
      message.success('已删除');
      loadData(keyword);
    } catch {
      message.error('删除失败');
    }
  };

  return (
    <div style={{ padding: 24 }}>
      {/* 顶部 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Title level={4} style={{ margin: 0 }}>数据集</Title>
          <Text type="secondary">{total} 个数据集</Text>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <Input.Search
            placeholder="搜索数据集"
            prefix={<SearchOutlined />}
            style={{ width: 240 }}
            onSearch={handleSearch}
            allowClear
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            新建数据集
          </Button>
        </div>
      </div>

      {/* 数据集网格 */}
      <Spin spinning={loading}>
        {datasets.length === 0 && !loading ? (
          <Empty description="暂无数据集" style={{ marginTop: 80 }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
              创建第一个数据集
            </Button>
          </Empty>
        ) : (
          <Row gutter={[16, 16]}>
            {datasets.map((ds) => (
              <Col xs={24} sm={12} md={8} lg={6} key={ds.id}>
                <Card
                  hoverable
                  onClick={() => navigate(`/datasets/${ds.id}`)}
                  actions={[
                    <Popconfirm
                      key="delete"
                      title="确认删除？"
                      onConfirm={(e) => { e?.stopPropagation(); handleDelete(ds.id); }}
                      onCancel={(e) => e?.stopPropagation()}
                    >
                      <DeleteOutlined onClick={(e) => e.stopPropagation()} style={{ color: '#ff4d4f' }} />
                    </Popconfirm>,
                  ]}
                >
                  <Card.Meta
                    avatar={
                      <div style={{
                        width: 40, height: 40, borderRadius: 8,
                        background: '#f0f5ff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 20, color: '#1890ff',
                      }}>
                        {dataTypeIconMap[ds.data_type] || <PictureOutlined />}
                      </div>
                    }
                    title={<Text ellipsis={{ tooltip: ds.name }} style={{ maxWidth: 160 }}>{ds.name}</Text>}
                    description={
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <div>
                          <Tag>{DataTypeLabels[ds.data_type] || '未知'}</Tag>
                          <Text type="secondary" style={{ fontSize: 12 }}>{ds.count} 文件</Text>
                        </div>
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {dayjs(ds.created_at).format('YYYY-MM-DD HH:mm')}
                        </Text>
                      </div>
                    }
                  />
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Spin>

      {/* 新建对话框 */}
      <Modal
        title="新建数据集"
        open={modalOpen}
        onCancel={() => { setModalOpen(false); form.resetFields(); }}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入数据集名称' }]}>
            <Input placeholder="输入数据集名称" />
          </Form.Item>
          <Form.Item name="data_type" label="数据类型" initialValue={0}>
            <Select options={[
              { label: '图像', value: 0 },
              { label: '文本', value: 1 },
              { label: '视频', value: 2 },
              { label: '音频', value: 3 },
            ]} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="可选描述" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Button onClick={() => { setModalOpen(false); form.resetFields(); }} style={{ marginRight: 8 }}>取消</Button>
            <Button type="primary" htmlType="submit" loading={creating}>创建</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DatasetListPage;
