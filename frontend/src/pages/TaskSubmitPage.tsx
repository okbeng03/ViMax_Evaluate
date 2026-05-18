/**
 * Task submission page
 * 
 * Implements US1: 提交图像评估任务
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Form,
  Input,
  Select,
  Upload,
  Button,
  Typography,
  message,
  Space,
  Divider,
} from 'antd';
import { UploadOutlined, InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

import { apiClient } from '../api/client';
import { wsClient } from '../api/websocket';
import type { ProjectWithStats, TaskCreateResponse } from '../types';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

export default function TaskSubmitPage() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState<ProjectWithStats[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await apiClient.listProjects(100, 0);
      setProjects(response.projects);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setProjectsLoading(false);
    }
  };

  const handleSubmit = async (values: {
    project_id?: string;
    image_url?: string;
    image_base64?: string;
    prompt: string;
  }) => {
    if (!values.image_url && !values.image_base64) {
      message.error('请提供图片URL或上传图片');
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.createTask({
        project_id: values.project_id,
        image_url: values.image_url,
        image_base64: values.image_base64,
        prompt: values.prompt,
      });

      message.success(`任务已提交，任务ID: ${response.task_id}`);
      
      wsClient.connect(response.task_id);
      
      navigate(`/evaluation/${response.task_id}`);
    } catch (error) {
      message.error(`提交失败: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const uploadProps: UploadProps = {
    name: 'file',
    maxCount: 1,
    beforeUpload: async (file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64 = e.target?.result as string;
        form.setFieldValue('image_base64', base64);
        form.setFieldValue('image_url', undefined);
      };
      reader.readAsDataURL(file);
      return false;
    },
    onRemove: () => {
      form.setFieldValue('image_base64', undefined);
    },
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 24 }}>
      <Card>
        <Title level={2}>提交图像评估任务</Title>
        <Text type="secondary">
          提交图片和提示词，系统将使用CLIP和LLM进行语义一致性评估
        </Text>

        <Divider />

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            project_id: undefined,
          }}
        >
          <Form.Item
            label="所属项目（可选）"
            name="project_id"
          >
            <Select
              placeholder="选择项目或留空"
              loading={projectsLoading}
              allowClear
              showSearch
              optionFilterProp="children"
            >
              {projects.map((project) => (
                <Option key={project.id} value={project.id}>
                  {project.name} ({project.task_count} 任务)
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="图片来源"
            name="image_source"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Input
                placeholder="图片URL (https://example.com/image.png)"
                onChange={(e) => {
                  form.setFieldValue('image_url', e.target.value || undefined);
                  if (e.target.value) {
                    form.setFieldValue('image_base64', undefined);
                  }
                }}
              />
              <Upload.Dragger {...uploadProps}>
                <p className="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p className="ant-upload-text">点击或拖拽上传图片</p>
                <p className="ant-upload-hint">支持 PNG, JPG, JPEG, WebP 格式</p>
              </Upload.Dragger>
            </Space>
          </Form.Item>

          <Form.Item
            label="Prompt / 描述"
            name="prompt"
            rules={[
              { required: true, message: '请输入Prompt描述' },
              { min: 1, message: 'Prompt不能为空' },
            ]}
          >
            <TextArea
              rows={4}
              placeholder="描述期望的图片内容，例如：一只橘色的猫坐在窗台上，阳光透过窗户照在猫身上"
              showCount
              maxLength={2000}
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<UploadOutlined />}
              size="large"
              block
            >
              提交评估任务
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
