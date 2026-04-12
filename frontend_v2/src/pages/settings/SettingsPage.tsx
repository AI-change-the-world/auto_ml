import React from 'react';
import { Typography, Card, Descriptions, Tag } from 'antd';

const { Title, Text } = Typography;

const SettingsPage: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      <Title level={4} style={{ margin: '0 0 16px' }}>设置</Title>

      <Card title="系统信息" style={{ marginBottom: 16 }}>
        <Descriptions column={1}>
          <Descriptions.Item label="平台名称">AutoML Platform</Descriptions.Item>
          <Descriptions.Item label="版本">v0.1.0</Descriptions.Item>
          <Descriptions.Item label="API 地址">
            <Text code>{window.location.origin}/api</Text>
          </Descriptions.Item>
          <Descriptions.Item label="后端代理">
            <Text code>http://localhost:8000</Text>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="功能模块">
        <Descriptions column={2}>
          <Descriptions.Item label="数据集管理"><Tag color="success">已启用</Tag></Descriptions.Item>
          <Descriptions.Item label="标注管理"><Tag color="success">已启用</Tag></Descriptions.Item>
          <Descriptions.Item label="训练任务"><Tag color="success">已启用</Tag></Descriptions.Item>
          <Descriptions.Item label="模型部署"><Tag color="success">已启用</Tag></Descriptions.Item>
          <Descriptions.Item label="用户管理"><Tag color="default">待开发</Tag></Descriptions.Item>
          <Descriptions.Item label="预测服务"><Tag color="default">待开发</Tag></Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
};

export default SettingsPage;
