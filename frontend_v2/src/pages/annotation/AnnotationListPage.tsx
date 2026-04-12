import React, { useEffect, useState, useCallback } from 'react';
import { Card, Row, Col, Button, Typography, Spin, Empty, Tag, Modal, Form, Input, Select, message, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { listAnnotations, createAnnotation, deleteAnnotation } from '../../api/annotation';
import { listDatasets } from '../../api/dataset';
import type { AnnotationProject, AnnotationCreate, Dataset } from '../../types';
import { AnnotationTypeLabels, AnnotationTypeColors } from '../../types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const AnnotationListPage: React.FC = () => {
  const navigate = useNavigate();
  const [annotations, setAnnotations] = useState<AnnotationProject[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [form] = Form.useForm();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const result = await listAnnotations(1, 50);
      setAnnotations(result.items || []);
      setTotal(result.total);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, []);

  const loadDatasets = async () => {
    try {
      const result = await listDatasets(1, 100);
      setDatasets(result.items || []);
    } catch { /* ignore */ }
  };

  useEffect(() => { loadData(); }, [loadData]);

  const handleOpenCreate = () => {
    loadDatasets();
    setModalOpen(true);
  };

  const handleCreate = async (values: AnnotationCreate & { classesInput?: string }) => {
    setCreating(true);
    try {
      const data: AnnotationCreate = {
        name: values.name,
        annotation_type: values.annotation_type ?? 0,
        dataset_id: values.dataset_id,
      };
      if (values.classesInput) {
        const classes = values.classesInput.split(',').map((c) => c.trim()).filter(Boolean);
        data.classes = JSON.stringify(classes);
      }
      await createAnnotation(data);
      message.success('标注项目创建成功');
      setModalOpen(false);
      form.resetFields();
      loadData();
    } catch {
      message.error('创建失败');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteAnnotation(id);
      message.success('已删除');
      loadData();
    } catch {
      message.error('删除失败');
    }
  };

  const parseClasses = (classesStr: string | null): string[] => {
    if (!classesStr) return [];
    try {
      const arr = JSON.parse(classesStr);
      return Array.isArray(arr) ? arr : [];
    } catch {
      return classesStr.split(',').map((c) => c.trim()).filter(Boolean);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Title level={4} style={{ margin: 0 }}>标注项目</Title>
          <Text type="secondary">{total} 个项目</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>新建标注</Button>
      </div>

      <Spin spinning={loading}>
        {annotations.length === 0 && !loading ? (
          <Empty description="暂无标注项目" style={{ marginTop: 80 }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>创建第一个项目</Button>
          </Empty>
        ) : (
          <Row gutter={[16, 16]}>
            {annotations.map((ann) => {
              const classes = parseClasses(ann.classes);
              return (
                <Col xs={24} sm={12} md={8} lg={6} key={ann.id}>
                  <Card
                    hoverable
                    onClick={() => navigate(`/annotations/${ann.id}/label`)}
                    actions={[
                      <EditOutlined key="edit" onClick={(e) => { e.stopPropagation(); navigate(`/annotations/${ann.id}/label`); }} />,
                      <Popconfirm
                        key="delete"
                        title="确认删除？"
                        onConfirm={(e) => { e?.stopPropagation(); handleDelete(ann.id); }}
                        onCancel={(e) => e?.stopPropagation()}
                      >
                        <DeleteOutlined onClick={(e) => e.stopPropagation()} style={{ color: '#ff4d4f' }} />
                      </Popconfirm>,
                    ]}
                  >
                    <Card.Meta
                      title={<Text ellipsis={{ tooltip: ann.name }}>{ann.name}</Text>}
                      description={
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                          <div>
                            <Tag color={AnnotationTypeColors[ann.annotation_type] || 'default'}>
                              {AnnotationTypeLabels[ann.annotation_type] || '未知'}
                            </Tag>
                            {classes.length > 0 && (
                              <Text type="secondary" style={{ fontSize: 12 }}>{classes.length} 个类别</Text>
                            )}
                          </div>
                          {ann.dataset_id && (
                            <Text type="secondary" style={{ fontSize: 12 }}>数据集 #{ann.dataset_id}</Text>
                          )}
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            {dayjs(ann.created_at).format('YYYY-MM-DD HH:mm')}
                          </Text>
                        </div>
                      }
                    />
                  </Card>
                </Col>
              );
            })}
          </Row>
        )}
      </Spin>

      {/* 新建对话框 */}
      <Modal
        title="新建标注项目"
        open={modalOpen}
        onCancel={() => { setModalOpen(false); form.resetFields(); }}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="输入标注项目名称" />
          </Form.Item>
          <Form.Item name="annotation_type" label="标注类型" initialValue={0}>
            <Select options={[
              { label: '检测', value: 0 },
              { label: '分类', value: 1 },
              { label: '分割', value: 2 },
            ]} />
          </Form.Item>
          <Form.Item name="dataset_id" label="关联数据集">
            <Select
              placeholder="选择数据集"
              allowClear
              options={datasets.map((d) => ({ label: d.name, value: d.id }))}
            />
          </Form.Item>
          <Form.Item name="classesInput" label="类别" extra="多个类别用逗号分隔，如: person, car, dog">
            <Input placeholder="person, car, dog" />
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

export default AnnotationListPage;
