import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Alert, Button, Empty, Input, Space, Spin, Tag, Typography, message } from 'antd';
import { ArrowLeftOutlined, CheckCircleFilled, DownloadOutlined, SaveOutlined, StarFilled } from '@ant-design/icons';
import { exportDpoAnnotation, getAnnotation, getAnnotationRecordsBySamples, saveAnnotationRecord } from '../../../api/annotation';
import { getDataset, getDatasetSamples } from '../../../api/dataset';
import { AnnotationType, type AnnotationProject, type AnnotationRecord, type Dataset, type SampleItem } from '../../../types';
import { useUnsavedChangesGuard } from '../../../hooks/useUnsavedChangesGuard';
import type { DpoWorkbenchMode } from './DpoAnnotationWorkbench';
import { showApiError } from '../../../utils/apiError';

const { Title, Text, Paragraph } = Typography;

type DpoDecision = 'left' | 'right' | 'selected' | 'tie' | 'skip' | null;

interface DpoPromptMessage {
  role: string;
  content: string;
}

interface DpoResponseItem {
  response_id: string;
  content: string;
  model_id?: string | null;
  metadata?: Record<string, unknown>;
}

interface DpoSamplePayload {
  version?: number;
  format?: string;
  task_type?: 'pairwise' | 'best_of_n';
  export_strategy?: 'winner_vs_all';
  prompt?: {
    system_prompt?: string;
    messages?: DpoPromptMessage[];
  };
  responses?: DpoResponseItem[];
  reference?: {
    content?: string;
  } | null;
  rubric?: {
    focus?: string[];
    guidance?: string;
  } | null;
  tags?: string[];
}

interface DpoRecordContent {
  version: number;
  format: 'dpo_preference';
  sample_item_id: number;
  task_type: 'pairwise' | 'best_of_n';
  decision: 'left' | 'right' | 'selected' | 'tie' | 'skip';
  selected_response_id: string | null;
  chosen_response_id: string | null;
  rejected_response_id: string | null;
  rejected_response_ids: string[];
  tie: boolean;
  skip: boolean;
  reason: string;
  reason_tags: string[];
  display_order: string[];
  duration_ms: number;
  annotated_at: string;
}

interface DpoModeMeta {
  title: string;
  badge: string;
  intro: string;
  promptTitle: string;
  decisionTitle: string;
}

interface DpoSampleState {
  displayOrder: DpoResponseItem[];
  decision: DpoDecision;
  selectedResponseId: string | null;
  reason: string;
  reasonTags: string[];
  savedSnapshot: string;
  startedAt: number;
}

const LIST_PAGE_SIZE = 20;
const REASON_TAGS = [
  '更准确',
  '更完整',
  '更安全',
  '更简洁',
  '更符合指令',
];

function parseDpoPayload(sample: SampleItem): DpoSamplePayload | null {
  const payload = sample.payload;
  if (!payload || typeof payload !== 'object') return null;
  return payload as DpoSamplePayload;
}

function sortResponsesForDisplay(sampleId: number, responses: DpoResponseItem[]): DpoResponseItem[] {
  if (responses.length <= 1) {
    return responses;
  }
  const rotatedIndex = sampleId % responses.length;
  return [
    ...responses.slice(rotatedIndex),
    ...responses.slice(0, rotatedIndex),
  ];
}

function normalizeRecordContent(record: AnnotationRecord | undefined): Partial<DpoRecordContent> | null {
  if (!record?.content || typeof record.content !== 'object') return null;
  return record.content as Partial<DpoRecordContent>;
}

function createSavedSnapshot(decision: DpoDecision, selectedResponseId: string | null, reason: string, reasonTags: string[]) {
  return JSON.stringify({
    decision,
    selectedResponseId,
    reason: reason.trim(),
    reasonTags: [...reasonTags].sort(),
  });
}

