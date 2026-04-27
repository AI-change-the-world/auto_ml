import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Empty,
  Image,
  Input,
  Modal,
  Pagination,
  Select,
  Skeleton,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  EyeOutlined,
  FolderOpenOutlined,
  LeftOutlined,
  RightOutlined,
  ReloadOutlined,
  SaveOutlined,
  TagsOutlined,
} from '@ant-design/icons';
import { getAnnotation, getAnnotationFiles, saveAnnotationFile, updateAnnotation } from '../../../api/annotation';
import { getDataset, getDatasetFiles, previewFile } from '../../../api/dataset';
import { AnnotationType, type AnnotationProject, type Dataset, type DatasetFile, getClassColor } from '../../../types';
import { isImageFileName } from '../../../utils/file';
import {
  buildClassificationLabelFileName,
  normalizeClassificationLabelIds,
  parseClassificationAnnotationContent,
  serializeClassificationAnnotationContent,
} from '../../../utils/classification';

const { Title, Text } = Typography;

interface PreviewState {
  loading: boolean;
  url?: string;
  error?: string;
}

interface TableRow {
  id: number;
  fileName: string;
  labelFileName: string;
  selected: number[];
  dirty: boolean;
}

const PAGE_SIZE = 12;
const API_BATCH_SIZE = 500;
const THUMB_WIDTH = 92;
const THUMB_HEIGHT = 68;

const parseProjectClasses = (raw: string | null): string[] => {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      return parsed.map((item) => String(item).trim()).filter(Boolean);
    }
  } catch {
    // ignore and fall back
  }
  return raw.split(/[,\n;；，]+/).map((item) => item.trim()).filter(Boolean);
};

async function loadAllDatasetFiles(datasetId: number): Promise<DatasetFile[]> {
  let page = 1;
  let totalPages = 1;
  const items: DatasetFile[] = [];

  while (page <= totalPages) {
    const response = await getDatasetFiles(datasetId, page, API_BATCH_SIZE);
    items.push(...(response.items || []));
    totalPages = response.pages || 1;
    page += 1;
  }

  return items;
}

async function loadAllAnnotationFiles(annotationId: number) {
  let page = 1;
  let totalPages = 1;
  const items: Array<{ file_name: string; content: string | null }> = [];

  while (page <= totalPages) {
    const response = await getAnnotationFiles(annotationId, page, API_BATCH_SIZE);
    items.push(...(response.items || []));
    totalPages = response.pages || 1;
    page += 1;
  }

  return items;
}

