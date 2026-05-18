/**
 * Project list page
 * 
 * Implements US3/US4: 项目管理功能
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Table,
  Typography,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  message,
} from 'antd';
import { PlusOutlined, ProjectOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

import { apiClient } from '../api/client';
import type { ProjectWithStats } from '../types';

const { Title, Text } = Typography;
const { TextArea } = Input;

export default function ProjectListPage() {
  const [projects, setProjects] = useState<ProjectWithStats[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  const loadProjects = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.listProjects(pageSize, (page - 1) * pageSize);
      setProjects(response.projects);
      setTotal(response.total);
    } catch (error) {
      message.error(`加载失败: ${error}`);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleCreate = async (values: { name: string; description?: string }) => {
    try {
      await apiClient.createProject(values);
      message.success('项目创建成功');
      setModalVisible(false);
      form.resetFields();
      loadProjects();
    } catch (error) {
      message.error(`创建失败: ${error}`);
    }
  };

  const columns: ColumnsType<ProjectWithStats> = [
    {
      title: '项目名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Space>
          <ProjectOutlined />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (desc: string | undefined) =>
        desc ? <Text type="secondary">{desc}</Text> : <Text type="secondary">-</Text>,
    },
    {
      title: '任务数',
      dataIndex: 'task_count',
      key: 'task_count',
      width: 100,
      render: (count: number) => <Tag>{count}</Tag>,
      sorter: (a, b) => a.task_count - b.task_count,
    },
    {
      title: '平均评分',
      dataIndex: 'avg_score',
      key: 'avg_score',
      width: 120,
      render: (score: number | undefined | null) =>
        score !== undefined && score !== null ? (
          <Tag color={score >= 70 ? 'green' : score >= 50 ? 'orange' : 'red'}>
            {score.toFixed(1)}
          </Tag>
        ) : (
          <Text type="secondary">-</Text>
        ),
      sorter: (a, b) => (a.avg_score || 0) - (b.avg_score || 0),
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
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={<Title level={3}>项目管理</Title>}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalVisible(true)}
          >
            新建项目
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={projects}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个项目`,
            onChange: (p, ps) => {
              setPage(p);
              setPageSize(ps);
            },
          }}
          size="middle"
        />
      </Card>

      <Modal
        title="创建项目"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        okText="创建"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
        >
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="例如：AI图片生成质量评估" />
          </Form.Item>
          <Form.Item
            name="description"
            label="项目描述（可选）"
          >
            <TextArea rows={3} placeholder="描述项目的用途..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
