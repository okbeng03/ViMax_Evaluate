/**
 * Evaluation detail page
 * 
 * Implements US4: 查看评估详情
 * Displays: task info, image, prompt, CLIP score, LLM analysis, processing details
 */

import { useState, useEffect, useCallback } from 'react';
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
  Space,
  Divider,
  Statistic,
  Empty,
} from 'antd';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  BarChartOutlined,
  ExperimentOutlined,
  RobotOutlined,
} from '@ant-design/icons';

import { apiClient } from '../api/client';
import { wsClient } from '../api/websocket';
import { useSSE, SSEEvent } from '../hooks/useSSE';
import type {
  TaskStatusResponse,
  EvaluationResultResponse,
  TaskStatus,
  ProgressInfo,
  ProjectWithStats,
} from '../types';
import ScoreCard from '../components/ScoreCard';
import ImagePreview from '../components/ImagePreview';
import AnalysisPanel from '../components/AnalysisPanel';

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

export default function EvaluationDetailPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [result, setResult] = useState<EvaluationResultResponse | null>(null);
  const [project, setProject] = useState<ProjectWithStats | null>(null);
  const [progress, setProgress] = useState<ProgressInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!taskId) return;
    loadTaskStatus();
    connectWebSocket();
    return () => { wsClient.disconnect(); };
  }, [taskId]);

  const loadTaskStatus = async () => {
    if (!taskId) return;
    setLoading(true);
    try {
      const status = await apiClient.getTaskStatus(taskId);
      setTaskStatus(status);

      if (status.status === 'completed') {
        const res = await apiClient.getTaskResult(taskId);
        setResult(res);
        if (res.project_id) loadProject(res.project_id);
      }

      if (status.project_id && status.status !== 'completed') {
        loadProject(status.project_id);
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
      if (res.project_id) loadProject(res.project_id);
    } catch (err) {
      console.error('Failed to load result:', err);
    }
  };

  const loadProject = async (projectId: string) => {
    try {
      const p = await apiClient.getProject(projectId);
      setProject(p);
    } catch {
      // Project may not exist - ignore
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
              llm_analysis: res.llm_description,
              llm_consistency: '',
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

    return () => { unsubStatus(); unsubResult(); unsubError(); };
  };

  // SSE: auto-refresh detail when matching task_id event arrives
  const handleSSEEvent = useCallback((event: SSEEvent) => {
    // Only refresh if the event's task_id matches the current page's taskId
    if (event.data.task_id === taskId) {
      if (event.type === 'task_completed') {
        message.success('评估完成！');
        loadResult();
      }
      loadTaskStatus();
    }
  }, [taskId]);

  // Enabled only when taskId is available
  const sseEnabled = !!taskId;
  useSSE('task_completed', handleSSEEvent, sseEnabled);
  useSSE('task_updated', handleSSEEvent, sseEnabled);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
        <Text style={{ display: 'block', marginTop: 16 }}>加载评估详情...</Text>
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

  const isProcessing = taskStatus?.status === 'processing' || taskStatus?.status === 'queued';
  const isFailed = taskStatus?.status === 'failed';

  // Resolve image source
  const getImageSrc = (): string | undefined => {
    if (taskStatus?.image_url) return taskStatus.image_url;
    if (taskStatus?.hash_id) return `/comfyui-output/${taskStatus.hash_id}_00001_.png`;
    if (taskStatus?.image_base64) return `data:image/png;base64,${taskStatus.image_base64}`;
    return undefined;
  };

  return (
    <div style={{ padding: 24, maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <Space style={{ marginBottom: 20, width: '100%', justifyContent: 'space-between' }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/history')}>
          返回列表
        </Button>
        <Space>
          {project && (
            <Tag color="blue" style={{ fontSize: 13, padding: '2px 12px' }}>
              {project.name}
            </Tag>
          )}
          <Tag color={statusColors[taskStatus?.status || 'pending']} style={{ fontSize: 16, padding: '4px 16px' }}>
            {statusText[taskStatus?.status || 'pending']}
          </Tag>
        </Space>
      </Space>

      <Row gutter={[20, 20]}>
        {/* === Task Meta Info === */}
        <Col span={24}>
          <Card size="small">
            <Descriptions column={{ xs: 1, sm: 2, md: 4 }} size="small">
              <Descriptions.Item label="任务 ID">
                <Text copyable style={{ fontSize: 12 }}>{taskId}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                <ClockCircleOutlined /> {taskStatus?.created_at && new Date(taskStatus.created_at).toLocaleString('zh-CN')}
              </Descriptions.Item>
              {taskStatus?.completed_at && (
                <Descriptions.Item label="完成时间">
                  {new Date(taskStatus.completed_at).toLocaleString('zh-CN')}
                </Descriptions.Item>
              )}
              {result?.processing_time_ms != null && result.processing_time_ms > 0 && (
                <Descriptions.Item label="处理耗时">
                  {(result.processing_time_ms / 1000).toFixed(2)} 秒
                </Descriptions.Item>
              )}
            </Descriptions>
          </Card>
        </Col>

        {/* === Processing Progress === */}
        {isProcessing && progress && (
          <Col span={24}>
            <Card title={<Space><ExperimentOutlined /> 评估进行中</Space>} style={{ borderColor: '#1890ff' }}>
              <div style={{ marginBottom: 12 }}>
                <Text strong>当前阶段: </Text>
                <Tag color="processing">{progress.current_phase}</Tag>
              </div>
              <Progress
                percent={progress.progress_percent}
                status="active"
                strokeColor={{ from: '#108ee9', to: '#87d068' }}
              />
              <Text type="secondary">
                已完成阶段: {progress.phases_completed?.join(' → ') || '初始化中'}
              </Text>
            </Card>
          </Col>
        )}

        {/* === Error State === */}
        {isFailed && (
          <Col span={24}>
            <Card style={{ borderColor: '#ff4d4f', background: '#fff2f0' }}>
              <Space>
                <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 24 }} />
                <div>
                  <Text strong style={{ color: '#ff4d4f' }}>任务执行失败</Text>
                  <br />
                  <Text type="secondary">{error || '未知错误'}</Text>
                </div>
              </Space>
            </Card>
          </Col>
        )}

        {/* === Image + Prompt === */}
        <Col xs={24} lg={12}>
          <Card title="待评估图片" styles={{ body: { padding: 12 } }}>
            <ImagePreview src={getImageSrc()} alt="评估图片" height={350} />
            {taskStatus?.hash_id && (
              <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>
                Hash: {taskStatus.hash_id}
              </Text>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="原始 Prompt" styles={{ body: { padding: 12 } }}>
            {taskStatus?.prompt || result?.prompt ? (
              <div style={{
                maxHeight: 350,
                overflow: 'auto',
                background: '#fafafa',
                borderRadius: 6,
                padding: 12,
                border: '1px solid #f0f0f0',
              }}>
                <pre style={{
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontFamily: 'SF Mono, Consolas, monospace',
                  fontSize: 13,
                  lineHeight: 1.7,
                  margin: 0,
                }}>
                  {taskStatus?.prompt || result?.prompt}
                </pre>
              </div>
            ) : (
              <Empty description="暂无 Prompt" />
            )}
          </Card>
        </Col>

        {/* === Evaluation Results (only when completed) === */}
        {result && (
          <>
            {/* Section Divider */}
            <Col span={24}>
              <Divider orientation="left">
                <Space>
                  <BarChartOutlined />
                  <Text strong style={{ fontSize: 16 }}>评估结果</Text>
                </Space>
              </Divider>
            </Col>

            {/* --- 综合评分 (CLIP 40% + LLM 60%) --- */}
            <Col span={24}>
              <Card style={{ textAlign: 'center' }}>
                <Text type="secondary" style={{ fontSize: 14 }}>
                  综合评分 (CLIP 40% + LLM 60%)
                </Text>
                <div style={{ margin: '12px 0' }}>
                  <Statistic
                    value={result.overall_score}
                    suffix="分"
                    valueStyle={{
                      color:
                        result.overall_score >= 70 ? '#52c41a' :
                        result.overall_score >= 50 ? '#faad14' : '#ff4d4f',
                      fontSize: 56,
                      fontWeight: 700,
                    }}
                  />
                </div>
                <Progress
                  percent={result.overall_score}
                  strokeColor={{
                    '0%': '#ff4d4f',
                    '50%': '#faad14',
                    '100%': '#52c41a',
                  }}
                  size={['100%', 10]}
                />
                <div style={{ marginTop: 8 }}>
                  <Tag
                    color={
                      result.llm_consistency === 'consistent' ? 'green' :
                      result.llm_consistency === 'partially_consistent' ? 'orange' : 'red'
                    }
                    style={{ fontSize: 14 }}
                  >
                    {result.llm_consistency === 'consistent' && <CheckCircleOutlined />}
                    {result.llm_consistency === 'partially_consistent' && <WarningOutlined />}
                    {result.llm_consistency === 'inconsistent' && <CloseCircleOutlined />}
                    {' '}
                    {result.llm_consistency === 'consistent' ? '内容一致' :
                     result.llm_consistency === 'partially_consistent' ? '部分一致' : '不一致'}
                  </Tag>
                  {result.processing_time_ms != null && result.processing_time_ms > 0 && (
                    <Text type="secondary" style={{ marginLeft: 16 }}>
                      <ClockCircleOutlined /> 耗时 {(result.processing_time_ms / 1000).toFixed(2)} 秒
                    </Text>
                  )}
                </div>
              </Card>
            </Col>

            {/* --- CLIP 评分 + LLM 原始评分 --- */}
            <Col xs={24} md={12}>
              <ScoreCard
                title="CLIP 语义相似度"
                score={result.clip_score}
                maxScore={1}
                interpretation={result.clip_interpretation}
              />
            </Col>

            <Col xs={24} md={12}>
              <Card title={<><RobotOutlined /> LLM 原始评分</>}>
                <div style={{ textAlign: 'center' }}>
                  {result.llm_overall_score != null ? (
                    <>
                      <Statistic
                        value={result.llm_overall_score}
                        suffix="分"
                        valueStyle={{
                          color:
                            result.llm_overall_score >= 70 ? '#52c41a' :
                            result.llm_overall_score >= 50 ? '#faad14' : '#ff4d4f',
                          fontSize: 40,
                        }}
                      />
                      <Progress
                        percent={result.llm_overall_score}
                        strokeColor={
                          result.llm_overall_score >= 70 ? '#52c41a' :
                          result.llm_overall_score >= 50 ? '#faad14' : '#ff4d4f'
                        }
                        showInfo={false}
                      />
                    </>
                  ) : (
                    <Text type="secondary">暂无</Text>
                  )}
                </div>
              </Card>
            </Col>

            {/* --- LLM 维度评分 --- */}
            {result.llm_dimension_scores && (
              <Col span={24}>
                <Card title={<><ExperimentOutlined /> LLM 维度评分</>}>
                  <Row gutter={[12, 12]}>
                    {([
                      ['subject_consistency', '主体一致性', result.llm_dimension_scores.subject_consistency],
                      ['action_consistency', '动作一致性', result.llm_dimension_scores.action_consistency],
                      ['attribute_consistency', '属性一致性', result.llm_dimension_scores.attribute_consistency],
                      ['spatial_consistency', '空间一致性', result.llm_dimension_scores.spatial_consistency],
                      ['composition_consistency', '构图一致性', result.llm_dimension_scores.composition_consistency],
                      ['lighting_consistency', '光影一致性', result.llm_dimension_scores.lighting_consistency],
                      ['style_consistency', '风格一致性', result.llm_dimension_scores.style_consistency],
                      ['anatomy_quality', '解剖质量', result.llm_dimension_scores.anatomy_quality],
                      ['artifact_quality', '生成质量', result.llm_dimension_scores.artifact_quality],
                    ] as [string, string, number][]).map(([key, label, score]) => (
                      <Col xs={24} sm={12} md={8} key={key}>
                        <div style={{ marginBottom: 4 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                            <Text style={{ fontSize: 13 }}>{label}</Text>
                            <Text strong style={{ fontSize: 13, color: score >= 70 ? '#52c41a' : score >= 50 ? '#faad14' : '#ff4d4f' }}>
                              {score.toFixed(0)}
                            </Text>
                          </div>
                          <Progress
                            percent={score}
                            strokeColor={score >= 70 ? '#52c41a' : score >= 50 ? '#faad14' : '#ff4d4f'}
                            size="small"
                            showInfo={false}
                          />
                        </div>
                      </Col>
                    ))}
                  </Row>
                </Card>
              </Col>
            )}

            {/* --- 需求分析详情 --- */}
            <Col span={24}>
              <AnalysisPanel
                structuredDescription={result.structured_description}
                llmAnalysis={result.llm_analysis}
                llmConsistency={result.llm_consistency}
                matchedRequirements={result.llm_matched_requirements}
                missingRequirements={result.llm_missing_requirements}
                incorrectRequirements={result.llm_incorrect_requirements}
                extraElements={result.llm_extra_elements}
                criticalFailures={result.llm_critical_failures}
              />
            </Col>
          </>
        )}

        {/* Waiting state */}
        {isProcessing && !result && (
          <Col span={24}>
            <Card>
              <div style={{ textAlign: 'center', padding: 40 }}>
                <RobotOutlined style={{ fontSize: 48, color: '#1677ff' }} />
                <Title level={4} style={{ marginTop: 16 }}>评估结果生成中...</Title>
                <Text type="secondary">请等待各评估阶段完成</Text>
              </div>
            </Card>
          </Col>
        )}
      </Row>
    </div>
  );
}
