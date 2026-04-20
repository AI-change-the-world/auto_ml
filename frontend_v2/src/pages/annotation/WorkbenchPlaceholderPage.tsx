import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Result } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';

interface Props {
  title: string;
  subtitle: string;
}

const WorkbenchPlaceholderPage: React.FC<Props> = ({ title, subtitle }) => {
  const navigate = useNavigate();
  const { annotationId } = useParams<{ annotationId: string }>();

  return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#fff' }}>
      <Result
        status="info"
        title={title}
        subTitle={subtitle}
        extra={[
          <Button
            key="back"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(annotationId ? `/annotations/${annotationId}/label/image` : '/annotations')}
          >
            返回当前可用工作台
          </Button>,
        ]}
      />
    </div>
  );
};

export default WorkbenchPlaceholderPage;
