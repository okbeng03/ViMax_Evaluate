/**
 * Analysis panel component for displaying LLM requirement analysis and descriptions
 */

import { Card, Typography, Divider, Tag, Space, Collapse, List, Empty } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  MinusCircleOutlined,
  ExclamationCircleOutlined,
  BulbOutlined,
} from '@ant-design/icons';
import type { RequirementMatch } from '../types';

const { Text, Paragraph } = Typography;

interface AnalysisPanelProps {
  structuredDescription?: string;
  llmAnalysis?: string;
  llmConsistency?: string;
  /** 匹配的需求 */
  matchedRequirements?: RequirementMatch[];
  /** 缺失的需求 */
  missingRequirements?: RequirementMatch[];
  /** 错误的需求 */
  incorrectRequirements?: RequirementMatch[];
  /** 多余的元素 */
  extraElements?: string[];
  /** 严重失败项 */
  criticalFailures?: string[];
}

const consistencyColors: Record<string, string> = {
  consistent: 'green',
  partially_consistent: 'orange',
  inconsistent: 'red',
};

const consistencyText: Record<string, string> = {
  consistent: '整体一致 — 图像与 Prompt 高度吻合',
  partially_consistent: '部分一致 — 存在部分偏差',
  inconsistent: '不一致 — 图像与 Prompt 存在重大偏差',
};

const formatItem = (label: string, count: number) => (
  <Space>
    <Text>{label}</Text>
    <Tag>{count}</Tag>
  </Space>
);

