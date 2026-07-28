import React from 'react';
import { UploadOutlined } from '@ant-design/icons';
import { Button, Modal, Upload, message } from 'antd';
import type { UploadFile } from 'antd';
import { uploadBatchAnnotationScript } from '../../../api/batchAnnotation';
import type { AiPipelineBatchScript } from '../../../types';

interface BatchScriptEditorModalProps {
  open: boolean;
  script?: AiPipelineBatchScript | null;
  onClose: () => void;
  onSubmitted: () => void;
}

const BatchScriptEditorModal: React.FC<BatchScriptEditorModalProps> = ({ open, script, onClose, onSubmitted }) => {
  const [file, setFile] = React.useState<File | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  React.useEffect(() => {
    if (open) setFile(null);
  }, [open]);

  const handleSubmit = async () => {
    if (!file) {
      message.warning('请选择 ZIP 脚本包');
      return;
    }
    setSubmitting(true);
    try {
      await uploadBatchAnnotationScript(file);
      message.success(script ? '脚本新版本已上传' : '脚本包已上传');
      onSubmitted();
      onClose();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '上传脚本失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      open={open}
      title={script ? `上传“${script.name}”新版本` : '上传脚本包'}
      onCancel={() => { if (!submitting) onClose(); }}
      onOk={() => void handleSubmit()}
      confirmLoading={submitting}
      okText="上传"
      destroyOnClose
    >
      <Upload
        accept=".zip"
        maxCount={1}
        beforeUpload={(nextFile) => { setFile(nextFile); return false; }}
        onRemove={() => setFile(null)}
        fileList={file ? [{ uid: file.name, name: file.name, status: 'done' } as UploadFile] : []}
      >
        <Button icon={<UploadOutlined />}>选择 ZIP 文件</Button>
      </Upload>
    </Modal>
  );
};

export default BatchScriptEditorModal;
