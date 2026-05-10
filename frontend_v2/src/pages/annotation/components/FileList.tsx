import React from 'react';
import { List, Typography, Spin, Empty, Button } from 'antd';
import { FileImageOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons';
import { useDatasetStore } from '../../../stores/datasetStore';
import { useAnnotationStore } from '../../../stores/annotationStore';
import { getSampleItemName } from '../../../utils/sampleItem';

const { Text } = Typography;

const FileList: React.FC = () => {
  const itemRefs = React.useRef<Record<number, HTMLDivElement | null>>({});
  const {
    sampleItems,
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
              return (
                <div
                  key={item.id}
                  ref={(node) => {
                    itemRefs.current[index] = node;
                  }}
                >
                  <List.Item
                    style={{
                      padding: '6px 12px',
                      cursor: 'pointer',
                      background: isActive ? '#e6f7ff' : 'transparent',
                      borderLeft: isActive ? '3px solid #1890ff' : '3px solid transparent',
                    }}
                    onClick={() => handleClick(index)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', minWidth: 0 }}>
                      <FileImageOutlined style={{ color: isActive ? '#1890ff' : '#999', flexShrink: 0 }} />
                      <Text
                        ellipsis={{ tooltip: sampleName }}
                        style={{
                          fontSize: 12,
                          color: isActive ? '#1890ff' : undefined,
                          flex: 1,
                          minWidth: 0,
                        }}
                      >
                        {sampleName}
                      </Text>
                    </div>
                  </List.Item>
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
