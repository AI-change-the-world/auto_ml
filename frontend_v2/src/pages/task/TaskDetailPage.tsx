import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography, Card, Descriptions, Tag, Button, Space, Spin, message,
} from 'antd';
import { ArrowLeftOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { getTask, getTaskLogs } from '../../api/task';
import type { TaskResponse, TaskLogResponse } from '../../types/task';
import { TaskStatusLabels, TaskStatusColors } from '../../types/task';

const { Title, Text } = Typography;

const TaskDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<TaskResponse | null>(null);
  const [logs, setLogs] = useState<TaskLogResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const taskId = Number(id);

  const fetchTask = useCallback(async () => {
    try {
      const res = await getTask(taskId);
      if (res) setTask(res);
    } catch {
      message.error('获取任务详情失败');
    }
  }, [taskId]);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await getTaskLogs(taskId, 1, 500);
      if (res) {
        setLogs(res.items);
        // 自动滚动到底部
        setTimeout(() => {
          if (logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
          }
        }, 100);
      }
    } catch {
      /* ignore */
    }
  }, [taskId]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([fetchTask(), fetchLogs()]);
      setLoading(false);
    };
    init();
  }, [fetchTask, fetchLogs]);

  // 运行中的任务自动刷新日志
  useEffect(() => {
    if (task && (task.status === 0 || task.status === 1)) {
      timerRef.current = setInterval(() => {
        fetchTask();
        fetchLogs();
      }, 5000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [task?.status, fetchTask, fetchLogs]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!task) {
    return (
      <div style={{ padding: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/tasks')}>返回</Button>
        <div style={{ textAlign: 'center', marginTop: 80 }}>
          <Text type="secondary">任务不存在</Text>
        </div>
      </div>
    );
  }

  const taskTypeLabels: Record<number, string> = { 0: '检测', 1: '分类', 2: '分割' };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/tasks')} />
          <Title level={4} style={{ margin: 0 }}>任务详情 #{task.id}</Title>
          <Tag color={TaskStatusColors[task.status]}>{TaskStatusLabels[task.status]}</Tag>
        </Space>
        <Button icon={<ReloadOutlined />} onClick={() => { fetchTask(); fetchLogs(); }}>刷新</Button>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={2}>
          <Descriptions.Item label="任务 ID">{task.id}</Descriptions.Item>
          <Descriptions.Item label="任务类型">{taskTypeLabels[task.task_type] ?? task.task_type}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={TaskStatusColors[task.status]}>{TaskStatusLabels[task.status]}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="数据集 ID">{task.dataset_id ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="标注 ID">{task.annotation_id ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{dayjs(task.created_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
          <Descriptions.Item label="更新时间">{dayjs(task.updated_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
          {task.error_message && (
            <Descriptions.Item label="错误信息" span={2}>
              <Text type="danger">{task.error_message}</Text>
            </Descriptions.Item>
          )}
          {task.result && (
            <Descriptions.Item label="结果" span={2}>
              <Text code>{task.result}</Text>
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      <Card
        title="训练日志"
        extra={
          <Text type="secondary" style={{ fontSize: 12 }}>
            {task.status <= 1 ? '每 5 秒自动刷新' : `共 ${logs.length} 条`}
          </Text>
        }
      >
        <div
          ref={logContainerRef}
          style={{
            background: '#1e1e1e',
            color: '#d4d4d4',
            padding: 16,
            borderRadius: 8,
            height: 400,
            overflow: 'auto',
            fontFamily: "'Cascadia Code', 'Fira Code', Consolas, monospace",
            fontSize: 13,
            lineHeight: 1.6,
          }}
        >
          {logs.length === 0 ? (
            <Text style={{ color: '#666' }}>暂无日志</Text>
          ) : (
            logs.map((log) => (
              <div key={log.id} style={{ marginBottom: 2 }}>
                <span style={{ color: '#6a9955' }}>
                  [{dayjs(log.created_at).format('HH:mm:ss')}]
                </span>
                {' '}
                <span
                  style={{
                    color: log.log_level === 'ERROR' ? '#f44747'
                      : log.log_level === 'WARNING' ? '#cca700'
                      : '#d4d4d4',
                  }}
                >
                  {log.content}
                </span>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
};

export default TaskDetailPage;
