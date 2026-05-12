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
  LeftOutlined,
  RightOutlined,
  ReloadOutlined,
  SaveOutlined,
  TagsOutlined,
} from '@ant-design/icons';
import { getAnnotation, getAnnotationRecords, saveAnnotationRecord, updateAnnotation } from '../../../api/annotation';
import { getDataset, getDatasetSamples, previewSample } from '../../../api/dataset';
import { AnnotationType, type AnnotationProject, type Dataset, type SampleItem, getClassColor } from '../../../types';
import { buildClassificationRecordContent, getRecordClassIds } from '../../../utils/annotationRecordContent';
import { parseAnnotationClasses } from '../../../utils/annotationClasses';
import { normalizeClassificationLabelIds } from '../../../utils/classification';
import { getSampleItemName, isImageSampleItem } from '../../../utils/sampleItem';
import { useUnsavedChangesGuard } from '../../../hooks/useUnsavedChangesGuard';
import { showApiError } from '../../../utils/apiError';

const { Title, Text } = Typography;

interface PreviewState {
  loading: boolean;
  url?: string;
  error?: string;
}

interface TableRow {
  sampleItemId: number;
  sampleName: string;
  selected: number[];
  dirty: boolean;
}

const PAGE_SIZE = 12;
const API_BATCH_SIZE = 500;
const THUMB_WIDTH = 92;
const THUMB_HEIGHT = 68;

async function loadAllDatasetSamples(datasetId: number): Promise<SampleItem[]> {
  let page = 1;
  let totalPages = 1;
  const items: SampleItem[] = [];

  while (page <= totalPages) {
    const response = await getDatasetSamples(datasetId, page, API_BATCH_SIZE);
    items.push(...(response.items || []));
    totalPages = response.pages || 1;
    page += 1;
  }

  return items;
}

