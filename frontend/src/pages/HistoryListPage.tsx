/**
 * History list page
 * 
 * Implements US3: 查看历史评估记录
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Typography,
  Button,
  Space,
  Tag,
  DatePicker,
  Select,
  Input,
  message,
} from 'antd';
import { SearchOutlined, ReloadOutlined, PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

import { apiClient } from '../api/client';
import type { TaskListItem, TaskStatus, TaskListResponse } from '../types';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

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

export default function HistoryListPage() {
  const [tasks, setTasks] = useState<TaskListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  
  const [filters, setFilters] = useState({
    status: undefined as TaskStatus | undefined,
    project_id: undefined as string | undefined,
    search: '',
  });

  const navigate = useNavigate();

  const loadTasks = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.listTasks({
        status: filters.status,
        project_id: filters.project_id,
        limit: pageSize,
        offset: (page - 1) * pageSize,
      });
      setTasks(response.tasks);
      setTotal(response.total);
    } catch (error) {
      message.error(`加载失败: ${error}`);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filters]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  const handleSearch = () => {
    setPage(1);
    loadTasks();
  };

  const handleReset = () => {
    setFilters({ status: undefined, project_id: undefined, search: '' });
    setPage(1);
    setTimeout(loadTasks, 0);
  };

  const columns: ColumnsType<TaskListItem> = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 200,
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
      render: (text: string) => <Text>{text}</Text>,
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
      sorter: (a, b) => (a.overall_score || 0) - (b.overall_score || 0),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
      sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      defaultSortOrder: 'descend',
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
    <div style={{ padding: 24 }}>
      <Card
        title={<Title level={3}>历史评估记录</Title>}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/submit')}
          >
            新建任务
          </Button>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Space wrap>
            <Input
              placeholder="搜索任务ID..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              style={{ width: 200 }}
              prefix={<SearchOutlined />}
              onPressEnter={handleSearch}
            />
            <Select
              placeholder="状态筛选"
              value={filters.status}
              onChange={(value) => setFilters({ ...filters, status: value })}
              allowClear
              style={{ width: 120 }}
            >
              <Option value="pending">等待中</Option>
              <Option value="queued">已入队</Option>
              <Option value="processing">处理中</Option>
              <Option value="completed">已完成</Option>
              <Option value="failed">失败</Option>
            </Select>
            <RangePicker
              onChange={(dates) => {
                setFilters({
                  ...filters,
                  start_date: dates?.[0]?.toISOString(),
                  end_date: dates?.[1]?.toISOString(),
                });
              }}
            />
            <Button onClick={handleReset} icon={<ReloadOutlined />}>
              重置
            </Button>
          </Space>

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
              showTotal: (total) => `共 ${total} 条记录`,
              onChange: (p, ps) => {
                setPage(p);
                setPageSize(ps);
              },
            }}
            size="middle"
          />
        </Space>
      </Card>
    </div>
  );
}
