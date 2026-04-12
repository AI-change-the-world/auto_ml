import React, { useState } from 'react';
import { List, Button, Tag, Select, Popconfirm, Empty, Badge } from 'antd';
import { DeleteOutlined, EyeOutlined, EyeInvisibleOutlined } from '@ant-design/icons';
import { useAnnotationStore } from '../../../stores/annotationStore';
import { getClassColor } from '../../../types';

const AnnotationList: React.FC = () => {
  const {
    annotations, selectedUuid, classes,
    selectAnnotation, toggleVisibility, deleteAnnotation, updateAnnotation,
  } = useAnnotationStore();

  const [editingUuid, setEditingUuid] = useState<string | null>(null);

  const getLabel = (classId: number) => {
    if (classId >= 0 && classId < classes.length) return classes[classId];
    return classId < 0 ? 'unknown' : `class_${classId}`;
  };

  const classOptions = classes.map((c, i) => ({ label: c, value: i }));

  return (
    <div style={{ width: 240, display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '8px 12px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontWeight: 600 }}>标注列表</span>
        <Badge count={annotations.length} showZero style={{ backgroundColor: '#1890ff' }} />
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {annotations.length === 0 ? (
          <Empty description="暂无标注" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ marginTop: 40 }} />
        ) : (
          <List
            size="small"
            dataSource={annotations}
            renderItem={(item) => {
              const isSelected = item.uuid === selectedUuid;
              const color = getClassColor(item.classId);

              return (
                <List.Item
                  key={item.uuid}
                  style={{
                    padding: '6px 12px',
                    cursor: 'pointer',
                    background: isSelected ? '#e6f7ff' : 'transparent',
                    borderLeft: isSelected ? `3px solid ${color}` : '3px solid transparent',
                  }}
                  onClick={() => selectAnnotation(item.uuid)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', width: '100%', gap: 8 }}>
                    {/* 类别标签 */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      {editingUuid === item.uuid ? (
                        <Select
                          size="small"
                          style={{ width: '100%' }}
                          value={item.classId}
                          options={classOptions}
                          onChange={(value) => {
                            updateAnnotation(item.uuid, { classId: value });
                            setEditingUuid(null);
                          }}
                          onBlur={() => setEditingUuid(null)}
                          autoFocus
                          open
                        />
                      ) : (
                        <Tag
                          color={color}
                          style={{ cursor: 'pointer', margin: 0 }}
                          onDoubleClick={(e) => {
                            e.stopPropagation();
                            if (classes.length > 0) setEditingUuid(item.uuid);
                          }}
                        >
                          {getLabel(item.classId)}
                        </Tag>
                      )}
                    </div>

                    {/* 可见性按钮 */}
                    <Button
                      type="text"
                      size="small"
                      icon={item.visible ? <EyeOutlined /> : <EyeInvisibleOutlined />}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleVisibility(item.uuid);
                      }}
                      style={{ opacity: item.visible ? 1 : 0.4 }}
                    />

                    {/* 删除按钮 */}
                    <Popconfirm
                      title="确认删除？"
                      onConfirm={(e) => {
                        e?.stopPropagation();
                        deleteAnnotation(item.uuid);
                      }}
                      onCancel={(e) => e?.stopPropagation()}
                    >
                      <Button
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </Popconfirm>
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

export default AnnotationList;
