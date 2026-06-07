import React from 'react';
import { Avatar, List, Tooltip, Typography } from 'antd';
import { FileImageOutlined, UserOutlined } from '@ant-design/icons';
import type { AnnotationSampleEditor } from '../../../hooks/useAnnotationCollaborationPresence';

const { Text } = Typography;

export type AnnotationSampleStatus = 'annotated' | 'unannotated' | 'editing';

interface AnnotationSampleStatusConfig {
  status: AnnotationSampleStatus;
  label: string;
  color: string;
}

interface AnnotationSampleListItemProps {
  sampleName: string;
  active: boolean;
  status: AnnotationSampleStatusConfig;
  editors?: AnnotationSampleEditor[];
  onClick: () => void;
}

export function getAnnotationSampleStatus(hasRecord: boolean, isEditing: boolean): AnnotationSampleStatusConfig {
  if (isEditing) return { status: 'editing', label: '正在标注', color: 'processing' };
  if (hasRecord) return { status: 'annotated', label: '已标注', color: 'success' };
  return { status: 'unannotated', label: '未标注', color: 'default' };
}

function getEditorInitial(name: string) {
  return name.trim().slice(0, 1).toUpperCase();
}

function getActiveEditor(editors: AnnotationSampleEditor[]) {
  return editors.find((editor) => editor.local) || editors[0] || null;
}

function getSoftColor(color: string) {
  if (!/^#[0-9a-fA-F]{6}$/.test(color)) return '#e6f7ff';
  const red = parseInt(color.slice(1, 3), 16);
  const green = parseInt(color.slice(3, 5), 16);
  const blue = parseInt(color.slice(5, 7), 16);
  return `rgb(${Math.round(red * 0.10 + 255 * 0.90)}, ${Math.round(green * 0.10 + 255 * 0.90)}, ${Math.round(blue * 0.10 + 255 * 0.90)})`;
}

function getStatusIconColor(status: AnnotationSampleStatus, editorColor?: string) {
  if (status === 'editing' && editorColor) return editorColor;
  if (status === 'editing') return '#1677ff';
  if (status === 'annotated') return '#52c41a';
  return '#bfbfbf';
}

function getStatusTextColor(status: AnnotationSampleStatus, active: boolean, editorColor?: string) {
  if (status === 'editing' && editorColor) return editorColor;
  if (active) return '#1677ff';
  if (status === 'editing') return '#0958d9';
  if (status === 'annotated') return '#237804';
  return '#595959';
}

function getEditorsTooltip(editors: AnnotationSampleEditor[]) {
  return editors.map((editor) => `${editor.name}${editor.local ? '（我）' : ''}`).join('、');
}

const AnnotationSampleListItem: React.FC<AnnotationSampleListItemProps> = ({
  sampleName,
  active,
  status,
  editors = [],
  onClick,
}) => {
  const singleEditor = editors.length === 1 ? editors[0] : null;
  const activeEditor = getActiveEditor(editors);
  const editingColor = status.status === 'editing' ? activeEditor?.color : undefined;
  const activeBorderColor = editingColor || '#1890ff';

  return (
    <List.Item
      style={{
        padding: '6px 10px',
        cursor: 'pointer',
        background: active ? getSoftColor(activeBorderColor) : 'transparent',
        borderLeft: active ? `3px solid ${activeBorderColor}` : '3px solid transparent',
      }}
      onClick={onClick}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', minWidth: 0 }}>
        <Tooltip title={status.label}>
          <FileImageOutlined style={{ color: getStatusIconColor(status.status, editingColor), flexShrink: 0 }} />
        </Tooltip>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1, minWidth: 0 }}>
          <Text
            ellipsis={{ tooltip: sampleName }}
            style={{
              fontSize: 12,
              color: getStatusTextColor(status.status, active, editingColor),
              minWidth: 0,
              flex: 1,
            }}
          >
            {sampleName}
          </Text>
        </div>
        {editors.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', width: 24, flexShrink: 0 }}>
            {singleEditor && (
              <Tooltip title={`${singleEditor.name}${singleEditor.local ? '（我）' : ''}`}>
                <Avatar
                  size={18}
                  style={{
                    backgroundColor: singleEditor.color,
                    color: '#fff',
                    fontSize: 10,
                    lineHeight: '18px',
                    flexShrink: 0,
                  }}
                  icon={getEditorInitial(singleEditor.name) ? undefined : <UserOutlined />}
                >
                  {getEditorInitial(singleEditor.name)}
                </Avatar>
              </Tooltip>
            )}
            {editors.length > 1 && (
              <Tooltip title={getEditorsTooltip(editors)}>
                <Avatar
                  size={18}
                  style={{
                    backgroundColor: activeEditor?.color || '#595959',
                    color: '#fff',
                    fontSize: 10,
                    lineHeight: '18px',
                    flexShrink: 0,
                  }}
                >
                  {editors.length}
                </Avatar>
              </Tooltip>
            )}
          </div>
        )}
      </div>
    </List.Item>
  );
};

export default AnnotationSampleListItem;
