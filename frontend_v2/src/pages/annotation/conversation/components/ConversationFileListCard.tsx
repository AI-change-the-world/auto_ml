import React from 'react';
import { Button, Card, List, Pagination, Tag } from 'antd';
import { FileImageOutlined, FileTextOutlined, MessageOutlined } from '@ant-design/icons';
import type { ConversationAnnotationMode } from '../../../../utils/conversationAnnotation';
import type { ConversationFileRow } from '../types';

interface Props {
  rows: ConversationFileRow[];
  mode: ConversationAnnotationMode;
  focusedSampleItemId: number | null;
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onOpen: (sampleItemId: number) => void;
  onFocus: (sampleItemId: number) => void;
}

const ConversationFileListCard: React.FC<Props> = ({
  rows,
  mode,
  focusedSampleItemId,
  total,
  page,
  pageSize,
  onPageChange,
  onOpen,
  onFocus,
}) => {
  const accentColor = mode === 'llm' ? '#165DFF' : '#7C3AED';

  return (
    <Card
      styles={{ body: { padding: 0 } }}
      style={{
        borderRadius: 24,
        borderColor: '#e5e7eb',
        overflow: 'hidden',
        boxShadow: '0 18px 36px rgba(15, 23, 42, 0.06)',
      }}
    >
      <div
        style={{
          padding: '16px 18px',
          borderBottom: '1px solid #edf1f5',
          background: 'linear-gradient(180deg, #ffffff 0%, #f8fbff 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
        }}
      >
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#1f2937' }}>待标注样本</div>
          <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
            当前页 {rows.length} 条
          </div>
        </div>
        <div
          style={{
            padding: '6px 10px',
            borderRadius: 999,
            background: mode === 'llm' ? '#eaf2ff' : '#f2ebff',
            color: accentColor,
            fontSize: 12,
            fontWeight: 600,
          }}
        >
          {mode.toUpperCase()}
        </div>
      </div>

      <List
        split={false}
        dataSource={rows}
        renderItem={(row) => (
          <List.Item
            onClick={() => onOpen(row.sampleItemId)}
            onMouseEnter={() => onFocus(row.sampleItemId)}
            style={{
              cursor: 'pointer',
              padding: 0,
              background: focusedSampleItemId === row.sampleItemId ? '#f7fbff' : '#fff',
              borderLeft: `4px solid ${focusedSampleItemId === row.sampleItemId ? accentColor : 'transparent'}`,
              borderBottom: '1px solid #f1f5f9',
              transition: 'background 0.2s ease, border-color 0.2s ease',
            }}
          >
            <div
              style={{
                width: '100%',
                padding: '16px 18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 16,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14, minWidth: 0, flex: 1 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 14,
                    background: mode === 'llm' ? '#eaf2ff' : '#f2ebff',
                    color: accentColor,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  {mode === 'llm' ? <FileTextOutlined style={{ fontSize: 18 }} /> : <FileImageOutlined style={{ fontSize: 18 }} />}
                </div>

                <div style={{ minWidth: 0, flex: 1 }}>
                  <div
                    style={{
                      fontSize: 14,
                      fontWeight: 600,
                      color: '#111827',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {row.fileName}
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
                    <Tag
                      bordered={false}
                      color={row.source === 'manual' ? 'geekblue' : 'default'}
                      style={{ marginInlineEnd: 0, borderRadius: 999, paddingInline: 10 }}
                    >
                      {row.source === 'manual' ? '手动' : '原始'}
                    </Tag>
                    <Tag
                      bordered={false}
                      style={{
                        marginInlineEnd: 0,
                        borderRadius: 999,
                        paddingInline: 10,
                        background: '#f3f4f6',
                        color: '#374151',
                      }}
                    >
                      {row.messageCount} 条对话
                    </Tag>
                    <Tag
                      bordered={false}
                      style={{
                        marginInlineEnd: 0,
                        borderRadius: 999,
                        paddingInline: 10,
                        background: row.dirty ? '#fff7e8' : '#edfdf3',
                        color: row.dirty ? '#d97706' : '#059669',
                      }}
                    >
                      {row.dirty ? '未保存' : '已保存'}
                    </Tag>
                  </div>
                </div>
              </div>

              <Button
                type="primary"
                icon={<MessageOutlined />}
                onClick={(event) => {
                  event.stopPropagation();
                  onOpen(row.sampleItemId);
                }}
                style={{
                  height: 38,
                  borderRadius: 12,
                  paddingInline: 16,
                  background: accentColor,
                  boxShadow: 'none',
                  flexShrink: 0,
                }}
              >
                标注
              </Button>
            </div>
          </List.Item>
        )}
      />
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          padding: '18px 24px 22px',
          background: '#fbfcfe',
        }}
      >
        <Pagination current={page} pageSize={pageSize} total={total} onChange={onPageChange} showSizeChanger={false} showTotal={(totalValue) => `共 ${totalValue} 条`} />
      </div>
    </Card>
  );
};

export default ConversationFileListCard;
