/**
 * Evaluation detail page
 * 
 * Implements US4: 查看评估详情
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Typography,
  Row,
  Col,
  Progress,
  Tag,
  Spin,
  message,
  Button,
  Descriptions,
  List,
  Space,
  Divider,
  Image,
  Collapse,
} from 'antd';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  PictureOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { Eye } from 'lucide-react';

import { apiClient } from '../api/client';
import { wsClient } from '../api/websocket';
import type {
  TaskStatusResponse,
  EvaluationResultResponse,
  TaskStatus,
  ProgressInfo,
} from '../types';

const { Title, Text, Paragraph } = Typography;

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

const consistencyColors: Record<string, string> = {
  consistent: 'green',
  partially_consistent: 'orange',
  inconsistent: 'red',
};

const consistencyText: Record<string, string> = {
  consistent: '一致',
  partially_consistent: '部分一致',
  inconsistent: '不一致',
};

export default function EvaluationDetailPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [result, setResult] = useState<EvaluationResultResponse | null>(null);
  const [progress, setProgress] = useState<ProgressInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!taskId) return;

    loadTaskStatus();
    connectWebSocket();

    return () => {
      wsClient.disconnect();
    };
  }, [taskId]);

  const loadTaskStatus = async () => {
    if (!taskId) return;

    setLoading(true);
    try {
      const status = await apiClient.getTaskStatus(taskId);
      setTaskStatus(status);
      
      if (status.status === 'completed') {
        loadResult();
      }
    } catch (err) {
      setError(`加载失败: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const loadResult = async () => {
    if (!taskId) return;

    try {
      const res = await apiClient.getTaskResult(taskId);
      setResult(res);
    } catch (err) {
      console.error('Failed to load result:', err);
    }
  };

  const connectWebSocket = () => {
    if (!taskId) return;

    wsClient.connect(taskId).catch(console.error);

    const unsubStatus = wsClient.onStatus((status, prog) => {
      setTaskStatus((prev) =>
        prev ? { ...prev, status, progress: prog } : null
      );
      setProgress(prog || null);

      if (status === 'completed') {
        message.success('评估完成！');
        loadResult();
      }
    });

    const unsubResult = wsClient.onResult((res) => {
      setResult((prev) =>
        prev
          ? prev
          : {
              task_id: taskId!,
              clip_score: res.clip_score,
              clip_interpretation: res.clip_interpretation,
              structured_description: '',
              llm_analysis: '',
              llm_consistency: res.llm_consistency,
              overall_score: res.overall_score,
              processing_time_ms: 0,
              created_at: new Date().toISOString(),
            }
      );
    });

    const unsubError = wsClient.onError((err) => {
      message.error(`评估错误: ${err.message}`);
      setError(err.message);
    });

    return () => {
      unsubStatus();
      unsubResult();
      unsubError();
    };
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
        <Text style={{ display: 'block', marginTop: 16 }}>加载中...</Text>
      </div>
    );
  }

  if (error && !taskStatus) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <CloseCircleOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
        <Title level={4} style={{ marginTop: 16 }}>加载失败</Title>
        <Text type="secondary">{error}</Text>
        <div style={{ marginTop: 24 }}>
          <Button onClick={() => navigate('/history')}>返回列表</Button>
        </div>
      </div>
    );
  }

  const isProcessing = taskStatus?.status === 'processing' || taskStatus?.status === 'queued' || taskStatus?.status === 'pending';

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/history')}
        style={{ marginBottom: 16 }}
      >
        返回列表
      </Button>

      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <div>
                <Title level={4}>任务状态</Title>
                <Tag color={statusColors[taskStatus?.status || 'pending']} style={{ fontSize: 16 }}>
                  {statusText[taskStatus?.status || 'pending']}
                </Tag>
              </div>
              <div>
                <Text type="secondary">任务ID: {taskId}</Text>
                <br />
                <Text type="secondary">
                  创建时间: {taskStatus?.created_at && new Date(taskStatus.created_at).toLocaleString('zh-CN')}
                </Text>
              </div>
            </Space>

            {isProcessing && progress && (
              <div style={{ marginTop: 24 }}>
                <Text strong>当前阶段: {progress.current_phase}</Text>
                <Progress
                  percent={progress.progress_percent}
                  status="active"
                  format={(percent) => `${percent}%`}
                />
                <Text type="secondary">
                  已完成: {progress.phases_completed.join(', ') || '无'}
                </Text>
              </div>
            )}
          </Card>
        </Col>

        {/* 图片和 Prompt 展示 */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <PictureOutlined />
                待评估图片
              </Space>
            }
          >
            {taskStatus?.image_url ? (
              <Image
                src={taskStatus.image_url}
                alt="待评估图片"
                style={{ width: '100%', maxHeight: 400, objectFit: 'contain' }}
                placeholder={<div style={{ textAlign: 'center', padding: 50 }}><Spin /></div>}
              />
            ) : taskStatus?.hash_id ? (
              <Image
                src={`/comfyui-output/${taskStatus.hash_id}_00001_.png`}
                alt="ComfyUI 输出图片"
                style={{ width: '100%', maxHeight: 400, objectFit: 'contain' }}
                placeholder={
                  <div style={{ textAlign: 'center', padding: 50 }}>
                    <Spin />
                    <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                      Hash: {taskStatus.hash_id}
                    </Text>
                  </div>
                }
                fallback=""
              />
            ) : taskStatus?.image_base64 ? (
              <Image
                src={`data:image/png;base64,${taskStatus.image_base64}`}
                alt="Base64 图片"
                style={{ width: '100%', maxHeight: 400, objectFit: 'contain' }}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <PictureOutlined style={{ fontSize: 48, color: '#999' }} />
                <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                  暂无图片
                </Text>
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <FileTextOutlined />
                评估 Prompt
              </Space>
            }
          >
            {taskStatus?.prompt ? (
              <div style={{ maxHeight: 400, overflow: 'auto' }}>
                <pre style={{ 
                  whiteSpace: 'pre-wrap', 
                  wordBreak: 'break-word',
                  fontFamily: 'monospace',
                  fontSize: 13,
                  lineHeight: 1.6,
                  margin: 0,
                  padding: 8,
                  background: '#f5f5f5',
                  borderRadius: 4,
                }}>
                  {taskStatus.prompt}
                </pre>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <FileTextOutlined style={{ fontSize: 48, color: '#999' }} />
                <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                  暂无 Prompt
                </Text>
              </div>
            )}
          </Card>
        </Col>

        {result && (
          <>
            <Col xs={24} lg={12}>
              <Card title="CLIP 语义评估">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text type="secondary">CLIP 相似度</Text>
                    <Title level={2} style={{ margin: 0 }}>
                      {(result.clip_score * 100).toFixed(1)}%
                    </Title>
                  </div>
                  <Progress
                    percent={result.clip_score * 100}
                    strokeColor={
                      result.clip_score >= 0.7
                        ? '#52c41a'
                        : result.clip_score <= 0.5
                        ? '#ff4d4f'
                        : '#faad14'
                    }
                  />
                  <Tag
                    color={
                      result.clip_interpretation === 'consistent'
                        ? 'green'
                        : result.clip_interpretation === 'inconsistent'
                        ? 'red'
                        : 'orange'
                    }
                    style={{ fontSize: 14 }}
                  >
                    {result.clip_interpretation === 'consistent' && <CheckCircleOutlined />}
                    {result.clip_interpretation === 'inconsistent' && <CloseCircleOutlined />}
                    {result.clip_interpretation === 'ambiguous' && <WarningOutlined />}
                    {' '}
                    {result.clip_interpretation === 'consistent'
                      ? '语义一致'
                      : result.clip_interpretation === 'inconsistent'
                      ? '语义不一致'
                      : '模糊区间'}
                  </Tag>
                </Space>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="LLM 结构化评估">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text type="secondary">综合评分</Text>
                    <Title level={2} style={{ margin: 0 }}>
                      {result.overall_score.toFixed(1)}
                    </Title>
                  </div>
                  <Progress
                    percent={result.overall_score}
                    strokeColor={
                      result.overall_score >= 70
                        ? '#52c41a'
                        : result.overall_score >= 50
                        ? '#faad14'
                        : '#ff4d4f'
                    }
                  />
                  <Tag
                    color={consistencyColors[result.llm_consistency]}
                    style={{ fontSize: 14 }}
                  >
                    {consistencyText[result.llm_consistency]}
                  </Tag>
                </Space>
              </Card>
            </Col>

            <Col span={24}>
              <Card title="评估详情">
                <Row gutter={16}>
                  <Col span={24}>
                    <Descriptions column={2}>
                      <Descriptions.Item label="处理耗时">
                        {(result.processing_time_ms / 1000).toFixed(2)} 秒
                      </Descriptions.Item>
                      <Descriptions.Item label="评估时间">
                        {new Date(result.created_at).toLocaleString('zh-CN')}
                      </Descriptions.Item>
                    </Descriptions>
                  </Col>
                  <Col span={24}>
                    <Divider>结构化描述</Divider>
                    <Paragraph>{result.structured_description || '暂无'}</Paragraph>
                  </Col>
                  <Col span={24}>
                    <Divider>LLM 分析</Divider>
                    <Paragraph>{result.llm_analysis || '暂无'}</Paragraph>
                  </Col>
                </Row>
              </Card>
            </Col>
          </>
        )}
      </Row>
    </div>
  );
}
