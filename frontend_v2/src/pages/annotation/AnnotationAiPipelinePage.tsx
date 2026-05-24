import React from 'react';
import { Navigate, useParams } from 'react-router-dom';

const AnnotationAiPipelinePage: React.FC = () => {
  const { annotationId } = useParams<{ annotationId: string }>();

  if (!annotationId) {
    return <Navigate to="/annotations" replace />;
  }

  return <Navigate to={`/annotations/${annotationId}/ai-binding`} replace />;
};

export default AnnotationAiPipelinePage;
