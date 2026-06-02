import React from 'react';
import { Button, Empty, List, Spin, Tag, Typography } from 'antd';
import { FileImageOutlined, LeftOutlined, PlusOutlined, RightOutlined } from '@ant-design/icons';
import { useAnnotationCollaborationStore } from '../../../stores/annotationCollaborationStore';
import { useAnnotationStore } from '../../../stores/annotationStore';
import { useDatasetStore } from '../../../stores/datasetStore';
import { getSampleItemName } from '../../../utils/sampleItem';

const { Text } = Typography;

function getAssignmentStatusLabel(status?: string, hasRecord?: boolean) {
  if (hasRecord) return { label: '已保存', color: 'success' };
  if (status === 'in_progress') return { label: '标注中', color: 'processing' };
  if (status === 'assigned') return { label: '已领取', color: 'default' };
  return { label: '未开始', color: 'default' };
}

const CollaborationFileList: React.FC = () => {
  const itemRefs = React.useRef<Record<number, HTMLDivElement | null>>({});
  const {
    sampleItems,
    annotationRecords,
    currentSampleIndex,
    loadSampleAtIndex,
    loading,
    samplePage,
    samplePageSize,
    totalSamples,
  } = useDatasetStore();
  const { modified } = useAnnotationStore();
  const { saveCurrentAnnotation } = useDatasetStore();
  const {
    assignments,
    collaborator,
    stats,
    claimMore,
    loadAssignedPage,
    loading: collaborationLoading,
  } = useAnnotationCollaborationStore();

  const totalPages = Math.max(1, Math.ceil(totalSamples / samplePageSize));
  const currentGlobalIndex = currentSampleIndex >= 0
    ? (samplePage - 1) * samplePageSize + currentSampleIndex + 1
    : 0;
  const assignmentMap = React.useMemo(
    () => new Map(assignments.map((item) => [item.sample_item_id, item])),
    [assignments],
  );
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
    if (modified) {
      await saveCurrentAnnotation();
    }
    await loadSampleAtIndex(index);
  };

  return (
    <div style={{ width: 220, display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '8px 12px', borderBottom: '1px solid #f0f0f0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
          <span style={{ fontWeight: 600 }}>协作样本</span>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {totalSamples > 0 ? `${currentGlobalIndex}/${totalSamples}` : '0/0'}
          </Text>
        </div>
        <div style={{ marginTop: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
          <Text type="secondary" ellipsis style={{ fontSize: 12, minWidth: 0 }}>
            {collaborator?.display_name || '未分配'}
          </Text>
          <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
            {stats ? `${stats.completed}/${stats.total}` : ''}
          </Text>
        </div>
      </div>

      <div style={{ padding: 8, borderBottom: '1px solid #f0f0f0' }}>
        <Button
          block
          size="small"
          icon={<PlusOutlined />}
          loading={collaborationLoading}
          onClick={() => void claimMore()}
        >
          领取下一批
        </Button>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {loading && sampleItems.length === 0 ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
            <Spin />
          </div>
        ) : sampleItems.length === 0 ? (
          <Empty description="暂无已领取样本" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ marginTop: 40 }} />
        ) : (
          <List
            size="small"
            dataSource={sampleItems}
            renderItem={(item, index) => {
              const sampleName = getSampleItemName(item);
              const isActive = index === currentSampleIndex;
              const status = getAssignmentStatusLabel(
                assignmentMap.get(item.id)?.status,
                recordSampleIds.has(item.id),
              );
              return (
                <div
                  key={item.id}
                  ref={(node) => {
                    itemRefs.current[index] = node;
                  }}
                >
                  <List.Item
                    style={{
                      padding: '6px 10px',
                      cursor: 'pointer',
                      background: isActive ? '#e6f7ff' : 'transparent',
                      borderLeft: isActive ? '3px solid #1890ff' : '3px solid transparent',
                    }}
                    onClick={() => void handleClick(index)}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, width: '100%', minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
                        <FileImageOutlined style={{ color: isActive ? '#1890ff' : '#999', flexShrink: 0 }} />
                        <Text
                          ellipsis={{ tooltip: sampleName }}
                          style={{ fontSize: 12, color: isActive ? '#1890ff' : undefined, flex: 1, minWidth: 0 }}
                        >
                          {sampleName}
                        </Text>
                      </div>
                      <Tag color={status.color} style={{ margin: 0, width: 'fit-content' }}>
                        {status.label}
                      </Tag>
                    </div>
                  </List.Item>
                </div>
              );
            }}
          />
        )}
      </div>

      {totalSamples > 0 && (
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
            onClick={() => void loadAssignedPage(samplePage - 1, 0)}
          />
          <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
            {samplePage}/{totalPages} 页
          </Text>
          <Button
            size="small"
            icon={<RightOutlined />}
            disabled={samplePage >= totalPages || loading}
            onClick={() => void loadAssignedPage(samplePage + 1, 0)}
          />
        </div>
      )}
    </div>
  );
};

export default CollaborationFileList;