const ClassificationAnnotationPage: React.FC = () => {
  const { annotationId } = useParams<{ annotationId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [project, setProject] = useState<AnnotationProject | null>(null);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [datasetFiles, setDatasetFiles] = useState<DatasetFile[]>([]);
  const [classes, setClasses] = useState<string[]>([]);
  const [selectedByFile, setSelectedByFile] = useState<Record<string, number[]>>({});
  const [savedByFile, setSavedByFile] = useState<Record<string, number[]>>({});
  const [previewByFile, setPreviewByFile] = useState<Record<string, PreviewState>>({});
  const [keyword, setKeyword] = useState('');
  const [classFilter, setClassFilter] = useState<number | 'all'>('all');
  const [page, setPage] = useState(1);
  const [newClassName, setNewClassName] = useState('');
  const [activeFileName, setActiveFileName] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [focusedFileName, setFocusedFileName] = useState<string | null>(null);

  const annotationNumericId = Number(annotationId);

  const loadPreview = useCallback(async (datasetId: number, fileName: string) => {
    setPreviewByFile((state) => {
      const current = state[fileName];
      if (current?.loading || current?.url) return state;
      return {
        ...state,
        [fileName]: { loading: true },
      };
    });

    try {
      const response = await previewFile(datasetId, fileName);
      setPreviewByFile((state) => ({
        ...state,
        [fileName]: { loading: false, url: response.presigned_url },
      }));
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
      if (annotation.annotation_type !== AnnotationType.Classification) {
        message.error('当前项目不是分类标注项目');
        navigate('/annotations', { replace: true });
        return;
      }

      setProject(annotation);
      setClasses(parseProjectClasses(annotation.classes));

      if (!annotation.dataset_id) {
        setDataset(null);
        setDatasetFiles([]);
        setSelectedByFile({});
        setSavedByFile({});
        return;
      }

      const [datasetDetail, datasetResult, annotationResult] = await Promise.all([
        getDataset(annotation.dataset_id),
        loadAllDatasetFiles(annotation.dataset_id),
        loadAllAnnotationFiles(annotation.id),
      ]);

      const imageFiles = (datasetResult || []).filter((file) => isImageFileName(file.file_name));
      const annotationMap = new Map(
        (annotationResult || []).map((file) => [file.file_name, parseClassificationAnnotationContent(file.content)]),
      );
      const initialSelectedByFile: Record<string, number[]> = {};

      imageFiles.forEach((file) => {
        initialSelectedByFile[file.file_name] = annotationMap.get(buildClassificationLabelFileName(file.file_name)) || [];
      });

      setDataset(datasetDetail);
      setDatasetFiles(imageFiles);
      setSelectedByFile(initialSelectedByFile);
      setSavedByFile(initialSelectedByFile);
      setPreviewByFile({});
      setPage(1);
      setActiveFileName(null);
      setModalOpen(false);
    } catch (error) {
      console.error('Failed to load classification annotation project', error);
      message.error('加载分类标注项目失败');
    } finally {
      setLoading(false);
    }
  }, [annotationId, annotationNumericId, navigate]);

  useEffect(() => {
    void loadProject();
  }, [loadProject]);

  const filteredFiles = useMemo(() => {
    return datasetFiles.filter((file) => {
      const matchesKeyword = !keyword || file.file_name.toLowerCase().includes(keyword.toLowerCase());
      const selected = selectedByFile[file.file_name] || [];
      const matchesClass = classFilter === 'all' || selected.includes(classFilter);
      return matchesKeyword && matchesClass;
    });
  }, [classFilter, datasetFiles, keyword, selectedByFile]);

  const pagedFiles = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filteredFiles.slice(start, start + PAGE_SIZE);
  }, [filteredFiles, page]);

  useEffect(() => {
    if (!dataset?.id) return;
    pagedFiles.forEach((file) => {
      void loadPreview(dataset.id, file.file_name);
    });
  }, [dataset?.id, loadPreview, pagedFiles]);

  useEffect(() => {
    const maxPage = Math.max(1, Math.ceil(filteredFiles.length / PAGE_SIZE));
    if (page > maxPage) {
      setPage(maxPage);
    }
  }, [filteredFiles.length, page]);

  const dirtyCount = useMemo(() => {
    return datasetFiles.reduce((count, file) => {
      const current = normalizeClassificationLabelIds(selectedByFile[file.file_name] || []);
      const saved = normalizeClassificationLabelIds(savedByFile[file.file_name] || []);
      return JSON.stringify(current) === JSON.stringify(saved) ? count : count + 1;
    }, 0);
  }, [datasetFiles, savedByFile, selectedByFile]);

  const activeSelected = activeFileName ? selectedByFile[activeFileName] || [] : [];
  const activeSaved = activeFileName ? savedByFile[activeFileName] || [] : [];
  const activeDirty = JSON.stringify(normalizeClassificationLabelIds(activeSelected)) !== JSON.stringify(normalizeClassificationLabelIds(activeSaved));
  const activeIndex = activeFileName ? filteredFiles.findIndex((file) => file.file_name === activeFileName) : -1;
  const canOpenPrev = activeIndex > 0;
  const canOpenNext = activeIndex >= 0 && activeIndex < filteredFiles.length - 1;

  const toggleFileLabel = (fileName: string, classId: number, checked: boolean) => {
    setSelectedByFile((state) => {
      const current = state[fileName] || [];
      const next = checked
        ? normalizeClassificationLabelIds([...current, classId])
        : current.filter((item) => item !== classId);
      return {
        ...state,
        [fileName]: next,
      };
    });
  };

  const openEditor = (fileName: string) => {
    setActiveFileName(fileName);
    setFocusedFileName(fileName);
    setModalOpen(true);
    if (dataset?.id) {
      void loadPreview(dataset.id, fileName);
    }
  };

  const openRelativeEditor = (offset: -1 | 1) => {
    if (activeIndex < 0) return;
    const nextFile = filteredFiles[activeIndex + offset];
    if (!nextFile) return;
    openEditor(nextFile.file_name);
  };

  const addClass = async (value: string) => {
    const name = value.trim();
    if (!name || !project) return;
    if (classes.includes(name)) return;

    const nextClasses = [...classes, name];
    setClasses(nextClasses);
    setNewClassName('');
    try {
      await updateAnnotation(project.id, { classes: JSON.stringify(nextClasses) });
      setProject({ ...project, classes: JSON.stringify(nextClasses) });
      message.success(`已新增类别: ${name}`);
    } catch (error) {
      console.error('Failed to update classes', error);
      setClasses(classes);
      setNewClassName(name);
      message.error('新增类别失败');
    }
  };

  const saveFileLabels = async (fileName: string) => {
    if (!project) return;
    const classIds = normalizeClassificationLabelIds(selectedByFile[fileName] || []);
    const content = serializeClassificationAnnotationContent(classIds);

    try {
      await saveAnnotationFile(project.id, {
        file_name: buildClassificationLabelFileName(fileName),
        content,
      });
      setSavedByFile((state) => ({
        ...state,
        [fileName]: classIds,
      }));
      message.success(`已保存 ${fileName}`);
    } catch (error) {
      console.error('Failed to save classification file', error);
      message.error(`保存失败: ${fileName}`);
    }
  };

  const saveAll = async () => {
    if (!project) return;
    setSaving(true);
    try {
      for (const file of datasetFiles) {
        const current = normalizeClassificationLabelIds(selectedByFile[file.file_name] || []);
        const saved = normalizeClassificationLabelIds(savedByFile[file.file_name] || []);
        if (JSON.stringify(current) === JSON.stringify(saved)) continue;
        const content = serializeClassificationAnnotationContent(current);
        await saveAnnotationFile(project.id, {
          file_name: buildClassificationLabelFileName(file.file_name),
          content,
        });
      }
      setSavedByFile(
        datasetFiles.reduce<Record<string, number[]>>((acc, file) => {
          acc[file.file_name] = normalizeClassificationLabelIds(selectedByFile[file.file_name] || []);
          return acc;
        }, {}),
      );
      message.success('分类标注已全部保存');
    } catch (error) {
      console.error('Failed to save all classification annotations', error);
      message.error('批量保存失败');
    } finally {
      setSaving(false);
    }
  };

  const renderThumb = (fileName: string, large = false) => {
    const preview = previewByFile[fileName];
    const width = large ? 320 : THUMB_WIDTH;
    const height = large ? 240 : THUMB_HEIGHT;

    if (!preview || preview.loading) {
      return <Skeleton.Image active style={{ width, height }} />;
    }
    if (preview.error || !preview.url) {
      return (
        <div
          style={{
            width,
            height,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#f5f5f5',
            borderRadius: 8,
          }}
        >
          <Text type="secondary">无预览</Text>
        </div>
      );
    }

    return (
      <Image
        src={preview.url}
        alt={fileName}
        preview={false}
        style={{
          width,
          height,
          objectFit: 'cover',
          borderRadius: 10,
          background: '#f5f5f5',
          display: 'block',
        }}
      />
    );
  };

  const rows: TableRow[] = useMemo(() => {
    return pagedFiles.map((file) => {
      const selected = normalizeClassificationLabelIds(selectedByFile[file.file_name] || []);
      const saved = normalizeClassificationLabelIds(savedByFile[file.file_name] || []);
      return {
        id: file.id,
        fileName: file.file_name,
        labelFileName: buildClassificationLabelFileName(file.file_name),
        selected,
        dirty: JSON.stringify(selected) !== JSON.stringify(saved),
      };
    });
  }, [pagedFiles, savedByFile, selectedByFile]);

  useEffect(() => {
    if (rows.length === 0) {
      setFocusedFileName(null);
      return;
    }
    if (!focusedFileName || !rows.some((row) => row.fileName === focusedFileName)) {
      setFocusedFileName(rows[0].fileName);
    }
  }, [focusedFileName, rows]);

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
          return;
        }
        return;
      }

      if (rows.length === 0) return;
      const currentIndex = rows.findIndex((row) => row.fileName === focusedFileName);
      const safeIndex = currentIndex >= 0 ? currentIndex : 0;

      if (event.key === 'ArrowDown') {
        event.preventDefault();
        const nextIndex = Math.min(rows.length - 1, safeIndex + 1);
        setFocusedFileName(rows[nextIndex].fileName);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        const prevIndex = Math.max(0, safeIndex - 1);
        setFocusedFileName(rows[prevIndex].fileName);
      } else if (event.key === 'Enter') {
        event.preventDefault();
        openEditor(rows[safeIndex].fileName);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [focusedFileName, modalOpen, rows, filteredFiles, activeIndex]);

  const columns: ColumnsType<TableRow> = [
    {
      title: '图像',
      dataIndex: 'fileName',
      key: 'fileName',
      render: (_, row) => (
        <Space direction="vertical" size={4}>
          <Text strong>{row.fileName}</Text>
          <Space size={8} wrap>
            <Tag icon={<FolderOpenOutlined />} color="default" style={{ marginInlineEnd: 0 }}>
              {row.labelFileName}
            </Tag>
            {row.dirty ? (
              <Tag color="warning" style={{ marginInlineEnd: 0 }}>未保存</Tag>
            ) : (
              <Tag icon={<CheckCircleOutlined />} color="success" style={{ marginInlineEnd: 0 }}>已保存</Tag>
            )}
          </Space>
        </Space>
      ),
    },
    {
      title: '标签',
      key: 'labels',
      render: (_, row) => (
        <Space size={[6, 6]} wrap>
          {row.selected.length === 0 ? (
            <Text type="secondary">未选择</Text>
          ) : (
            row.selected.map((classId) => (
              <Tag key={`${row.fileName}-${classId}`} color={getClassColor(classId)} icon={<TagsOutlined />}>
                {classes[classId] ?? `class_${classId}`}
              </Tag>
            ))
          )}
        </Space>
      ),
    },
    {
      title: '缩略图',
      key: 'thumb',
      width: 132,
      align: 'right',
      render: (_, row) => renderThumb(row.fileName),
    },
    {
      title: '操作',
      key: 'action',
      width: 144,
      align: 'right',
      render: (_, row) => (
        <Space>
          <Button
            icon={<EyeOutlined />}
            onClick={(event) => {
              event.stopPropagation();
              openEditor(row.fileName);
            }}
          >
            标注
          </Button>
          <Button
            type="primary"
            ghost
            icon={<SaveOutlined />}
            disabled={!row.dirty}
            onClick={(event) => {
              event.stopPropagation();
              void saveFileLabels(row.fileName);
            }}
          >
            保存
          </Button>
        </Space>
      ),
    },
  ];

  if (!annotationId || Number.isNaN(annotationNumericId)) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f6f8fb' }}>
        <Title level={4} type="secondary">无效的分类标注项目</Title>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f6f8fb' }}>
        <Spin size="large" tip="正在加载分类标注页面..." />
      </div>
    );
  }

  if (!project) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f6f8fb' }}>
        <Empty description="分类标注项目不存在" />
      </div>
    );
  }

  if (dataset && dataset.data_type !== 0) {
    return (
      <div style={{ minHeight: '100vh', padding: 32, background: '#f6f8fb' }}>
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/annotations')}>
            返回标注项目
          </Button>
          <Alert
            type="info"
            showIcon
            message="当前分类页面先支持图像分类"
            description="这个独立分类工作台已与图像检测/分割页面解耦，后续可以在此基础上继续扩展文本分类等场景。"
          />
        </Space>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f6f8fb', padding: 24 }}>
      <Space direction="vertical" size={20} style={{ width: '100%' }}>
        <Card styles={{ body: { padding: 20 } }} style={{ borderRadius: 20, borderColor: '#e8ebf2' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
            <div>
              <Space size={12} align="center">
                <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/annotations')}>
                  返回
                </Button>
                <Tag color="green" style={{ marginInlineEnd: 0 }}>图像分类</Tag>
                <Tag color="blue" style={{ marginInlineEnd: 0 }}>{dataset?.name || '未绑定数据集'}</Tag>
              </Space>
              <Title level={3} style={{ margin: '16px 0 8px' }}>{project.name}</Title>
            </div>
            <Space size={12} wrap align="start">
              <Card size="small" style={{ minWidth: 140, borderRadius: 16, background: '#fafbff' }}>
                <Text type="secondary">图像数量</Text>
                <div style={{ fontSize: 24, fontWeight: 700 }}>{datasetFiles.length}</div>
              </Card>
              <Card size="small" style={{ minWidth: 140, borderRadius: 16, background: '#fffdf7' }}>
                <Text type="secondary">未保存</Text>
                <div style={{ fontSize: 24, fontWeight: 700, color: dirtyCount > 0 ? '#d46b08' : '#389e0d' }}>{dirtyCount}</div>
              </Card>
            </Space>
          </div>
        </Card>

        <Card styles={{ body: { padding: 20 } }} style={{ borderRadius: 20, borderColor: '#e8ebf2' }}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
              <Space wrap>
                <Input.Search
                  allowClear
                  placeholder="按文件名搜索"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  style={{ width: 280 }}
                />
                <Select
                  value={classFilter}
                  onChange={(value) => setClassFilter(value)}
                  style={{ width: 220 }}
                  options={[
                    { label: '全部标签状态', value: 'all' },
                    ...classes.map((className, index) => ({
                      label: className,
                      value: index,
                    })),
                  ]}
                />
              </Space>
              <Space wrap>
                <Input.Search
                  placeholder="新增类别"
                  value={newClassName}
                  onChange={(e) => setNewClassName(e.target.value)}
                  onSearch={(value) => void addClass(value)}
                  enterButton="添加"
                  style={{ width: 260 }}
                />
                <Button icon={<ReloadOutlined />} onClick={() => void loadProject()}>
                  刷新
                </Button>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={() => void saveAll()}
                  loading={saving}
                  disabled={dirtyCount === 0}
                >
                  保存全部
                </Button>
              </Space>
            </div>

            {classes.length === 0 ? (
              <Alert
                type="warning"
                showIcon
                message="当前还没有分类类别"
                description="请先新增类别"
              />
            ) : (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {classes.map((className, index) => (
                  <Tag key={className} color={getClassColor(index)} style={{ marginInlineEnd: 0, paddingInline: 10, lineHeight: '26px' }}>
                    {className}
                  </Tag>
                ))}
              </div>
            )}
          </Space>
        </Card>

        <Card styles={{ body: { padding: 0 } }} style={{ borderRadius: 20, borderColor: '#e8ebf2', overflow: 'hidden' }}>
          {filteredFiles.length === 0 ? (
            <div style={{ padding: 48 }}>
              <Empty description="没有符合条件的图像" />
            </div>
          ) : (
            <>
              <Table<TableRow>
                rowKey="id"
                columns={columns}
                dataSource={rows}
                pagination={false}
                onRow={(record) => ({
                  onClick: () => openEditor(record.fileName),
                  onMouseEnter: () => setFocusedFileName(record.fileName),
                  style: {
                    cursor: 'pointer',
                    background: focusedFileName === record.fileName ? '#f5f8ff' : undefined,
                  },
                })}
              />
              <div style={{ display: 'flex', justifyContent: 'center', padding: '20px 24px 24px' }}>
                <Pagination
                  current={page}
                  pageSize={PAGE_SIZE}
                  total={filteredFiles.length}
                  onChange={setPage}
                  showSizeChanger={false}
                  showTotal={(totalValue) => `共 ${totalValue} 张图像`}
                />
              </div>
            </>
          )}
        </Card>
      </Space>

      <Modal
        title={activeFileName ? `分类标注: ${activeFileName}` : '分类标注'}
        open={modalOpen}
        width={860}
        onCancel={() => setModalOpen(false)}
        footer={
          <Space>
            <Button icon={<LeftOutlined />} disabled={!canOpenPrev} onClick={() => openRelativeEditor(-1)}>
              上一张
            </Button>
            <Button icon={<RightOutlined />} disabled={!canOpenNext} onClick={() => openRelativeEditor(1)}>
              下一张
            </Button>
            <Button onClick={() => setModalOpen(false)}>关闭</Button>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              disabled={!activeFileName || !activeDirty}
              onClick={() => {
                if (activeFileName) {
                  void saveFileLabels(activeFileName);
                }
              }}
            >
              保存当前
            </Button>
          </Space>
        }
      >
        {activeFileName ? (
          <div style={{ display: 'grid', gridTemplateColumns: '340px minmax(0, 1fr)', gap: 24 }}>
            <div>
              <div style={{ marginBottom: 12 }}>{renderThumb(activeFileName, true)}</div>
              <Space size={8} wrap>
                <Tag icon={<FolderOpenOutlined />} color="default">{buildClassificationLabelFileName(activeFileName)}</Tag>
                {activeDirty ? <Tag color="warning">未保存</Tag> : <Tag color="success">已保存</Tag>}
              </Space>
            </div>
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              <div>
                <Text strong>已选标签</Text>
                <div style={{ marginTop: 10, minHeight: 36 }}>
                  <Space size={[6, 6]} wrap>
                    {activeSelected.length === 0 ? (
                      <Text type="secondary">未选择标签</Text>
                    ) : (
                      activeSelected.map((classId) => (
                        <Tag key={`${activeFileName}-active-${classId}`} color={getClassColor(classId)} icon={<TagsOutlined />}>
                          {classes[classId] ?? `class_${classId}`}
                        </Tag>
                      ))
                    )}
                  </Space>
                </div>
              </div>

              <div>
                <Text strong>标签编辑</Text>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
                    gap: 10,
                    marginTop: 12,
                  }}
                >
                  {classes.map((className, classId) => {
                    const checked = activeSelected.includes(classId);
                    return (
                      <label
                        key={`${activeFileName}-${className}`}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          padding: '12px 14px',
                          borderRadius: 14,
                          border: `1px solid ${checked ? getClassColor(classId) : '#e8ebf2'}`,
                          background: checked ? `${getClassColor(classId)}12` : '#fff',
                          cursor: 'pointer',
                        }}
                      >
                        <Checkbox
                          checked={checked}
                          onChange={(event) => toggleFileLabel(activeFileName, classId, event.target.checked)}
                        />
                        <span style={{ color: '#1f1f1f', fontSize: 13 }}>{className}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            </Space>
          </div>
        ) : (
          <Empty description="请选择一个图像条目" />
        )}
      </Modal>
    </div>
  );
};

export default ClassificationAnnotationPage;
