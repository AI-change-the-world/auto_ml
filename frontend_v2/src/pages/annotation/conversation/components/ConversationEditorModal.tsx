import React, { useEffect, useState } from 'react';
import { CloseOutlined, EditOutlined, LeftOutlined, PlusOutlined, RightOutlined, SaveOutlined } from '@ant-design/icons';
import { Button, Empty, Image, Input, Modal, Select, Space, Tag, Typography } from 'antd';
import type {
  ConversationAnnotationEntry,
  ConversationAnnotationMode,
  ConversationMessageRole,
} from '../../../../utils/conversationAnnotation';
import type { PreviewState } from '../types';
import './ConversationEditorModal.css';

const { Text } = Typography;
const PRIMARY_COLOR = '#165DFF';
const USER_COLOR = '#0E9F6E';
const ASSISTANT_COLOR = '#3B82F6';
const PANEL_BORDER = '#E5E7EB';
const SURFACE_BG = '#F8FAFC';

interface Props {
  open: boolean;
  activeFileName: string | null;
  activeEntry: ConversationAnnotationEntry;
  activeDirty: boolean;
  activeIndex: number;
  totalCount: number;
  hasSourceFile: boolean;
  mode: ConversationAnnotationMode;
  preview?: PreviewState;
  draftRole: ConversationMessageRole;
  draftContent: string;
  onCancel: () => void;
  onDraftRoleChange: (value: ConversationMessageRole) => void;
  onDraftContentChange: (value: string) => void;
  onUpdateSystemPrompt: (value: string) => void;
  onUpdateMessage: (messageId: string, content: string) => void;
  onDeleteMessage: (messageId: string) => void;
  onAddMessage: () => void;
  onSaveCurrent: () => void;
  onOpenPrevious: () => void;
  onOpenNext: () => void;
}

