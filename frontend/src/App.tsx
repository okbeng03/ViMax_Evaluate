/**
 * Root application component with routing
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  UploadOutlined,
  HistoryOutlined,
  FolderOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

import TaskSubmitPage from './pages/TaskSubmitPage';
import HistoryListPage from './pages/HistoryListPage';
import EvaluationDetailPage from './pages/EvaluationDetailPage';
import ProjectListPage from './pages/ProjectListPage';

const { Header, Content } = Layout;

function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const selectedKey = location.pathname.startsWith('/evaluation')
    ? '/submit'
    : location.pathname;

  const menuItems = [
    { key: '/submit', icon: <UploadOutlined />, label: '提交任务' },
    { key: '/history', icon: <HistoryOutlined />, label: '历史记录' },
    { key: '/projects', icon: <FolderOutlined />, label: '项目管理' },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <div style={{ color: 'white', fontSize: 18, fontWeight: 'bold', marginRight: 32 }}>
          Agent图像评估系统
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ flex: 1 }}
        />
      </Header>
      <Content style={{ padding: 0 }}>
        <Routes>
          <Route path="/submit" element={<TaskSubmitPage />} />
          <Route path="/history" element={<HistoryListPage />} />
          <Route path="/evaluation/:taskId" element={<EvaluationDetailPage />} />
          <Route path="/projects" element={<ProjectListPage />} />
          <Route path="/" element={<Navigate to="/submit" replace />} />
          <Route path="*" element={<Navigate to="/submit" replace />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default App;
