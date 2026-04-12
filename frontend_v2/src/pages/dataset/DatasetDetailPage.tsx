import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Typography, Spin, Row, Col, Upload, message, Descriptions, Tag, Image, Empty, Popconfirm, Breadcrumb } from 'antd';
import { InboxOutlined, ArrowLeftOutlined, DeleteOutlined, PictureOutlined } from '@ant-design/icons';
import { getDataset, getDatasetFiles, uploadDatasetFiles, previewFile, deleteDataset } from '../../api/dataset';
import type { Dataset, DatasetFile } from '../../types';
import { DataTypeLabels } from '../../types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Dragger } = Upload;

const DatasetDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [files, setFiles] = useState<DatasetFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [previewUrls, setPreviewUrls] = useState<Record<string, string>>({});

  const datasetId = id ? parseInt(id, 10) : 0;

  const loadData = useCallback(async () => {
    if (!datasetId) return;
    setLoading(true);
    try {
      const [ds, fileResult] = await Promise.all([
        getDataset(datasetId),
        getDatasetFiles(datasetId),
      ]);
      setDataset(ds);
      setFiles(fileResult.items || []);

      // 加载缩略图
      const urls: Record<string, string> = {};
      const imageFiles = (fileResult.items || []).slice(0, 20);
      const previews = await Promise.allSettled(
        imageFiles.map((f) => previewFile(datasetId, f.file_name)),
      );
      previews.forEach((p, i) => {
        if (p.status === 'fulfilled' && p.value) {
          urls[imageFiles[i].file_name] = p.value.presigned_url;
        }
      });
      setPreviewUrls(urls);
    } catch {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleUpload = async (fileList: File[]) => {
    if (!datasetId || fileList.length === 0) return;
    setUploading(true);
    try {
      const count = await uploadDatasetFiles(datasetId, fileList);
      message.success(`成功上传 ${count} 个文件`);
      loadData();
    } catch {
      message.error('上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    if (!datasetId) return;
    try {
      await deleteDataset(datasetId);
      message.success('数据集已删除');
      navigate('/datasets');
    } catch {
      message.error('删除失败');
    }
  };

  if (loading && !dataset) {
    return <div style={{ padding: 24, textAlign: 'center' }}><Spin size="large" /></div>;
  }

  if (!dataset) {
    return <div style={{ padding: 24 }}><Empty description="数据集不存在" /></div>;
  }

  return (
    <div style={{ padding: 24 }}>
      {/* 面包屑 */}
      <Breadcrumb style={{ marginBottom: 16 }} items={[
        { title: <a onClick={() => navigate('/datasets')}>数据集</a> },
        { title: dataset.name },
      ]} />

      {/* 头部 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <Button icon={<ArrowLeftOutlined />} type="text" onClick={() => navigate('/datasets')} style={{ marginRight: 8 }} />
          <Title level={4} style={{ display: 'inline', margin: 0 }}>{dataset.name}</Title>
        </div>
        <Popconfirm title="确认删除数据集？" onConfirm={handleDelete}>
          <Button danger icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      </div>

      {/* 信息卡片 */}
      <Card style={{ marginBottom: 24 }}>
        <Descriptions column={{ xs: 1, sm: 2, md: 4 }}>
          <Descriptions.Item label="数据类型"><Tag>{DataTypeLabels[dataset.data_type] || '未知'}</Tag></Descriptions.Item>
          <Descriptions.Item label="文件数量">{dataset.count}</Descriptions.Item>
          <Descriptions.Item label="存储类型">{dataset.storage_type === 1 ? 'S3' : dataset.storage_type === 0 ? '本地' : 'WebDAV'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{dayjs(dataset.created_at).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
          {dataset.description && <Descriptions.Item label="描述" span={4}>{dataset.description}</Descriptions.Item>}
        </Descriptions>
      </Card>

      {/* 上传区域 */}
      <Card title="上传文件" style={{ marginBottom: 24 }}>
        <Dragger
          multiple
          showUploadList={false}
          beforeUpload={(_, fileList) => {
            handleUpload(fileList as unknown as File[]);
            return false;
          }}
          disabled={uploading}
        >
          <p className="ant-upload-drag-icon"><InboxOutlined /></p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">支持批量上传图像文件</p>
        </Dragger>
      </Card>

      {/* 文件网格 */}
      <Card title={`文件列表 (${files.length})`}>
        {files.length === 0 ? (
          <Empty description="暂无文件，请上传" />
        ) : (
          <Row gutter={[12, 12]}>
            {files.map((file) => (
              <Col xs={12} sm={8} md={6} lg={4} xl={3} key={file.id}>
                <Card
                  size="small"
                  hoverable
                  cover={
                    previewUrls[file.file_name] ? (
                      <Image
                        src={previewUrls[file.file_name]}
                        alt={file.file_name}
                        style={{ height: 120, objectFit: 'cover' }}
                        preview={{ src: previewUrls[file.file_name] }}
                      />
                    ) : (
                      <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#fafafa' }}>
                        <PictureOutlined style={{ fontSize: 32, color: '#d9d9d9' }} />
                      </div>
                    )
                  }
                >
                  <Text ellipsis={{ tooltip: file.file_name }} style={{ fontSize: 12 }}>{file.file_name}</Text>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Card>
    </div>
  );
};

export default DatasetDetailPage;