function getDpoModeMeta(mode: DpoWorkbenchMode, candidateCount: number, activeTaskType: 'pairwise' | 'best_of_n'): DpoModeMeta {
  if (mode === 'pairwise') {
    return {
      title: 'DPO 二选一标注',
      badge: 'A/B 偏好',
      intro: '直接比较两条候选回复，判断哪一条更好。',
      promptTitle: '输入与上下文',
      decisionTitle: '偏好判断',
    };
  }

  if (mode === 'best_of_n') {
    return {
      title: 'DPO 多选一标注',
      badge: `N 选 1 · ${candidateCount} 个候选`,
      intro: '从多条候选回复中选出最佳答案，导出时会按 Winner vs All 展开。',
      promptTitle: '输入与上下文',
      decisionTitle: '最佳回复判断',
    };
  }

  if (mode === 'reference_choice') {
    return {
      title: 'DPO 参考增强标注',
      badge: '参考增强',
      intro: '优先依据参考答案或规则说明判断候选回复的事实准确性与一致性。',
      promptTitle: '问题与参考信息',
      decisionTitle: '参考增强判断',
    };
  }

  if (mode === 'multi_turn') {
    return {
      title: 'DPO 多轮对话标注',
      badge: '多轮对话',
      intro: '结合完整对话历史，判断候选回复是否承接上下文、保持一致。',
      promptTitle: '对话历史',
      decisionTitle: '多轮对话判断',
    };
  }

  return {
    title: 'DPO 偏好标注',
    badge: activeTaskType === 'best_of_n' ? `N 选 1 · ${candidateCount} 个候选` : 'A/B 偏好',
    intro: '兼容旧 DPO 项目，按样本中的任务类型进行偏好标注。',
    promptTitle: '输入与上下文',
    decisionTitle: '偏好判断',
  };
}

function getDpoExportFileName(mode: DpoWorkbenchMode, annotationId: number) {
  if (mode === 'pairwise') return `dpo_pairwise_annotation_${annotationId}.jsonl`;
  if (mode === 'best_of_n') return `dpo_best_of_n_annotation_${annotationId}.jsonl`;
  if (mode === 'reference_choice') return `dpo_reference_annotation_${annotationId}.jsonl`;
  if (mode === 'multi_turn') return `dpo_multi_turn_annotation_${annotationId}.jsonl`;
  return `dpo_annotation_${annotationId}.jsonl`;
}

interface DpoAnnotationPageProps {
  mode?: DpoWorkbenchMode;
}

