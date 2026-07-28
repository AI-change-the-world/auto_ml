import React from 'react';
import { Navigate, Routes, Route, unstable_HistoryRouter as HistoryRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import { useTranslation } from 'react-i18next';
import { appHistory } from './router/appHistory';

import MainLayout from './layouts/MainLayout';
import AnnotationLayout from './layouts/AnnotationLayout';

import HomePage from './pages/home/HomePage';
import DatasetListPage from './pages/dataset/DatasetListPage';
import DatasetDetailPage from './pages/dataset/DatasetDetailPage';
import BatchAnnotationPage from './pages/dataset/BatchAnnotationPage';
import AnnotationListPage from './pages/annotation/AnnotationListPage';
import AnnotationPage from './pages/annotation/AnnotationPage';
import AnnotationAiBindingPage from './pages/annotation/AnnotationAiBindingPage';
import AnnotationAiPipelinePage from './pages/annotation/AnnotationAiPipelinePage';
import AnnotationWorkbenchRouter from './pages/annotation/AnnotationWorkbenchRouter';
import AerialAnnotationPage from './pages/annotation/aerial/AerialAnnotationPage';
import ClassificationAnnotationPage from './pages/annotation/classification/ClassificationAnnotationPage';
import ConversationAnnotationPage from './pages/annotation/conversation/ConversationAnnotationPage';
import DpoAnnotationPage from './pages/annotation/dpo/DpoAnnotationPage';
import DpoPairwiseAnnotationPage from './pages/annotation/dpo/DpoPairwiseAnnotationPage';
import DpoBestOfNAnnotationPage from './pages/annotation/dpo/DpoBestOfNAnnotationPage';
import DpoReferenceChoiceAnnotationPage from './pages/annotation/dpo/DpoReferenceChoiceAnnotationPage';
import DpoMultiTurnAnnotationPage from './pages/annotation/dpo/DpoMultiTurnAnnotationPage';
import TaskListPage from './pages/task/TaskListPage';
import TaskDetailPage from './pages/task/TaskDetailPage';
import DeployPage from './pages/deploy/DeployPage';
import DeployDetailPage from './pages/deploy/DeployDetailPage';
import SettingsPage from './pages/settings/SettingsPage';
import AiPipelineTemplateManagementPage from './pages/settings/AiPipelineTemplateManagementPage';
import AiPipelineProviderManagementPage from './pages/settings/AiPipelineProviderManagementPage';
import AiPipelineVersionEditorPage from './pages/settings/AiPipelineVersionEditorPage';
import ExampleDatasetPage from './pages/example/ExampleDatasetPage';

const App: React.FC = () => {
  const { i18n } = useTranslation();
  const antdLocale = i18n.language === 'en' ? enUS : zhCN;

  return (
    <ConfigProvider
      locale={antdLocale}
      theme={{
        token: {
          colorPrimary: '#667eea',
          borderRadius: 8,
        },
      }}
    >
      <HistoryRouter history={appHistory}>
        <Routes>
          <Route path="/ai-pipeline/editor" element={<AiPipelineVersionEditorPage />} />
          <Route path="/ai-pipeline/editor/:templateKey" element={<AiPipelineVersionEditorPage />} />

          {/* 主布局路由 */}
          <Route element={<MainLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/datasets" element={<DatasetListPage />} />
            <Route path="/datasets/:id" element={<DatasetDetailPage />} />
            <Route path="/datasets/:id/batch-annotation" element={<BatchAnnotationPage />} />
            <Route path="/annotations" element={<AnnotationListPage />} />
            <Route path="/annotations/:annotationId/ai-binding" element={<AnnotationAiBindingPage />} />
            <Route path="/annotations/:annotationId/ai-pipeline" element={<AnnotationAiPipelinePage />} />
            <Route path="/tasks" element={<TaskListPage />} />
            <Route path="/tasks/:id" element={<TaskDetailPage />} />
            <Route path="/deploy" element={<DeployPage />} />
            <Route path="/deploy/:id" element={<DeployDetailPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/ai-pipeline" element={<AiPipelineTemplateManagementPage />} />
            <Route path="/ai-pipeline/providers" element={<AiPipelineProviderManagementPage />} />
            <Route path="/settings/ai-pipeline/templates" element={<Navigate to="/ai-pipeline" replace />} />
            <Route path="/example-dataset" element={<ExampleDatasetPage />} />
          </Route>

          {/* 标注工具独立全屏布局 */}
          <Route element={<AnnotationLayout />}>
            <Route path="/annotations/:annotationId/label" element={<AnnotationWorkbenchRouter />} />
            <Route path="/annotations/:annotationId/label/image" element={<AnnotationPage />} />
            <Route path="/annotations/:annotationId/label/collab-detection" element={<AnnotationPage />} />
            <Route path="/annotations/:annotationId/label/aerial" element={<AerialAnnotationPage />} />
            <Route path="/annotations/:annotationId/label/classification" element={<ClassificationAnnotationPage />} />
            <Route path="/annotations/:annotationId/label/llm" element={<ConversationAnnotationPage />} />
            <Route path="/annotations/:annotationId/label/mllm" element={<ConversationAnnotationPage />} />
            <Route path="/annotations/:annotationId/label/dpo" element={<DpoAnnotationPage />} />
            <Route path="/annotations/:annotationId/label/dpo-pairwise" element={<DpoPairwiseAnnotationPage />} />
            <Route path="/annotations/:annotationId/label/dpo-best-of-n" element={<DpoBestOfNAnnotationPage />} />
            <Route path="/annotations/:annotationId/label/dpo-reference" element={<DpoReferenceChoiceAnnotationPage />} />
            <Route path="/annotations/:annotationId/label/dpo-multi-turn" element={<DpoMultiTurnAnnotationPage />} />
          </Route>

          {/* 兼容旧路由 */}
          <Route path="/annotation/:annotationId" element={<Navigate to="/annotations" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </HistoryRouter>
    </ConfigProvider>
  );
};

export default App;
