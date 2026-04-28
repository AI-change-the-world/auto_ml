/** 首页统计数据 */
export interface HomeStats {
  datasets: number;
  images: number;
  annotations: number;
  tasks: {
    total: number;
    running: number;
    completed: number;
  };
  models: {
    total: number;
    deployed: number;
  };
  recent_annotations: {
    id: number;
    name: string;
    annotation_type: number;
    created_at: string | null;
  }[];
  recent_datasets: {
    id: number;
    name: string;
    count: number;
    data_type: number;
    created_at: string | null;
  }[];
  assist_pipelines: {
    id: string;
    name: string;
    description?: string | null;
    supported_annotation_types: number[];
    supported_shapes: string[];
    enabled: boolean;
    steps: {
      name: string;
      capability: string;
      provider?: string | null;
    }[];
  }[];
}
