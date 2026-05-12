import apiClient from './client';
import type { Result, CapabilitySnapshot } from '../types';

export async function getCapabilitySnapshot() {
  const res = await apiClient.get<Result<CapabilitySnapshot>>('/system/capabilities');
  return res.data.data;
}
