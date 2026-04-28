import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Card, Empty, Input, Modal, Space, Spin, Tag, Typography, message } from 'antd';
import { ArrowLeftOutlined, PlusOutlined, ReloadOutlined, SaveOutlined } from '@ant-design/icons';
import { getAnnotation, getAnnotationRecords, saveAnnotationRecord } from '../../../api/annotation';
import { createDatasetSample, getDataset, getDatasetSampleContent, getDatasetSamples, previewSample } from '../../../api/dataset';
import { AnnotationType, type AnnotationProject, type Dataset, DataTypeLabels, type SampleItem } from '../../../types';
import {
  createEmptyConversationAnnotationEntry,
  createConversationMessage,
  parseConversationAnnotationContent,
  serializeConversationAnnotationContent,
  type ConversationAnnotationMode,
} from '../../../utils/conversationAnnotation';
import ConversationEditorModal from './components/ConversationEditorModal';
import ConversationFileListCard from './components/ConversationFileListCard';
import type { ConversationEntriesBySample, ConversationFileRow, PreviewState } from './types';

const { Title, Text } = Typography;

const PAGE_SIZE = 12;

const getSampleDisplayName = (sample: SampleItem) => sample.asset?.file_name || sample.item_key;

const ConversationAnnotationPage: React.FC = () => {
  const { annotationId } = useParams<{ annotationId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [project, setProject] = useState<AnnotationProject | null>(null);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [sampleItems, setSampleItems] = useState<SampleItem[]>([]);
  const [entriesBySample, setEntriesBySample] = useState<ConversationEntriesBySample>({});
  const [savedBySample, setSavedBySample] = useState<ConversationEntriesBySample>({});
  const [previewByFile, setPreviewByFile] = useState<Record<string, PreviewState>>({});
  const [keyword, setKeyword] = useState('');
  const [page, setPage] = useState(1);
  const [activeSampleId, setActiveSampleId] = useState<number | null>(null);
  const [focusedSampleId, setFocusedSampleId] = useState<number | null>(null);
  const [draftRole, setDraftRole] = useState<'user' | 'assistant'>('user');
  const [draftContent, setDraftContent] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [createSampleOpen, setCreateSampleOpen] = useState(false);
  const [newSampleName, setNewSampleName] = useState('');

  const annotationNumericId = Number(annotationId);
  const mode: ConversationAnnotationMode = project?.annotation_type === AnnotationType.LLM ? 'llm' : 'mllm';

  const loadSamplePreview = useCallback(async (datasetId: number, sample: SampleItem, previewMode: ConversationAnnotationMode) => {
    const sampleName = getSampleDisplayName(sample);
    setPreviewByFile((state) => {
      const current = state[sampleName];
      if (current?.loading || current?.url || current?.textContent) return state;
      return { ...state, [sampleName]: { loading: true } };
    });

    try {
      if (previewMode === 'llm') {
        const response = await getDatasetSampleContent(datasetId, sample.id);
        setPreviewByFile((state) => ({
          ...state,
          [sampleName]: { loading: false, textContent: response.content },
        }));
      } else {
        const response = await previewSample(datasetId, sample.id);
        setPreviewByFile((state) => ({
          ...state,
          [sampleName]: { loading: false, url: response.presigned_url },
        }));
      }
    } catch (error) {
      console.error('Failed to load preview', error);
      setPreviewByFile((state) => ({
        ...state,
        [sampleName]: { loading: false, error: '预览加载失败' },
      }));
    }
  }, []);

  const loadProject = useCallback(async () => {
    if (!annotationId || Number.isNaN(annotationNumericId)) {
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const annotation = await getAnnotation(annotationNumericId);
      if (annotation.annotation_type !== AnnotationType.LLM && annotation.annotation_type !== AnnotationType.MLLM) {
        message.error('当前项目不是 LLM / MLLM 标注项目');
        navigate('/annotations', { replace: true });
        return;
      }
      if (!annotation.dataset_id) {
        message.error('当前标注项目未绑定数据集');
        navigate('/annotations', { replace: true });
        return;
      }

      const [datasetDetail, sampleResult, recordResult] = await Promise.all([
        getDataset(annotation.dataset_id),
        getDatasetSamples(annotation.dataset_id, 1, 500, 'conversation'),
        getAnnotationRecords(annotation.id, 1, 500),
      ]);

      const samples = sampleResult?.items || [];
      const recordMap = new Map(
        (recordResult?.items || []).filter((record) => record.sample_item_id !== null).map((record) => [record.sample_item_id, record.content]),
      );
      const initialEntriesBySample: ConversationEntriesBySample = {};
      samples.forEach((sample) => {
        const recordContent = recordMap.get(sample.id);
        initialEntriesBySample[sample.id] = recordContent
          ? parseConversationAnnotationContent(JSON.stringify(recordContent))
          : createEmptyConversationAnnotationEntry();
      });

      setProject(annotation);
      setDataset(datasetDetail);
      setSampleItems(samples);
      setEntriesBySample(initialEntriesBySample);
      setSavedBySample(initialEntriesBySample);
      setPreviewByFile({});
      setActiveSampleId(null);
      setFocusedSampleId(null);
      setModalOpen(false);
      setCreateSampleOpen(false);
      setNewSampleName('');
      setPage(1);
    } catch (error) {
      console.error('Failed to load conversation annotation project', error);
      message.error('加载标注项目失败');
    } finally {
      setLoading(false);
    }
  }, [annotationId, annotationNumericId, navigate]);

  useEffect(() => {
    void loadProject();
  }, [loadProject]);

  const sourceSampleIds = useMemo(() => new Set(
    sampleItems.filter((sample) => sample.asset_id).map((sample) => sample.id),
  ), [sampleItems]);

  const filteredFiles = useMemo(() => (
    sampleItems.filter((sample) => !keyword || getSampleDisplayName(sample).toLowerCase().includes(keyword.toLowerCase()))
  ), [getSampleDisplayName, sampleItems, keyword]);

  const pagedFiles = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filteredFiles.slice(start, start + PAGE_SIZE);
  }, [filteredFiles, page]);

  useEffect(() => {
    if (!dataset?.id) return;
    const targetSamples = new Map(pagedFiles.filter((sample) => sample.asset_id).map((sample) => [sample.id, sample]));
    const activeSample = activeSampleId ? sampleItems.find((sample) => sample.id === activeSampleId) : undefined;
    if (activeSample?.asset_id) {
      targetSamples.set(activeSample.id, activeSample);
    }
    targetSamples.forEach((sample) => {
      void loadSamplePreview(dataset.id, sample, mode);
    });
  }, [activeSampleId, dataset?.id, loadSamplePreview, mode, pagedFiles, sampleItems]);

  useEffect(() => {
    const maxPage = Math.max(1, Math.ceil(filteredFiles.length / PAGE_SIZE));
    if (page > maxPage) setPage(maxPage);
  }, [filteredFiles.length, page]);

  const rows: ConversationFileRow[] = useMemo(() => (
    pagedFiles.map((sample) => {
      const current = entriesBySample[sample.id] || createEmptyConversationAnnotationEntry();
      const saved = savedBySample[sample.id] || createEmptyConversationAnnotationEntry();
      return {
        sampleItemId: sample.id,
        fileName: getSampleDisplayName(sample),
        messageCount: current.messages.length,
        dirty: JSON.stringify(current) !== JSON.stringify(saved),
        source: sourceSampleIds.has(sample.id) ? 'dataset' : 'manual',
      };
    })
  ), [entriesBySample, getSampleDisplayName, pagedFiles, savedBySample, sourceSampleIds]);

  useEffect(() => {
    if (rows.length === 0) {
      setFocusedSampleId(null);
      return;
    }
    if (!focusedSampleId || !rows.some((row) => row.sampleItemId === focusedSampleId)) {
      setFocusedSampleId(rows[0].sampleItemId);
    }
  }, [focusedSampleId, rows]);

  const dirtyCount = useMemo(() => (
    sampleItems.reduce((count, sample) => {
      const current = JSON.stringify(entriesBySample[sample.id] || createEmptyConversationAnnotationEntry());
      const saved = JSON.stringify(savedBySample[sample.id] || createEmptyConversationAnnotationEntry());
      return current === saved ? count : count + 1;
    }, 0)
  ), [entriesBySample, sampleItems, savedBySample]);

  const activeSample = activeSampleId ? sampleItems.find((sample) => sample.id === activeSampleId) : undefined;
  const activeFileName = activeSample ? getSampleDisplayName(activeSample) : null;
  const activeEntry = activeSampleId ? entriesBySample[activeSampleId] || createEmptyConversationAnnotationEntry() : createEmptyConversationAnnotationEntry();
  const activeSaved = activeSampleId ? savedBySample[activeSampleId] || createEmptyConversationAnnotationEntry() : createEmptyConversationAnnotationEntry();
  const activeDirty = JSON.stringify(activeEntry) !== JSON.stringify(activeSaved);
  const activeIndex = activeSampleId ? filteredFiles.findIndex((sample) => sample.id === activeSampleId) : -1;

  const openEditor = (sampleItemId: number) => {
    const sample = sampleItems.find((item) => item.id === sampleItemId);
    if (!sample) return;
    setActiveSampleId(sampleItemId);
    setFocusedSampleId(sampleItemId);
    setDraftRole('user');
    setDraftContent('');
    setModalOpen(true);
    if (dataset?.id && sample.asset_id) {
      void loadSamplePreview(dataset.id, sample, mode);
    }
  };

  const openRelativeEditor = (offset: -1 | 1) => {
    if (activeIndex < 0) return;
    const nextSample = filteredFiles[activeIndex + offset];
    if (!nextSample) return;
    openEditor(nextSample.id);
  };

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const tagName = target?.tagName?.toLowerCase();
      const isTyping = tagName === 'input' || tagName === 'textarea' || target?.isContentEditable;
      if (isTyping) return;

      if (modalOpen) {
        if (event.key === 'ArrowLeft') {
          event.preventDefault();
          openRelativeEditor(-1);
          return;
        }
        if (event.key === 'ArrowRight') {
          event.preventDefault();
          openRelativeEditor(1);
        }
        return;
      }

      if (rows.length === 0) return;
      const currentIndex = rows.findIndex((row) => row.sampleItemId === focusedSampleId);
      const safeIndex = currentIndex >= 0 ? currentIndex : 0;

      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setFocusedSampleId(rows[Math.min(rows.length - 1, safeIndex + 1)].sampleItemId);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setFocusedSampleId(rows[Math.max(0, safeIndex - 1)].sampleItemId);
      } else if (event.key === 'Enter') {
        event.preventDefault();
        openEditor(rows[safeIndex].sampleItemId);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeIndex, filteredFiles, focusedSampleId, modalOpen, rows]);

  const buildRecordContent = (entry: ReturnType<typeof createEmptyConversationAnnotationEntry>) => (
    JSON.parse(serializeConversationAnnotationContent(mode, entry)) as Record<string, unknown>
  );

  const buildSavePayload = (sample: SampleItem, entry: ReturnType<typeof createEmptyConversationAnnotationEntry>) => ({
    sample_item_id: sample.id,
    content: buildRecordContent(entry),
    status: 'saved',
  });

  const saveCurrentSample = async (sampleItemId: number) => {
    if (!project) return;
    const sample = sampleItems.find((item) => item.id === sampleItemId);
    if (!sample) return;
    const displayName = sample ? getSampleDisplayName(sample) : String(sampleItemId);
    try {
      const entry = entriesBySample[sampleItemId] || createEmptyConversationAnnotationEntry();
      await saveAnnotationRecord(project.id, buildSavePayload(sample, entry));
      setSavedBySample((state) => ({ ...state, [sampleItemId]: entry }));
      message.success(`已保存 ${displayName}`);
    } catch (error) {
      console.error('Failed to save conversation annotation', error);
      message.error(`保存失败: ${displayName}`);
    }
  };

  const saveAll = async () => {
    if (!project) return;
    setSaving(true);
    try {
      for (const sample of sampleItems) {
        const entry = entriesBySample[sample.id] || createEmptyConversationAnnotationEntry();
        const current = JSON.stringify(entry);
        const saved = JSON.stringify(savedBySample[sample.id] || createEmptyConversationAnnotationEntry());
        if (current === saved) continue;
        await saveAnnotationRecord(project.id, buildSavePayload(sample, entry));
      }
      setSavedBySample(entriesBySample);
      message.success('全部对话标注已保存');
    } catch (error) {
      console.error('Failed to save all conversation annotations', error);
      message.error('批量保存失败');
    } finally {
      setSaving(false);
    }
  };

  const addMessage = () => {
    const content = draftContent.trim();
    if (!activeSampleId || !content) return;
    setEntriesBySample((state) => ({
      ...state,
      [activeSampleId]: {
        ...(state[activeSampleId] || createEmptyConversationAnnotationEntry()),
        messages: [
          ...((state[activeSampleId]?.messages) || []),
          createConversationMessage(draftRole, content),
        ],
      },
    }));
    setDraftContent('');
  };

  const deleteMessage = (messageId: string) => {
    if (!activeSampleId) return;
    setEntriesBySample((state) => ({
      ...state,
      [activeSampleId]: {
        ...(state[activeSampleId] || createEmptyConversationAnnotationEntry()),
        messages: ((state[activeSampleId]?.messages) || []).filter((item) => item.id !== messageId),
      },
    }));
  };

  const updateMessage = (messageId: string, content: string) => {
    const nextContent = content.trim();
    if (!activeSampleId || !nextContent) return;
    setEntriesBySample((state) => ({
      ...state,
      [activeSampleId]: {
        ...(state[activeSampleId] || createEmptyConversationAnnotationEntry()),
        messages: ((state[activeSampleId]?.messages) || []).map((item) => (
          item.id === messageId ? { ...item, content: nextContent } : item
        )),
      },
    }));
  };

  const updateSystemPrompt = (sampleItemId: number, systemPrompt: string) => {
    setEntriesBySample((state) => ({
      ...state,
      [sampleItemId]: {
        ...(state[sampleItemId] || createEmptyConversationAnnotationEntry()),
        systemPrompt,
      },
    }));
  };

  const createManualSample = async () => {
    if (!dataset) return;
    const sampleName = newSampleName.trim();
    if (!sampleName) {
      message.warning('请输入样本名称');
      return;
    }
    if (sampleItems.some((sample) => getSampleDisplayName(sample) === sampleName)) {
      message.warning('样本名称已存在');
      return;
    }

    try {
      const sample = await createDatasetSample(dataset.id, {
        item_type: 'conversation',
        item_key: sampleName,
        payload: { mode },
      });
      if (!sample) return;
      setSampleItems((state) => [sample, ...state]);
      setEntriesBySample((state) => ({ ...state, [sample.id]: createEmptyConversationAnnotationEntry() }));
      setSavedBySample((state) => ({ ...state, [sample.id]: createEmptyConversationAnnotationEntry() }));
      setCreateSampleOpen(false);
      setNewSampleName('');
      setPage(1);
      setActiveSampleId(sample.id);
      setFocusedSampleId(sample.id);
      setDraftRole('user');
      setDraftContent('');
      setModalOpen(true);
    } catch (error) {
      console.error('Failed to create conversation sample', error);
      message.error('创建样本失败');
    }
  };

  if (!annotationId || Number.isNaN(annotationNumericId)) {
    return <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Title level={4} type="secondary">无效的标注项目</Title></div>;
  }

  if (loading) {
    return <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Spin size="large" tip="正在加载标注工作台..." /></div>;
  }

  if (!project || !dataset) {
    return <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Empty description="标注项目不存在" /></div>;
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f6f8fb', padding: 24 }}>
      <Space direction="vertical" size={20} style={{ width: '100%' }}>
        <Card styles={{ body: { padding: 20 } }} style={{ borderRadius: 20, borderColor: '#e8ebf2' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
            <div>
              <Space size={12} align="center">
                <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/annotations')}>返回</Button>
                <Tag color={mode === 'llm' ? 'geekblue' : 'purple'}>{mode.toUpperCase()}</Tag>
                <Tag color="blue">{dataset.name}</Tag>
                <Tag color="default">{DataTypeLabels[dataset.data_type] ?? '未知类型'}</Tag>
              </Space>
              <Title level={3} style={{ margin: '16px 0 8px' }}>{project.name}</Title>
            </div>
            <Space size={12} wrap align="start">
              <Card size="small" style={{ minWidth: 140, borderRadius: 16, background: '#fafbff' }}>
                <Text type="secondary">数据条目</Text>
                <div style={{ fontSize: 24, fontWeight: 700 }}>{sampleItems.length}</div>
              </Card>
              <Card size="small" style={{ minWidth: 140, borderRadius: 16, background: '#fffdf7' }}>
                <Text type="secondary">未保存</Text>
                <div style={{ fontSize: 24, fontWeight: 700, color: dirtyCount > 0 ? '#d46b08' : '#389e0d' }}>{dirtyCount}</div>
              </Card>
            </Space>
          </div>
        </Card>

        <Card styles={{ body: { padding: 20 } }} style={{ borderRadius: 20, borderColor: '#e8ebf2' }}>
          <Space wrap>
            <Input.Search allowClear placeholder="按文件名搜索" value={keyword} onChange={(e) => setKeyword(e.target.value)} style={{ width: 280 }} />
            <Button icon={<PlusOutlined />} onClick={() => setCreateSampleOpen(true)}>新建样本</Button>
            <Button icon={<ReloadOutlined />} onClick={() => void loadProject()}>刷新</Button>
            <Button type="primary" icon={<SaveOutlined />} onClick={() => void saveAll()} loading={saving} disabled={dirtyCount === 0}>保存全部</Button>
          </Space>
        </Card>

        {rows.length === 0 ? (
          <Card style={{ borderRadius: 20, borderColor: '#e8ebf2' }}>
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无样本" />
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateSampleOpen(true)} style={{ width: 'fit-content' }}>
                新建样本
              </Button>
            </Space>
          </Card>
        ) : (
            <ConversationFileListCard
              rows={rows}
              mode={mode}
              focusedSampleItemId={focusedSampleId}
              total={filteredFiles.length}
              page={page}
              pageSize={PAGE_SIZE}
              onPageChange={setPage}
              onOpen={openEditor}
              onFocus={setFocusedSampleId}
            />
        )}
      </Space>

      <ConversationEditorModal
        open={modalOpen}
        activeFileName={activeFileName}
        activeEntry={activeEntry}
        activeDirty={activeDirty}
        activeIndex={activeIndex}
        totalCount={filteredFiles.length}
        hasSourceFile={activeSampleId ? sourceSampleIds.has(activeSampleId) : false}
        mode={mode}
        preview={activeFileName ? previewByFile[activeFileName] : undefined}
        draftRole={draftRole}
        draftContent={draftContent}
        onCancel={() => setModalOpen(false)}
        onDraftRoleChange={setDraftRole}
        onDraftContentChange={setDraftContent}
        onUpdateSystemPrompt={(value) => {
          if (!activeSampleId) return;
          updateSystemPrompt(activeSampleId, value);
        }}
        onUpdateMessage={updateMessage}
        onDeleteMessage={deleteMessage}
        onAddMessage={addMessage}
        onSaveCurrent={() => {
          if (!activeSampleId) return;
          void saveCurrentSample(activeSampleId);
        }}
        onOpenPrevious={() => openRelativeEditor(-1)}
        onOpenNext={() => openRelativeEditor(1)}
      />

      <Modal
        title="新建样本"
        open={createSampleOpen}
        onOk={createManualSample}
        onCancel={() => {
          setCreateSampleOpen(false);
          setNewSampleName('');
        }}
        okText="创建"
        cancelText="取消"
      >
        <div style={{ marginTop: 16 }}>
          <Input
            placeholder={mode === 'llm' ? '输入样本名称，例如 sample-001' : '输入样本名称，例如 image-note-001'}
            value={newSampleName}
            onChange={(e) => setNewSampleName(e.target.value)}
            onPressEnter={createManualSample}
          />
        </div>
      </Modal>
    </div>
  );
};

export default ConversationAnnotationPage;
