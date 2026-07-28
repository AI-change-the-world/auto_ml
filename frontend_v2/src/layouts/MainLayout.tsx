import React, { useCallback, useEffect, useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  AppstoreOutlined,
  ApartmentOutlined,
  CloudServerOutlined,
  DownOutlined,
  EditOutlined,
  ExperimentOutlined,
  GlobalOutlined,
  HomeOutlined,
  LeftOutlined,
  QuestionCircleOutlined,
  RightOutlined,
  RobotOutlined,
  SearchOutlined,
  SettingOutlined,
  TagsOutlined,
} from '@ant-design/icons';
import { driver } from 'driver.js';
import 'driver.js/dist/driver.css';
import { getAnnotationSummary, listAnnotations, listPlatformAssistPipelines } from '../api/annotation';
import { getDatasetSummary, listDatasets } from '../api/dataset';
import { getDeploymentOverview, getDeploymentSummary } from '../api/deploy';
import { getTaskSummary, listTasks } from '../api/task';
import { listBatchAnnotationRuns } from '../api/batchAnnotation';
import WorkbenchAssistantModal from '../components/WorkbenchAssistantModal';
import {
  DATASETS_CHANGED_EVENT,
  ANNOTATIONS_CHANGED_EVENT,
  TASKS_CHANGED_EVENT,
  BATCH_ANNOTATION_RUNS_CHANGED_EVENT,
} from '../utils/projectEvents';
import type { AiPipelineBatchRun, AnnotationProject, Dataset, DeploymentOverviewItem, HomeStats, TaskResponse } from '../types';

interface NavItem {
  key: string;
  icon: React.ReactNode;
  label: string;
  children?: { key: string; label: string; icon?: React.ReactNode; badge?: string }[];
}

const emptyHomeStats: HomeStats = {
  datasets: 0,
  images: 0,
  annotations: 0,
  tasks: {
    total: 0,
    running: 0,
    completed: 0,
  },
  models: {
    total: 0,
    deployed: 0,
  },
  recent_annotations: [],
  recent_datasets: [],
  assist_pipelines: [],
};

