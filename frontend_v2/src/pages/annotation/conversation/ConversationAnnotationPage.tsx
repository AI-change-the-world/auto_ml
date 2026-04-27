import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Card, Empty, Input, Modal, Space, Spin, Tag, Typography, message } from 'antd';
import { ArrowLeftOutlined, PlusOutlined, ReloadOutlined, SaveOutlined } from '@ant-design/icons';
import { getAnnotation, saveAnnotationFile } from '../../../api/annotation';
import { getDataset, getDatasetFileContent, previewFile } from '../../../api/dataset';
import { AnnotationType, type AnnotationProject, type Dataset, DataTypeLabels } from '../../../types';
import { isImageFileName, isTextFileName } from '../../../utils/file';
import {
  buildConversationAnnotationFileName,
  createEmptyConversationAnnotationEntry,
  createConversationMessage,
  parseConversationAnnotationFileName,
  parseConversationAnnotationContent,
  serializeConversationAnnotationContent,
  type ConversationAnnotationMode,
} from '../../../utils/conversationAnnotation';
import { loadAllAnnotationFiles, loadAllDatasetFiles } from './data';
import ConversationEditorModal from './components/ConversationEditorModal';
import ConversationFileListCard from './components/ConversationFileListCard';
import type { ConversationEntriesByFile, ConversationFileRow, PreviewState } from './types';

const { Title, Text } = Typography;

const PAGE_SIZE = 12;