function renderPreview(
  preview: PreviewState | undefined,
  mode: ConversationAnnotationMode,
  fileName: string,
): React.ReactNode {
  if (!preview) return null;

  if (preview.loading) {
    return <div style={{ width: '100%', minHeight: 220, borderRadius: 18, background: '#eff4fb' }} />;
  }

  if (preview.error) {
    return (
      <div
        style={{
          width: '100%',
          minHeight: 220,
          borderRadius: 18,
          background: '#eff4fb',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Text type="secondary">{preview.error}</Text>
      </div>
    );
  }

  if (mode === 'llm') {
    if (!preview.textContent) return null;
    return (
      <div
        style={{
          width: '100%',
          minHeight: 220,
          maxHeight: 280,
          overflow: 'auto',
          borderRadius: 18,
          border: `1px solid ${PANEL_BORDER}`,
          background: '#ffffff',
          padding: 18,
          whiteSpace: 'pre-wrap',
          lineHeight: 1.7,
          color: '#1f2937',
        }}
      >
        {preview.textContent}
      </div>
    );
  }

  if (!preview.url) return null;
  return (
    <Image
      src={preview.url}
      alt={fileName}
      preview={false}
      style={{ width: '100%', maxHeight: 360, objectFit: 'contain', borderRadius: 18, background: '#fff' }}
    />
  );
}

const sectionStyle: React.CSSProperties = {
  paddingTop: 20,
  borderTop: `1px solid ${PANEL_BORDER}`,
};

const ConversationEditorModal: React.FC<Props> = ({
  open,
  activeFileName,
  activeEntry,
  activeDirty,
  activeIndex,
  totalCount,
  hasSourceFile,
  mode,
  preview,
  draftRole,
  draftContent,
  onCancel,
  onDraftRoleChange,
  onDraftContentChange,
  onUpdateSystemPrompt,
  onUpdateMessage,
  onDeleteMessage,
  onAddMessage,
  onSaveCurrent,
  onOpenPrevious,
  onOpenNext,
}) => {
  const canOpenPrevious = activeIndex > 0;
  const canOpenNext = activeIndex >= 0 && activeIndex < totalCount - 1;
  const previewNode = activeFileName ? renderPreview(preview, mode, activeFileName) : null;
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingMessageContent, setEditingMessageContent] = useState('');

  useEffect(() => {
    setEditingMessageId(null);
    setEditingMessageContent('');
  }, [activeFileName, open]);

  const startEditingMessage = (messageId: string, content: string) => {
    setEditingMessageId(messageId);
    setEditingMessageContent(content);
  };

  const cancelEditingMessage = () => {
    setEditingMessageId(null);
    setEditingMessageContent('');
  };

  const saveEditingMessage = () => {
    const content = editingMessageContent.trim();
    if (!editingMessageId) return;
    if (!content) {
      cancelEditingMessage();
      return;
    }
    onUpdateMessage(editingMessageId, editingMessageContent);
    cancelEditingMessage();
  };

  return (
    <Modal
      title={null}
      open={open}
      width={980}
      onCancel={onCancel}
      style={{ top: 24 }}
      styles={{
        body: {
          padding: 0,
          background: SURFACE_BG,
          borderRadius: 24,
          overflow: 'hidden',
        },
        footer: {
          marginTop: 0,
          padding: '16px 24px 20px',
          borderTop: `1px solid ${PANEL_BORDER}`,
          background: '#fff',
        },
      }}
      footer={
        <Space>
          <Button icon={<LeftOutlined />} disabled={!canOpenPrevious} onClick={onOpenPrevious}>
            上一条
          </Button>
          <Button icon={<RightOutlined />} disabled={!canOpenNext} onClick={onOpenNext}>
            下一条
          </Button>
          <Button onClick={onCancel}>关闭</Button>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={onSaveCurrent}
            disabled={!activeFileName || !activeDirty}
            style={{
              background: PRIMARY_COLOR,
              borderColor: PRIMARY_COLOR,
              color: '#ffffff',
              fontWeight: 500,
            }}
          >
            保存当前
          </Button>
        </Space>
      }
    >
      {activeFileName ? (
        <div>
          <div
            style={{
              padding: '22px 24px 20px',
              background: 'linear-gradient(180deg, #ffffff 0%, #f4f8ff 100%)',
              borderBottom: `1px solid ${PANEL_BORDER}`,
            }}
          >
            <div style={{ fontSize: 20, fontWeight: 700, color: '#1f2937', lineHeight: 1.2 }}>
              对话内容标注
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginTop: 14 }}>
              <Tag bordered={false} style={{ marginInlineEnd: 0, borderRadius: 999, paddingInline: 12, background: '#e8f1ff', color: PRIMARY_COLOR }}>
                {activeFileName}
              </Tag>
              {hasSourceFile ? (
                <Tag bordered={false} style={{ marginInlineEnd: 0, borderRadius: 999, paddingInline: 12, background: '#f3f4f6', color: '#374151' }}>
                  原始
                </Tag>
              ) : (
                <Tag bordered={false} style={{ marginInlineEnd: 0, borderRadius: 999, paddingInline: 12, background: '#eef2ff', color: '#5b21b6' }}>
                  手动
                </Tag>
              )}
              <Tag
                bordered={false}
                style={{
                  marginInlineEnd: 0,
                  borderRadius: 999,
                  paddingInline: 12,
                  background: activeDirty ? '#fff7e8' : '#edfdf3',
                  color: activeDirty ? '#d97706' : '#059669',
                }}
              >
                {activeDirty ? '未保存' : '已保存'}
              </Tag>
            </div>
          </div>

          <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div
              style={{
                background: '#fff',
                border: `1px solid ${PANEL_BORDER}`,
                borderRadius: 20,
                padding: 18,
              }}
            >
              <div style={{ fontSize: 13, fontWeight: 600, color: '#1f2937', marginBottom: 10 }}>
                System Prompt
              </div>
              <Input.TextArea
                rows={4}
                placeholder={mode === 'llm' ? '输入当前样本的 system prompt' : '输入当前样本的 VL / MLLM system prompt'}
                value={activeEntry.systemPrompt}
                onChange={(event) => onUpdateSystemPrompt(event.target.value)}
                style={{ borderRadius: 14 }}
              />
            </div>

            {previewNode ? (
              <div style={sectionStyle}>
                <div
                  style={{
                    background: '#fff',
                    border: `1px solid ${PANEL_BORDER}`,
                    borderRadius: 20,
                    padding: 18,
                  }}
                >
                  {previewNode}
                </div>
              </div>
            ) : null}

            <div style={sectionStyle}>
              <div
                style={{
                  background: '#fff',
                  border: `1px solid ${PANEL_BORDER}`,
                  borderRadius: 20,
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    padding: '14px 18px',
                    borderBottom: `1px solid ${PANEL_BORDER}`,
                    background: '#f9fafb',
                    fontSize: 13,
                    fontWeight: 600,
                    color: '#1f2937',
                  }}
                >
                  对话内容
                </div>
                <div
                  style={{
                    minHeight: 320,
                    maxHeight: 440,
                    overflowY: 'auto',
                    padding: 20,
                    background: '#ffffff',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 14,
                  }}
                >
                  {activeEntry.messages.length === 0 ? (
                    <div style={{ minHeight: 260, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="空白对话" />
                    </div>
                  ) : (
                    activeEntry.messages.map((item) => (
                      <div
                        key={item.id}
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: item.role === 'user' ? 'flex-end' : 'flex-start',
                          gap: 8,
                        }}
                      >
                        {editingMessageId === item.id ? (
                          <div
                            style={{
                              padding: 14,
                              borderRadius: 18,
                              border: `1px solid ${item.role === 'user' ? USER_COLOR : ASSISTANT_COLOR}`,
                              background: '#ffffff',
                              boxShadow: '0 8px 18px rgba(15, 23, 42, 0.08)',
                              width: '100%',
                              maxWidth: '85%',
                            }}
                          >
                            <Input.TextArea
                              autoSize={{ minRows: 3, maxRows: 8 }}
                              value={editingMessageContent}
                              onChange={(event) => setEditingMessageContent(event.target.value)}
                              style={{ borderRadius: 12 }}
                              onBlur={saveEditingMessage}
                              onPressEnter={(event) => {
                                if (!event.shiftKey) {
                                  event.preventDefault();
                                  saveEditingMessage();
                                }
                              }}
                            />
                          </div>
                        ) : (
                          <div
                            style={{
                              padding: '13px 15px',
                              borderRadius: item.role === 'user' ? '18px 18px 6px 18px' : '18px 18px 18px 6px',
                              color: '#fff',
                              background: item.role === 'user' ? USER_COLOR : ASSISTANT_COLOR,
                              whiteSpace: 'pre-wrap',
                              lineHeight: 1.7,
                              boxShadow: '0 8px 18px rgba(15, 23, 42, 0.08)',
                              width: 'fit-content',
                              maxWidth: '85%',
                              wordBreak: 'break-word',
                            }}
                          >
                            {item.content}
                          </div>
                        )}
                        <div className="conversation-message-actions" style={{ justifyContent: item.role === 'user' ? 'flex-end' : 'flex-start' }}>
                          <Tag
                            bordered={false}
                            style={{
                              marginInlineEnd: 0,
                              borderRadius: 999,
                              paddingInline: 10,
                              background: item.role === 'user' ? '#e7f8f1' : '#eaf2ff',
                              color: item.role === 'user' ? USER_COLOR : ASSISTANT_COLOR,
                            }}
                          >
                            {item.role === 'user' ? '用户' : '助手'}
                          </Tag>
                          <button
                            type="button"
                            className="conversation-message-action"
                            onClick={() => startEditingMessage(item.id, item.content)}
                          >
                            <EditOutlined />
                            <span>编辑</span>
                          </button>
                          <button
                            type="button"
                            className="conversation-message-action conversation-message-action--delete"
                            onClick={() => onDeleteMessage(item.id)}
                          >
                            <CloseOutlined />
                            <span>删除</span>
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            <div style={sectionStyle}>
              <div
                style={{
                  background: '#fff',
                  border: `1px solid ${PANEL_BORDER}`,
                  borderRadius: 20,
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    padding: '14px 18px',
                    borderBottom: `1px solid ${PANEL_BORDER}`,
                    background: '#f9fafb',
                    fontSize: 13,
                    fontWeight: 600,
                    color: '#1f2937',
                  }}
                >
                  添加对话
                </div>
                <div style={{ padding: 18 }}>
                  <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Select
                        value={draftRole}
                        onChange={(value) => onDraftRoleChange(value)}
                        style={{ width: 120 }}
                        options={[
                          { label: '用户', value: 'user' },
                          { label: '助手', value: 'assistant' },
                        ]}
                      />
                      <button
                        type="button"
                        className="conversation-add-button"
                        onClick={onAddMessage}
                        disabled={!draftContent.trim()}
                      >
                        <PlusOutlined />
                        <span>添加</span>
                      </button>
                    </Space>
                    <Input.TextArea
                      rows={4}
                      placeholder={draftRole === 'user' ? '输入用户内容' : '输入助手内容'}
                      value={draftContent}
                      onChange={(event) => onDraftContentChange(event.target.value)}
                      style={{ borderRadius: 14 }}
                      onPressEnter={(event) => {
                        if (!event.shiftKey) {
                          event.preventDefault();
                          onAddMessage();
                        }
                      }}
                    />
                  </Space>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </Modal>
  );
};

export default ConversationEditorModal;
