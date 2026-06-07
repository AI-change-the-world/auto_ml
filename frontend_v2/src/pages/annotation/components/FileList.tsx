import React from 'react';
import { List, Typography, Spin, Empty, Button } from 'antd';
import { LeftOutlined, RightOutlined } from '@ant-design/icons';
import { useDatasetStore } from '../../../stores/datasetStore';
import { useAnnotationStore } from '../../../stores/annotationStore';
import { getSampleItemName } from '../../../utils/sampleItem';
import type { AnnotationSampleEditor } from '../../../hooks/useAnnotationCollaborationPresence';
import AnnotationSampleListItem, { getAnnotationSampleStatus } from './AnnotationSampleListItem';

const { Text } = Typography;

interface FileListProps {
  editorsBySampleId?: Record<number, AnnotationSampleEditor[]>;
}

const FileList: React.FC<FileListProps> = ({
  editorsBySampleId = {},
}) => {
  const itemRefs = React.useRef<Record<number, HTMLDivElement | null>>({});
  const {
    sampleItems,
    annotationRecords,
    currentSampleIndex,
    loadSampleAtIndex,
    loadSamplePage,
    loading,
    samplePage,
    samplePageSize,
    totalSamples,
    pagedSamplesEnabled,
  } = useDatasetStore();
  const { modified } = useAnnotationStore();
  const { saveCurrentAnnotation } = useDatasetStore();
  const totalPages = Math.max(1, Math.ceil(totalSamples / samplePageSize));
  const currentGlobalIndex = currentSampleIndex >= 0
    ? (samplePage - 1) * samplePageSize + currentSampleIndex + 1
    : 0;
  const recordSampleIds = React.useMemo(
    () => new Set(annotationRecords.map((item) => item.sample_item_id)),
    [annotationRecords],
  );

  React.useEffect(() => {
    const activeItem = itemRefs.current[currentSampleIndex];
    if (activeItem) {
      activeItem.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  }, [currentSampleIndex, samplePage]);

  const handleClick = async (index: number) => {
    if (index === currentSampleIndex) return;
    // 自动保存
    if (modified) {
      await saveCurrentAnnotation();
    }
    await loadSampleAtIndex(index);
  };

  return (
    <div style={{ width: 200, display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '8px 12px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontWeight: 600 }}>文件列表</span>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {totalSamples > 0 ? `${currentGlobalIndex}/${totalSamples}` : '0/0'}
        </Text>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {loading && sampleItems.length === 0 ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
            <Spin />
          </div>
        ) : sampleItems.length === 0 ? (
          <Empty description="暂无文件" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ marginTop: 40 }} />
        ) : (
          <List
            size="small"
            dataSource={sampleItems}
            renderItem={(item, index) => {
              const sampleName = getSampleItemName(item);
              const isActive = index === currentSampleIndex;
              const editors = editorsBySampleId[item.id] || [];
              const status = getAnnotationSampleStatus(recordSampleIds.has(item.id), isActive);
              return (
                <div
                  key={item.id}
                  ref={(node) => {
                    itemRefs.current[index] = node;
                  }}
                >
                  <AnnotationSampleListItem
                    sampleName={sampleName}
                    active={isActive}
                    status={status}
                    editors={editors}
                    onClick={() => void handleClick(index)}
                  />
                </div>
              );
            }}
          />
        )}
      </div>

      {pagedSamplesEnabled && totalSamples > 0 && (
        <div
          style={{
            padding: '8px 10px',
            borderTop: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 8,
          }}
        >
          <Button
            size="small"
            icon={<LeftOutlined />}
            disabled={samplePage <= 1 || loading}
            onClick={() => loadSamplePage(samplePage - 1, 0)}
          />
          <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
            {samplePage}/{totalPages} 页
          </Text>
          <Button
            size="small"
            icon={<RightOutlined />}
            disabled={samplePage >= totalPages || loading}
            onClick={() => loadSamplePage(samplePage + 1, 0)}
          />
        </div>
      )}
    </div>
  );
};

export default FileList;
