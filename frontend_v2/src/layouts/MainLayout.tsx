import React, { useState } from 'react';
import { Layout, Menu, Typography } from 'antd';
import {
  HomeOutlined,
  DatabaseOutlined,
  TagsOutlined,
  ThunderboltOutlined,
  CloudServerOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';

const { Sider, Content } = Layout;
const { Text } = Typography;

const menuItems = [
  { key: '/', icon: <HomeOutlined />, label: '首页' },
  { key: '/datasets', icon: <DatabaseOutlined />, label: '数据集' },
  { key: '/annotations', icon: <TagsOutlined />, label: '标注' },
  { key: '/tasks', icon: <ThunderboltOutlined />, label: '任务' },
  { key: '/deploy', icon: <CloudServerOutlined />, label: '模型部署' },
  { key: '/settings', icon: <SettingOutlined />, label: '设置' },
];

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const selectedKey = menuItems
    .filter((item) => item.key !== '/')
    .find((item) => location.pathname.startsWith(item.key))?.key || '/';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        trigger={null}
        width={220}
        style={{
          background: '#fff',
          borderRight: '1px solid #f0f0f0',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Logo */}
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: collapsed ? 0 : '0 20px',
            borderBottom: '1px solid #f0f0f0',
            cursor: 'pointer',
          }}
          onClick={() => navigate('/')}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontWeight: 700,
              fontSize: 16,
              flexShrink: 0,
            }}
          >
            A
          </div>
          {!collapsed && (
            <span style={{ marginLeft: 12, fontWeight: 600, fontSize: 16, color: '#1a1a1a' }}>
              AutoML
            </span>
          )}
        </div>

        {/* 折叠按钮 */}
        <div
          style={{
            padding: '12px 0 4px',
            display: 'flex',
            justifyContent: collapsed ? 'center' : 'flex-end',
            paddingRight: collapsed ? 0 : 16,
          }}
        >
          <div
            onClick={() => setCollapsed(!collapsed)}
            style={{ cursor: 'pointer', color: '#999', fontSize: 16 }}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </div>
        </div>

        {/* 菜单 */}
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ border: 'none', flex: 1 }}
        />

        {/* 底部版本 */}
        <div
          style={{
            padding: '12px 16px',
            borderTop: '1px solid #f0f0f0',
            textAlign: 'center',
          }}
        >
          <Text type="secondary" style={{ fontSize: 11 }}>
            {collapsed ? 'v0.1' : 'AutoML Platform v0.1.0'}
          </Text>
        </div>
      </Sider>

      <Layout>
        <Content
          style={{
            background: '#f5f5f5',
            overflow: 'auto',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
