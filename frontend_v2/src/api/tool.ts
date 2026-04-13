import apiClient from './client';
import type { Result, PageResult, ToolModelCreate, ToolModelResponse } from '../types';

/** 获取工具模型列表 */
export async function listToolModels(page = 1, pageSize = 10) {
    const res = await apiClient.get<Result<PageResult<ToolModelResponse>>>('/tool/list', {
        params: { page, page_size: pageSize },
    });
    return res.data.data;
}

/** 创建工具模型 */
export async function createToolModel(data: ToolModelCreate) {
    const res = await apiClient.post<Result<ToolModelResponse>>('/tool/new', data);
    return res.data.data;
}
