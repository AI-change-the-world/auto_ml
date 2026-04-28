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
import { getHomeStats } from '../../api/home';
import type { HomeStats } from '../../types/home';
import { AnnotationTypeLabels, DataTypeLabels } from '../../types';
import { useTranslation } from 'react-i18next';

const surfaceClassName =
  'rounded-[22px] border border-slate-200/80 bg-white shadow-[0_18px_44px_-36px_rgba(15,23,42,0.24)]';

const datasetTypeMeta: Record<number, { icon: React.ReactNode; tone: string }> = {
  0: {
    icon: <PictureOutlined className="text-base" />,
    tone: 'bg-sky-50 text-sky-600 ring-sky-100',
  },
  1: {
    icon: <FileTextOutlined className="text-base" />,
    tone: 'bg-violet-50 text-violet-600 ring-violet-100',
  },
  2: {
    icon: <VideoCameraOutlined className="text-base" />,
    tone: 'bg-amber-50 text-amber-600 ring-amber-100',
  },
  3: {
    icon: <SoundOutlined className="text-base" />,
    tone: 'bg-emerald-50 text-emerald-600 ring-emerald-100',
  },
};

const annotationToneMap: Record<number, string> = {
  0: 'bg-sky-50 text-sky-600 ring-sky-100',
  1: 'bg-emerald-50 text-emerald-600 ring-emerald-100',
  2: 'bg-amber-50 text-amber-600 ring-amber-100',
  3: 'bg-fuchsia-50 text-fuchsia-600 ring-fuchsia-100',
  4: 'bg-cyan-50 text-cyan-600 ring-cyan-100',
  5: 'bg-indigo-50 text-indigo-600 ring-indigo-100',
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
        icon: <DatabaseOutlined className="text-lg" />,
        tone: 'bg-amber-50 text-amber-600 ring-amber-100',
      },
      {
        key: 'samples',
        label: t('images'),
        value: formatNumber(stats?.images),
        icon: <PictureOutlined className="text-lg" />,
        tone: 'bg-sky-50 text-sky-600 ring-sky-100',
      },
      {
        key: 'annotations',
        label: t('annotations'),
        value: formatNumber(stats?.annotations),
        icon: <TagsOutlined className="text-lg" />,
        tone: 'bg-violet-50 text-violet-600 ring-violet-100',
      },
      {
        key: 'models',
        label: t('models'),
        value: formatNumber(stats?.models?.total),
        icon: <ExperimentOutlined className="text-lg" />,
        tone: 'bg-emerald-50 text-emerald-600 ring-emerald-100',
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
        tone: 'border-slate-200 bg-slate-100 text-slate-700',
      },
      {
        key: 'running',
        label: t('runningTasks'),
        value: formatNumber(stats?.tasks?.running),
        tone: 'border-emerald-200 bg-emerald-50 text-emerald-700',
      },
      {
        key: 'completed',
        label: t('completedTasks'),
        value: formatNumber(stats?.tasks?.completed),
        tone: 'border-sky-200 bg-sky-50 text-sky-700',
      },
      {
        key: 'deployments',
        label: t('deployments'),
        value: formatNumber(stats?.models?.deployed),
        tone: 'border-violet-200 bg-violet-50 text-violet-700',
      },
    ],
    [stats, t],
  );

  const recentDatasets = stats?.recent_datasets ?? [];
  const recentAnnotations = stats?.recent_annotations ?? [];
  const assistPipelines = stats?.assist_pipelines ?? [];
  const fallbackTimeText = t('unknownTime');
  const displayedDatasets = recentDatasets.slice(0, 3);
  const displayedAnnotations = recentAnnotations.slice(0, 3);
  const displayedPipelines = assistPipelines.slice(0, 3);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="page-container h-full overflow-y-auto bg-[#f6f7fb] pb-6">
      <div className="mx-auto flex max-w-[1320px] flex-col gap-4">
        <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="inline-flex w-fit items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-medium text-slate-600 shadow-[0_12px_24px_-20px_rgba(15,23,42,0.26)]">
            <HomeOutlined />
            <span>{t('title')}</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => navigate('/datasets')}
              className="inline-flex h-9 items-center gap-2 rounded-full bg-[#4f6ef7] px-4 text-[13px] font-medium text-white transition hover:bg-[#4562e5]"
            >
              <span>{t('openDatasets')}</span>
              <ArrowRightOutlined className="text-[12px]" />
            </button>
            <button
              type="button"
              onClick={() => navigate('/annotations')}
              className="inline-flex h-9 items-center gap-2 rounded-full border border-[#dbe4ff] bg-[#eef3ff] px-4 text-[13px] font-medium text-[#4f6ef7] transition hover:bg-[#e5ecff]"
            >
              <span>{t('openAnnotations')}</span>
              <ArrowRightOutlined className="text-[12px]" />
            </button>
          </div>
        </header>

        <section className={`${surfaceClassName} px-5 py-5 sm:px-6`}>
          <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div className="max-w-xl">
              <div className="inline-flex w-fit items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-[11px] font-medium text-slate-600">
                <span className="h-2 w-2 rounded-full bg-cyan-500" />
                <span>{t('heroTag')}</span>
              </div>
              <h1 className="mt-3 text-[17px] font-semibold text-slate-950 sm:text-[18px]">{t('heroTitle')}</h1>
              <p className="mt-2 text-[13px] leading-5 text-slate-500">{t('heroSubtitle')}</p>
            </div>

            <div className="grid gap-2 sm:grid-cols-2 xl:min-w-[448px] xl:grid-cols-4">
              {overviewMetrics.map((item) => (
                <div
                  key={item.key}
                  className="rounded-[18px] border border-slate-200/80 bg-slate-50/90 px-4 py-3 transition hover:border-slate-300 hover:bg-white"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-[11px] font-medium text-slate-500">{item.label}</span>
                    <span
                      className={`flex h-8 w-8 items-center justify-center rounded-xl ring-1 ${item.tone}`}
                    >
                      {item.icon}
                    </span>
                  </div>
                  <div className="mt-3 text-[26px] font-semibold text-slate-950">{item.value}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 border-t border-slate-200 pt-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-900">
              <CloudServerOutlined />
              <span>{t('taskOverview')}</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {taskMetrics.map((item) => (
                <div
                  key={item.key}
                  className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[13px] font-medium ${item.tone}`}
                >
                  <span className="font-semibold text-slate-950">{item.value}</span>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="grid gap-4 xl:grid-cols-3">
          <section className={`${surfaceClassName} flex h-full flex-col overflow-hidden px-5 py-5 sm:px-6`}>
            <div className="flex min-h-[32px] items-center gap-2">
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-slate-950">{t('recentDatasets')}</h2>
                {/* <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-500">
                  {t('recentCount')}
                </span> */}
              </div>
            </div>

            <div className="mt-5 flex flex-1 flex-col gap-2.5">
              {displayedDatasets.length === 0 ? (
                <button
                  type="button"
                  onClick={() => navigate('/datasets')}
                  className="flex min-h-[132px] flex-1 flex-col items-center justify-center rounded-[18px] border border-dashed border-slate-200 bg-slate-50/80 px-6 py-8 text-center transition hover:border-slate-300 hover:bg-white"
                >
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-slate-500 ring-1 ring-slate-200">
                    <DatabaseOutlined className="text-base" />
                  </span>
                  <span className="mt-4 text-base font-medium text-slate-900">{t('emptyDatasets')}</span>
                  <span className="mt-2 text-sm text-slate-500">{t('createFirstDataset')}</span>
                </button>
              ) : (
                displayedDatasets.map((dataset) => {
                  const typeMeta = datasetTypeMeta[dataset.data_type] ?? datasetTypeMeta[0];

                  return (
                    <button
                      key={dataset.id}
                      type="button"
                      onClick={() => navigate(`/datasets/${dataset.id}`)}
                      className="group flex w-full items-center gap-4 rounded-[18px] border border-slate-200/80 bg-slate-50/85 px-4 py-3.5 text-left transition hover:-translate-y-0.5 hover:border-slate-300 hover:bg-white hover:shadow-[0_18px_40px_-28px_rgba(15,23,42,0.32)]"
                    >
                      <span
                        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ring-1 ${typeMeta.tone}`}
                      >
                        {typeMeta.icon}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="flex flex-wrap items-center gap-2">
                          <span className="truncate text-sm font-medium text-slate-950">{dataset.name}</span>
                          <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-slate-500 ring-1 ring-slate-200">
                            {DataTypeLabels[dataset.data_type] ?? t('unknownType')}
                          </span>
                        </span>
                        <span className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                          <span>{t('sampleCount', { count: formatNumber(dataset.count) })}</span>
                          <span className="text-slate-300">/</span>
                          <span>{t('createdAt', { date: formatDate(dataset.created_at, fallbackTimeText) })}</span>
                        </span>
                      </span>
                      <ArrowRightOutlined className="text-[12px] text-slate-300 transition group-hover:text-slate-600" />
                    </button>
                  );
                })
              )}
            </div>
          </section>

          <section className={`${surfaceClassName} flex h-full flex-col overflow-hidden px-5 py-5 sm:px-6`}>
            <div className="flex min-h-[32px] items-center gap-2">
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-slate-950">{t('recentAnnotations')}</h2>
                {/* <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-500">
                  {t('recentCount')}
                </span> */}
              </div>
            </div>

            <div className="mt-5 flex flex-1 flex-col gap-2.5">
              {displayedAnnotations.length === 0 ? (
                <button
                  type="button"
                  onClick={() => navigate('/annotations')}
                  className="flex min-h-[132px] flex-1 flex-col items-center justify-center rounded-[18px] border border-dashed border-slate-200 bg-slate-50/80 px-6 py-8 text-center transition hover:border-slate-300 hover:bg-white"
                >
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-slate-500 ring-1 ring-slate-200">
                    <FolderOpenOutlined className="text-base" />
                  </span>
                  <span className="mt-4 text-base font-medium text-slate-900">{t('emptyAnnotations')}</span>
                  <span className="mt-2 text-sm text-slate-500">{t('createFirstAnnotation')}</span>
                </button>
              ) : (
                displayedAnnotations.map((annotation) => {
                  const tone = annotationToneMap[annotation.annotation_type] ?? 'bg-slate-100 text-slate-600 ring-slate-200';
                  const initial = annotation.name?.trim().charAt(0)?.toUpperCase() || 'A';

                  return (
                    <button
                      key={annotation.id}
                      type="button"
                      onClick={() => navigate(`/annotations/${annotation.id}/label`)}
                      className="group flex w-full items-center gap-4 rounded-[18px] border border-slate-200/80 bg-slate-50/85 px-4 py-3.5 text-left transition hover:-translate-y-0.5 hover:border-slate-300 hover:bg-white hover:shadow-[0_18px_40px_-28px_rgba(15,23,42,0.32)]"
                    >
                      <span
                        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-semibold ring-1 ${tone}`}
                      >
                        {initial}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="flex flex-wrap items-center gap-2">
                          <span className="truncate text-sm font-medium text-slate-950">{annotation.name}</span>
                          <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-slate-500 ring-1 ring-slate-200">
                            {AnnotationTypeLabels[annotation.annotation_type] ?? t('unknownType')}
                          </span>
                        </span>
                        <span className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                          <span>{t('createdAt', { date: formatDate(annotation.created_at, fallbackTimeText) })}</span>
                        </span>
                      </span>
                      <ArrowRightOutlined className="text-[12px] text-slate-300 transition group-hover:text-slate-600" />
                    </button>
                  );
                })
              )}
            </div>
          </section>

          <section className={`${surfaceClassName} flex h-full flex-col overflow-hidden px-5 py-5 sm:px-6`}>
            <div className="flex min-h-[32px] items-center gap-2">
              <h2 className="text-base font-semibold text-slate-950">{t('pipelineOverview')}</h2>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-500">
                {t('pipelineCount', { count: assistPipelines.length })}
              </span>
            </div>

            <div className="mt-5 flex flex-1 flex-col gap-2.5">
              {displayedPipelines.length === 0 ? (
                <div className="flex min-h-[132px] flex-1 items-center justify-center rounded-[18px] border border-dashed border-slate-200 bg-slate-50/80 px-5 text-center text-sm text-slate-500">
                  {t('emptyPipelines')}
                </div>
              ) : (
                displayedPipelines.map((pipeline) => (
                  <button
                    key={pipeline.id}
                    type="button"
                    onClick={() => setSelectedPipeline(pipeline)}
                    className="group rounded-[18px] border border-slate-200/80 bg-slate-50/85 px-4 py-3 text-left transition hover:-translate-y-0.5 hover:border-slate-300 hover:bg-white hover:shadow-[0_18px_40px_-28px_rgba(15,23,42,0.32)]"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="text-sm font-medium leading-5 text-slate-950">{pipeline.name}</div>
                      <ArrowRightOutlined className="mt-1 text-[12px] text-slate-300 transition group-hover:text-slate-600" />
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {(pipeline.supported_annotation_types.length ? pipeline.supported_annotation_types : [0])
                        .slice(0, 1)
                        .map((type) => (
                          <span
                            key={`${pipeline.id}-type-${type}`}
                            className="rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-slate-500 ring-1 ring-slate-200"
                          >
                            {type === 0 ? t('pipelineTypeDetection') : (AnnotationTypeLabels[type] ?? t('unknownType'))}
                          </span>
                        ))}
                      {(pipeline.supported_shapes.length ? pipeline.supported_shapes : ['bbox'])
                        .slice(0, 2)
                        .map((shape) => (
                          <span
                            key={`${pipeline.id}-shape-${shape}`}
                            className="rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-slate-500 ring-1 ring-slate-200"
                          >
                            {t('pipelineShape', { shape: shape.toUpperCase() })}
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
