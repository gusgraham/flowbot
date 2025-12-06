import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastProvider } from './contexts/ToastContext';
import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';
import Hub from './pages/Hub';
import Login from './pages/Login';
import SurveyList from './pages/fsm/SurveyList';
import SurveyDashboard from './pages/fsm/SurveyDashboard';
import MonitorDetail from './pages/fsm/MonitorDetail';
import InstallManagement from './pages/fsm/InstallManagement';
import InterimReviewPage from './pages/fsm/InterimReviewPage';
import AnalysisProjectList from './pages/analysis/AnalysisProjectList';
import AnalysisWorkbench from './pages/analysis/AnalysisWorkbench';
import VerificationProjectList from './pages/verification/VerificationProjectList';
import VerificationDashboard from './pages/verification/VerificationDashboard';
import WQProjectList from './pages/wq/WQProjectList';
import UserManagement from './pages/admin/UserManagement';

// Placeholder components for other routes
const Placeholder = ({ title }: { title: string }) => (
  <div className="p-8 text-center text-gray-500">
    <h2 className="text-2xl font-bold text-gray-300 mb-4">{title}</h2>
    <p>Module coming soon...</p>
  </div>
);

const ProtectedRoute = () => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
};

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<AuthLayout />}>
              <Route index element={<Login />} />
            </Route>

            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<MainLayout />}>
                <Route index element={<Hub />} />
                <Route path="fsm" element={<SurveyList />} />
                <Route path="fsm/:projectId" element={<SurveyDashboard />} />
                <Route path="fsm/monitor/:monitorId" element={<MonitorDetail />} />
                <Route path="fsm/install/:installId" element={<InstallManagement />} />
                <Route path="fsm/interim/:interimId" element={<InterimReviewPage />} />
                <Route path="analysis" element={<AnalysisProjectList />} />
                <Route path="analysis/:projectId" element={<AnalysisWorkbench />} />
                <Route path="verification" element={<VerificationProjectList />} />
                <Route path="verification/:projectId" element={<VerificationDashboard />} />
                <Route path="wq" element={<WQProjectList />} />
                <Route path="admin/users" element={<UserManagement />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App;
