import React, { useState } from 'react';
import { List, Button, Tag, Empty, Badge, AutoComplete, Input, Modal } from 'antd';
import {
  DeleteOutlined, EyeOutlined, EyeInvisibleOutlined,
  BorderOutlined, StarOutlined, GatewayOutlined,
} from '@ant-design/icons';
import { useAnnotationStore } from '../../../stores/annotationStore';
import { createClassificationAnnotation, getClassColor, AnnotationShape, AnnotationType } from '../../../types';
import type { Annotation, PolygonAnnotation, OBBAnnotation } from '../../../types';
import { useDatasetStore } from '../../../stores/datasetStore';
import { getAnnotationDeleteConfirmEnabled } from '../../../utils/localSettings';

const ShapeIcon: React.FC<{ shape: AnnotationShape }> = ({ shape }) => {
  switch (shape) {
    case AnnotationShape.BBox:
      return <BorderOutlined style={{ fontSize: 12, color: '#999' }} />;
    case AnnotationShape.OBB:
      return <StarOutlined style={{ fontSize: 12, color: '#999' }} />;
    case AnnotationShape.Polygon:
      return <GatewayOutlined style={{ fontSize: 12, color: '#999' }} />;
    default:
      return null;
  }
};

const getShapeInfo = (item: Annotation): string => {
  switch (item.shape) {
    case AnnotationShape.Polygon:
      return `${(item as PolygonAnnotation).points.length} pts`;
    case AnnotationShape.OBB: {
      const deg = Math.round(((item as OBBAnnotation).angle * 180) / Math.PI);
      return `${deg}°`;
    }
    default:
      return '';
  }
};

const AnnotationList: React.FC = () => {
  const {
    annotations, selectedUuid, classes,
    selectAnnotation, toggleVisibility, deleteAnnotation, updateAnnotation,
    addOrGetClassId, setDefaultClassId, addAnnotation,
  } = useAnnotationStore();
  const annotationType = useDatasetStore((s) => s.annotationProject?.annotation_type ?? AnnotationType.Detection);
  const isClassification = annotationType === AnnotationType.Classification;

  const [editingUuid, setEditingUuid] = useState<string | null>(null);
  const [editingText, setEditingText] = useState('');

  const getLabel = (classId: number) => {
    if (classId >= 0 && classId < classes.length) return classes[classId];
    return `class_${classId}`;
  };

  const startEditing = (uuid: string, classId: number) => {
    setEditingUuid(uuid);
    setEditingText(getLabel(classId));
  };

  /** 提交编辑：支持已有类别和新类别 */
  const commitEditing = (uuid: string) => {
    const text = editingText.trim();
    if (text) {
      const classId = addOrGetClassId(text);
      updateAnnotation(uuid, { classId });
      setDefaultClassId(classId); // 记住选择，下次新建用同一类别
    }
    setEditingUuid(null);
  };

  /** 下拉选项：匹配输入的已有 classes */
  const getFilteredOptions = () => {
    const search = editingText.trim().toLowerCase();
    return classes
      .map((c, _i) => ({ value: c, label: c }))
      .filter((o) => !search || o.value.toLowerCase().includes(search));
  };

  const setClassification = (className: string) => {
    const text = className.trim();
    if (!text) return;
    const classId = addOrGetClassId(text);
    if (annotations[0]) {
      updateAnnotation(annotations[0].uuid, { classId, selected: true });
      selectAnnotation(annotations[0].uuid);
    } else {
      addAnnotation(createClassificationAnnotation(classId));
    }
    setDefaultClassId(classId);
  };

  const confirmDelete = async (title: string, onDelete: () => Promise<void> | void) => {
    if (!getAnnotationDeleteConfirmEnabled()) {
      await onDelete();
      return;
    }
    Modal.confirm({
      title,
      okButtonProps: { danger: true },
      onOk: onDelete,
    });
  };

  if (isClassification) {
    const current = annotations[0];
    return (
      <div style={{ width: 240, display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ padding: '8px 12px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 600 }}>分类标签</span>
          <Badge count={current ? 1 : 0} showZero style={{ backgroundColor: '#1890ff' }} />
        </div>
        <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <AutoComplete
            style={{ width: '100%' }}
            value={editingText}
            options={getFilteredOptions()}
            onChange={(value) => setEditingText(value)}
            onSelect={(value) => {
              setEditingText(value);
              setClassification(value);
            }}
          >
            <Input
              placeholder="输入类别名或选择"
              onPressEnter={() => {
                setClassification(editingText);
              }}
            />
          </AutoComplete>

          {current ? (
            <Tag color={getClassColor(current.classId)} style={{ margin: 0, width: 'fit-content' }}>
              当前类别: {getLabel(current.classId)}
            </Tag>
          ) : (
            <Empty description="未设置分类标签" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          )}

          {classes.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {classes.map((className) => (
                <Tag
                  key={className}
                  color={current && getLabel(current.classId) === className ? getClassColor(current.classId) : 'default'}
                  style={{ cursor: 'pointer', margin: 0 }}
                  onClick={() => {
                    setEditingText(className);
                    setClassification(className);
                  }}
                >
                  {className}
                </Tag>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={{ width: 240, display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* ─── 标注列表 ─── */}
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
              const shapeInfo = getShapeInfo(item);

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
                    {/* 形状图标 */}
                    <ShapeIcon shape={item.shape} />

                    {/* 类别：点击编辑，AutoComplete 支持下拉选择 + 输入新类别 */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      {editingUuid === item.uuid ? (
                        <AutoComplete
                          size="small"
                          style={{ width: '100%' }}
                          value={editingText}
                          options={getFilteredOptions()}
                          onChange={(value) => setEditingText(value)}
                          onSelect={(value) => {
                            setEditingText(value);
                            const classId = addOrGetClassId(value);
                            updateAnnotation(item.uuid, { classId });
                            setDefaultClassId(classId);
                            setEditingUuid(null);
                          }}
                          onBlur={() => commitEditing(item.uuid)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              commitEditing(item.uuid);
                            }
                            if (e.key === 'Escape') {
                              setEditingUuid(null);
                            }
                          }}
                          autoFocus
                          open
                        >
                          <Input size="small" placeholder="输入类别名或选择" />
                        </AutoComplete>
                      ) : (
                        <Tag
                          color={color}
                          style={{ cursor: 'pointer', margin: 0 }}
                          onClick={(e) => {
                            e.stopPropagation();
                            startEditing(item.uuid, item.classId);
                          }}
                        >
                          {getLabel(item.classId)}
                        </Tag>
                      )}
                    </div>

                    {/* 形状信息 */}
                    {shapeInfo && (
                      <span style={{ fontSize: 11, color: '#999', whiteSpace: 'nowrap' }}>
                        {shapeInfo}
                      </span>
                    )}

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
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={(e) => {
                        e.stopPropagation();
                        void confirmDelete('确认删除？', () => deleteAnnotation(item.uuid));
                      }}
                    />
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