async function loadAllAnnotationRecords(annotationId: number) {
  let page = 1;
  let totalPages = 1;
  const items: Array<{ sample_item_id: number; content: Record<string, unknown> | null }> = [];

  while (page <= totalPages) {
    const response = await getAnnotationRecords(annotationId, page, API_BATCH_SIZE);
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
  const [sampleItems, setSampleItems] = useState<SampleItem[]>([]);
  const [classes, setClasses] = useState<string[]>([]);
  const [selectedBySample, setSelectedBySample] = useState<Record<number, number[]>>({});
  const [savedBySample, setSavedBySample] = useState<Record<number, number[]>>({});
  const [previewBySample, setPreviewBySample] = useState<Record<number, PreviewState>>({});
  const [keyword, setKeyword] = useState('');
  const [classFilter, setClassFilter] = useState<number | 'all'>('all');
  const [page, setPage] = useState(1);
  const [newClassName, setNewClassName] = useState('');
  const [activeSampleId, setActiveSampleId] = useState<number | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [focusedSampleId, setFocusedSampleId] = useState<number | null>(null);

  const annotationNumericId = Number(annotationId);

  const loadPreview = useCallback(async (datasetId: number, sample: SampleItem) => {
    setPreviewBySample((state) => {
      const current = state[sample.id];
      if (current?.loading || current?.url) return state;
      return { ...state, [sample.id]: { loading: true } };
    });

    try {
      const response = await previewSample(datasetId, sample.id);
      setPreviewBySample((state) => ({
        ...state,
        [sample.id]: { loading: false, url: response.presigned_url },
      }));
    } catch (error) {
      console.error('Failed to load preview', error);
      setPreviewBySample((state) => ({
        ...state,
        [sample.id]: { loading: false, error: '预览加载失败' },
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
      setClasses(parseAnnotationClasses(annotation.classes));

      if (!annotation.dataset_id) {
        setDataset(null);
        setSampleItems([]);
        setSelectedBySample({});
        setSavedBySample({});
        return;
      }

      const [datasetDetail, samplesResult, recordsResult] = await Promise.all([
        getDataset(annotation.dataset_id),
        loadAllDatasetSamples(annotation.dataset_id),
        loadAllAnnotationRecords(annotation.id),
      ]);

      const imageSamples = (samplesResult || []).filter(isImageSampleItem);
      const recordMap = new Map(
        (recordsResult || []).map((record) => [record.sample_item_id, getRecordClassIds(record.content)]),
      );
      const initialSelectedBySample: Record<number, number[]> = {};
      imageSamples.forEach((sample) => {
        initialSelectedBySample[sample.id] = recordMap.get(sample.id) || [];
      });

      setDataset(datasetDetail);
      setSampleItems(imageSamples);
      setSelectedBySample(initialSelectedBySample);
      setSavedBySample(initialSelectedBySample);
      setPreviewBySample({});
      setPage(1);
      setActiveSampleId(null);
      setModalOpen(false);
    } catch (error) {
      console.error('Failed to load classification annotation project', error);
      showApiError(error, '加载分类标注项目失败');
    } finally {
      setLoading(false);
    }
  }, [annotationId, annotationNumericId, navigate]);

  useEffect(() => {
    void loadProject();
  }, [loadProject]);

  const filteredSamples = useMemo(() => {
    return sampleItems.filter((sample) => {
      const sampleName = getSampleItemName(sample);
      const matchesKeyword = !keyword || sampleName.toLowerCase().includes(keyword.toLowerCase());
      const selected = selectedBySample[sample.id] || [];
      const matchesClass = classFilter === 'all' || selected.includes(classFilter);
      return matchesKeyword && matchesClass;
    });
  }, [classFilter, keyword, sampleItems, selectedBySample]);

  const pagedSamples = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filteredSamples.slice(start, start + PAGE_SIZE);
  }, [filteredSamples, page]);

  useEffect(() => {
    if (!dataset?.id) return;
    pagedSamples.forEach((sample) => {
      void loadPreview(dataset.id, sample);
    });
  }, [dataset?.id, loadPreview, pagedSamples]);

  useEffect(() => {
    const maxPage = Math.max(1, Math.ceil(filteredSamples.length / PAGE_SIZE));
    if (page > maxPage) setPage(maxPage);
  }, [filteredSamples.length, page]);

  const dirtyCount = useMemo(() => {
    return sampleItems.reduce((count, sample) => {
      const current = normalizeClassificationLabelIds(selectedBySample[sample.id] || []);
      const saved = normalizeClassificationLabelIds(savedBySample[sample.id] || []);
      return JSON.stringify(current) === JSON.stringify(saved) ? count : count + 1;
    }, 0);
  }, [sampleItems, savedBySample, selectedBySample]);
  const classesDirty = useMemo(
    () => JSON.stringify(classes) !== JSON.stringify(parseAnnotationClasses(project?.classes)),
    [classes, project?.classes],
  );
  useUnsavedChangesGuard(dirtyCount > 0 || classesDirty);

  const activeSample = activeSampleId ? sampleItems.find((sample) => sample.id === activeSampleId) : undefined;
  const activeSampleName = activeSample ? getSampleItemName(activeSample) : null;
  const activeSelected = activeSampleId ? selectedBySample[activeSampleId] || [] : [];
  const activeSaved = activeSampleId ? savedBySample[activeSampleId] || [] : [];
  const activeDirty = JSON.stringify(normalizeClassificationLabelIds(activeSelected)) !== JSON.stringify(normalizeClassificationLabelIds(activeSaved));
  const activeIndex = activeSampleId ? filteredSamples.findIndex((sample) => sample.id === activeSampleId) : -1;
  const canOpenPrev = activeIndex > 0;
  const canOpenNext = activeIndex >= 0 && activeIndex < filteredSamples.length - 1;

  const toggleSampleLabel = (sampleId: number, classId: number, checked: boolean) => {
    setSelectedBySample((state) => {
      const current = state[sampleId] || [];
      const next = checked
        ? normalizeClassificationLabelIds([...current, classId])
        : current.filter((item) => item !== classId);
      return { ...state, [sampleId]: next };
    });
  };

  const openEditor = (sampleId: number) => {
    const sample = sampleItems.find((item) => item.id === sampleId);
    if (!sample) return;
    setActiveSampleId(sampleId);
    setFocusedSampleId(sampleId);
    setModalOpen(true);
    if (dataset?.id) void loadPreview(dataset.id, sample);
  };

  const openRelativeEditor = (offset: -1 | 1) => {
    if (activeIndex < 0) return;
    const nextSample = filteredSamples[activeIndex + offset];
    if (!nextSample) return;
    openEditor(nextSample.id);
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
      showApiError(error, '新增类别失败');
    }
  };

  const saveSampleLabels = async (sampleId: number) => {
    if (!project) return;
    const sample = sampleItems.find((item) => item.id === sampleId);
    const sampleName = sample ? getSampleItemName(sample) : String(sampleId);
    const classIds = normalizeClassificationLabelIds(selectedBySample[sampleId] || []);

    try {
      await saveAnnotationRecord(project.id, {
        sample_item_id: sampleId,
        content: buildClassificationRecordContent(classIds),
        status: 'saved',
      });
      setSavedBySample((state) => ({ ...state, [sampleId]: classIds }));
      message.success(`已保存 ${sampleName}`);
    } catch (error) {
      console.error('Failed to save classification sample', error);
      showApiError(error, `保存失败: ${sampleName}`);
    }
  };

  const saveAll = async () => {
    if (!project) return;
    setSaving(true);
    try {
      for (const sample of sampleItems) {
        const current = normalizeClassificationLabelIds(selectedBySample[sample.id] || []);
        const saved = normalizeClassificationLabelIds(savedBySample[sample.id] || []);
        if (JSON.stringify(current) === JSON.stringify(saved)) continue;
        await saveAnnotationRecord(project.id, {
          sample_item_id: sample.id,
          content: buildClassificationRecordContent(current),
          status: 'saved',
        });
      }
      setSavedBySample(
        sampleItems.reduce<Record<number, number[]>>((acc, sample) => {
          acc[sample.id] = normalizeClassificationLabelIds(selectedBySample[sample.id] || []);
          return acc;
        }, {}),
      );
      message.success('分类标注已全部保存');
    } catch (error) {
      console.error('Failed to save all classification annotations', error);
      showApiError(error, '批量保存失败');
    } finally {
      setSaving(false);
    }
  };

  const renderThumb = (sample: SampleItem, large = false) => {
    const preview = previewBySample[sample.id];
    const width = large ? 320 : THUMB_WIDTH;
    const height = large ? 240 : THUMB_HEIGHT;
    const sampleName = getSampleItemName(sample);

    if (!preview || preview.loading) {
      return <Skeleton.Image active style={{ width, height }} />;
    }
    if (preview.error || !preview.url) {
      return (
        <div style={{ width, height, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5', borderRadius: 8 }}>
          <Text type="secondary">无预览</Text>
        </div>
      );
    }

    return (
      <Image
        src={preview.url}
        alt={sampleName}
        preview={false}
        style={{ width, height, objectFit: 'cover', borderRadius: 10, background: '#f5f5f5', display: 'block' }}
      />
    );
  };

  const rows: TableRow[] = useMemo(() => {
    return pagedSamples.map((sample) => {
      const selected = normalizeClassificationLabelIds(selectedBySample[sample.id] || []);
      const saved = normalizeClassificationLabelIds(savedBySample[sample.id] || []);
      return {
        sampleItemId: sample.id,
        sampleName: getSampleItemName(sample),
        selected,
        dirty: JSON.stringify(selected) !== JSON.stringify(saved),
      };
    });
  }, [pagedSamples, savedBySample, selectedBySample]);

  useEffect(() => {
    if (rows.length === 0) {
      setFocusedSampleId(null);
      return;
    }
    if (!focusedSampleId || !rows.some((row) => row.sampleItemId === focusedSampleId)) {
      setFocusedSampleId(rows[0].sampleItemId);
    }
  }, [focusedSampleId, rows]);

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
  }, [focusedSampleId, modalOpen, rows, filteredSamples, activeIndex]);

  const columns: ColumnsType<TableRow> = [
    {
      title: '样本',
      dataIndex: 'sampleName',
      key: 'sampleName',
      render: (_, row) => (
        <Space direction="vertical" size={4}>
          <Text strong>{row.sampleName}</Text>
          <Space size={8} wrap>
            <Tag color="default" style={{ marginInlineEnd: 0 }}>Sample #{row.sampleItemId}</Tag>
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
              <Tag key={`${row.sampleItemId}-${classId}`} color={getClassColor(classId)} icon={<TagsOutlined />}>
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
      render: (_, row) => {
        const sample = sampleItems.find((item) => item.id === row.sampleItemId);
        return sample ? renderThumb(sample) : null;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 144,
      align: 'right',
      render: (_, row) => (
        <Space>
          <Button icon={<EyeOutlined />} onClick={(event) => { event.stopPropagation(); openEditor(row.sampleItemId); }}>
            标注
          </Button>
          <Button
            type="primary"
            ghost
            icon={<SaveOutlined />}
            disabled={!row.dirty}
            onClick={(event) => {
              event.stopPropagation();
              void saveSampleLabels(row.sampleItemId);
            }}
          >
            保存
          </Button>
        </Space>
      ),
    },
  ];

  if (!annotationId || Number.isNaN(annotationNumericId)) {
    return <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f6f8fb' }}><Title level={4} type="secondary">无效的分类标注项目</Title></div>;
  }

  if (loading) {
    return <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f6f8fb' }}><Spin size="large" tip="正在加载分类标注页面..." /></div>;
  }

  if (!project) {
    return <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f6f8fb' }}><Empty description="分类标注项目不存在" /></div>;
  }

  if (dataset && dataset.data_type !== 0) {
    return (
      <div style={{ minHeight: '100vh', padding: 32, background: '#f6f8fb' }}>
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/annotations')}>
            返回标注项目
          </Button>
          <Alert type="info" showIcon message="当前分类页面先支持图像分类" description="这个独立分类工作台已与图像检测/分割页面解耦，后续可以在此基础上继续扩展文本分类等场景。" />
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
                <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/annotations')}>返回</Button>
                <Tag color="green" style={{ marginInlineEnd: 0 }}>图像分类</Tag>
                <Tag color="blue" style={{ marginInlineEnd: 0 }}>{dataset?.name || '未绑定数据集'}</Tag>
              </Space>
              <Title level={3} style={{ margin: '16px 0 8px' }}>{project.name}</Title>
            </div>
            <Space size={12} wrap align="start">
              <Card size="small" style={{ minWidth: 140, borderRadius: 16, background: '#fafbff' }}>
                <Text type="secondary">样本数量</Text>
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
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
              <Space wrap>
                <Input.Search allowClear placeholder="按样本名搜索" value={keyword} onChange={(e) => setKeyword(e.target.value)} style={{ width: 280 }} />
                <Select
                  value={classFilter}
                  onChange={(value) => setClassFilter(value)}
                  style={{ width: 220 }}
                  options={[
                    { label: '全部标签状态', value: 'all' },
                    ...classes.map((className, index) => ({ label: className, value: index })),
                  ]}
                />
              </Space>
              <Space wrap>
                <Input.Search placeholder="新增类别" value={newClassName} onChange={(e) => setNewClassName(e.target.value)} onSearch={(value) => void addClass(value)} enterButton="添加" style={{ width: 260 }} />
                <Button icon={<ReloadOutlined />} onClick={() => void loadProject()}>刷新</Button>
                <Button type="primary" icon={<SaveOutlined />} onClick={() => void saveAll()} loading={saving} disabled={dirtyCount === 0}>保存全部</Button>
              </Space>
            </div>

            {classes.length === 0 ? (
              <Alert type="warning" showIcon message="当前还没有分类类别" description="请先新增类别" />
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
          {filteredSamples.length === 0 ? (
            <div style={{ padding: 48 }}>
              <Empty description="没有符合条件的图像样本" />
            </div>
          ) : (
            <>
              <Table<TableRow>
                rowKey="sampleItemId"
                columns={columns}
                dataSource={rows}
                pagination={false}
                onRow={(record) => ({
                  onClick: () => openEditor(record.sampleItemId),
                  onMouseEnter: () => setFocusedSampleId(record.sampleItemId),
                  style: {
                    cursor: 'pointer',
                    background: focusedSampleId === record.sampleItemId ? '#f5f8ff' : undefined,
                  },
                })}
              />
              <div style={{ display: 'flex', justifyContent: 'center', padding: '20px 24px 24px' }}>
                <Pagination current={page} pageSize={PAGE_SIZE} total={filteredSamples.length} onChange={setPage} showSizeChanger={false} showTotal={(totalValue) => `共 ${totalValue} 个样本`} />
              </div>
            </>
          )}
        </Card>
      </Space>

      <Modal
        title={activeSampleName ? `分类标注: ${activeSampleName}` : '分类标注'}
        open={modalOpen}
        width={860}
        onCancel={() => setModalOpen(false)}
        footer={
          <Space>
            <Button icon={<LeftOutlined />} disabled={!canOpenPrev} onClick={() => openRelativeEditor(-1)}>上一张</Button>
            <Button icon={<RightOutlined />} disabled={!canOpenNext} onClick={() => openRelativeEditor(1)}>下一张</Button>
            <Button onClick={() => setModalOpen(false)}>关闭</Button>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              disabled={!activeSampleId || !activeDirty}
              onClick={() => {
                if (activeSampleId) void saveSampleLabels(activeSampleId);
              }}
            >
              保存当前
            </Button>
          </Space>
        }
      >
        {activeSample ? (
          <div style={{ display: 'grid', gridTemplateColumns: '340px minmax(0, 1fr)', gap: 24 }}>
            <div>
              <div style={{ marginBottom: 12 }}>{renderThumb(activeSample, true)}</div>
              <Space size={8} wrap>
                <Tag color="default">Sample #{activeSample.id}</Tag>
                {activeDirty ? <Tag color="warning">未保存</Tag> : <Tag color="success">已保存</Tag>}
              </Space>
            </div>
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              <Text strong>选择类别</Text>
              {classes.length === 0 ? (
                <Alert type="warning" showIcon message="请先新增类别" />
              ) : (
                <Space direction="vertical" size={10} style={{ width: '100%' }}>
                  {classes.map((className, index) => (
                    <Checkbox
                      key={className}
                      checked={activeSelected.includes(index)}
                      onChange={(event) => toggleSampleLabel(activeSample.id, index, event.target.checked)}
                    >
                      <Tag color={getClassColor(index)} style={{ marginInlineEnd: 8 }}>{className}</Tag>
                    </Checkbox>
                  ))}
                </Space>
              )}
            </Space>
          </div>
        ) : (
          <Empty description="未选择样本" />
        )}
      </Modal>
    </div>
  );
};

export default ClassificationAnnotationPage;
