import React from 'react';
import { List, Typography, Spin, Empty } from 'antd';
import { FileImageOutlined } from '@ant-design/icons';
import { useDatasetStore } from '../../../stores/datasetStore';
import { useAnnotationStore } from '../../../stores/annotationStore';

const { Text } = Typography;

const FileList: React.FC = () => {
  const { datasetFiles, currentFileIndex, loadFileAtIndex, loading } = useDatasetStore();
  const { modified } = useAnnotationStore();
  const { saveCurrentAnnotation } = useDatasetStore();

  const handleClick = async (index: number) => {
    if (index === currentFileIndex) return;
    // 自动保存
    if (modified) {
      await saveCurrentAnnotation();
    }
    await loadFileAtIndex(index);
  };

  return (
    <div style={{ width: 200, display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '8px 12px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontWeight: 600 }}>文件列表</span>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {datasetFiles.length > 0 ? `${currentFileIndex + 1}/${datasetFiles.length}` : '0/0'}
        </Text>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {loading && datasetFiles.length === 0 ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
            <Spin />
          </div>
        ) : datasetFiles.length === 0 ? (
          <Empty description="暂无文件" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ marginTop: 40 }} />
        ) : (
          <List
            size="small"
            dataSource={datasetFiles}
            renderItem={(item, index) => {
              const isActive = index === currentFileIndex;
              return (
                <List.Item
                  key={item.id}
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
                      ellipsis={{ tooltip: item.file_name }}
                      style={{
                        fontSize: 12,
                        color: isActive ? '#1890ff' : undefined,
                        flex: 1,
                        minWidth: 0,
                      }}
                    >
                      {item.file_name}
                    </Text>
                  </div>
                </List.Item>
              );
            }}
          />
        )}
      </div>
    </div>
  );
};

export default FileList;