const DpoAnnotationPage: React.FC<DpoAnnotationPageProps> = ({ mode = 'legacy' }) => {
  const { annotationId } = useParams<{ annotationId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [pageLoading, setPageLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [project, setProject] = useState<AnnotationProject | null>(null);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [samples, setSamples] = useState<SampleItem[]>([]);
  const [sampleStates, setSampleStates] = useState<Record<number, DpoSampleState>>({});
  const [activeSampleId, setActiveSampleId] = useState<number | null>(null);
  const [keywordInput, setKeywordInput] = useState('');
  const [keyword, setKeyword] = useState('');
  const [page, setPage] = useState(1);
  const [totalSamples, setTotalSamples] = useState(0);

  const annotationNumericId = Number(annotationId);

  const buildSampleState = useCallback((sample: SampleItem, record?: AnnotationRecord): DpoSampleState | null => {
    const payload = parseDpoPayload(sample);
    const responses = (payload?.responses || []).slice(0, 6) as DpoResponseItem[];
    if (!payload || responses.length < 2) return null;

    const displayOrder = sortResponsesForDisplay(sample.id, responses);
    const saved = normalizeRecordContent(record);
    const decision = ((saved?.decision === 'selected' ? 'selected' : saved?.decision) as DpoDecision) ?? null;
    const selectedResponseId = typeof saved?.selected_response_id === 'string'
      ? saved.selected_response_id
      : typeof saved?.chosen_response_id === 'string'
        ? saved.chosen_response_id
        : null;
    const reason = typeof saved?.reason === 'string' ? saved.reason : '';
    const reasonTags = Array.isArray(saved?.reason_tags)
      ? saved.reason_tags.filter((item): item is string => typeof item === 'string')
      : [];

    return {
      displayOrder,
      decision,
      selectedResponseId,
      reason,
      reasonTags,
      savedSnapshot: createSavedSnapshot(decision, selectedResponseId, reason, reasonTags),
      startedAt: Date.now(),
    };
  }, []);

  const loadSamplePage = useCallback(async (
    annotationProjectId: number,
    datasetId: number,
    nextPage: number,
    currentKeyword: string,
  ) => {
    setPageLoading(true);
    try {
      const result = await getDatasetSamples(
        datasetId,
        nextPage,
        LIST_PAGE_SIZE,
        'preference',
        currentKeyword.trim() || undefined,
      );
      const pageItems = (result?.items || []).filter((sample) => {
        const payload = parseDpoPayload(sample);
        return Boolean(payload?.responses && payload.responses.length >= 2);
      });
      const pageSampleIds = pageItems.map((sample) => sample.id);
      const pageRecords = pageSampleIds.length > 0
        ? await getAnnotationRecordsBySamples(annotationProjectId, pageSampleIds)
        : [];
      const nextRecordMap: Record<number, AnnotationRecord> = {};
      pageRecords.forEach((record) => {
        nextRecordMap[record.sample_item_id] = record;
      });

      setSamples(pageItems);
      setTotalSamples(result?.total || 0);
      setSampleStates((prev) => {
        const merged = { ...prev };
        pageItems.forEach((sample) => {
          const current = merged[sample.id];
          const currentSnapshot = current
            ? createSavedSnapshot(current.decision, current.selectedResponseId, current.reason, current.reasonTags)
            : null;
          if (current && currentSnapshot !== current.savedSnapshot) {
            return;
          }
          const built = buildSampleState(sample, nextRecordMap[sample.id]);
          if (built) {
            merged[sample.id] = built;
          }
        });
        return merged;
      });
      setActiveSampleId((prev) => {
        if (prev && pageItems.some((sample) => sample.id === prev)) return prev;
        return pageItems[0]?.id ?? null;
      });
    } catch (error) {
      console.error('Failed to load DPO samples', error);
      showApiError(error, '加载 DPO 样本失败');
    } finally {
      setPageLoading(false);
    }
  }, [buildSampleState]);

  const loadProject = useCallback(async () => {
    if (!annotationId || Number.isNaN(annotationNumericId)) {
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const annotation = await getAnnotation(annotationNumericId);
      const allowedAnnotationTypes = mode === 'legacy'
        ? [AnnotationType.DPO]
        : mode === 'pairwise'
          ? [AnnotationType.DpoPairwise]
          : mode === 'best_of_n'
            ? [AnnotationType.DpoBestOfN]
            : mode === 'reference_choice'
              ? [AnnotationType.DpoReferenceChoice]
              : [AnnotationType.DpoMultiTurn];
      if (!allowedAnnotationTypes.includes(annotation.annotation_type)) {
        message.error('当前项目不是 DPO 标注项目');
        navigate('/annotations', { replace: true });
        return;
      }
      if (!annotation.dataset_id) {
        message.error('当前标注项目未绑定数据集');
        navigate('/annotations', { replace: true });
        return;
      }

      const datasetDetail = await getDataset(annotation.dataset_id);

      setProject(annotation);
      setDataset(datasetDetail);
      setSamples([]);
      setSampleStates({});
      setActiveSampleId(null);
      setTotalSamples(0);
      setPage(1);
      setKeyword('');
      setKeywordInput('');
    } catch (error) {
      console.error('Failed to load DPO annotation project', error);
      showApiError(error, '加载 DPO 标注项目失败');
    } finally {
      setLoading(false);
    }
  }, [annotationId, annotationNumericId, navigate]);

  useEffect(() => {
    void loadProject();
  }, [loadProject]);

  useEffect(() => {
    if (!project?.dataset_id || !dataset) return;
    if (loading) return;
    void loadSamplePage(project.id, project.dataset_id, page, keyword);
  }, [dataset, keyword, loadSamplePage, loading, page, project?.dataset_id, project?.id]);

  const activeSample = useMemo(
    () => samples.find((sample) => sample.id === activeSampleId) ?? null,
    [activeSampleId, samples],
  );

  const activePayload = activeSample ? parseDpoPayload(activeSample) : null;
  const activeState = activeSampleId ? sampleStates[activeSampleId] : undefined;

  const activeDirty = useMemo(() => {
    if (!activeSampleId || !activeState) return false;
    return createSavedSnapshot(activeState.decision, activeState.selectedResponseId, activeState.reason, activeState.reasonTags) !== activeState.savedSnapshot;
  }, [activeSampleId, activeState]);

  const dirtyCount = useMemo(() => {
    return Object.values(sampleStates).reduce((count, state) => (
      createSavedSnapshot(state.decision, state.selectedResponseId, state.reason, state.reasonTags) === state.savedSnapshot ? count : count + 1
    ), 0);
  }, [sampleStates]);
  useUnsavedChangesGuard(dirtyCount > 0);

  const activeTaskType = mode === 'best_of_n'
    ? 'best_of_n'
    : activePayload?.task_type === 'best_of_n'
      ? 'best_of_n'
      : 'pairwise';
  const modeMeta = getDpoModeMeta(mode, activePayload?.responses?.length || 0, activeTaskType);
  const isReferenceMode = mode === 'reference_choice';
  const isMultiTurnMode = mode === 'multi_turn';

  const updateActiveState = (updater: (current: DpoSampleState) => DpoSampleState) => {
    if (!activeSampleId) return;
    setSampleStates((prev) => {
      const current = prev[activeSampleId];
      if (!current) return prev;
      return {
        ...prev,
        [activeSampleId]: updater(current),
      };
    });
  };

  const handleSelectDecision = (decision: Exclude<DpoDecision, null>) => {
    updateActiveState((current) => ({
      ...current,
      decision,
      selectedResponseId: decision === 'left'
        ? current.displayOrder[0]?.response_id ?? null
        : decision === 'right'
          ? current.displayOrder[1]?.response_id ?? null
          : decision === 'tie' || decision === 'skip'
            ? null
            : current.selectedResponseId,
    }));
  };

  const handleSelectResponse = (responseId: string) => {
    updateActiveState((current) => ({
      ...current,
      decision: 'selected',
      selectedResponseId: responseId,
    }));
  };

  const handleToggleReasonTag = (tag: string) => {
    updateActiveState((current) => {
      const exists = current.reasonTags.includes(tag);
      return {
        ...current,
        reasonTags: exists
          ? current.reasonTags.filter((item) => item !== tag)
          : [...current.reasonTags, tag],
      };
    });
  };

  const handleSave = async (moveToNext = false) => {
    if (!project || !activeSampleId) return;
    const sample = samples.find((item) => item.id === activeSampleId);
    const state = sampleStates[activeSampleId];
    const payload = sample ? parseDpoPayload(sample) : null;
    if (!sample || !state || !payload) return;
    if (!state.decision || (activeTaskType === 'best_of_n' && state.decision === 'selected' && !state.selectedResponseId)) {
      message.warning('请先选择偏好结果');
      return;
    }

    const displayOrder = state.displayOrder;
    const [left, right] = displayOrder;
    let chosenResponseId: string | null = null;
    let rejectedResponseId: string | null = null;
    let rejectedResponseIds: string[] = [];
    if (state.decision === 'left') {
      chosenResponseId = left.response_id;
      rejectedResponseId = right.response_id;
      rejectedResponseIds = [right.response_id];
    } else if (state.decision === 'right') {
      chosenResponseId = right.response_id;
      rejectedResponseId = left.response_id;
      rejectedResponseIds = [left.response_id];
    } else if (state.decision === 'selected' && state.selectedResponseId) {
      chosenResponseId = state.selectedResponseId;
      rejectedResponseIds = displayOrder
        .map((item) => item.response_id)
        .filter((responseId) => responseId !== state.selectedResponseId);
      rejectedResponseId = rejectedResponseIds[0] ?? null;
    }

    setSaving(true);
    try {
      const content: DpoRecordContent = {
        version: 1,
        format: 'dpo_preference',
        sample_item_id: activeSampleId,
        task_type: activeTaskType,
        decision: state.decision,
        selected_response_id: chosenResponseId,
        chosen_response_id: chosenResponseId,
        rejected_response_id: rejectedResponseId,
        rejected_response_ids: rejectedResponseIds,
        tie: state.decision === 'tie',
        skip: state.decision === 'skip',
        reason: state.reason.trim(),
        reason_tags: state.reasonTags,
        display_order: displayOrder.map((item) => item.response_id),
        duration_ms: Math.max(0, Date.now() - state.startedAt),
        annotated_at: new Date().toISOString(),
      };

      await saveAnnotationRecord(project.id, {
        sample_item_id: activeSampleId,
        content: content as unknown as Record<string, unknown>,
        status: 'saved',
      });

      setSampleStates((prev) => {
        const current = prev[activeSampleId];
        if (!current) return prev;
        return {
          ...prev,
          [activeSampleId]: {
            ...current,
            savedSnapshot: createSavedSnapshot(current.decision, current.selectedResponseId, current.reason, current.reasonTags),
            startedAt: Date.now(),
          },
        };
      });
      message.success('保存成功');

      if (moveToNext) {
        const currentIndex = samples.findIndex((item) => item.id === activeSampleId);
        const nextSample = samples[currentIndex + 1];
        if (nextSample) {
          setActiveSampleId(nextSample.id);
        } else if (page * LIST_PAGE_SIZE < totalSamples) {
          setPage((value) => value + 1);
        }
      }
    } catch (error) {
      console.error('Failed to save DPO annotation', error);
      showApiError(error, '保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleExport = async () => {
    if (!project) return;
    setExporting(true);
    try {
      const blob = await exportDpoAnnotation(project.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = getDpoExportFileName(mode, project.id);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export DPO annotation', error);
      showApiError(error, '导出失败');
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const tagName = target?.tagName?.toLowerCase();
      const isTyping = tagName === 'input' || tagName === 'textarea' || target?.isContentEditable;
      if (isTyping || !activeSampleId) return;

      if (event.key.toLowerCase() === 'a') {
        event.preventDefault();
        if (activeTaskType === 'pairwise') handleSelectDecision('left');
      } else if (event.key.toLowerCase() === 'd') {
        event.preventDefault();
        if (activeTaskType === 'pairwise') handleSelectDecision('right');
      } else if (event.key.toLowerCase() === 'w') {
        event.preventDefault();
        handleSelectDecision('tie');
      } else if (event.key.toLowerCase() === 's') {
        event.preventDefault();
        handleSelectDecision('skip');
      } else if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        void handleSave(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeSampleId, activeTaskType, samples, handleSave]);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#fff' }}>
        <Spin size="large" tip="正在加载 DPO 标注工作台..." />
      </div>
    );
  }

  if (!project || !dataset) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#fff' }}>
        <Empty description="DPO 标注项目不存在或无法加载" />
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', height: '100vh', background: '#f8fafc' }}>
      <aside style={{ borderRight: '1px solid #e5e7eb', background: '#fff', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <div style={{ padding: 16, borderBottom: '1px solid #e5e7eb' }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/annotations')} style={{ marginBottom: 12 }}>
            返回
          </Button>
          <Title level={4} style={{ margin: 0 }}>{project.name}</Title>
          <Text type="secondary">{dataset.name}</Text>
          <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <Tag color="blue">{totalSamples} 条样本</Tag>
            <Tag color={dirtyCount > 0 ? 'orange' : 'green'}>{dirtyCount > 0 ? `${dirtyCount} 未保存` : '已保存'}</Tag>
          </div>
          <Input
            style={{ marginTop: 12 }}
            placeholder="搜索样本"
            value={keywordInput}
            onChange={(event) => setKeywordInput(event.target.value)}
            onPressEnter={() => {
              setPage(1);
              setKeyword(keywordInput.trim());
            }}
            allowClear
            onClear={() => {
              setKeywordInput('');
              setKeyword('');
              setPage(1);
            }}
          />
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          {pageLoading ? (
            <div style={{ paddingTop: 48, textAlign: 'center' }}>
              <Spin />
            </div>
          ) : samples.length === 0 ? (
            <Empty style={{ marginTop: 48 }} description="暂无可标注样本" />
          ) : (
            samples.map((sample) => {
              const state = sampleStates[sample.id];
              const isActive = sample.id === activeSampleId;
              const isSaved = state ? createSavedSnapshot(state.decision, state.selectedResponseId, state.reason, state.reasonTags) === state.savedSnapshot : false;
              return (
                <button
                  key={sample.id}
                  type="button"
                  onClick={() => setActiveSampleId(sample.id)}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    border: 'none',
                    borderBottom: '1px solid #f1f5f9',
                    background: isActive ? '#eef2ff' : '#fff',
                    padding: '12px 16px',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                    <span className="body-text-sm" style={{ fontWeight: 600, color: '#111', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {sample.item_key}
                    </span>
                    <span className="tag-text" style={{ color: isSaved ? '#16a34a' : '#f59e0b' }}>
                      {isSaved ? '已保存' : '未保存'}
                    </span>
                  </div>
                  <div className="caption-text" style={{ marginTop: 6, color: '#64748b' }}>
                    {state?.decision === 'left' && '偏好左侧'}
                    {state?.decision === 'right' && '偏好右侧'}
                    {state?.decision === 'selected' && state.selectedResponseId && `已选 ${state.selectedResponseId}`}
                    {state?.decision === 'tie' && '平局'}
                    {state?.decision === 'skip' && '跳过'}
                    {!state?.decision && '未判断'}
                  </div>
                </button>
              );
            })
          )}
        </div>

        {totalSamples > LIST_PAGE_SIZE && (
          <div style={{ padding: 12, borderTop: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>
            <Button size="small" disabled={page <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>上一页</Button>
            <Text type="secondary">第 {page} 页</Text>
            <Button size="small" disabled={page * LIST_PAGE_SIZE >= totalSamples} onClick={() => setPage((value) => value + 1)}>下一页</Button>
          </div>
        )}
      </aside>

      <main style={{ minWidth: 0, overflowY: 'auto' }}>
        {!activeSample || !activePayload || !activeState ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <Empty description="请选择样本" />
          </div>
        ) : (
          <div style={{ maxWidth: 1400, margin: '0 auto', padding: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <div>
                <Title level={4} style={{ margin: 0 }}>{modeMeta.title}</Title>
                <Text type="secondary">{activeSample.item_key}</Text>
                <div style={{ marginTop: 8 }}>
                  <Space size={8} wrap>
                    <Tag color={activeTaskType === 'best_of_n' ? 'gold' : 'blue'}>
                      {modeMeta.badge}
                    </Tag>
                    {activePayload.export_strategy === 'winner_vs_all' && activeTaskType === 'best_of_n' ? (
                      <Tag color="processing">导出为 Winner vs All</Tag>
                    ) : null}
                  </Space>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <Button icon={<DownloadOutlined />} loading={exporting} onClick={handleExport}>导出 JSONL</Button>
                <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={() => void handleSave(true)}>
                  保存并下一条
                </Button>
              </div>
            </div>

            {project.prompt && (
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 12, marginBottom: 12 }}>
                <Text type="secondary">标注说明</Text>
                <Paragraph style={{ marginTop: 6, marginBottom: 0, whiteSpace: 'pre-wrap' }}>{project.prompt}</Paragraph>
              </div>
            )}

            <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, marginBottom: 16 }}>
              <Text type="secondary">{modeMeta.promptTitle}</Text>
              <Paragraph style={{ margin: '8px 0 0', color: '#64748b' }}>{modeMeta.intro}</Paragraph>
              {activePayload.prompt?.system_prompt ? (
                <div style={{ marginTop: 10, padding: 10, borderRadius: 6, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                  <Text strong>System</Text>
                  <Paragraph style={{ margin: '6px 0 0', whiteSpace: 'pre-wrap' }}>{activePayload.prompt.system_prompt}</Paragraph>
                </div>
              ) : null}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 12 }}>
                {(activePayload.prompt?.messages || []).map((messageItem, index) => (
                  <div
                    key={`${messageItem.role}-${index}`}
                    style={{
                      padding: 12,
                      borderRadius: 8,
                      background: isMultiTurnMode
                        ? messageItem.role === 'user'
                          ? '#eff6ff'
                          : '#f8fafc'
                        : messageItem.role === 'user'
                          ? '#eef2ff'
                          : '#f8fafc',
                      border: '1px solid #e5e7eb',
                    }}
                  >
                    <Text strong>{messageItem.role}</Text>
                    <Paragraph style={{ margin: '6px 0 0', whiteSpace: 'pre-wrap' }}>{messageItem.content}</Paragraph>
                  </div>
                ))}
              </div>
              {activePayload.reference?.content ? (
                <div style={{
                  marginTop: 12,
                  padding: 12,
                  borderRadius: 8,
                  background: isReferenceMode ? '#fff7ed' : '#fffbea',
                  border: `1px solid ${isReferenceMode ? '#fdba74' : '#fde68a'}`,
                }}>
                  <Text strong>{isReferenceMode ? '标准答案 / 参考依据' : '参考答案'}</Text>
                  <Paragraph style={{ margin: '6px 0 0', whiteSpace: 'pre-wrap' }}>{activePayload.reference.content}</Paragraph>
                </div>
              ) : null}
              {activePayload.rubric?.guidance || (activePayload.rubric?.focus && activePayload.rubric.focus.length > 0) ? (
                <div style={{ marginTop: 12 }}>
                  <Alert
                    type={isReferenceMode ? 'warning' : 'info'}
                    showIcon
                    message={isReferenceMode ? '优先判定依据' : '判定标准'}
                    description={(
                      <div>
                        {activePayload.rubric?.guidance ? (
                          <div style={{ marginBottom: activePayload.rubric.focus?.length ? 8 : 0, whiteSpace: 'pre-wrap' }}>
                            {activePayload.rubric.guidance}
                          </div>
                        ) : null}
                        {activePayload.rubric?.focus?.length ? (
                          <Space size={[6, 6]} wrap>
                            {activePayload.rubric.focus.map((item) => (
                              <Tag key={item}>{item}</Tag>
                            ))}
                          </Space>
                        ) : null}
                      </div>
                    )}
                  />
                </div>
              ) : null}
              {isMultiTurnMode && (
                <div style={{ marginTop: 12, padding: 12, borderRadius: 8, background: '#f8fafc', border: '1px dashed #cbd5e1' }}>
                  <Text strong>多轮对话关注点</Text>
                  <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {['承接上下文', '前后说法一致', '记住用户约束', '回答最后一轮问题'].map((item) => (
                      <Tag key={item}>{item}</Tag>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: activeTaskType === 'pairwise' ? '1fr 1fr' : 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
              {activeState.displayOrder.map((response, index) => {
                const isLeft = index === 0;
                const selected = activeTaskType === 'pairwise'
                  ? (isLeft && activeState.decision === 'left') || (!isLeft && activeState.decision === 'right')
                  : activeState.selectedResponseId === response.response_id;
                return (
                  <div
                    key={response.response_id}
                    style={{
                      background: '#fff',
                      border: selected ? '1px solid #4f6ef7' : '1px solid #e5e7eb',
                      borderRadius: 8,
                      padding: 16,
                      minHeight: 360,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                      <Space size={8} wrap>
                        <Tag color={selected ? 'blue' : 'default'}>
                          {activeTaskType === 'pairwise' ? (isLeft ? '回答 A' : '回答 B') : `候选 ${index + 1}`}
                        </Tag>
                        {response.model_id ? <Tag>{response.model_id}</Tag> : null}
                        {selected ? <Tag color="success" icon={<CheckCircleFilled />}>当前已选</Tag> : null}
                      </Space>
                      <Button
                        size="small"
                        type={selected ? 'primary' : 'default'}
                        icon={selected ? <StarFilled /> : undefined}
                        onClick={() => activeTaskType === 'pairwise'
                          ? handleSelectDecision(isLeft ? 'left' : 'right')
                          : handleSelectResponse(response.response_id)}
                      >
                        {activeTaskType === 'pairwise' ? '选择这个' : '设为最佳'}
                      </Button>
                    </div>
                    {isReferenceMode && (
                      <div className="caption-text" style={{ marginBottom: 12, padding: 10, borderRadius: 6, background: '#f8fafc', border: '1px solid #e5e7eb', color: '#64748b' }}>
                        请优先对照上方参考答案，关注事实是否准确、是否遗漏关键信息。
                      </div>
                    )}
                    {isMultiTurnMode && (
                      <div className="caption-text" style={{ marginBottom: 12, padding: 10, borderRadius: 6, background: '#f8fafc', border: '1px solid #e5e7eb', color: '#64748b' }}>
                        请结合完整对话历史判断该回复是否真正回答了最后一轮问题，并与前文保持一致。
                      </div>
                    )}
                    <Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>{response.content || '空回复'}</Paragraph>
                  </div>
                );
              })}
            </div>

            <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, marginTop: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <Text strong>{modeMeta.decisionTitle}</Text>
                <Text type={activeDirty ? 'warning' : 'secondary'}>{activeDirty ? '当前有未保存修改' : '当前已保存'}</Text>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
                {activeTaskType === 'pairwise' ? (
                  <>
                    <Button type={activeState.decision === 'left' ? 'primary' : 'default'} onClick={() => handleSelectDecision('left')}>偏好左侧</Button>
                    <Button type={activeState.decision === 'right' ? 'primary' : 'default'} onClick={() => handleSelectDecision('right')}>偏好右侧</Button>
                  </>
                ) : (
                  <Tag color={activeState.selectedResponseId ? 'success' : 'default'}>
                    {activeState.selectedResponseId
                      ? `当前最佳：${activeState.selectedResponseId}`
                      : isReferenceMode
                        ? '请结合参考答案从上方候选中选择最佳回复'
                        : isMultiTurnMode
                          ? '请结合完整对话历史从上方候选中选择最佳回复'
                          : '请从上方候选中选择最佳回复'}
                  </Tag>
                )}
                <Button type={activeState.decision === 'tie' ? 'primary' : 'default'} onClick={() => handleSelectDecision('tie')}>平局</Button>
                <Button type={activeState.decision === 'skip' ? 'primary' : 'default'} onClick={() => handleSelectDecision('skip')}>跳过</Button>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
                {REASON_TAGS.map((tag) => (
                  <Tag.CheckableTag
                    key={tag}
                    checked={activeState.reasonTags.includes(tag)}
                    onChange={() => handleToggleReasonTag(tag)}
                  >
                    {tag}
                  </Tag.CheckableTag>
                ))}
              </div>

              <Input.TextArea
                rows={4}
                placeholder="可选：补充判断理由"
                value={activeState.reason}
                onChange={(event) => updateActiveState((current) => ({ ...current, reason: event.target.value }))}
              />

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, marginTop: 12 }}>
                <Text type="secondary">
                  {activeTaskType === 'pairwise'
                    ? '快捷键：A 左侧，D 右侧，W 平局，S 跳过，Ctrl+Enter 保存'
                    : '快捷键：W 平局，S 跳过，Ctrl+Enter 保存'}
                </Text>
                <div style={{ display: 'flex', gap: 8 }}>
                  <Button onClick={() => {
                    const currentIndex = samples.findIndex((item) => item.id === activeSample.id);
                    const previous = samples[currentIndex - 1];
                    if (previous) setActiveSampleId(previous.id);
                    else if (page > 1) setPage((value) => Math.max(1, value - 1));
                  }}>
                    上一条
                  </Button>
                  <Button onClick={() => {
                    const currentIndex = samples.findIndex((item) => item.id === activeSample.id);
                    const next = samples[currentIndex + 1];
                    if (next) setActiveSampleId(next.id);
                    else if (page * LIST_PAGE_SIZE < totalSamples) setPage((value) => value + 1);
                  }}>
                    下一条
                  </Button>
                  <Button type="primary" loading={saving} icon={<SaveOutlined />} onClick={() => void handleSave()}>
                    保存
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default DpoAnnotationPage;
