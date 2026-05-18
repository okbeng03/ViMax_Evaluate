/**
 * Task filter controls component
 */

import { Space, Input, Select, DatePicker, Button } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import type { TaskStatus, TaskFilterParams } from '../types';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface TaskFiltersProps {
  filters: TaskFilterParams;
  onFiltersChange: (filters: TaskFilterParams) => void;
  onSearch: () => void;
  onReset: () => void;
}

export default function TaskFilters({
  filters,
  onFiltersChange,
  onSearch,
  onReset,
}: TaskFiltersProps) {
  return (
    <Space wrap>
      <Input
        placeholder="搜索任务ID..."
        value={filters.project_id || ''}
        onChange={(e) =>
          onFiltersChange({ ...filters, project_id: e.target.value || undefined })
        }
        style={{ width: 200 }}
        prefix={<SearchOutlined />}
      />
      <Select
        placeholder="状态筛选"
        value={filters.status}
        onChange={(value) => onFiltersChange({ ...filters, status: value })}
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
        onChange={(dates) =>
          onFiltersChange({
            ...filters,
            start_date: dates?.[0]?.toISOString(),
            end_date: dates?.[1]?.toISOString(),
          })
        }
      />
      <Button onClick={onReset} icon={<ReloadOutlined />}>
        重置
      </Button>
    </Space>
  );
}
