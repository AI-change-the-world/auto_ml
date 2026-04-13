/** 增强能力 */
export interface AugmentCapability {
  id: string;
  name: string;
  description: string;
}

/** 增强请求 */
export interface AugmentRequest {
  dataset_id: number;
  augment_type: string;
  config?: Record<string, unknown>;
}

/** 增强类型标签 */
export const AugmentTypeLabels: Record<string, string> = {
  cv: '传统CV增强',
  gan: 'GAN增强',
  sd: 'Stable Diffusion',
};

export const AugmentTypeColors: Record<string, string> = {
  cv: '#16a34a',
  gan: '#8b5cf6',
  sd: '#f59e0b',
};
