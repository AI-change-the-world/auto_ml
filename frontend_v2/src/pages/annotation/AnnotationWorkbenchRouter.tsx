import React, { useEffect, useState } from 'react';
import { Navigate, useParams } from 'react-router-dom';
import { Spin, Typography } from 'antd';
import { getAnnotation } from '../../api/annotation';
import { getDataset } from '../../api/dataset';
import { AnnotationType, DatasetScenarioType } from '../../types';

const { Title, Paragraph } = Typography;

const AnnotationWorkbenchRouter: React.FC = () => {
  const { annotationId } = useParams<{ annotationId: string }>();
  const [targetPath, setTargetPath] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const resolveTarget = async () => {
      if (!annotationId) {
        setFailed(true);
        return;
      }

      try {
        const annotation = await getAnnotation(Number(annotationId));
        let workbench = 'image';

        if (annotation.annotation_type === AnnotationType.Classification) {
          workbench = 'classification';
        } else if (annotation.annotation_type === AnnotationType.LLM) {
          workbench = 'llm';
        } else if (annotation.annotation_type === AnnotationType.MLLM) {
          workbench = 'mllm';
        } else if (annotation.dataset_id) {
          const dataset = await getDataset(annotation.dataset_id);
          if (dataset.scenario_type === DatasetScenarioType.AerialStitch) {
            workbench = 'aerial';
          }
        }

        if (!cancelled) {
          setTargetPath(`/annotations/${annotationId}/label/${workbench}`);
        }
      } catch (error) {
        console.error('Failed to resolve annotation workbench', error);
        if (!cancelled) setFailed(true);
      }
    };

    resolveTarget();
    return () => {
      cancelled = true;
    };
  }, [annotationId]);

  if (targetPath) {
    return <Navigate to={targetPath} replace />;
  }

  if (failed) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#fff' }}>
        <div style={{ textAlign: 'center' }}>
          <Title level={4} type="secondary">无法打开标注工作台</Title>
          <Paragraph type="secondary">请检查标注项目是否存在，或返回标注列表后重试。</Paragraph>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#fff' }}>
      <Spin size="large" tip="正在加载标注工作台..." />
    </div>
  );
};

export default AnnotationWorkbenchRouter;