const ConversationAnnotationPage: React.FC = () => {
  const { annotationId } = useParams<{ annotationId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [project, setProject] = useState<AnnotationProject | null>(null);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [sourceFiles, setSourceFiles] = useState<Array<{ id: number; file_name: string }>>([]);
  const [sampleFiles, setSampleFiles] = useState<Array<{ id: number; file_name: string }>>([]);
  const [entriesByFile, setEntriesByFile] = useState<ConversationEntriesByFile>({});
  const [savedByFile, setSavedByFile] = useState<ConversationEntriesByFile>({});
  const [previewByFile, setPreviewByFile] = useState<Record<string, PreviewState>>({});
  const [keyword, setKeyword] = useState('');
  const [page, setPage] = useState(1);
  const [activeFileName, setActiveFileName] = useState<string | null>(null);
  const [focusedFileName, setFocusedFileName] = useState<string | null>(null);
  const [draftRole, setDraftRole] = useState<'user' | 'assistant'>('user');
  const [draftContent, setDraftContent] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [createSampleOpen, setCreateSampleOpen] = useState(false);
  const [newSampleName, setNewSampleName] = useState('');

  const annotationNumericId = Number(annotationId);
  const mode: ConversationAnnotationMode = project?.annotation_type === AnnotationType.LLM ? 'llm' : 'mllm';
  const allowedFileNames = useMemo(() => new Set(
    sourceFiles
      .filter((file) => mode === 'llm' ? isTextFileName(file.file_name) : isImageFileName(file.file_name))
      .map((file) => file.file_name),
  ), [sourceFiles, mode]);

  const loadFilePreview = useCallback(async (datasetId: number, fileName: string, previewMode: ConversationAnnotationMode) => {
    setPreviewByFile((state) => {
      const current = state[fileName];
      if (current?.loading || current?.url || current?.textContent) return state;
      return { ...state, [fileName]: { loading: true } };
    });

    try {
      if (previewMode === 'llm') {
        const response = await getDatasetFileContent(datasetId, fileName);
        setPreviewByFile((state) => ({
          ...state,
          [fileName]: { loading: false, textContent: response.content },
        }));
      } else {
        const response = await previewFile(datasetId, fileName);
        setPreviewByFile((state) => ({
          ...state,
          [fileName]: { loading: false, url: response.presigned_url },
        }));
      }
    } catch (error) {
      console.error('Failed to load preview', error);
      setPreviewByFile((state) => ({
        ...state,
        [fileName]: { loading: false, error: '预览加载失败' },
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

      const [datasetDetail, datasetResult, annotationResult] = await Promise.all([
        getDataset(annotation.dataset_id),
        loadAllDatasetFiles(annotation.dataset_id),
        loadAllAnnotationFiles(annotation.id),
      ]);

      const allowedFiles = datasetResult.filter((file) => (
        annotation.annotation_type === AnnotationType.LLM
          ? isTextFileName(file.file_name)
          : isImageFileName(file.file_name)
      ));
      const annotationMap = new Map(
        annotationResult.map((file) => [file.file_name, parseConversationAnnotationContent(file.content)]),
      );
      const initialEntriesByFile: ConversationEntriesByFile = {};

      allowedFiles.forEach((file) => {
        initialEntriesByFile[file.file_name] = annotationMap.get(buildConversationAnnotationFileName(file.file_name)) || createEmptyConversationAnnotationEntry();
      });
      annotationResult.forEach((file) => {
        const sampleName = parseConversationAnnotationFileName(file.file_name);
        if (!sampleName || initialEntriesByFile[sampleName]) return;
        initialEntriesByFile[sampleName] = parseConversationAnnotationContent(file.content);
      });

      setProject(annotation);
      setDataset(datasetDetail);
      const mergedFileNames = new Set<string>([
        ...allowedFiles.map((file) => file.file_name),
        ...Object.keys(initialEntriesByFile),
      ]);
      setSourceFiles(allowedFiles);
      setSampleFiles(Array.from(mergedFileNames).map((fileName, index) => ({ id: -(index + 1), file_name: fileName })));
      setEntriesByFile(initialEntriesByFile);
      setSavedByFile(initialEntriesByFile);
      setPreviewByFile({});
      setActiveFileName(null);
      setFocusedFileName(null);
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

  const filteredFiles = useMemo(() => (
    sampleFiles.filter((file) => !keyword || file.file_name.toLowerCase().includes(keyword.toLowerCase()))
  ), [sampleFiles, keyword]);

  const pagedFiles = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filteredFiles.slice(start, start + PAGE_SIZE);
  }, [filteredFiles, page]);

  useEffect(() => {
    if (!dataset?.id) return;
    const targetFileNames = new Set(pagedFiles.map((file) => file.file_name));
    if (activeFileName) {
      targetFileNames.add(activeFileName);
    }
    targetFileNames.forEach((fileName) => {
      if (!allowedFileNames.has(fileName)) return;
      void loadFilePreview(dataset.id, fileName, mode);
    });
  }, [activeFileName, allowedFileNames, dataset?.id, loadFilePreview, mode, pagedFiles]);

  useEffect(() => {
    const maxPage = Math.max(1, Math.ceil(filteredFiles.length / PAGE_SIZE));
    if (page > maxPage) setPage(maxPage);
  }, [filteredFiles.length, page]);

  const rows: ConversationFileRow[] = useMemo(() => (
    pagedFiles.map((file) => {
      const current = entriesByFile[file.file_name] || createEmptyConversationAnnotationEntry();
      const saved = savedByFile[file.file_name] || createEmptyConversationAnnotationEntry();
      return {
        fileName: file.file_name,
        messageCount: current.messages.length,
        dirty: JSON.stringify(current) !== JSON.stringify(saved),
        source: allowedFileNames.has(file.file_name) ? 'dataset' : 'manual',
      };
    })
  ), [allowedFileNames, entriesByFile, pagedFiles, savedByFile]);

  useEffect(() => {
    if (rows.length === 0) {
      setFocusedFileName(null);
      return;
    }
    if (!focusedFileName || !rows.some((row) => row.fileName === focusedFileName)) {
      setFocusedFileName(rows[0].fileName);
    }
  }, [focusedFileName, rows]);

  const dirtyCount = useMemo(() => (
    sampleFiles.reduce((count, file) => {
      const current = JSON.stringify(entriesByFile[file.file_name] || createEmptyConversationAnnotationEntry());
      const saved = JSON.stringify(savedByFile[file.file_name] || createEmptyConversationAnnotationEntry());
      return current === saved ? count : count + 1;
    }, 0)
  ), [entriesByFile, sampleFiles, savedByFile]);

  const activeEntry = activeFileName ? entriesByFile[activeFileName] || createEmptyConversationAnnotationEntry() : createEmptyConversationAnnotationEntry();
  const activeSaved = activeFileName ? savedByFile[activeFileName] || createEmptyConversationAnnotationEntry() : createEmptyConversationAnnotationEntry();
  const activeDirty = JSON.stringify(activeEntry) !== JSON.stringify(activeSaved);
  const activeIndex = activeFileName ? filteredFiles.findIndex((file) => file.file_name === activeFileName) : -1;

  const openEditor = (fileName: string) => {
    setActiveFileName(fileName);
    setFocusedFileName(fileName);
    setDraftRole('user');
    setDraftContent('');
    setModalOpen(true);
    if (dataset?.id && allowedFileNames.has(fileName)) {
      void loadFilePreview(dataset.id, fileName, mode);
    }
  };

  const openRelativeEditor = (offset: -1 | 1) => {
    if (activeIndex < 0) return;
    const nextFile = filteredFiles[activeIndex + offset];
    if (!nextFile) return;
    openEditor(nextFile.file_name);
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
      const currentIndex = rows.findIndex((row) => row.fileName === focusedFileName);
      const safeIndex = currentIndex >= 0 ? currentIndex : 0;

      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setFocusedFileName(rows[Math.min(rows.length - 1, safeIndex + 1)].fileName);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setFocusedFileName(rows[Math.max(0, safeIndex - 1)].fileName);
      } else if (event.key === 'Enter') {
        event.preventDefault();
        openEditor(rows[safeIndex].fileName);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeIndex, filteredFiles, focusedFileName, modalOpen, rows]);

  const saveCurrentFile = async (fileName: string) => {
    if (!project) return;
    try {
      await saveAnnotationFile(project.id, {
        file_name: buildConversationAnnotationFileName(fileName),
        content: serializeConversationAnnotationContent(mode, entriesByFile[fileName] || createEmptyConversationAnnotationEntry()),
      });
      setSavedByFile((state) => ({ ...state, [fileName]: entriesByFile[fileName] || createEmptyConversationAnnotationEntry() }));
      message.success(`已保存 ${fileName}`);
    } catch (error) {
      console.error('Failed to save conversation annotation', error);
      message.error(`保存失败: ${fileName}`);
    }
  };

  const saveAll = async () => {
    if (!project) return;
    setSaving(true);
    try {
      for (const file of sampleFiles) {
        const current = JSON.stringify(entriesByFile[file.file_name] || createEmptyConversationAnnotationEntry());
        const saved = JSON.stringify(savedByFile[file.file_name] || createEmptyConversationAnnotationEntry());
        if (current === saved) continue;
        await saveAnnotationFile(project.id, {
          file_name: buildConversationAnnotationFileName(file.file_name),
          content: serializeConversationAnnotationContent(mode, entriesByFile[file.file_name] || createEmptyConversationAnnotationEntry()),
        });
      }
      setSavedByFile(entriesByFile);
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
    if (!activeFileName || !content) return;
    setEntriesByFile((state) => ({
      ...state,
      [activeFileName]: {
        ...(state[activeFileName] || createEmptyConversationAnnotationEntry()),
        messages: [
          ...((state[activeFileName]?.messages) || []),
          createConversationMessage(draftRole, content),
        ],
      },
    }));
    setDraftContent('');
  };

  const deleteMessage = (messageId: string) => {
    if (!activeFileName) return;
    setEntriesByFile((state) => ({
      ...state,
      [activeFileName]: {
        ...(state[activeFileName] || createEmptyConversationAnnotationEntry()),
        messages: ((state[activeFileName]?.messages) || []).filter((item) => item.id !== messageId),
      },
    }));
  };

  const updateMessage = (messageId: string, content: string) => {
    const nextContent = content.trim();
    if (!activeFileName || !nextContent) return;
    setEntriesByFile((state) => ({
      ...state,
      [activeFileName]: {
        ...(state[activeFileName] || createEmptyConversationAnnotationEntry()),
        messages: ((state[activeFileName]?.messages) || []).map((item) => (
          item.id === messageId ? { ...item, content: nextContent } : item
        )),
      },
    }));
  };

  const updateSystemPrompt = (fileName: string, systemPrompt: string) => {
    setEntriesByFile((state) => ({
      ...state,
      [fileName]: {
        ...(state[fileName] || createEmptyConversationAnnotationEntry()),
        systemPrompt,
      },
    }));
  };

  const createManualSample = () => {
    const sampleName = newSampleName.trim();
    if (!sampleName) {
      message.warning('请输入样本名称');
      return;
    }
    if (entriesByFile[sampleName]) {
      message.warning('样本名称已存在');
      return;
    }

    setSampleFiles((state) => [{ id: -(state.length + 1), file_name: sampleName }, ...state]);
    setEntriesByFile((state) => ({ ...state, [sampleName]: createEmptyConversationAnnotationEntry() }));
    setSavedByFile((state) => ({ ...state, [sampleName]: createEmptyConversationAnnotationEntry() }));
    setCreateSampleOpen(false);
    setNewSampleName('');
    setPage(1);
    openEditor(sampleName);
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
                <div style={{ fontSize: 24, fontWeight: 700 }}>{sampleFiles.length}</div>
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
            focusedFileName={focusedFileName}
            total={filteredFiles.length}
            page={page}
            pageSize={PAGE_SIZE}
            onPageChange={setPage}
            onOpen={openEditor}
            onFocus={setFocusedFileName}
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
        hasSourceFile={activeFileName ? allowedFileNames.has(activeFileName) : false}
        mode={mode}
        preview={activeFileName ? previewByFile[activeFileName] : undefined}
        draftRole={draftRole}
        draftContent={draftContent}
        onCancel={() => setModalOpen(false)}
        onDraftRoleChange={setDraftRole}
        onDraftContentChange={setDraftContent}
        onUpdateSystemPrompt={(value) => {
          if (!activeFileName) return;
          updateSystemPrompt(activeFileName, value);
        }}
        onUpdateMessage={updateMessage}
        onDeleteMessage={deleteMessage}
        onAddMessage={addMessage}
        onSaveCurrent={() => {
          if (!activeFileName) return;
          void saveCurrentFile(activeFileName);
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
