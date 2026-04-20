import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import { useTranslation } from 'react-i18next';

import MainLayout from './layouts/MainLayout';
import AnnotationLayout from './layouts/AnnotationLayout';

import HomePage from './pages/home/HomePage';
import DatasetListPage from './pages/dataset/DatasetListPage';
import DatasetDetailPage from './pages/dataset/DatasetDetailPage';
import AnnotationListPage from './pages/annotation/AnnotationListPage';
import AnnotationPage from './pages/annotation/AnnotationPage';
import AnnotationWorkbenchRouter from './pages/annotation/AnnotationWorkbenchRouter';
import AerialAnnotationPage from './pages/annotation/aerial/AerialAnnotationPage';
import WorkbenchPlaceholderPage from './pages/annotation/WorkbenchPlaceholderPage';
import TaskListPage from './pages/task/TaskListPage';
import TaskDetailPage from './pages/task/TaskDetailPage';
import DeployPage from './pages/deploy/DeployPage';
import SettingsPage from './pages/settings/SettingsPage';
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
      <BrowserRouter>
        <Routes>
          {/* 主布局路由 */}
          <Route element={<MainLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/datasets" element={<DatasetListPage />} />
            <Route path="/datasets/:id" element={<DatasetDetailPage />} />
            <Route path="/annotations" element={<AnnotationListPage />} />
            <Route path="/tasks" element={<TaskListPage />} />
            <Route path="/tasks/:id" element={<TaskDetailPage />} />
            <Route path="/deploy" element={<DeployPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/example-dataset" element={<ExampleDatasetPage />} />
          </Route>

          {/* 标注工具独立全屏布局 */}
          <Route element={<AnnotationLayout />}>
            <Route path="/annotations/:annotationId/label" element={<AnnotationWorkbenchRouter />} />
            <Route path="/annotations/:annotationId/label/image" element={<AnnotationPage />} />
            <Route path="/annotations/:annotationId/label/aerial" element={<AerialAnnotationPage />} />
            <Route
              path="/annotations/:annotationId/label/mllm"
              element={<WorkbenchPlaceholderPage title="MLLM 标注工作台待实现" subtitle="该标注类型将使用独立工作台，避免与图像/航拍标注页面冲突。" />}
            />
          </Route>

          {/* 兼容旧路由 */}
          <Route path="/annotation/:annotationId" element={<Navigate to="/annotations" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