export default function AnalysisPanel({
  structuredDescription,
  llmAnalysis,
  llmConsistency,
  matchedRequirements,
  missingRequirements,
  incorrectRequirements,
  extraElements,
  criticalFailures,
}: AnalysisPanelProps) {
  const hasRequirements =
    (matchedRequirements && matchedRequirements.length > 0) ||
    (missingRequirements && missingRequirements.length > 0) ||
    (incorrectRequirements && incorrectRequirements.length > 0) ||
    (extraElements && extraElements.length > 0) ||
    (criticalFailures && criticalFailures.length > 0);

  return (
    <Card title={<><BulbOutlined /> 需求分析详情</>}>
      {/* Consistency Summary */}
      {llmConsistency && (
        <div style={{ marginBottom: 20, textAlign: 'center' }}>
          <Tag
            color={consistencyColors[llmConsistency]}
            style={{ fontSize: 15, padding: '4px 20px', marginBottom: 6 }}
          >
            {llmConsistency === 'consistent' && <CheckCircleOutlined />}
            {llmConsistency === 'partially_consistent' && <WarningOutlined />}
            {llmConsistency === 'inconsistent' && <CloseCircleOutlined />}
            {' '}
            {consistencyText[llmConsistency] || llmConsistency}
          </Tag>
        </div>
      )}

      {/* Requirement Matching Stats */}
      {hasRequirements && (
        <>
          <Divider orientation="left">
            <Space size="middle">
              {formatItem('✅ 匹配需求', matchedRequirements?.length || 0)}
              {formatItem('⚠️ 缺失需求', missingRequirements?.length || 0)}
              {formatItem('❌ 错误需求', incorrectRequirements?.length || 0)}
              {extraElements && extraElements.length > 0 && formatItem('➕ 多余元素', extraElements.length)}
              {criticalFailures && criticalFailures.length > 0 && formatItem('🔥 严重失败', criticalFailures.length)}
            </Space>
          </Divider>

          <Collapse
            size="small"
            items={[
              matchedRequirements && matchedRequirements.length > 0 && {
                key: 'matched',
                label: (
                  <Space>
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                    <Text strong>已匹配需求 ({matchedRequirements.length})</Text>
                  </Space>
                ),
                children: (
                  <List
                    size="small"
                    dataSource={matchedRequirements}
                    renderItem={(item: RequirementMatch) => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                          title={item.item}
                          description={item.evidence && (
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              依据: {item.evidence}
                              {item.confidence != null && (
                                <Tag style={{ marginLeft: 8 }}>置信度 {item.confidence}</Tag>
                              )}
                            </Text>
                          )}
                        />
                      </List.Item>
                    )}
                  />
                ),
              },
              missingRequirements && missingRequirements.length > 0 && {
                key: 'missing',
                label: (
                  <Space>
                    <WarningOutlined style={{ color: '#faad14' }} />
                    <Text strong>缺失需求 ({missingRequirements.length})</Text>
                  </Space>
                ),
                children: (
                  <List
                    size="small"
                    dataSource={missingRequirements}
                    renderItem={(item: RequirementMatch) => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={<WarningOutlined style={{ color: '#faad14' }} />}
                          title={<Text style={{ color: '#faad14' }}>{item.item}</Text>}
                          description={item.evidence && (
                            <Text type="secondary" style={{ fontSize: 12 }}>依据: {item.evidence}</Text>
                          )}
                        />
                      </List.Item>
                    )}
                  />
                ),
              },
              incorrectRequirements && incorrectRequirements.length > 0 && {
                key: 'incorrect',
                label: (
                  <Space>
                    <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                    <Text strong>错误需求 ({incorrectRequirements.length})</Text>
                  </Space>
                ),
                children: (
                  <List
                    size="small"
                    dataSource={incorrectRequirements}
                    renderItem={(item: RequirementMatch) => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
                          title={<Text style={{ color: '#ff4d4f' }}>{item.item}</Text>}
                          description={item.evidence && (
                            <Text type="secondary" style={{ fontSize: 12 }}>依据: {item.evidence}</Text>
                          )}
                        />
                      </List.Item>
                    )}
                  />
                ),
              },
              extraElements && extraElements.length > 0 && {
                key: 'extra',
                label: (
                  <Space>
                    <MinusCircleOutlined style={{ color: '#1677ff' }} />
                    <Text strong>多余元素 ({extraElements.length})</Text>
                  </Space>
                ),
                children: (
                  <List
                    size="small"
                    dataSource={extraElements}
                    renderItem={(item: string) => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={<MinusCircleOutlined style={{ color: '#1677ff' }} />}
                          title={item}
                        />
                      </List.Item>
                    )}
                  />
                ),
              },
              criticalFailures && criticalFailures.length > 0 && {
                key: 'critical',
                label: (
                  <Space>
                    <ExclamationCircleOutlined style={{ color: '#cf1322' }} />
                    <Text strong style={{ color: '#cf1322' }}>严重失败 ({criticalFailures.length})</Text>
                  </Space>
                ),
                children: (
                  <List
                    size="small"
                    dataSource={criticalFailures}
                    renderItem={(item: string) => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={<ExclamationCircleOutlined style={{ color: '#cf1322' }} />}
                          title={<Text style={{ color: '#cf1322' }}>{item}</Text>}
                        />
                      </List.Item>
                    )}
                  />
                ),
              },
            ].filter(Boolean) as { key: string; label: React.ReactNode; children: React.ReactNode }[]}
          />
        </>
      )}

      {/* Structured Description */}
      <Divider orientation="left" style={{ marginTop: 20 }}>结构化描述</Divider>
      {structuredDescription ? (
        <Paragraph style={{
          background: '#fafafa',
          borderRadius: 6,
          padding: 12,
          border: '1px solid #f0f0f0',
          whiteSpace: 'pre-wrap',
        }}>
          {structuredDescription}
        </Paragraph>
      ) : (
        <Empty description="暂无结构化描述" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}

      {/* LLM Analysis */}
      <Divider orientation="left">LLM 详细分析</Divider>
      {llmAnalysis ? (
        <Paragraph style={{
          background: '#fafafa',
          borderRadius: 6,
          padding: 12,
          border: '1px solid #f0f0f0',
          whiteSpace: 'pre-wrap',
        }}>
          {llmAnalysis}
        </Paragraph>
      ) : (
        <Empty description="暂无 LLM 分析" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </Card>
  );
}
