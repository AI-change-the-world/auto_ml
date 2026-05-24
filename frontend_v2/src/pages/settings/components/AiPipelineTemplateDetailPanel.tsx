import React from 'react';
import { Button, Popconfirm, Space, Spin, Typography } from 'antd';
import type { AiPipelineTemplateDetail } from '../../../types';

const { Text } = Typography;

const safeJsonStringify = (value: unknown) => {
  if (value == null) return '';
  if (typeof value === 'string') return value;
  return JSON.stringify(value, null, 2);
};

interface AiPipelineTemplateDetailPanelProps {
  detailLoading: boolean;
  selectedTemplate: AiPipelineTemplateDetail | null;
  actionLoading: boolean;
  onEdit: () => void;
  onDisable: () => void;
  onDelete: () => void;
}

const AiPipelineTemplateDetailPanel: React.FC<AiPipelineTemplateDetailPanelProps> = ({
  detailLoading,
  selectedTemplate,
  actionLoading,
  onEdit,
  onDisable,
  onDelete,
}) => {
  if (detailLoading) {
    return (
      <div style={{ padding: 80, textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!selectedTemplate) {
    return (
      <div style={{ padding: 80, textAlign: 'center', color: '#999' }}>
        <Text type="secondary">选择左侧模板，查看当前定义和表单 schema。</Text>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
        <div>
          <div className="page-title" style={{ fontSize: 20 }}>{selectedTemplate.name}</div>
          <div className="caption-text" style={{ color: '#888', marginTop: 4 }}>{selectedTemplate.template_key}</div>
        </div>
        <Space wrap>
          <Button onClick={onEdit}>修改</Button>
          <Button
            disabled={selectedTemplate.status === 'disabled'}
            loading={actionLoading}
            onClick={onDisable}
          >
            禁用模板
          </Button>
          <Popconfirm
            title="确认删除当前模板？"
            description="已有 Binding 的模板不能删除。"
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
            onConfirm={onDelete}
          >
            <Button danger loading={actionLoading}>删除模板</Button>
          </Popconfirm>
        </Space>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 12 }}>
        {[
          { label: '场景', value: selectedTemplate.scene_type },
          { label: '输入', value: selectedTemplate.input_kind || '-' },
          { label: '输出', value: selectedTemplate.output_kind || '-' },
          { label: '状态', value: selectedTemplate.status },
        ].map((item) => (
          <div key={item.label} style={{ background: '#fafafa', borderRadius: 8, padding: 12 }}>
            <div className="caption-text" style={{ color: '#888', marginBottom: 6 }}>{item.label}</div>
            <div className="body-text-sm" style={{ color: '#111' }}>{item.value}</div>
          </div>
        ))}
      </div>

      <div>
        <div className="caption-text" style={{ color: '#888', marginBottom: 6 }}>描述</div>
        <div className="body-text-sm" style={{ color: '#333' }}>{selectedTemplate.description || '无描述'}</div>
      </div>

      {selectedTemplate.change_note ? (
        <div>
          <div className="caption-text" style={{ color: '#888', marginBottom: 6 }}>最近变更</div>
          <div className="body-text-sm" style={{ color: '#333' }}>{selectedTemplate.change_note}</div>
        </div>
      ) : null}

      <div>
        <div className="caption-text" style={{ color: '#888', marginBottom: 6 }}>Definition JSON</div>
        <pre style={{ margin: 0, padding: 12, borderRadius: 8, background: '#f8fafc', border: '1px solid #eee', overflow: 'auto', maxHeight: 220 }}>
          {safeJsonStringify(selectedTemplate.definition_json) || '{}'}
        </pre>
      </div>

      <div>
        <div className="caption-text" style={{ color: '#888', marginBottom: 6 }}>Form Schema JSON</div>
        <pre style={{ margin: 0, padding: 12, borderRadius: 8, background: '#f8fafc', border: '1px solid #eee', overflow: 'auto', maxHeight: 220 }}>
          {safeJsonStringify(selectedTemplate.form_schema_json) || '{}'}
        </pre>
      </div>
    </div>
  );
};

export default AiPipelineTemplateDetailPanel;
