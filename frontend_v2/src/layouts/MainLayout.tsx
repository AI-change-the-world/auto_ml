import React, { useCallback, useEffect, useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  CloudServerOutlined,
  DownOutlined,
  EditOutlined,
  ExperimentOutlined,
  GlobalOutlined,
  HomeOutlined,
  MenuOutlined,
  QuestionCircleOutlined,
  SearchOutlined,
  SettingOutlined,
  TagsOutlined,
} from '@ant-design/icons';
import { driver } from 'driver.js';
import 'driver.js/dist/driver.css';
import { listAnnotations } from '../api/annotation';
import { getDeploymentOverview } from '../api/deploy';
import { listTasks } from '../api/task';
import {
  ANNOTATIONS_CHANGED_EVENT,
  TASKS_CHANGED_EVENT,
} from '../utils/projectEvents';
import type { AnnotationProject, DeploymentOverviewItem, TaskResponse } from '../types';

interface NavItem {
  key: string;
  icon: React.ReactNode;
  label: string;
  children?: { key: string; label: string; icon?: React.ReactNode; badge?: string }[];
}

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation('common');

  const [annotationProjects, setAnnotationProjects] = useState<AnnotationProject[]>([]);
  const [taskProjects, setTaskProjects] = useState<TaskResponse[]>([]);
  const [deploymentProjects, setDeploymentProjects] = useState<DeploymentOverviewItem[]>([]);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    '/annotations': true,
    '/tasks': true,
    '/deploy': true,
  });

  const refreshAnnotations = useCallback(() => {
    listAnnotations(1, 50).then((res) => {
      setAnnotationProjects(res.items || []);
    }).catch(() => { });
  }, []);

  const refreshTasks = useCallback(() => {
    listTasks(1, 50).then((res) => {
      setTaskProjects(res.items || []);
    }).catch(() => { });
  }, []);

  const refreshDeployments = useCallback(() => {
    getDeploymentOverview(true).then((res) => {
      setDeploymentProjects((res?.items || []).filter((item) => (
        item.is_deployed && item.runtime_status?.status === 'running'
      )));
    }).catch(() => { });
  }, []);

  useEffect(() => {
    refreshAnnotations();
    refreshTasks();
    refreshDeployments();
  }, [location.pathname, refreshAnnotations, refreshDeployments, refreshTasks]);

  useEffect(() => {
    window.addEventListener(ANNOTATIONS_CHANGED_EVENT, refreshAnnotations);
    window.addEventListener(TASKS_CHANGED_EVENT, refreshTasks);
    window.addEventListener('automl:deployments-changed', refreshDeployments);
    return () => {
      window.removeEventListener(ANNOTATIONS_CHANGED_EVENT, refreshAnnotations);
      window.removeEventListener(TASKS_CHANGED_EVENT, refreshTasks);
      window.removeEventListener('automl:deployments-changed', refreshDeployments);
    };
  }, [refreshAnnotations, refreshDeployments, refreshTasks]);

  const startTour = useCallback(() => {
    const driverObj = driver({
      showProgress: true,
      animate: true,
      overlayColor: 'rgba(0,0,0,0.5)',
      stagePadding: 8,
      stageRadius: 10,
      popoverClass: 'automl-tour-popover',
      nextBtnText: '下一步 →',
      prevBtnText: '← 上一步',
      doneBtnText: '开始使用 ✔',
      progressText: '{{current}} / {{total}}',
      steps: [
        {
          element: '[data-tour="nav-home"]',
          popover: {
            title: '首页总览',
            description: '这里显示平台概况：数据集、标注、模型等统计信息。',
            side: 'right', align: 'start',
          },
        },
        {
          element: '[data-tour="nav-browse"]',
          popover: {
            title: '数据集管理',
            description: '上传图片、视频或文本数据集，支持批量导入。',
            side: 'right', align: 'start',
          },
        },
        {
          element: '[data-tour="nav-annotation"]',
          popover: {
            title: '标注项目',
            description: '创建标注项目并进入工作台。',
            side: 'right', align: 'start',
          },
        },
        {
          element: '[data-tour="nav-training"]',
          popover: {
            title: '训练任务',
            description: '选择数据集和模型，查看训练进度。',
            side: 'right', align: 'start',
          },
        },
        {
          element: '[data-tour="nav-deploy"]',
          popover: {
            title: '模型部署',
            description: '查看在线部署与推理服务实例。',
            side: 'right', align: 'start',
          },
        },
        {
          element: '[data-tour="lang-toggle"]',
          popover: {
            title: '语言切换',
            description: '支持中文和 English 双语切换。',
            side: 'bottom', align: 'end',
          },
        },
      ],
    });
    driverObj.drive();
  }, []);

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
        icon: <EditOutlined className="text-violet-500" />,
      })),
    },
    {
      key: '/tasks',
      icon: <ExperimentOutlined />,
      label: t('nav.training'),
      children: taskProjects.map((task) => ({
        key: `/tasks/${task.id}`,
        label: `任务 #${task.id}`,
        icon: <ExperimentOutlined className="text-rose-500" />,
      })),
    },
    {
      key: '/deploy',
      icon: <CloudServerOutlined />,
      label: t('nav.deploy'),
      children: deploymentProjects.map((item) => ({
        key: `/deploy/${item.model_id}`,
        label: item.model_name || `模型 #${item.model_id}`,
        icon: <CloudServerOutlined className={item.runtime_status.healthy ? 'text-emerald-500' : 'text-amber-500'} />,
        badge: item.deployment_port ? `:${item.deployment_port}` : undefined,
      })),
    },
  ];

  useEffect(() => {
    for (const item of myProjectsNav) {
      if (location.pathname.startsWith(item.key)) {
        setExpanded((prev) => ({ ...prev, [item.key]: true }));
      }
    }
  }, [location.pathname]);

  const isActive = (key: string) => {
    if (key === '/') return location.pathname === '/';
    return location.pathname === key || location.pathname.startsWith(`${key}/`);
  };

  const pageTitle = (() => {
    if (location.pathname === '/') return t('nav.home');
    if (location.pathname.startsWith('/datasets')) return t('nav.datasets');
    if (location.pathname.startsWith('/annotations')) return t('nav.annotation');
    if (location.pathname.startsWith('/tasks')) return t('nav.training');
    if (location.pathname.startsWith('/deploy')) return t('nav.deploy');
    if (location.pathname.startsWith('/settings')) return t('nav.settings');
    return t('nav.home');
  })();

  return (
    <div className="flex h-screen overflow-hidden bg-[#f8fafc] text-slate-800 antialiased">
      <aside className="relative z-10 flex h-full w-64 flex-shrink-0 flex-col border-r border-slate-200 bg-white">
        <div
          className="flex h-16 cursor-pointer items-center border-b border-slate-100 px-6"
          onClick={() => navigate('/')}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-lg font-bold text-white shadow-sm">
            A
          </div>
          <span className="ml-3 text-lg font-bold tracking-tight text-slate-900">AutoML</span>
        </div>

        <div className="px-4 py-5">
          <div className="relative group">
            <SearchOutlined className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400 transition-colors group-focus-within:text-indigo-500" />
            <input
              type="text"
              readOnly
              placeholder={t('nav.search')}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pl-9 pr-12 text-sm placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
            <div className="absolute right-2 top-1/2 -translate-y-1/2 rounded bg-slate-200 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
              Ctrl K
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto px-3">
          {[
            { key: '/', icon: <HomeOutlined className="text-[18px]" />, label: t('nav.home'), tour: 'nav-home' },
            { key: '/datasets', icon: <SearchOutlined className="text-[18px]" />, label: t('nav.browse'), tour: 'nav-browse' },
          ].map((item) => {
            const active = isActive(item.key);
            return (
              <button
                key={item.key}
                type="button"
                data-tour={item.tour}
                onClick={() => navigate(item.key)}
                className={`group mb-1 flex w-full items-center rounded-xl px-3 py-2.5 text-left text-sm font-medium transition-colors ${
                  active
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <span className={`mr-3 ${active ? 'text-indigo-600' : 'text-slate-400 group-hover:text-slate-600'}`}>
                  {item.icon}
                </span>
                {item.label}
              </button>
            );
          })}

          <div className="px-3 pb-2 pt-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{t('nav.myProjects')}</p>
          </div>

          {myProjectsNav.map((group) => {
            const active = isActive(group.key);
            const tourMap: Record<string, string> = {
              '/annotations': 'nav-annotation',
              '/tasks': 'nav-training',
              '/deploy': 'nav-deploy',
            };
            return (
              <div key={group.key} className="mt-2 space-y-1" data-tour={tourMap[group.key]}>
                <button
                  type="button"
                  onClick={() => navigate(group.key)}
                  className={`group flex w-full items-center rounded-xl px-3 py-2 text-left text-sm transition-colors ${
                    active ? 'text-indigo-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <span className="mr-3 text-slate-400">{group.icon}</span>
                  <span className="flex-1 font-medium">{group.label}</span>
                  {group.children && group.children.length > 0 ? (
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        setExpanded((prev) => ({ ...prev, [group.key]: !prev[group.key] }));
                      }}
                      className="flex h-5 w-5 items-center justify-center text-[10px] text-slate-400"
                    >
                      <DownOutlined className={expanded[group.key] ? '' : '-rotate-90'} />
                    </button>
                  ) : null}
                </button>

                {group.children && group.children.length > 0 && expanded[group.key] ? (
                  <div className="space-y-1">
                    {group.children.map((child) => (
                      <button
                        key={child.key}
                        type="button"
                        onClick={() => navigate(child.key)}
                        className="flex w-full items-center rounded-xl px-10 py-2 text-left text-xs text-slate-500 transition-colors hover:bg-slate-50"
                      >
                        <span className="mr-2 flex items-center">{child.icon}</span>
                        <span className="flex-1 truncate">{child.label}</span>
                        {child.badge ? <span className="text-[11px] text-slate-400">{child.badge}</span> : null}
                      </button>
                    ))}
                  </div>
                ) : null}

                {group.children && group.children.length === 0 ? (
                  <p className="px-10 py-1 text-xs text-slate-400">
                    {group.key === '/deploy' ? t('nav.noActiveDeploy') : t('nav.noItems', { defaultValue: '暂无内容' })}
                  </p>
                ) : null}
              </div>
            );
          })}
        </nav>

        <div className="space-y-1 border-t border-slate-100 p-4">
          {[
            { key: '/settings', icon: <SettingOutlined className="text-[16px]" />, label: t('nav.settings') },
            { key: '/example-dataset', icon: <QuestionCircleOutlined className="text-[16px]" />, label: t('nav.help'), tour: 'example-link' },
          ].map((item) => (
            <button
              key={item.key}
              type="button"
              data-tour={item.tour}
              onClick={() => navigate(item.key)}
              className="flex w-full items-center rounded-xl px-3 py-2 text-left text-sm text-slate-600 transition-colors hover:bg-slate-50"
            >
              <span className="mr-3 text-slate-400">{item.icon}</span>
              {item.label}
            </button>
          ))}

          <div className="mt-4 flex cursor-pointer items-center justify-between px-2 pt-4 group">
            <div className="flex items-center">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-orange-500 text-sm font-semibold text-white shadow-sm ring-2 ring-white">
                A
              </div>
              <span className="ml-3 text-sm font-medium text-slate-700 transition-colors group-hover:text-indigo-600">AutoML</span>
            </div>
            <MenuOutlined className="text-sm text-slate-400" />
          </div>
        </div>
      </aside>

      <main className="relative flex h-full flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/80 px-8 backdrop-blur-md">
          <div className="flex items-center text-sm">
            <span className="mr-2 text-slate-400">›</span>
            <span className="font-medium text-slate-600">{pageTitle}</span>
          </div>
          <div className="flex items-center space-x-4">
            <button
              type="button"
              onClick={startTour}
              className="text-slate-400 transition-colors hover:text-slate-600"
            >
              <QuestionCircleOutlined className="text-lg" />
            </button>
            <button
              type="button"
              data-tour="lang-toggle"
              onClick={toggleLanguage}
              className="flex items-center space-x-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50"
            >
              <GlobalOutlined className="text-sm text-indigo-500" />
              <span>{i18n.language === 'en' ? '中文' : 'English'}</span>
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default MainLayout;
