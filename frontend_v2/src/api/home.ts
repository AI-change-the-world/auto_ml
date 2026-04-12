import apiClient from './client';
import type { Result, HomeStats } from '../types';

export async function getHomeStats() {
  const res = await apiClient.get<Result<HomeStats>>('/home/stats');
  return res.data.data;
}
