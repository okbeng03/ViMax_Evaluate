/**
 * Analysis panel component for displaying LLM analysis
 */

import { Card, Typography, Divider, Tag, Space } from 'antd';

const { Title, Text, Paragraph } = Typography;

interface AnalysisPanelProps {
  structuredDescription?: string;
  llmAnalysis?: string;
  llmConsistency?: string;
}

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

export default function AnalysisPanel({
  structuredDescription,
  llmAnalysis,
  llmConsistency,
}: AnalysisPanelProps) {
  return (
    <Card title="分析详情">
      {llmConsistency && (
        <Space style={{ marginBottom: 16 }}>
          <Text type="secondary">一致性判断:</Text>
          <Tag color={consistencyColors[llmConsistency]}>
            {consistencyText[llmConsistency] || llmConsistency}
          </Tag>
        </Space>
      )}

      <Divider orientation="left">结构化描述</Divider>
      <Paragraph>
        {structuredDescription || (
          <Text type="secondary">暂无描述</Text>
        )}
      </Paragraph>

      <Divider orientation="left">LLM 分析</Divider>
      <Paragraph>
        {llmAnalysis || (
          <Text type="secondary">暂无分析</Text>
        )}
      </Paragraph>
    </Card>
  );
}
