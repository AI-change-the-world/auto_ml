import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Modal, Spin } from 'antd';
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
import { getHomeStats } from '../../api/home';
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

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation('home');
  const [stats, setStats] = useState<HomeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPipeline, setSelectedPipeline] = useState<HomeStats['assist_pipelines'][number] | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await getHomeStats();
        if (res) {
          setStats(res);
        }
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const overviewMetrics = useMemo(
    () => [
      {
        key: 'datasets',
        label: t('datasets'),
        value: formatNumber(stats?.datasets),
        icon: <DatabaseOutlined className="h-4 w-4" />,
      },
      {
        key: 'samples',
        label: t('images'),
        value: formatNumber(stats?.images),
        icon: <PictureOutlined className="h-4 w-4" />,
      },
      {
        key: 'annotations',
        label: t('annotations'),
        value: formatNumber(stats?.annotations),
        icon: <TagsOutlined className="h-4 w-4" />,
      },
      {
        key: 'models',
        label: t('models'),
        value: formatNumber(stats?.models?.total),
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
        value: formatNumber(stats?.tasks?.total),
        tone: 'border-slate-200 bg-slate-100 text-slate-600',
      },
      {
        key: 'running',
        label: t('runningTasks'),
        value: formatNumber(stats?.tasks?.running),
        tone: 'border-emerald-100 bg-emerald-50 text-emerald-600',
      },
      {
        key: 'completed',
        label: t('completedTasks'),
        value: formatNumber(stats?.tasks?.completed),
        tone: 'border-blue-100 bg-blue-50 text-blue-600',
      },
      {
        key: 'deployments',
        label: t('deployments'),
        value: formatNumber(stats?.models?.deployed),
        tone: 'border-purple-100 bg-purple-50 text-purple-600',
      },
    ],
    [stats, t],
  );

  const recentDatasets = stats?.recent_datasets ?? [];
  const recentAnnotations = stats?.recent_annotations ?? [];
  const assistPipelines = stats?.assist_pipelines ?? [];
  const displayedDatasets = recentDatasets.slice(0, 3);
  const displayedAnnotations = recentAnnotations.slice(0, 3);
  const displayedPipelines = assistPipelines.slice(0, 3);
  const fallbackTimeText = t('unknownTime');

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="mx-auto max-w-[1400px] space-y-6">
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="rounded-xl bg-indigo-50 p-2 text-indigo-600">
              <HomeOutlined className="h-5 w-5" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-800">{t('title')}</h1>
          </div>
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={() => navigate('/datasets')}
              className="flex items-center space-x-2 rounded-xl bg-gradient-to-r from-indigo-600 to-blue-600 px-5 py-2.5 font-medium text-white shadow-md shadow-indigo-200 transition-all hover:from-indigo-700 hover:to-blue-700"
            >
              <span>{t('openDatasets')}</span>
              <ArrowRightOutlined className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => navigate('/annotations')}
              className="flex items-center space-x-2 rounded-xl bg-indigo-50 px-5 py-2.5 font-medium text-indigo-700 transition-all hover:bg-indigo-100"
            >
              <span>{t('openAnnotations')}</span>
              <ArrowRightOutlined className="h-4 w-4" />
            </button>
          </div>
        </div>

        <section className="rounded-2xl border border-slate-100 bg-white p-8 shadow-sm">
          <div className="flex flex-col justify-between gap-8 lg:flex-row lg:items-center">
            <div className="flex-1">
              <span className="mb-4 inline-flex items-center rounded-md border border-blue-100 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-600">
                <span className="mr-2 h-1.5 w-1.5 rounded-full bg-blue-500" />
                {t('heroTag')}
              </span>
              <h2 className="mb-2 text-xl font-bold text-slate-900">{t('heroTitle')}</h2>
              <p className="text-sm text-slate-500">{t('heroSubtitle')}</p>

              <div className="mt-6 flex flex-wrap items-center gap-3">
                <div className="flex items-center text-sm text-slate-600">
                  <CloudServerOutlined className="mr-2 h-4 w-4 text-slate-400" />
                  {t('taskOverview')}
                </div>
                {taskMetrics.map((item) => (
                  <span
                    key={item.key}
                    className={`rounded-full border px-3 py-1 text-xs font-medium ${item.tone}`}
                  >
                    <span className="mr-1 font-bold">{item.value}</span>
                    {item.label}
                  </span>
                ))}
              </div>
            </div>

            <div className="grid w-full grid-cols-2 gap-4 sm:grid-cols-4 lg:w-auto">
              {overviewMetrics.map((item, index) => (
                <div
                  key={item.key}
                  className="rounded-2xl border border-slate-100/50 bg-slate-50 p-5 transition-shadow hover:shadow-md"
                >
                  <div className="mb-2 flex items-start justify-between">
                    <span className="text-sm font-medium text-slate-500">{item.label}</span>
                    <div className={`rounded-lg p-1.5 ${overviewToneMap[index]}`}>
                      {item.icon}
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-slate-800">{item.value}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <section className="flex h-[320px] flex-col rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-base font-bold text-slate-900">{t('recentDatasets')}</h3>
            <div className="flex-1 overflow-y-auto">
              {displayedDatasets.length === 0 ? (
                <button
                  type="button"
                  onClick={() => navigate('/datasets')}
                  className="flex h-full w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/50"
                >
                  <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full border border-slate-100 bg-white text-slate-400 shadow-sm">
                    <DatabaseOutlined className="h-6 w-6" />
                  </div>
                  <p className="font-medium text-slate-700">{t('emptyDatasets')}</p>
                  <p className="mt-1 text-sm text-slate-400">{t('createFirstDataset')}</p>
                </button>
              ) : (
                displayedDatasets.map((dataset) => {
                  const typeMeta = datasetTypeMeta[dataset.data_type] ?? datasetTypeMeta[0];

                  return (
                    <button
                      key={dataset.id}
                      type="button"
                      onClick={() => navigate(`/datasets/${dataset.id}`)}
                      className="group flex w-full items-center rounded-xl border border-transparent p-3 transition-all hover:border-slate-100 hover:bg-slate-50"
                    >
                      <div className={`flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg ${typeMeta.tone}`}>
                        {typeMeta.icon}
                      </div>
                      <div className="ml-4 flex-1 text-left">
                        <div className="flex items-center space-x-2">
                          <h4 className="truncate font-medium text-slate-800">{dataset.name}</h4>
                          <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">
                            {DataTypeLabels[dataset.data_type] ?? t('unknownType')}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-slate-400">
                          {t('sampleCount', { count: formatNumber(dataset.count) })} · {t('createdAt', { date: formatDate(dataset.created_at, fallbackTimeText) })}
                        </p>
                      </div>
                      <ArrowRightOutlined className="h-4 w-4 text-slate-300 transition-colors group-hover:text-indigo-500" />
                    </button>
                  );
                })
              )}
            </div>
          </section>

          <section className="flex h-[320px] flex-col rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-base font-bold text-slate-900">{t('recentAnnotations')}</h3>
            {displayedAnnotations.length === 0 ? (
              <button
                type="button"
                onClick={() => navigate('/annotations')}
                className="flex flex-1 flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/50"
              >
                <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full border border-slate-100 bg-white text-slate-400 shadow-sm">
                  <FolderOpenOutlined className="h-6 w-6" />
                </div>
                <p className="font-medium text-slate-700">{t('emptyAnnotations')}</p>
                <p className="mt-1 text-sm text-slate-400">{t('createFirstAnnotation')}</p>
              </button>
            ) : (
              <div className="flex-1 overflow-y-auto space-y-3">
                {displayedAnnotations.map((annotation) => {
                  const tone = annotationToneMap[annotation.annotation_type] ?? 'bg-slate-100 text-slate-500';
                  const initial = annotation.name?.trim().charAt(0)?.toUpperCase() || 'A';

                  return (
                    <button
                      key={annotation.id}
                      type="button"
                      onClick={() => navigate(`/annotations/${annotation.id}/label`)}
                      className="group flex w-full items-center rounded-xl border border-transparent p-3 transition-all hover:border-slate-100 hover:bg-slate-50"
                    >
                      <div className={`flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg text-sm font-semibold ${tone}`}>
                        {initial}
                      </div>
                      <div className="ml-4 flex-1 text-left">
                        <div className="flex items-center space-x-2">
                          <h4 className="truncate font-medium text-slate-800">{annotation.name}</h4>
                          <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">
                            {AnnotationTypeLabels[annotation.annotation_type] ?? t('unknownType')}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-slate-400">
                          {t('createdAt', { date: formatDate(annotation.created_at, fallbackTimeText) })}
                        </p>
                      </div>
                      <ArrowRightOutlined className="h-4 w-4 text-slate-300 transition-colors group-hover:text-indigo-500" />
                    </button>
                  );
                })}
              </div>
            )}
          </section>

          <section className="flex h-[320px] flex-col rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900">{t('pipelineOverview')}</h3>
              <span className="rounded-full bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-600">
                {t('pipelineCount', { count: assistPipelines.length })}
              </span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-3">
              {displayedPipelines.length === 0 ? (
                <div className="flex h-full items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/50 px-5 text-center text-sm text-slate-500">
                  {t('emptyPipelines')}
                </div>
              ) : (
                displayedPipelines.map((pipeline) => (
                  <button
                    key={pipeline.id}
                    type="button"
                    onClick={() => setSelectedPipeline(pipeline)}
                    className="group w-full cursor-pointer rounded-xl border border-slate-100 p-4 text-left transition-all hover:border-indigo-200 hover:bg-indigo-50/30 hover:shadow-sm"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <h4 className="truncate text-sm font-semibold text-slate-800">{pipeline.name}</h4>
                      <ArrowRightOutlined className="h-4 w-4 text-slate-300 transition-colors group-hover:text-indigo-500" />
                    </div>
                    <div className="flex space-x-2">
                      {(pipeline.supported_annotation_types.length ? pipeline.supported_annotation_types : [0])
                        .slice(0, 1)
                        .map((type) => (
                          <span
                            key={`${pipeline.id}-type-${type}`}
                            className="rounded border border-slate-200 bg-white px-2 py-0.5 text-[10px] text-slate-500"
                          >
                            {type === 0 ? t('pipelineTypeDetection') : (AnnotationTypeLabels[type] ?? t('unknownType'))}
                          </span>
                        ))}
                      {(pipeline.supported_shapes.length ? pipeline.supported_shapes : ['bbox'])
                        .slice(0, 1)
                        .map((shape) => (
                          <span
                            key={`${pipeline.id}-shape-${shape}`}
                            className="rounded border border-slate-200 bg-white px-2 py-0.5 text-[10px] text-slate-500"
                          >
                            {shape.toUpperCase()}
                          </span>
                        ))}
                    </div>
                  </button>
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
