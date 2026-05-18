/**
 * Score card component for displaying scores
 */

import { Card, Typography, Progress, Tag } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

interface ScoreCardProps {
  title: string;
  score: number;
  maxScore?: number;
  interpretation?: string;
  color?: string;
}

export default function ScoreCard({
  title,
  score,
  maxScore = 100,
  interpretation,
  color,
}: ScoreCardProps) {
  const percent = (score / maxScore) * 100;
  const progressColor =
    color ||
    (percent >= 70 ? '#52c41a' : percent >= 50 ? '#faad14' : '#ff4d4f');

  const getIcon = () => {
    if (!interpretation) return null;
    if (interpretation === 'consistent' || interpretation === 'consistent') {
      return <CheckCircleOutlined />;
    }
    if (interpretation === 'inconsistent' || interpretation === 'inconsistent') {
      return <CloseCircleOutlined />;
    }
    return <WarningOutlined />;
  };

  const getInterpretationText = () => {
    if (!interpretation) return null;
    const textMap: Record<string, string> = {
      consistent: '一致',
      inconsistent: '不一致',
      ambiguous: '模糊区间',
      partially_consistent: '部分一致',
    };
    return textMap[interpretation] || interpretation;
  };

  return (
    <Card title={title}>
      <div style={{ textAlign: 'center' }}>
        <Text type="secondary">{title}</Text>
        <Typography.Title level={2} style={{ margin: '8px 0' }}>
          {typeof score === 'number' && score <= 1
            ? `${(score * 100).toFixed(1)}%`
            : score.toFixed(1)}
        </Typography.Title>
        <Progress
          percent={percent}
          strokeColor={progressColor}
          showInfo={false}
        />
        {interpretation && (
          <Tag color={progressColor.replace('#', '')} style={{ marginTop: 8 }}>
            {getIcon()} {getInterpretationText()}
          </Tag>
        )}
      </div>
    </Card>
  );
}
