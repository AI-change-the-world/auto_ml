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
        accent: 'bg-slate-500',
      },
      {
        key: 'running',
        label: t('runningTasks'),
        value: formatNumber(stats?.tasks?.running),
        accent: 'bg-emerald-500',
      },
      {
        key: 'completed',
        label: t('completedTasks'),
        value: formatNumber(stats?.tasks?.completed),
        accent: 'bg-blue-500',
      },
      {
        key: 'deployments',
        label: t('deployments'),
        value: formatNumber(stats?.models?.deployed),
        accent: 'bg-violet-500',
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
          <div className="page-title-block">
            <div className="page-title-icon">
              <HomeOutlined className="h-5 w-5" />
            </div>
            <div>
              <h1 className="page-title">{t('title')}</h1>
            </div>
          </div>
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={() => navigate('/datasets')}
              className="button-text flex items-center space-x-2 rounded-lg bg-slate-900 px-4 py-2.5 text-white transition-colors hover:bg-slate-800"
            >
              <span>{t('openDatasets')}</span>
              <ArrowRightOutlined className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => navigate('/annotations')}
              className="button-text flex items-center space-x-2 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-slate-700 transition-colors hover:border-slate-300 hover:bg-slate-50"
            >
              <span>{t('openAnnotations')}</span>
              <ArrowRightOutlined className="h-4 w-4" />
            </button>
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
                    <p className="metric-value-lg text-slate-900">{item.value}</p>
                  </div>
                  <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${overviewToneMap[index]}`}>
                    {item.icon}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t border-slate-100 bg-slate-50/50 px-8 py-6">
            <div className="card-title mb-6 flex items-center gap-2 text-slate-800">
              <CloudServerOutlined className="h-5 w-5 text-slate-500" />
              {t('taskOverview')}
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
                  <p className="metric-value-sm ml-[18px] text-slate-900">{item.value}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <section className="flex h-[320px] flex-col rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <h3 className="card-title mb-4">{t('recentDatasets')}</h3>
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
                  <p className="body-text-sm mt-1 text-slate-400">{t('createFirstDataset')}</p>
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
                          <span className="tag-text rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-slate-600">
                            {DataTypeLabels[dataset.data_type] ?? t('unknownType')}
                          </span>
                        </div>
                        <p className="caption-text mt-1 text-slate-400">
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
            <h3 className="card-title mb-4">{t('recentAnnotations')}</h3>
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
                <p className="body-text-sm mt-1 text-slate-400">{t('createFirstAnnotation')}</p>
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
                          <span className="tag-text rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-slate-600">
                            {AnnotationTypeLabels[annotation.annotation_type] ?? t('unknownType')}
                          </span>
                        </div>
                        <p className="caption-text mt-1 text-slate-400">
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
              <h3 className="card-title">{t('pipelineOverview')}</h3>
              <span className="tag-text rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-slate-600">
                {t('pipelineCount', { count: assistPipelines.length })}
              </span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-3">
              {displayedPipelines.length === 0 ? (
                <div className="body-text flex h-full items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/50 px-5 text-center text-slate-500">
                  {t('emptyPipelines')}
                </div>
              ) : (
                displayedPipelines.map((pipeline) => (
                  <button
                    key={pipeline.id}
                    type="button"
                    onClick={() => setSelectedPipeline(pipeline)}
                    className="group w-full cursor-pointer rounded-xl border border-slate-200 bg-white p-4 text-left transition-colors hover:border-slate-300 hover:bg-slate-50"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <h4 className="body-text truncate font-semibold text-slate-800">{pipeline.name}</h4>
                      <ArrowRightOutlined className="h-4 w-4 text-slate-300 transition-colors group-hover:text-indigo-500" />
                    </div>
                    <div className="flex space-x-2">
                      {(pipeline.supported_annotation_types.length ? pipeline.supported_annotation_types : [0])
                        .slice(0, 1)
                        .map((type) => (
                          <span
                            key={`${pipeline.id}-type-${type}`}
                            className="tag-text rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-slate-600"
                          >
                            {type === 0 ? t('pipelineTypeDetection') : (AnnotationTypeLabels[type] ?? t('unknownType'))}
                          </span>
                        ))}
                      {(pipeline.supported_shapes.length ? pipeline.supported_shapes : ['bbox'])
                        .slice(0, 1)
                        .map((shape) => (
                          <span
                            key={`${pipeline.id}-shape-${shape}`}
                            className="tag-text rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-slate-600"
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
