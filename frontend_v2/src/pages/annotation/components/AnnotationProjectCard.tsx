import React from 'react';
import {
  BorderOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  DeploymentUnitOutlined,
  GatewayOutlined,
  MessageOutlined,
  PictureOutlined,
  RobotOutlined,
  SettingOutlined,
  TagsOutlined,
} from '@ant-design/icons';
import type { TFunction } from 'i18next';
import type { AnnotationProject, AnnotationTypeModel } from '../../../types';

const colorMap: Record<string, { bg: string; fg: string }> = {
  blue: { bg: '#eef2ff', fg: '#4f6ef7' },
  green: { bg: '#f0fdf4', fg: '#16a34a' },
  orange: { bg: '#fff7ed', fg: '#ea580c' },
  purple: { bg: '#faf5ff', fg: '#9333ea' },
  geekblue: { bg: '#eef2ff', fg: '#1d4ed8' },
  cyan: { bg: '#ecfeff', fg: '#0891b2' },
};

export const parseAnnotationClasses = (rawClasses: string | null): string[] => {
  if (!rawClasses) return [];
  try {
    const parsed = JSON.parse(rawClasses);
    if (Array.isArray(parsed)) {
      return parsed.map((item) => String(item).trim()).filter(Boolean);
    }
  } catch {
    return rawClasses.split(/[;；,，]/).map((item) => item.trim()).filter(Boolean);
  }
  return [];
};

export const renderAnnotationTypeIcon = (
  iconKey: string | undefined,
  color = '#a5b4fc',
  size = 28,
) => {
  const iconStyle = { fontSize: size, color };
  switch (iconKey) {
    case 'bbox':
      return <BorderOutlined style={iconStyle} />;
    case 'classification':
      return <PictureOutlined style={iconStyle} />;
    case 'polygon':
      return <GatewayOutlined style={iconStyle} />;
    case 'mllm':
      return <RobotOutlined style={iconStyle} />;
    case 'llm':
      return <MessageOutlined style={iconStyle} />;
    case 'pose':
      return <DeploymentUnitOutlined style={iconStyle} />;
    default:
      return <TagsOutlined style={iconStyle} />;
  }
};

interface AnnotationProjectCardProps {
  annotation: AnnotationProject;
  typeModel?: AnnotationTypeModel;
  unknownLabel: string;
  t: TFunction<'annotation'>;
  onOpen: (annotation: AnnotationProject) => void;
  onEditClasses: (event: React.MouseEvent, annotation: AnnotationProject) => void;
  onDelete: (event: React.MouseEvent, annotationId: number) => void;
}

const AnnotationProjectCard: React.FC<AnnotationProjectCardProps> = ({
  annotation,
  typeModel,
  unknownLabel,
  t,
  onOpen,
  onEditClasses,
  onDelete,
}) => {
  const color = colorMap[typeModel?.color ?? 'blue'] || colorMap.blue;
  const classes = parseAnnotationClasses(annotation.classes);

  return (
    <div
      key={annotation.id}
      onClick={() => onOpen(annotation)}
      style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, overflow: 'hidden', cursor: 'pointer', transition: 'box-shadow 0.2s' }}
      onMouseEnter={(event) => { event.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.06)'; }}
      onMouseLeave={(event) => { event.currentTarget.style.boxShadow = 'none'; }}
    >
      <div style={{ height: 90, background: 'linear-gradient(135deg, #eef2ff, #e8dff5)', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
        {renderAnnotationTypeIcon(typeModel?.iconKey)}
        <div style={{ position: 'absolute', top: 8, right: 8, display: 'flex', gap: 4 }}>
          {typeModel?.supportsClasses && (
            <button
              onClick={(event) => onEditClasses(event, annotation)}
              style={{
                width: 28,
                height: 28,
                borderRadius: 6,
                background: 'rgba(255,255,255,0.8)',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#666',
                fontSize: 13,
              }}
              title="编辑类别"
            >
              <SettingOutlined />
            </button>
          )}
          <button
            onClick={(event) => onDelete(event, annotation.id)}
            style={{
              width: 28,
              height: 28,
              borderRadius: 6,
              background: 'rgba(255,255,255,0.8)',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#999',
              fontSize: 13,
            }}
          >
            <DeleteOutlined />
          </button>
        </div>
      </div>
      <div style={{ padding: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: '#111', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{annotation.name}</span>
          <span style={{ fontSize: 11, padding: '1px 8px', background: color.bg, color: color.fg, borderRadius: 999, flexShrink: 0 }}>
            {typeModel?.label ?? unknownLabel}
          </span>
        </div>
        {typeModel?.supportsClasses && classes.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
            {classes.slice(0, 5).map((className, index) => (
              <span key={`${annotation.id}-${className}-${index}`} style={{ padding: '1px 6px', background: '#f5f5f5', color: '#666', fontSize: 11, borderRadius: 4 }}>{className}</span>
            ))}
            {classes.length > 5 && <span style={{ fontSize: 11, color: '#bbb' }}>+{classes.length - 5}</span>}
          </div>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, color: '#999' }}>
          {typeModel?.supportsClasses && <span>{t('classCount', { count: classes.length })}</span>}
          <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <ClockCircleOutlined /> {new Date(annotation.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>
    </div>
  );
};

export default AnnotationProjectCard;
