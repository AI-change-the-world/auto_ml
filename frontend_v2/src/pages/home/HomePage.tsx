import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Button, Spin, Typography } from 'antd';
import {
  DatabaseOutlined,
  TagsOutlined,
  ThunderboltOutlined,
  CloudServerOutlined,
  PlusOutlined,
  RocketOutlined,
  CheckCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getHomeStats } from '../../api/home';
import type { HomeStats } from '../../types';

const { Title, Text } = Typography;

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<HomeStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await getHomeStats();
      setStats(data);
    } catch {
      // API 可能未连接
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      {/* 欢迎区 */}
      <div style={{ marginBottom: 32 }}>
        <Title level={3} style={{ marginBottom: 4 }}>AutoML Platform</Title>
        <Text type="secondary">标注、训练、部署你的计算机视觉模型</Text>
      </div>

      {/* 统计卡片 */}
      <Spin spinning={loading}>
        <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
          <Col xs={12} sm={6}>
            <Card hoverable onClick={() => navigate('/datasets')} style={{ cursor: 'pointer' }}>
              <Statistic
                title="数据集"
                value={stats?.datasets ?? 0}
                prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card hoverable onClick={() => navigate('/annotations')} style={{ cursor: 'pointer' }}>
              <Statistic
                title="标注项目"
                value={stats?.annotations ?? 0}
                prefix={<TagsOutlined style={{ color: '#52c41a' }} />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card hoverable onClick={() => navigate('/tasks')} style={{ cursor: 'pointer' }}>
              <Statistic
                title="任务"
                value={stats?.tasks?.total ?? 0}
                prefix={<ThunderboltOutlined style={{ color: '#fa8c16' }} />}
                suffix={
                  <span style={{ fontSize: 13, color: '#999' }}>
                    {stats?.tasks?.running ? (
                      <span><SyncOutlined spin style={{ color: '#1890ff', marginLeft: 8 }} /> {stats.tasks.running} 运行中</span>
                    ) : null}
                  </span>
                }
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card hoverable onClick={() => navigate('/deploy')} style={{ cursor: 'pointer' }}>
              <Statistic
                title="模型"
                value={stats?.models?.total ?? 0}
                prefix={<CloudServerOutlined style={{ color: '#722ed1' }} />}
                suffix={
                  <span style={{ fontSize: 13, color: '#999' }}>
                    {stats?.models?.deployed ? (
                      <span><CheckCircleOutlined style={{ color: '#52c41a', marginLeft: 8 }} /> {stats.models.deployed} 已部署</span>
                    ) : null}
                  </span>
                }
              />
            </Card>
          </Col>
        </Row>
      </Spin>

      {/* 快速操作 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card
            title={<span><DatabaseOutlined style={{ marginRight: 8 }} />数据集</span>}
            extra={<Button type="primary" icon={<PlusOutlined />} size="small" onClick={() => navigate('/datasets')}>新建</Button>}
          >
            <Text type="secondary">上传图像、视频等数据集，管理训练数据</Text>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card
            title={<span><TagsOutlined style={{ marginRight: 8 }} />标注</span>}
            extra={<Button type="primary" icon={<PlusOutlined />} size="small" onClick={() => navigate('/annotations')}>新建</Button>}
          >
            <Text type="secondary">创建标注项目，进行目标检测、分类等标注</Text>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card
            title={<span><RocketOutlined style={{ marginRight: 8 }} />训练</span>}
            extra={<Button type="primary" icon={<PlusOutlined />} size="small" onClick={() => navigate('/tasks')}>创建</Button>}
          >
            <Text type="secondary">启动模型训练任务，自动优化模型参数</Text>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default HomePage;
