import React, { useEffect, useMemo, useState } from 'react';
import { Button, Empty, Input, Modal, Space, Spin } from 'antd';
import { ArrowRightOutlined, RobotOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { AnnotationProject, DeploymentOverviewItem, HomeStats, TaskResponse } from '../types';

interface WorkbenchAssistantModalProps {
  open: boolean;
  loading: boolean;
  onClose: () => void;
  onNavigate: (path: string) => void;
  stats: HomeStats | null;
  annotations: AnnotationProject[];
  tasks: TaskResponse[];
  deployments: DeploymentOverviewItem[];
}

interface AssistantAction {
  key: string;
  label: string;
  path?: string;
  onClick?: () => void;
}

interface AssistantMessage {
  id: string;
  role: 'assistant' | 'user';
  content: string;
  actions?: AssistantAction[];
}

function includesAny(source: string, keywords: string[]) {
  return keywords.some((keyword) => source.includes(keyword));
}

const WorkbenchAssistantModal: React.FC<WorkbenchAssistantModalProps> = ({
  open,
  loading,
  onClose,
  onNavigate,
  stats,
  annotations,
  tasks,
  deployments,
}) => {
  const { t, i18n } = useTranslation('common');
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<AssistantMessage[]>([]);

  useEffect(() => {
    if (!open) {
      return;
    }
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: `${t('assistant.welcomeTitle')}\n${t('assistant.welcomeBody')}`,
      },
    ]);
  }, [open, t]);

  const suggestionTexts = useMemo(
    () => [
      t('assistant.suggestions.datasetCount'),
      t('assistant.suggestions.runningTasks'),
      t('assistant.suggestions.latestAnnotation'),
      t('assistant.suggestions.openDeploy'),
      t('assistant.suggestions.dpoStart'),
    ],
    [t],
  );

  const handleNavigate = (path: string) => {
    onNavigate(path);
    onClose();
  };

  const buildResponse = (question: string): AssistantMessage => {
    const normalized = question.trim().toLowerCase();
    const latestDataset = stats?.recent_datasets?.[0];
    const latestAnnotation = stats?.recent_annotations?.[0] ?? annotations[0];
    const latestTask = tasks[0];
    const latestDeployment = deployments[0];
    const isZh = i18n.language !== 'en';

    if (includesAny(normalized, ['数据集', 'dataset', 'datasets', '样本', 'sample'])) {
      const datasetCount = stats?.datasets ?? 0;
      const sampleCount = stats?.images ?? 0;
      const content = isZh
        ? `当前共有 ${datasetCount} 个数据集，累计 ${sampleCount} 条样本。${latestDataset ? `最近的数据集是「${latestDataset.name}」。` : ''}`
        : `There are currently ${datasetCount} datasets with ${sampleCount} total samples.${latestDataset ? ` The latest dataset is "${latestDataset.name}".` : ''}`;
      const actions: AssistantAction[] = [{ key: 'datasets', label: t('assistant.actions.datasets'), path: '/datasets' }];
      if (latestDataset) {
        actions.push({ key: 'latest-dataset', label: t('assistant.actions.latestDataset'), path: `/datasets/${latestDataset.id}` });
      }
      return { id: `assistant-${Date.now()}`, role: 'assistant', content, actions };
    }

    if (includesAny(normalized, ['标注', 'annotation', 'dpo', '项目', 'project'])) {
      const annotationCount = stats?.annotations ?? annotations.length;
      const content = isZh
        ? `当前共有 ${annotationCount} 个标注项目。${latestAnnotation ? `最近项目是「${latestAnnotation.name}」。` : ''}${includesAny(normalized, ['dpo']) ? ' 如果要开始 DPO 标注，先创建 DPO 数据集，再创建对应的 DPO 标注项目。' : ''}`
        : `There are currently ${annotationCount} annotation projects.${latestAnnotation ? ` The latest project is "${latestAnnotation.name}".` : ''}${includesAny(normalized, ['dpo']) ? ' To start DPO annotation, create a DPO dataset first, then create the matching DPO annotation project.' : ''}`;
      const actions: AssistantAction[] = [{ key: 'annotations', label: t('assistant.actions.annotations'), path: '/annotations' }];
      if (latestAnnotation) {
        actions.push({ key: 'latest-annotation', label: t('assistant.actions.latestAnnotation'), path: `/annotations/${latestAnnotation.id}/label` });
      }
      return { id: `assistant-${Date.now()}`, role: 'assistant', content, actions };
    }

    if (includesAny(normalized, ['训练', 'task', 'tasks', '训练任务', 'running'])) {
      const total = stats?.tasks?.total ?? tasks.length;
      const running = stats?.tasks?.running ?? 0;
      const completed = stats?.tasks?.completed ?? 0;
      const content = isZh
        ? `当前共有 ${total} 个训练任务，其中运行中 ${running} 个，已完成 ${completed} 个。${latestTask ? `最近任务是 #${latestTask.id}。` : ''}`
        : `There are ${total} training tasks right now, with ${running} running and ${completed} completed.${latestTask ? ` The latest task is #${latestTask.id}.` : ''}`;
      const actions: AssistantAction[] = [{ key: 'tasks', label: t('assistant.actions.tasks'), path: '/tasks' }];
      if (latestTask) {
        actions.push({ key: 'latest-task', label: t('assistant.actions.latestTask'), path: `/tasks/${latestTask.id}` });
      }
      return { id: `assistant-${Date.now()}`, role: 'assistant', content, actions };
    }

    if (includesAny(normalized, ['部署', 'deploy', 'deployment', 'model', '模型'])) {
      const totalModels = stats?.models?.total ?? 0;
      const live = stats?.models?.deployed ?? deployments.length;
      const content = isZh
        ? `当前模型库共有 ${totalModels} 个模型，其中在线部署 ${live} 个。${latestDeployment ? `最近部署模型是「${latestDeployment.model_name || `模型 #${latestDeployment.model_id}`}」。` : ''}`
        : `The model library currently has ${totalModels} models, with ${live} live deployments.${latestDeployment ? ` The latest deployed model is "${latestDeployment.model_name || `Model #${latestDeployment.model_id}`}".` : ''}`;
      const actions: AssistantAction[] = [{ key: 'deploy', label: t('assistant.actions.deploy'), path: '/deploy' }];
      if (latestDeployment) {
        actions.push({ key: 'latest-deployment', label: t('assistant.actions.latestDeployment'), path: `/deploy/${latestDeployment.model_id}` });
      }
      return { id: `assistant-${Date.now()}`, role: 'assistant', content, actions };
    }

    if (includesAny(normalized, ['设置', 'setting'])) {
      return {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: isZh ? '可以直接进入设置页查看系统配置和运行状态。' : 'You can open Settings to review system configuration and runtime status.',
        actions: [{ key: 'settings', label: t('assistant.actions.settings'), path: '/settings' }],
      };
    }

    if (includesAny(normalized, ['首页', 'home'])) {
      return {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: isZh ? '可以，直接回到首页控制台查看整体概览。' : 'Sure. You can jump back to the console home for the overall overview.',
        actions: [{ key: 'home', label: t('assistant.open'), path: '/' }],
      };
    }

    return {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: t('assistant.unsupported'),
      actions: [
        { key: 'datasets', label: t('assistant.actions.datasets'), path: '/datasets' },
        { key: 'annotations', label: t('assistant.actions.annotations'), path: '/annotations' },
        { key: 'tasks', label: t('assistant.actions.tasks'), path: '/tasks' },
        { key: 'deploy', label: t('assistant.actions.deploy'), path: '/deploy' },
      ],
    };
  };

  const submitQuestion = (value: string) => {
    const question = value.trim();
    if (!question) {
      return;
    }

    setMessages((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, role: 'user', content: question },
      buildResponse(question),
    ]);
    setInputValue('');
  };

  const resetConversation = () => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: `${t('assistant.welcomeTitle')}\n${t('assistant.welcomeBody')}`,
      },
    ]);
  };

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={960}
      centered
      destroyOnHidden
      title={(
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-600">
            <RobotOutlined />
          </div>
          <div>
            <div className="text-base font-semibold text-slate-900">{t('assistant.title')}</div>
            <div className="mt-0.5 text-xs text-slate-500">{t('assistant.subtitle')}</div>
          </div>
        </div>
      )}
    >
      <div className="flex h-[72vh] min-h-[560px] gap-5">
        <div className="flex w-[240px] flex-shrink-0 flex-col rounded-xl border border-slate-200 bg-slate-50/70 p-4">
          <div className="text-sm font-semibold text-slate-900">{t('assistant.welcomeTitle')}</div>
          <div className="mt-2 text-sm leading-6 text-slate-500">{t('assistant.welcomeBody')}</div>
          <div className="mt-5 flex flex-col gap-2">
            {suggestionTexts.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => submitQuestion(suggestion)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-sm text-slate-600 transition-colors hover:border-slate-300 hover:bg-slate-50"
              >
                {suggestion}
              </button>
            ))}
          </div>
          <Button type="text" className="mt-auto px-0 text-left" onClick={resetConversation}>
            {t('assistant.clear')}
          </Button>
        </div>

        <div className="flex min-w-0 flex-1 flex-col">
          <div className="min-h-0 flex-1 overflow-y-auto rounded-xl border border-slate-200 bg-white p-4">
            {loading ? (
              <div className="flex h-full items-center justify-center gap-2 text-sm text-slate-500">
                <Spin size="small" />
                <span>{t('assistant.syncing')}</span>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={t('assistant.welcomeBody')} />
              </div>
            ) : (
              <div className="space-y-3">
                {messages.map((message) => (
                  <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-6 ${message.role === 'user' ? 'bg-slate-900 text-white' : 'border border-slate-200 bg-slate-50 text-slate-700'}`}>
                      <div className="whitespace-pre-line">{message.content}</div>
                      {message.actions && message.actions.length > 0 ? (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {message.actions.map((action) => (
                            <button
                              key={action.key}
                              type="button"
                              onClick={() => {
                                if (action.path) {
                                  handleNavigate(action.path);
                                } else {
                                  action.onClick?.();
                                }
                              }}
                              className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 transition-colors hover:border-slate-300 hover:bg-slate-50"
                            >
                              {action.label}
                              <ArrowRightOutlined />
                            </button>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <Space.Compact className="mt-4 w-full">
            <Input
              value={inputValue}
              onChange={(event) => setInputValue(event.target.value)}
              onPressEnter={() => submitQuestion(inputValue)}
              prefix={<RobotOutlined className="text-slate-400" />}
              placeholder={t('assistant.placeholder')}
              disabled={loading}
              size="large"
            />
            <Button type="primary" size="large" onClick={() => submitQuestion(inputValue)} disabled={loading}>
              {t('assistant.send')}
            </Button>
          </Space.Compact>
        </div>
      </div>
    </Modal>
  );
};

export default WorkbenchAssistantModal;
