/**
 * Task table component with status badges
 */

import { Table, Tag, Button, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType } from 'antd/es/table';
import type { TaskListItem, TaskStatus } from '../types';

const { Text } = Typography;

const statusColors: Record<TaskStatus, string> = {
  pending: 'default',
  queued: 'processing',
  processing: 'blue',
  completed: 'success',
  failed: 'error',
};

const statusText: Record<TaskStatus, string> = {
  pending: '等待中',
  queued: '已入队',
  processing: '处理中',
  completed: '已完成',
  failed: '失败',
};

interface TaskTableProps {
  tasks: TaskListItem[];
  loading?: boolean;
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number, pageSize: number) => void;
}

export default function TaskTable({
  tasks,
  loading = false,
  total,
  page,
  pageSize,
  onPageChange,
}: TaskTableProps) {
  const navigate = useNavigate();

  const columns: ColumnsType<TaskListItem> = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 150,
      ellipsis: true,
      render: (id: string) => (
        <Button type="link" onClick={() => navigate(`/evaluation/${id}`)}>
          {id.slice(0, 8)}...
        </Button>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: TaskStatus) => (
        <Tag color={statusColors[status]}>{statusText[status]}</Tag>
      ),
    },
    {
      title: 'Prompt摘要',
      dataIndex: 'prompt_summary',
      key: 'prompt_summary',
      ellipsis: true,
    },
    {
      title: '综合评分',
      dataIndex: 'overall_score',
      key: 'overall_score',
      width: 100,
      render: (score: number | undefined) =>
        score !== undefined && score !== null ? (
          <Tag color={score >= 70 ? 'green' : score >= 50 ? 'orange' : 'red'}>
            {score.toFixed(1)}
          </Tag>
        ) : (
          <Text type="secondary">-</Text>
        ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          onClick={() => navigate(`/evaluation/${record.task_id}`)}
        >
          查看详情
        </Button>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={tasks}
      rowKey="task_id"
      loading={loading}
      pagination={{
        current: page,
        pageSize: pageSize,
        total: total,
        showSizeChanger: true,
        showTotal: (t) => `共 ${t} 条记录`,
        onChange: onPageChange,
      }}
      size="middle"
    />
  );
}
