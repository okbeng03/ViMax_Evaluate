/**
 * Evaluation detail page
 * 
 * TBD: Implements US4 evaluation detail functionality
 */

import { Card, Typography } from 'antd';
import { useParams } from 'react-router-dom';

const { Title } = Typography;

export default function EvaluationDetailPage() {
  const { taskId } = useParams<{ taskId: string }>();

  return (
    <Card>
      <Title level={2}>评估详情 - {taskId}</Title>
      <p>页面开发中...</p>
    </Card>
  );
}
