import apiClient from './client';
import type {
  Result,
  PageResult,
  AiPipelineTemplateCreateRequest,
  AiPipelineCapabilityItem,
  AiPipelineTemplateDetail,
  AiPipelineTemplateDraftSaveRequest,
  AiPipelineBindingCreateRequest,
  AiPipelineBindingResponse,
  AiPipelineBindingUpdateRequest,
  AiPipelineModelResourceItem,
  AiPipelineTemplateListItem,
} from '../types';

export async function listAiPipelineTemplates(params?: {
  page?: number;
  page_size?: number;
  scene_type?: string;
  status?: string;
  keyword?: string;
}) {
  const res = await apiClient.get<Result<PageResult<AiPipelineTemplateListItem>>>('/ai-pipeline/templates', {
    params,
  });
  return res.data.data;
}

export async function listAiPipelineCapabilities() {
  const res = await apiClient.get<Result<AiPipelineCapabilityItem[]>>('/ai-pipeline/capabilities');
  return res.data.data ?? [];
}

export async function getAiPipelineTemplateDetail(templateKey: string) {
  const res = await apiClient.get<Result<AiPipelineTemplateDetail>>(`/ai-pipeline/templates/${templateKey}`);
  return res.data.data;
}

export async function createAiPipelineTemplate(data: AiPipelineTemplateCreateRequest) {
  const res = await apiClient.post<Result<AiPipelineTemplateListItem>>('/ai-pipeline/templates', data);
  return res.data.data;
}

export async function updateAiPipelineTemplate(
  templateKey: string,
  data: AiPipelineTemplateDraftSaveRequest,
) {
  const res = await apiClient.put<Result<AiPipelineTemplateDetail>>(`/ai-pipeline/templates/${templateKey}`, data);
  return res.data.data;
}

export async function disableAiPipelineTemplate(templateKey: string) {
  const res = await apiClient.post<Result<AiPipelineTemplateDetail>>(`/ai-pipeline/templates/${templateKey}/disable`);
  return res.data.data;
}

export async function deleteAiPipelineTemplate(templateKey: string) {
  const res = await apiClient.delete<Result>(`/ai-pipeline/templates/${templateKey}`);
  return res.data;
}

export async function listAiPipelineBindings(params?: {
  page?: number;
  page_size?: number;
  binding_type?: string;
  binding_target_id?: number;
}) {
  const res = await apiClient.get<Result<PageResult<AiPipelineBindingResponse>>>('/ai-pipeline/bindings', {
    params,
  });
  return res.data.data;
}

export async function createAiPipelineBinding(data: AiPipelineBindingCreateRequest) {
  const res = await apiClient.post<Result<AiPipelineBindingResponse>>('/ai-pipeline/bindings', data);
  return res.data.data;
}

export async function updateAiPipelineBinding(bindingId: number, data: AiPipelineBindingUpdateRequest) {
  const res = await apiClient.put<Result<AiPipelineBindingResponse>>(`/ai-pipeline/bindings/${bindingId}`, data);
  return res.data.data;
}

export async function deleteAiPipelineBinding(bindingId: number) {
  const res = await apiClient.delete<Result>(`/ai-pipeline/bindings/${bindingId}`);
  return res.data;
}

export async function listAiPipelineModelResources(deployedOnly = true) {
  const res = await apiClient.get<Result<AiPipelineModelResourceItem[]>>('/ai-pipeline/resources/models', {
    params: { deployed_only: deployedOnly },
  });
  return res.data.data ?? [];
}