function isEditableTarget(target: EventTarget | null) {
  const element = target as HTMLElement | null;
  if (!element) {
    return false;
  }
  return element.tagName === 'INPUT'
    || element.tagName === 'TEXTAREA'
    || element.isContentEditable
    || Boolean(element.closest('[contenteditable="true"], input, textarea'));
}

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation('common');
  const assistantShortcutLabel = typeof navigator !== 'undefined' && /mac/i.test(navigator.platform) ? '⌘ K' : 'Ctrl K';

  const [annotationProjects, setAnnotationProjects] = useState<AnnotationProject[]>([]);
  const [datasetProjects, setDatasetProjects] = useState<Dataset[]>([]);
  const [taskProjects, setTaskProjects] = useState<TaskResponse[]>([]);
  const [batchAnnotationRuns, setBatchAnnotationRuns] = useState<AiPipelineBatchRun[]>([]);
  const [deploymentProjects, setDeploymentProjects] = useState<DeploymentOverviewItem[]>([]);
  const [homeStats, setHomeStats] = useState<HomeStats | null>(null);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    '/datasets': true,
    '/annotations': true,
    '/tasks': true,
    '/deploy': true,
  });

  const refreshDatasets = useCallback(() => {
    listDatasets(1, 50).then((res) => {
      setDatasetProjects(res.items || []);
    }).catch(() => { });
  }, []);

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

  const refreshBatchAnnotationRuns = useCallback(() => {
    listBatchAnnotationRuns(undefined, 50).then((runs) => {
      setBatchAnnotationRuns(runs);
    }).catch(() => { });
  }, []);

  const refreshDeployments = useCallback(() => {
    getDeploymentOverview(true).then((res) => {
      setDeploymentProjects((res?.items || []).filter((item) => (
        item.is_deployed && item.runtime_status?.status === 'running'
      )));
    }).catch(() => { });
  }, []);

  const refreshHomeStats = useCallback(() => {
    setAssistantLoading(true);
    Promise.allSettled([
      getDatasetSummary(),
      getAnnotationSummary(),
      getTaskSummary(),
      getDeploymentSummary(),
      listPlatformAssistPipelines(),
    ]).then(([datasetSummary, annotationSummary, taskSummary, deploymentSummary, pipelineSummary]) => {
      setHomeStats({
        ...emptyHomeStats,
        datasets: datasetSummary.status === 'fulfilled' ? datasetSummary.value.total : 0,
        images: datasetSummary.status === 'fulfilled' ? datasetSummary.value.images : 0,
        recent_datasets: datasetSummary.status === 'fulfilled' ? datasetSummary.value.recent_datasets : [],
        annotations: annotationSummary.status === 'fulfilled' ? annotationSummary.value.total : 0,
        recent_annotations: annotationSummary.status === 'fulfilled' ? annotationSummary.value.recent_annotations : [],
        tasks: {
          total: taskSummary.status === 'fulfilled' ? taskSummary.value.total : 0,
          running: taskSummary.status === 'fulfilled' ? taskSummary.value.running : 0,
          completed: taskSummary.status === 'fulfilled' ? taskSummary.value.completed : 0,
        },
        models: {
          total: deploymentSummary.status === 'fulfilled' ? deploymentSummary.value.total : 0,
          deployed: deploymentSummary.status === 'fulfilled' ? deploymentSummary.value.deployed : 0,
        },
        assist_pipelines: pipelineSummary.status === 'fulfilled' ? pipelineSummary.value : [],
      });
    }).catch(() => { }).finally(() => {
      setAssistantLoading(false);
    });
  }, []);

  useEffect(() => {
    refreshDatasets();
    refreshAnnotations();
    refreshTasks();
    refreshBatchAnnotationRuns();
    refreshDeployments();
    refreshHomeStats();
  }, [location.pathname, refreshAnnotations, refreshBatchAnnotationRuns, refreshDatasets, refreshDeployments, refreshHomeStats, refreshTasks]);

  useEffect(() => {
    const handleAssistantShortcut = (event: KeyboardEvent) => {
      if (isEditableTarget(event.target)) {
        return;
      }

      const isOpenShortcut = (event.ctrlKey || event.metaKey)
        && !event.altKey
        && !event.shiftKey
        && event.key.toLowerCase() === 'k';

      if (!isOpenShortcut) {
        return;
      }

      event.preventDefault();
      setAssistantOpen((prev) => !prev);
    };

    window.addEventListener('keydown', handleAssistantShortcut, true);
    return () => window.removeEventListener('keydown', handleAssistantShortcut, true);
  }, []);

  useEffect(() => {
    window.addEventListener(DATASETS_CHANGED_EVENT, refreshDatasets);
    window.addEventListener(ANNOTATIONS_CHANGED_EVENT, refreshAnnotations);
    window.addEventListener(TASKS_CHANGED_EVENT, refreshTasks);
    window.addEventListener(BATCH_ANNOTATION_RUNS_CHANGED_EVENT, refreshBatchAnnotationRuns);
    window.addEventListener('automl:deployments-changed', refreshDeployments);
    return () => {
      window.removeEventListener(DATASETS_CHANGED_EVENT, refreshDatasets);
      window.removeEventListener(ANNOTATIONS_CHANGED_EVENT, refreshAnnotations);
      window.removeEventListener(TASKS_CHANGED_EVENT, refreshTasks);
      window.removeEventListener(BATCH_ANNOTATION_RUNS_CHANGED_EVENT, refreshBatchAnnotationRuns);
      window.removeEventListener('automl:deployments-changed', refreshDeployments);
    };
  }, [refreshAnnotations, refreshBatchAnnotationRuns, refreshDatasets, refreshDeployments, refreshTasks]);

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
          element: '[data-tour="nav-datasets"]',
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
      key: '/datasets',
      icon: <AppstoreOutlined />,
      label: t('nav.datasets'),
      children: datasetProjects.map((dataset) => ({
        key: `/datasets/${dataset.id}`,
        label: dataset.name,
        icon: <AppstoreOutlined className="text-sky-500" />,
      })),
    },
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
      key: '/batch-annotation/runs',
      icon: <RobotOutlined />,
      label: '批量标注任务',
      children: batchAnnotationRuns.map((run) => ({
        key: `/batch-annotation/runs/${run.run_id}`,
        label: `${run.script_key} · ${run.run_id.slice(-8)}`,
        icon: <RobotOutlined className={run.status === 'failed' ? 'text-rose-500' : run.status === 'succeeded' ? 'text-emerald-500' : 'text-amber-500'} />,
        badge: `${run.progress}%`,
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
    if (location.pathname.startsWith('/batch-annotation/tools')) return '批量标注工具';
    if (location.pathname.startsWith('/batch-annotation/runs')) return '批量标注任务';
    if (location.pathname.startsWith('/annotations')) return t('nav.annotation');
    if (location.pathname.startsWith('/tasks')) return t('nav.training');
    if (location.pathname.startsWith('/deploy')) return t('nav.deploy');
    if (location.pathname.startsWith('/ai-pipeline')) return t('nav.aiPipeline');
    if (location.pathname.startsWith('/settings')) return t('nav.settings');
    if (location.pathname.startsWith('/example-dataset')) return t('nav.help');
    return t('nav.home');
  })();

  return (
    <div className="flex h-screen overflow-hidden bg-[#f8fafc] text-slate-800 antialiased">
      <aside className={`relative z-10 flex h-full flex-shrink-0 flex-col border-r border-slate-200 bg-white transition-[width] duration-200 ${sidebarCollapsed ? 'w-[84px]' : 'w-64'}`}>
        <div
          className={`flex h-16 cursor-pointer items-center border-b border-slate-100 ${sidebarCollapsed ? 'justify-center px-3' : 'px-6'}`}
          onClick={() => navigate('/')}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-lg font-bold text-white shadow-sm">
            A
          </div>
          {!sidebarCollapsed ? (
            <span className="sidebar-brand-text ml-3 tracking-tight text-slate-900">AutoML</span>
          ) : null}
        </div>

        {!sidebarCollapsed ? (
          <div className="px-4 py-5">
            <button
              type="button"
              onClick={() => setAssistantOpen(true)}
              className="group flex w-full items-center rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-left transition-colors hover:border-slate-300 hover:bg-white"
            >
              <SearchOutlined className="text-sm text-slate-400 transition-colors group-hover:text-slate-600" />
              <div className="ml-3 min-w-0 flex-1">
                <div className="assistant-entry-title truncate text-slate-700">{t('assistant.entry')}</div>
                {/* <div className="assistant-entry-subtitle truncate text-slate-400">{t('assistant.placeholder')}</div> */}
              </div>
              <div className="ml-3 rounded bg-slate-200 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                {assistantShortcutLabel}
              </div>
            </button>
          </div>
        ) : (
          <div className="px-3 py-4">
            <button
              type="button"
              onClick={() => setAssistantOpen(true)}
              title={t('assistant.entry')}
              className="flex h-10 w-full items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-500 transition-colors hover:border-slate-300 hover:bg-white hover:text-slate-700"
            >
              <SearchOutlined className="text-[16px]" />
            </button>
          </div>
        )}

        <nav className={`flex-1 overflow-y-auto ${sidebarCollapsed ? 'px-2' : 'px-3'}`}>
          {[
            { key: '/', icon: <HomeOutlined className="text-[18px]" />, label: t('nav.home'), tour: 'nav-home' },
            { key: '/ai-pipeline', icon: <ApartmentOutlined className="text-[18px]" />, label: t('nav.aiPipeline') },
            { key: '/batch-annotation/tools', icon: <RobotOutlined className="text-[18px]" />, label: '批量标注工具' },
          ].map((item) => {
            const active = isActive(item.key);
            return (
              <button
                key={item.key}
                type="button"
                data-tour={item.tour}
                onClick={() => navigate(item.key)}
                title={sidebarCollapsed ? item.label : undefined}
                className={`group sidebar-nav-text mb-1 flex w-full items-center rounded-xl text-left transition-colors ${active
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  } ${sidebarCollapsed ? 'justify-center px-0 py-2.5' : 'px-3 py-2.5'}`}
              >
                <span className={`${sidebarCollapsed ? '' : 'mr-3'} ${active ? 'text-indigo-600' : 'text-slate-400 group-hover:text-slate-600'}`}>
                  {item.icon}
                </span>
                {!sidebarCollapsed ? item.label : null}
              </button>
            );
          })}

          {!sidebarCollapsed ? (
            <div className="px-3 pb-2 pt-6">
              <p className="sidebar-meta-text text-slate-400">{t('nav.myProjects')}</p>
            </div>
          ) : (
            <div className="px-2 pb-2 pt-5">
              <div className="border-t border-slate-100" />
            </div>
          )}

          {myProjectsNav.map((group) => {
            const active = isActive(group.key);
            const tourMap: Record<string, string> = {
              '/datasets': 'nav-datasets',
              '/annotations': 'nav-annotation',
              '/tasks': 'nav-training',
              '/batch-annotation/runs': 'nav-batch-annotation',
              '/deploy': 'nav-deploy',
            };
            return (
              <div key={group.key} className="mt-2 space-y-1" data-tour={tourMap[group.key]}>
                <button
                  type="button"
                  onClick={() => navigate(group.key)}
                  title={sidebarCollapsed ? group.label : undefined}
                  className={`group sidebar-nav-text flex w-full items-center rounded-xl text-left transition-colors ${active ? 'text-indigo-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    } ${sidebarCollapsed ? 'justify-center px-0 py-2.5' : 'px-3 py-2'}`}
                >
                  <span className={`${sidebarCollapsed ? '' : 'mr-3'} text-slate-400`}>{group.icon}</span>
                  {!sidebarCollapsed ? <span className="flex-1 font-medium">{group.label}</span> : null}
                  {!sidebarCollapsed && group.children && group.children.length > 0 ? (
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

                {!sidebarCollapsed && group.children && group.children.length > 0 && expanded[group.key] ? (
                  <div className="space-y-1">
                    {group.children.map((child) => (
                      <button
                        key={child.key}
                        type="button"
                        onClick={() => navigate(child.key)}
                        className="sidebar-subnav-text flex w-full items-center rounded-xl px-10 py-2 text-left text-slate-500 transition-colors hover:bg-slate-50"
                      >
                        <span className="mr-2 flex items-center">{child.icon}</span>
                        <span className="flex-1 truncate">{child.label}</span>
                        {child.badge ? <span className="text-[11px] text-slate-400">{child.badge}</span> : null}
                      </button>
                    ))}
                  </div>
                ) : null}

                {!sidebarCollapsed && group.children && group.children.length === 0 ? (
                  <p className="sidebar-subnav-text px-10 py-1 text-slate-400">
                    {group.key === '/deploy' ? t('nav.noActiveDeploy') : t('nav.noItems', { defaultValue: '暂无内容' })}
                  </p>
                ) : null}
              </div>
            );
          })}
        </nav>

        <div className={`space-y-1 border-t border-slate-100 ${sidebarCollapsed ? 'p-2' : 'p-4'}`}>
          {[
            { key: '/settings', icon: <SettingOutlined className="text-[16px]" />, label: t('nav.settings') },
            { key: '/example-dataset', icon: <QuestionCircleOutlined className="text-[16px]" />, label: t('nav.help'), tour: 'example-link' },
          ].map((item) => {
            const active = isActive(item.key);
            return (
              <button
                key={item.key}
                type="button"
                data-tour={item.tour}
                onClick={() => navigate(item.key)}
                title={sidebarCollapsed ? item.label : undefined}
                className={`sidebar-nav-text flex w-full items-center rounded-xl text-left transition-colors ${active
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  } ${sidebarCollapsed ? 'justify-center px-0 py-2.5' : 'px-3 py-2'}`}
              >
                <span className={`${sidebarCollapsed ? '' : 'mr-3'} ${active ? 'text-indigo-600' : 'text-slate-400'}`}>{item.icon}</span>
                {!sidebarCollapsed ? item.label : null}
              </button>
            );
          })}

          <div className={`mt-4 border-t border-slate-100 pt-3 ${sidebarCollapsed ? '' : 'px-1'}`}>
            <div className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'justify-between gap-3'}`}>
              {!sidebarCollapsed ? (
                <div className="min-w-0">
                  <div className="sidebar-meta-text text-slate-400">Workspace</div>
                </div>
              ) : null}
              <button
                type="button"
                onClick={() => setSidebarCollapsed((prev) => !prev)}
                title={sidebarCollapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')}
                className={`flex h-9 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-500 transition-colors hover:border-slate-300 hover:bg-white hover:text-slate-700 ${sidebarCollapsed ? 'w-full' : 'w-9'}`}
              >
                {sidebarCollapsed ? <RightOutlined className="text-[13px]" /> : <LeftOutlined className="text-[13px]" />}
              </button>
            </div>
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
      <WorkbenchAssistantModal
        open={assistantOpen}
        loading={assistantLoading}
        onClose={() => setAssistantOpen(false)}
        onNavigate={(path) => navigate(path)}
        stats={homeStats}
        annotations={annotationProjects}
        tasks={taskProjects}
        deployments={deploymentProjects}
      />
    </div>
  );
};

export default MainLayout;
