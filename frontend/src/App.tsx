/**
 * Root application component with routing
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import TaskSubmitPage from './pages/TaskSubmitPage';
import HistoryListPage from './pages/HistoryListPage';
import EvaluationDetailPage from './pages/EvaluationDetailPage';
import ProjectListPage from './pages/ProjectListPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<TaskSubmitPage />} />
      <Route path="/history" element={<HistoryListPage />} />
      <Route path="/detail/:taskId" element={<EvaluationDetailPage />} />
      <Route path="/projects" element={<ProjectListPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
