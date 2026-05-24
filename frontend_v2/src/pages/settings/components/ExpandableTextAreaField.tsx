import React from 'react';
import { Button, Input, Modal } from 'antd';

interface ExpandableTextAreaFieldProps {
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  title?: string;
  rows?: number;
}

const ExpandableTextAreaField: React.FC<ExpandableTextAreaFieldProps> = ({
  value,
  onChange,
  placeholder,
  title = '文本',
  rows = 3,
}) => {
  const [open, setOpen] = React.useState(false);
  const [draft, setDraft] = React.useState('');
  const currentValue = typeof value === 'string' ? value : '';

  React.useEffect(() => {
    if (open) {
      setDraft(currentValue);
    }
  }, [currentValue, open]);

  const openEditor = () => {
    setDraft(currentValue);
    setOpen(true);
  };

  const closeEditor = () => {
    setOpen(false);
  };

  const handleSave = () => {
    onChange?.(draft);
    setOpen(false);
  };

  return (
    <>
      <div style={{ display: 'grid', gap: 6, width: '100%' }}>
        <Input.TextArea
          value={currentValue}
          placeholder={placeholder}
          rows={rows}
          readOnly
          onClick={openEditor}
          style={{ cursor: 'pointer', resize: 'none' }}
        />
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button type="link" size="small" onClick={openEditor} style={{ padding: 0 }}>
            展开编辑
          </Button>
        </div>
      </div>
      <Modal
        open={open}
        title={`编辑${title ? ` - ${title}` : ''}`}
        onCancel={closeEditor}
        onOk={handleSave}
        okText="保存"
        cancelText="取消"
        width={840}
        destroyOnClose
      >
        <Input.TextArea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={placeholder}
          rows={16}
          style={{ resize: 'vertical' }}
        />
      </Modal>
    </>
  );
};

export default ExpandableTextAreaField;
