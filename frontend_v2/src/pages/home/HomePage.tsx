import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Modal, Skeleton } from 'antd';
import {
  ArrowRightOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  FolderOpenOutlined,
  HomeOutlined,
  PictureOutlined,
  SoundOutlined,
  TagsOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { getAnnotationSummary, listPlatformAssistPipelines } from '../../api/annotation';
import { getDatasetSummary } from '../../api/dataset';
import { getDeploymentSummary } from '../../api/deploy';
import { getTaskSummary } from '../../api/task';
import type { HomeStats } from '../../types/home';
import { AnnotationTypeLabels, DataTypeLabels } from '../../types';

const datasetTypeMeta: Record<number, { icon: React.ReactNode; tone: string }> = {
  0: {
    icon: <PictureOutlined className="h-6 w-6" />,
    tone: 'bg-blue-50 text-blue-500',
  },
  1: {
    icon: <FileTextOutlined className="h-6 w-6" />,
    tone: 'bg-violet-50 text-violet-500',
  },
  2: {
    icon: <VideoCameraOutlined className="h-6 w-6" />,
    tone: 'bg-amber-50 text-amber-500',
  },
  3: {
    icon: <SoundOutlined className="h-6 w-6" />,
    tone: 'bg-emerald-50 text-emerald-500',
  },
};

const overviewToneMap = [
  'bg-orange-100 text-orange-600',
  'bg-blue-100 text-blue-600',
  'bg-purple-100 text-purple-600',
  'bg-emerald-100 text-emerald-600',
];

const annotationToneMap: Record<number, string> = {
  0: 'bg-sky-50 text-sky-500',
  1: 'bg-emerald-50 text-emerald-500',
  2: 'bg-amber-50 text-amber-500',
  3: 'bg-fuchsia-50 text-fuchsia-500',
  4: 'bg-cyan-50 text-cyan-500',
  5: 'bg-indigo-50 text-indigo-500',
};

const pipelineCapabilityLabels: Record<string, string> = {
  describe_image: '图像理解',
  draft_annotation: '草稿标注',
  draft_annotation_preview: '草稿标注 + 预览',
  extract_white_annotations: '白框提取',
  render_white_annotation_overlay: '生成白框图',
  understand_white_annotations: '白框多模态理解',
  assist_annotation: '辅助标注',
};

const initialStats: HomeStats = {
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

type HomeSectionStatus = 'idle' | 'loading' | 'ready' | 'error';

interface HomeSectionState<T> {
  data: T;
  status: HomeSectionStatus;
}

const initialDatasetSection: HomeSectionState<{
  total: number;
  images: number;
  recent_datasets: HomeStats['recent_datasets'];
}> = {
  data: {
    total: 0,
    images: 0,
    recent_datasets: [],
  },
  status: 'loading',
};

const initialAnnotationSection: HomeSectionState<{
  total: number;
  recent_annotations: HomeStats['recent_annotations'];
}> = {
  data: {
    total: 0,
    recent_annotations: [],
  },
  status: 'loading',
};

const initialTaskSection: HomeSectionState<HomeStats['tasks']> = {
  data: {
    total: 0,
    running: 0,
    completed: 0,
  },
  status: 'loading',
};

const initialModelSection: HomeSectionState<HomeStats['models']> = {
  data: {
    total: 0,
    deployed: 0,
  },
  status: 'loading',
};

const initialPipelineSection: HomeSectionState<HomeStats['assist_pipelines']> = {
  data: [],
  status: 'loading',
};

const numberFormatter = new Intl.NumberFormat();

function formatNumber(value?: number) {
  return numberFormatter.format(value ?? 0);
}

function formatDate(value: string | null | undefined, fallback: string) {
  if (!value) {
    return fallback;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return fallback;
  }

  return new Intl.DateTimeFormat(undefined, {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function formatPipelineCapability(value: string) {
  if (!value) {
    return 'Step';
  }

  return pipelineCapabilityLabels[value] ?? value.replaceAll('_', ' ');
}

function isSectionLoading(status: HomeSectionStatus) {
  return status === 'loading' || status === 'idle';
}

function isSectionError(status: HomeSectionStatus) {
  return status === 'error';
}

function renderSectionBadge(status: HomeSectionStatus, label: string) {
  if (!isSectionError(status)) {
    return null;
  }
  return (
    <span className="tag-text rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-amber-700">
      {label}
    </span>
  );
}

function joinMetaParts(parts: Array<string | null | undefined | false>) {
  return parts.filter((part): part is string => Boolean(part)).join(' · ');
}

interface HomeListItemProps {
  icon: React.ReactNode;
  tone: string;
  title: string;
  meta: string;
  onClick: () => void;
}

function HomeListItem({ icon, tone, title, meta, onClick }: HomeListItemProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex h-16 w-full items-center gap-3 rounded-xl border border-slate-100 bg-slate-50/40 px-3 text-left transition-all hover:border-slate-200 hover:bg-slate-50"
    >
      <div className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg ${tone}`}>
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <h4 className="body-text truncate font-semibold text-slate-800">{title}</h4>
        <p className="caption-text truncate text-slate-500">{meta}</p>
      </div>
      <ArrowRightOutlined className="h-4 w-4 flex-shrink-0 text-slate-300 transition-colors group-hover:text-slate-500" />
    </button>
  );
}

function HomeListSkeleton() {
  return (
    <div className="space-y-2.5">
      {[0, 1, 2].map((item) => (
        <div
          key={item}
          className="flex h-16 items-center gap-3 rounded-xl border border-slate-100 bg-slate-50/40 px-3"
        >
          <Skeleton.Avatar active size={36} shape="square" className="!rounded-lg" />
          <div className="flex-1">
            <Skeleton active paragraph={{ rows: 1, width: ['72%'] }} title={{ width: '48%' }} />
          </div>
        </div>
      ))}
    </div>
  );
}

interface HomeEmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description?: string;
  onClick?: () => void;
}

function HomeEmptyState({ icon, title, description, onClick }: HomeEmptyStateProps) {
  const content = (
    <>
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full border border-slate-100 bg-white text-slate-400 shadow-sm">
        {icon}
      </div>
      <p className="font-medium text-slate-700">{title}</p>
      {description ? <p className="body-text-sm mt-1 text-slate-400">{description}</p> : null}
    </>
  );

  if (!onClick) {
    return (
      <div className="flex h-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/50 px-5 text-center">
        {content}
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className="flex h-full w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/50 px-5 text-center"
    >
      {content}
    </button>
  );
}

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation('home');
  const [datasetSection, setDatasetSection] = useState(initialDatasetSection);
  const [annotationSection, setAnnotationSection] = useState(initialAnnotationSection);
  const [taskSection, setTaskSection] = useState(initialTaskSection);
  const [modelSection, setModelSection] = useState(initialModelSection);
  const [pipelineSection, setPipelineSection] = useState(initialPipelineSection);
  const [selectedPipeline, setSelectedPipeline] = useState<HomeStats['assist_pipelines'][number] | null>(null);

  useEffect(() => {
    let active = true;

    setDatasetSection((prev) => ({ ...prev, status: 'loading' }));
    getDatasetSummary()
      .then((res) => {
        if (!active) {
          return;
        }
        setDatasetSection({
          data: {
            total: res?.total ?? 0,
            images: res?.images ?? 0,
            recent_datasets: res?.recent_datasets ?? [],
          },
          status: 'ready',
        });
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setDatasetSection((prev) => ({
          data: prev.data,
          status: 'error',
        }));
      });

    setAnnotationSection((prev) => ({ ...prev, status: 'loading' }));
    getAnnotationSummary()
      .then((res) => {
        if (!active) {
          return;
        }
        setAnnotationSection({
          data: {
            total: res?.total ?? 0,
            recent_annotations: res?.recent_annotations ?? [],
          },
          status: 'ready',
        });
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setAnnotationSection((prev) => ({
          data: prev.data,
          status: 'error',
        }));
      });

    setTaskSection((prev) => ({ ...prev, status: 'loading' }));
    getTaskSummary()
      .then((res) => {
        if (!active) {
          return;
        }
        setTaskSection({
          data: {
            total: res?.total ?? 0,
            running: res?.running ?? 0,
            completed: res?.completed ?? 0,
          },
          status: 'ready',
        });
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setTaskSection((prev) => ({
          data: prev.data,
          status: 'error',
        }));
      });

    setModelSection((prev) => ({ ...prev, status: 'loading' }));
    getDeploymentSummary()
      .then((res) => {
        if (!active) {
          return;
        }
        setModelSection({
          data: {
            total: res?.total ?? 0,
            deployed: res?.deployed ?? 0,
          },
          status: 'ready',
        });
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setModelSection((prev) => ({
          data: prev.data,
          status: 'error',
        }));
      });

    setPipelineSection((prev) => ({ ...prev, status: 'loading' }));
    listPlatformAssistPipelines()
      .then((res) => {
        if (!active) {
          return;
        }
        setPipelineSection({
          data: res ?? [],
          status: 'ready',
        });
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setPipelineSection((prev) => ({
          data: prev.data,
          status: 'error',
        }));
      });

    return () => {
      active = false;
    };
  }, []);

  const stats = useMemo<HomeStats>(() => ({
    ...initialStats,
    datasets: datasetSection.data.total,
    images: datasetSection.data.images,
    recent_datasets: datasetSection.data.recent_datasets,
    annotations: annotationSection.data.total,
    recent_annotations: annotationSection.data.recent_annotations,
    tasks: taskSection.data,
    models: modelSection.data,
    assist_pipelines: pipelineSection.data,
  }), [annotationSection.data, datasetSection.data, modelSection.data, pipelineSection.data, taskSection.data]);

  const overviewMetrics = useMemo(
    () => [
      {
        key: 'datasets',
        label: t('datasets'),
        value: formatNumber(stats.datasets),
        icon: <DatabaseOutlined className="h-4 w-4" />,
      },
      {
        key: 'samples',
        label: t('images'),
        value: formatNumber(stats.images),
        icon: <PictureOutlined className="h-4 w-4" />,
      },
      {
        key: 'annotations',
        label: t('annotations'),
        value: formatNumber(stats.annotations),
        icon: <TagsOutlined className="h-4 w-4" />,
      },
      {
        key: 'models',
        label: t('models'),
        value: formatNumber(stats.models.total),
        icon: <ExperimentOutlined className="h-4 w-4" />,
      },
    ],
    [stats, t],
  );

  const taskMetrics = useMemo(
    () => [
      {
        key: 'tasks',
        label: t('tasks'),
        value: formatNumber(stats.tasks.total),
        accent: 'bg-slate-500',
      },
      {
        key: 'running',
        label: t('runningTasks'),
        value: formatNumber(stats.tasks.running),
        accent: 'bg-emerald-500',
      },
      {
        key: 'completed',
        label: t('completedTasks'),
        value: formatNumber(stats.tasks.completed),
        accent: 'bg-blue-500',
      },
      {
        key: 'deployments',
        label: t('deployments'),
        value: formatNumber(stats.models.deployed),
        accent: 'bg-violet-500',
      },
    ],
    [stats, t],
  );

  const recentDatasets = stats.recent_datasets;
  const recentAnnotations = stats.recent_annotations;
  const assistPipelines = stats.assist_pipelines;
  const displayedDatasets = recentDatasets.slice(0, 3);
  const displayedAnnotations = recentAnnotations.slice(0, 3);
  const displayedPipelines = assistPipelines.slice(0, 3);
  const fallbackTimeText = t('unknownTime');
  const overviewLoading = isSectionLoading(datasetSection.status) || isSectionLoading(annotationSection.status) || isSectionLoading(modelSection.status);
  const taskOverviewLoading = isSectionLoading(taskSection.status) || isSectionLoading(modelSection.status);
  const datasetsLoading = isSectionLoading(datasetSection.status);
  const annotationsLoading = isSectionLoading(annotationSection.status);
  const pipelinesLoading = isSectionLoading(pipelineSection.status);
  const taskOverviewError = isSectionError(taskSection.status) || isSectionError(modelSection.status);
  const datasetsError = isSectionError(datasetSection.status);
  const annotationsError = isSectionError(annotationSection.status);
  const pipelinesError = isSectionError(pipelineSection.status);

  return (
    <div className="page-container">
      <div className="mx-auto max-w-[1400px] space-y-6">
        <div className="mb-8">
          <div className="page-title-block">
            <div className="page-title-icon">
              <HomeOutlined className="h-5 w-5" />
            </div>
            <div>
              <h1 className="page-title">{t('title')}</h1>
            </div>
          </div>
        </div>

        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-col gap-10 p-8 lg:flex-row lg:items-center">
            <div className="w-full flex-1 self-start">
              <div className="flex flex-col items-start gap-4">
                <div className="caption-text inline-flex items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1.5 font-semibold text-emerald-700">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  {t('heroTag')}
                </div>
                <div className="flex flex-col gap-3">
                  <h2 className="section-title tracking-tight">{t('heroTitle')}</h2>
                  <p className="body-text max-w-xl text-slate-500">{t('heroSubtitle')}</p>
                  {/* {overviewError ? renderSectionBadge('error', t('partialUnavailable')) : null} */}
                </div>
              </div>
            </div>

            <div className="grid w-full grid-cols-2 gap-4 lg:w-[500px]">
              {overviewMetrics.map((item, index) => (
                <div
                  key={item.key}
                  className="group flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-5 transition-all hover:bg-slate-50/80"
                >
                  <div>
                    <p className="body-text-sm mb-1 font-medium text-slate-500">{item.label}</p>
                    {overviewLoading ? (
                      <Skeleton.Button active size="small" className="!h-8 !w-20" />
                    ) : (
                      <p className="metric-value-lg text-slate-900">{item.value}</p>
                    )}
                  </div>
                  <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${overviewToneMap[index]}`}>
                    {item.icon}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t border-slate-100 bg-slate-50/50 px-8 py-6">
            <div className="mb-6 flex items-center justify-between gap-3">
              <div className="card-title flex items-center gap-2 text-slate-800">
                <CloudServerOutlined className="h-5 w-5 text-slate-500" />
                {t('taskOverview')}
              </div>
              {taskOverviewError ? renderSectionBadge('error', t('partialUnavailable')) : null}
            </div>
            <div className="grid grid-cols-2 gap-4 divide-slate-200/60 md:grid-cols-4 md:divide-x">
              {taskMetrics.map((item, index) => (
                <div
                  key={item.key}
                  className={`pt-4 md:px-6 md:pt-0 ${index === 0 ? 'md:pl-0 pt-0' : ''}`}
                >
                  <div className="body-text mb-2 flex items-center gap-2 text-slate-500">
                    <span className={`h-2.5 w-2.5 rounded-full ${item.accent}`} />
                    {item.label}
                  </div>
                  {taskOverviewLoading ? (
                    <div className="ml-[18px]">
                      <Skeleton.Button active size="small" className="!h-7 !w-16" />
                    </div>
                  ) : (
                    <p className="metric-value-sm ml-[18px] text-slate-900">{item.value}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <section className="flex h-[280px] flex-col rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
            <div className="mb-2.5 flex items-center justify-between gap-3">
              <h3 className="card-title">{t('recentDatasets')}</h3>
              {datasetsError ? renderSectionBadge('error', t('partialUnavailable')) : null}
            </div>
            <div className="flex-1 space-y-2.5 overflow-y-auto pr-1">
              {datasetsLoading ? (
                <HomeListSkeleton />
              ) : datasetsError && displayedDatasets.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-amber-200 bg-amber-50/40 px-5 text-center">
                  <p className="font-medium text-amber-800">{t('sectionUnavailable')}</p>
                  <p className="body-text-sm mt-1 text-amber-700">{t('retryLater')}</p>
                </div>
              ) : displayedDatasets.length === 0 ? (
                <HomeEmptyState
                  icon={<DatabaseOutlined className="h-6 w-6" />}
                  title={t('emptyDatasets')}
                  description={t('createFirstDataset')}
                  onClick={() => navigate('/datasets')}
                />
              ) : (
                displayedDatasets.map((dataset) => {
                  const typeMeta = datasetTypeMeta[dataset.data_type] ?? datasetTypeMeta[0];
                  const meta = joinMetaParts([
                    DataTypeLabels[dataset.data_type] ?? t('unknownType'),
                    t('sampleCount', { count: formatNumber(dataset.count) }),
                    t('createdAt', { date: formatDate(dataset.created_at, fallbackTimeText) }),
                  ]);

                  return (
                    <HomeListItem
                      key={dataset.id}
                      onClick={() => navigate(`/datasets/${dataset.id}`)}
                      icon={typeMeta.icon}
                      tone={typeMeta.tone}
                      title={dataset.name}
                      meta={meta}
                    />
                  );
                })
              )}
            </div>
          </section>

          <section className="flex h-[280px] flex-col rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
            <div className="mb-2.5 flex items-center justify-between gap-3">
              <h3 className="card-title">{t('recentAnnotations')}</h3>
              {annotationsError ? renderSectionBadge('error', t('partialUnavailable')) : null}
            </div>
            {annotationsLoading ? (
              <div className="flex-1 overflow-y-auto pr-1">
                <HomeListSkeleton />
              </div>
            ) : annotationsError && displayedAnnotations.length === 0 ? (
              <div className="flex flex-1 flex-col items-center justify-center rounded-xl border-2 border-dashed border-amber-200 bg-amber-50/40 px-5 text-center">
                <p className="font-medium text-amber-800">{t('sectionUnavailable')}</p>
                <p className="body-text-sm mt-1 text-amber-700">{t('retryLater')}</p>
              </div>
            ) : displayedAnnotations.length === 0 ? (
              <HomeEmptyState
                icon={<FolderOpenOutlined className="h-6 w-6" />}
                title={t('emptyAnnotations')}
                description={t('createFirstAnnotation')}
                onClick={() => navigate('/annotations')}
              />
            ) : (
              <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
                {displayedAnnotations.map((annotation) => {
                  const tone = annotationToneMap[annotation.annotation_type] ?? 'bg-slate-100 text-slate-500';
                  const initial = annotation.name?.trim().charAt(0)?.toUpperCase() || 'A';
                  const meta = joinMetaParts([
                    AnnotationTypeLabels[annotation.annotation_type] ?? t('unknownType'),
                    t('createdAt', { date: formatDate(annotation.created_at, fallbackTimeText) }),
                  ]);

                  return (
                    <HomeListItem
                      key={annotation.id}
                      onClick={() => navigate(`/annotations/${annotation.id}/label`)}
                      icon={<span className="text-sm font-semibold">{initial}</span>}
                      tone={tone}
                      title={annotation.name}
                      meta={meta}
                    />
                  );
                })}
              </div>
            )}
          </section>

          <section className="flex h-[280px] flex-col rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
            <div className="mb-2.5 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h3 className="card-title">{t('pipelineOverview')}</h3>
                {pipelinesError ? renderSectionBadge('error', t('partialUnavailable')) : null}
              </div>
              <span className="tag-text rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-slate-600">
                {pipelinesLoading ? '...' : t('pipelineCount', { count: assistPipelines.length })}
              </span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
              {pipelinesLoading ? (
                <HomeListSkeleton />
              ) : pipelinesError && displayedPipelines.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-amber-200 bg-amber-50/40 px-5 text-center">
                  <p className="font-medium text-amber-800">{t('sectionUnavailable')}</p>
                  <p className="body-text-sm mt-1 text-amber-700">{t('retryLater')}</p>
                </div>
              ) : displayedPipelines.length === 0 ? (
                <HomeEmptyState
                  icon={<CloudServerOutlined className="h-6 w-6" />}
                  title={t('emptyPipelines')}
                />
              ) : (
                displayedPipelines.map((pipeline) => (
                  <HomeListItem
                    key={pipeline.id}
                    onClick={() => setSelectedPipeline(pipeline)}
                    icon={<CloudServerOutlined className="h-5 w-5" />}
                    tone="bg-indigo-50 text-indigo-500"
                    title={pipeline.name}
                    meta={joinMetaParts([
                      (() => {
                        const type = pipeline.supported_annotation_types[0] ?? 0;
                        return type === 0 ? t('pipelineTypeDetection') : (AnnotationTypeLabels[type] ?? t('unknownType'));
                      })(),
                      (pipeline.supported_shapes[0] ?? 'bbox').toUpperCase(),
                      t('pipelineStepCount', { count: pipeline.steps.length }),
                    ])}
                  />
                ))
              )}
            </div>
          </section>
        </div>
      </div>

      <Modal
        open={Boolean(selectedPipeline)}
        onCancel={() => setSelectedPipeline(null)}
        footer={null}
        width={720}
        title={selectedPipeline ? `${selectedPipeline.name} · ${t('pipelineFlow')}` : t('pipelineFlow')}
      >
        {selectedPipeline && (
          <div className="flex flex-col gap-4 pt-2">
            {selectedPipeline.description ? (
              <div className="text-sm leading-6 text-slate-500">{selectedPipeline.description}</div>
            ) : null}

            {selectedPipeline.steps.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
                {t('pipelineNoSteps')}
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {selectedPipeline.steps.map((step, index) => (
                  <div key={`${selectedPipeline.id}-${step.name}-${index}`} className="flex flex-col gap-3">
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-xs font-medium text-slate-400">{t('pipelineStep', { index: index + 1 })}</div>
                          <div className="mt-1 text-sm font-semibold text-slate-950">{formatPipelineCapability(step.capability)}</div>
                          <div className="mt-1 text-xs text-slate-500">{step.name}</div>
                        </div>
                        {step.provider ? (
                          <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-slate-500 ring-1 ring-slate-200">
                            {t('pipelineProvider', { provider: step.provider })}
                          </span>
                        ) : null}
                      </div>
                    </div>
                    {index < selectedPipeline.steps.length - 1 ? (
                      <div className="flex justify-center">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                          <ArrowRightOutlined className="rotate-90 text-[12px]" />
                        </div>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default HomePage;
