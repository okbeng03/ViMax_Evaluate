/**
 * Project form component for creating/editing projects
 */

import { Form, Input, Button, message } from 'antd';
import type { ProjectCreateRequest } from '../types';

interface ProjectFormProps {
  initialValues?: Partial<ProjectCreateRequest>;
  onSubmit: (values: ProjectCreateRequest) => Promise<void>;
  onCancel?: () => void;
  loading?: boolean;
}

export default function ProjectForm({
  initialValues,
  onSubmit,
  onCancel,
  loading = false,
}: ProjectFormProps) {
  const [form] = Form.useForm<ProjectCreateRequest>();

  const handleFinish = async (values: ProjectCreateRequest) => {
    try {
      await onSubmit(values);
      form.resetFields();
    } catch (error) {
      message.error(`操作失败: ${error}`);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={initialValues}
      onFinish={handleFinish}
    >
      <Form.Item
        name="name"
        label="项目名称"
        rules={[
          { required: true, message: '请输入项目名称' },
          { min: 1, max: 255, message: '名称长度应在1-255字符之间' },
        ]}
      >
        <Input placeholder="例如：AI图片生成质量评估" />
      </Form.Item>

      <Form.Item
        name="description"
        label="项目描述（可选）"
      >
        <Input.TextArea
          rows={3}
          placeholder="描述项目的用途..."
          maxLength={1000}
          showCount
        />
      </Form.Item>

      <Form.Item style={{ marginBottom: 0 }}>
        <Space>
          <Button type="primary" htmlType="submit" loading={loading}>
            提交
          </Button>
          {onCancel && (
            <Button onClick={onCancel}>
              取消
            </Button>
          )}
        </Space>
      </Form.Item>
    </Form>
  );
}
