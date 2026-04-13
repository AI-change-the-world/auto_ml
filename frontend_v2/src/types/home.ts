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
}
