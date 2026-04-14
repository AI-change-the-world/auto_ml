import React, { useState, useEffect, useCallback } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  HomeOutlined,
  SearchOutlined,
  DatabaseOutlined,
  TagsOutlined,
  ExperimentOutlined,
  CloudServerOutlined,
  SettingOutlined,
  DeleteOutlined,
  QuestionCircleOutlined,
  DownOutlined,
  RightOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  AimOutlined,
  ThunderboltOutlined,
  ToolOutlined,
  EditOutlined,
} from '@ant-design/icons';
import { listAnnotations } from '../api/annotation';
import type { AnnotationProject } from '../types';

/* ─── types ─── */
interface NavItem {
  key: string;
  icon: React.ReactNode;
  label: string;
  children?: { key: string; label: string; icon?: React.ReactNode; badge?: string }[];
}

/* ─── component ─── */

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation('common');

  // 动态加载标注项目列表
  const [annotationProjects, setAnnotationProjects] = useState<AnnotationProject[]>([]);
  useEffect(() => {
    listAnnotations(1, 50).then((res) => {
      setAnnotationProjects(res.items || []);
    }).catch(() => { });
  }, [location.pathname]); // 路由变化时刷新（如新建项目后返回）

  const toggleLanguage = useCallback(() => {
    const next = i18n.language === 'en' ? 'zh' : 'en';
    i18n.changeLanguage(next);
    localStorage.setItem('automl-lang', next);
  }, [i18n]);

  const myProjectsNav: NavItem[] = [
    {
      key: '/annotations',
      icon: <TagsOutlined />,
      label: t('nav.annotation'),
      children: annotationProjects.map((p) => ({
        key: `/annotations/${p.id}/label`,
        label: p.name,
        icon: <EditOutlined style={{ color: '#8b5cf6' }} />,
      })),
    },
    {
      key: '/tasks',
      icon: <ExperimentOutlined />,
      label: t('nav.training'),
      children: [
        { key: '/tasks/example', label: t('nav.exampleProject'), icon: <ExperimentOutlined style={{ color: '#ef4444' }} />, badge: '1' },
      ],
    },
    {
      key: '/deploy',
      icon: <CloudServerOutlined />,
      label: t('nav.deploy'),
      children: [],
    },
    {
      key: '/predict',
      icon: <AimOutlined />,
      label: t('nav.predict'),
      children: [],
    },
    {
      key: '/augment',
      icon: <ThunderboltOutlined />,
      label: t('nav.augment'),
      children: [],
    },
    {
      key: '/tools',
      icon: <ToolOutlined />,
      label: t('nav.tools'),
      children: [],
    },
  ];

  const bottomItems = [
    { key: '/trash', icon: <DeleteOutlined />, label: t('nav.trash') },
    { key: '/settings', icon: <SettingOutlined />, label: t('nav.settings') },
    { key: '/help', icon: <QuestionCircleOutlined />, label: t('nav.help') },
  ];
  const [collapsed, setCollapsed] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    '/annotations': true,
    '/tasks': true,
    '/deploy': true,
    '/predict': true,
    '/augment': true,
    '/tools': true,
  });

  // Auto-expand based on route
  useEffect(() => {
    for (const item of myProjectsNav) {
      if (location.pathname.startsWith(item.key)) {
        setExpanded((prev) => ({ ...prev, [item.key]: true }));
      }
    }
  }, [location.pathname]);

  const isActive = (key: string) => {
    if (key === '/') return location.pathname === '/';
    return location.pathname === key || location.pathname.startsWith(key + '/');
  };

  const toggleExpand = (key: string) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const sidebarWidth = collapsed ? 56 : 220;

  const navItemStyle = (active: boolean): React.CSSProperties => ({
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: collapsed ? '8px 0' : '7px 12px',
    borderRadius: 8,
    cursor: 'pointer',
    fontSize: 14,
    color: active ? '#4f6ef7' : '#333',
    background: active ? '#eef2ff' : 'transparent',
    fontWeight: active ? 600 : 400,
    transition: 'all 0.15s',
    justifyContent: collapsed ? 'center' : undefined,
    whiteSpace: 'nowrap' as const,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    marginBottom: 1,
  });

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', background: '#fff' }}>
      {/* ─── Sidebar ─── */}
      <aside
        style={{
          width: sidebarWidth,
          minWidth: sidebarWidth,
          borderRight: '1px solid #eee',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
          background: '#fff',
          transition: 'width 0.2s, min-width 0.2s',
          overflow: 'hidden',
        }}
      >
        {/* Logo */}
        <div
          style={{
            height: 52,
            display: 'flex',
            alignItems: 'center',
            padding: collapsed ? '0 14px' : '0 16px',
            cursor: 'pointer',
            borderBottom: '1px solid #f5f5f5',
            gap: 10,
            justifyContent: collapsed ? 'center' : undefined,
          }}
          onClick={() => navigate('/')}
        >
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: 8,
              background: 'linear-gradient(135deg, #4f6ef7 0%, #7c3aed 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontWeight: 700,
              fontSize: 14,
              flexShrink: 0,
            }}
          >
            A
          </div>
          {!collapsed && (
            <span style={{ fontWeight: 700, fontSize: 16, color: '#111', letterSpacing: -0.5 }}>
              AutoML
            </span>
          )}
        </div>

        {/* Search bar */}
        {!collapsed && (
          <div style={{ padding: '10px 12px 6px' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '7px 10px',
                background: '#f7f7f8',
                borderRadius: 8,
                color: '#999',
                fontSize: 13,
                cursor: 'pointer',
              }}
            >
              <SearchOutlined style={{ fontSize: 12 }} />
              <span>{t('nav.search')}</span>
              <span
                style={{
                  marginLeft: 'auto',
                  fontSize: 10,
                  color: '#ccc',
                  border: '1px solid #e5e5e5',
                  borderRadius: 4,
                  padding: '0 4px',
                  lineHeight: '18px',
                }}
              >
                Ctrl K
              </span>
            </div>
          </div>
        )}

        {/* Top nav */}
        <nav style={{ padding: '4px 8px', overflow: 'hidden' }}>
          {[
            { key: '/', icon: <HomeOutlined />, label: t('nav.home') },
            { key: '/datasets', icon: <SearchOutlined />, label: t('nav.browse') },
          ].map((item) => {
            const active = isActive(item.key);
            return (
              <div
                key={item.key}
                onClick={() => navigate(item.key)}
                style={navItemStyle(active)}
                onMouseEnter={(e) => {
                  if (!active) e.currentTarget.style.background = '#f7f7f8';
                }}
                onMouseLeave={(e) => {
                  if (!active) e.currentTarget.style.background = 'transparent';
                }}
              >
                <span style={{ fontSize: 16, display: 'flex', flexShrink: 0 }}>{item.icon}</span>
                {!collapsed && <span>{item.label}</span>}
              </div>
            );
          })}
        </nav>

        {/* My Projects tree */}
        {!collapsed && (
          <div style={{ padding: '8px 8px 0' }}>
            <div
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: '#999',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
                padding: '4px 12px 6px',
              }}
            >
              {t('nav.myProjects')}
            </div>

            {myProjectsNav.map((group) => {
              const isExp = expanded[group.key] ?? false;
              const groupActive = isActive(group.key);
              return (
                <div key={group.key}>
                  {/* Group header */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '7px 12px',
                      borderRadius: 8,
                      cursor: 'pointer',
                      fontSize: 14,
                      color: groupActive ? '#4f6ef7' : '#333',
                      fontWeight: groupActive ? 600 : 400,
                      background: groupActive && !group.children?.length ? '#eef2ff' : 'transparent',
                    }}
                    onClick={() => {
                      if (group.children && group.children.length > 0) {
                        toggleExpand(group.key);
                      }
                      navigate(group.key);
                    }}
                    onMouseEnter={(e) => {
                      if (!groupActive) e.currentTarget.style.background = '#f7f7f8';
                    }}
                    onMouseLeave={(e) => {
                      if (!groupActive || (group.children && group.children.length > 0))
                        e.currentTarget.style.background = 'transparent';
                    }}
                  >
                    <span style={{ fontSize: 15, display: 'flex', flexShrink: 0 }}>
                      {group.icon}
                    </span>
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {group.label}
                    </span>
                    {group.children && group.children.length > 0 && (
                      <span
                        style={{
                          fontSize: 10,
                          color: '#bbb',
                          display: 'flex',
                          transition: 'transform 0.2s',
                          transform: isExp ? 'rotate(0deg)' : 'rotate(-90deg)',
                        }}
                      >
                        <DownOutlined />
                      </span>
                    )}
                  </div>

                  {/* Children */}
                  {group.children && group.children.length > 0 && (
                    <div
                      className="sidebar-tree-children"
                      style={{ maxHeight: isExp ? Math.min(group.children.length, 10) * 40 : 0 }}
                    >
                      {group.children.map((child) => (
                        <div
                          key={child.key}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 8,
                            padding: '6px 12px 6px 36px',
                            fontSize: 13,
                            color: '#555',
                            cursor: 'pointer',
                            borderRadius: 6,
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = '#f7f7f8';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'transparent';
                          }}
                          onClick={() => navigate(child.key)}
                        >
                          <span style={{ fontSize: 13, display: 'flex', flexShrink: 0 }}>
                            {child.icon}
                          </span>
                          <span
                            style={{
                              flex: 1,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {child.label}
                          </span>
                          {child.badge && (
                            <span style={{ fontSize: 11, color: '#bbb' }}>{child.badge}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Empty state for deploy */}
                  {group.children && group.children.length === 0 && isExp && (
                    <div
                      style={{
                        padding: '4px 12px 6px 36px',
                        fontSize: 12,
                        color: '#ccc',
                      }}
                    >
                      {t('nav.noActiveDeploy')}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* Bottom nav */}
        <div style={{ borderTop: '1px solid #f5f5f5', padding: '6px 8px' }}>
          {bottomItems.map((item) => {
            const active = isActive(item.key);
            return (
              <div
                key={item.key}
                onClick={() => {
                  if (item.key === '/settings') navigate(item.key);
                }}
                style={navItemStyle(active)}
                onMouseEnter={(e) => {
                  if (!active) e.currentTarget.style.background = '#f7f7f8';
                }}
                onMouseLeave={(e) => {
                  if (!active) e.currentTarget.style.background = 'transparent';
                }}
              >
                <span style={{ fontSize: 15, display: 'flex', flexShrink: 0 }}>{item.icon}</span>
                {!collapsed && <span>{item.label}</span>}
              </div>
            );
          })}
        </div>

        {/* User area */}
        <div
          style={{
            borderTop: '1px solid #f5f5f5',
            padding: collapsed ? '10px 8px' : '10px 12px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            justifyContent: collapsed ? 'center' : undefined,
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #f97316, #ef4444)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: 12,
              fontWeight: 700,
              flexShrink: 0,
            }}
          >
            A
          </div>
          {!collapsed && (
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 500,
                  color: '#111',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                AutoML
              </div>
              <div style={{ fontSize: 11, color: '#aaa' }}>admin@automl.local</div>
            </div>
          )}
          {!collapsed && (
            <span
              style={{ fontSize: 12, color: '#ccc', cursor: 'pointer', padding: 4, display: 'flex' }}
              onClick={(e) => {
                e.stopPropagation();
                setCollapsed(true);
              }}
            >
              <MenuFoldOutlined />
            </span>
          )}
        </div>
      </aside>

      {/* ─── Main Content ─── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Top bar */}
        <header
          style={{
            height: 48,
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            padding: '0 20px',
            gap: 12,
            flexShrink: 0,
            background: '#fff',
          }}
        >
          {collapsed && (
            <MenuUnfoldOutlined
              style={{ fontSize: 16, color: '#666', cursor: 'pointer' }}
              onClick={() => setCollapsed(false)}
            />
          )}
          <RightOutlined style={{ fontSize: 10, color: '#ddd' }} />
          <span style={{ fontSize: 14, color: '#555', fontWeight: 500 }}>
            {location.pathname === '/' && t('nav.home')}
            {location.pathname.startsWith('/datasets') && t('nav.datasets')}
            {location.pathname.startsWith('/annotations') && t('nav.annotation')}
            {location.pathname.startsWith('/tasks') && t('nav.training')}
            {location.pathname.startsWith('/deploy') && t('nav.deploy')}
            {location.pathname.startsWith('/predict') && t('nav.predict')}
            {location.pathname.startsWith('/augment') && t('nav.augment')}
            {location.pathname.startsWith('/tools') && t('nav.tools')}
            {location.pathname.startsWith('/settings') && t('nav.settings')}
          </span>
          <button
            onClick={toggleLanguage}
            style={{
              marginLeft: 'auto',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: '4px 12px',
              border: '1px solid #e5e7eb',
              borderRadius: 6,
              background: '#f9fafb',
              color: '#374151',
              fontSize: 12,
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = '#eef2ff'; e.currentTarget.style.borderColor = '#4f6ef7'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = '#f9fafb'; e.currentTarget.style.borderColor = '#e5e7eb'; }}
          >
            🌐 {i18n.language === 'en' ? '中文' : 'English'}
          </button>
        </header>

        <main style={{ flex: 1, overflow: 'auto', background: '#fafafa' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
