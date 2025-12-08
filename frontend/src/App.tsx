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
import { useCurrentUser } from './api/hooks';

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

const RequireAccess = ({ module }: { module: 'fsm' | 'fsa' | 'wq' | 'verification' | 'admin' }) => {
  const { data: user, isLoading } = useCurrentUser();

  if (isLoading) return <div className="p-8 text-center text-gray-400">Loading permissions...</div>;

  if (user?.is_superuser) return <Outlet />;

  let hasAccess = false;
  switch (module) {
    case 'fsm': hasAccess = !!user?.access_fsm; break;
    case 'fsa': hasAccess = !!user?.access_fsa; break;
    case 'wq': hasAccess = !!user?.access_wq; break;
    case 'verification': hasAccess = !!user?.access_verification; break;
    case 'admin': hasAccess = user?.role === 'Admin'; break;
  }

  if (!hasAccess) {
    return <Navigate to="/" replace />;
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

                {/* FSM Routes */}
                <Route element={<RequireAccess module="fsm" />}>
                  <Route path="fsm" element={<SurveyList />} />
                  <Route path="fsm/:projectId" element={<SurveyDashboard />} />
                  <Route path="fsm/monitor/:monitorId" element={<MonitorDetail />} />
                  <Route path="fsm/install/:installId" element={<InstallManagement />} />
                  <Route path="fsm/interim/:interimId" element={<InterimReviewPage />} />
                </Route>

                {/* Analysis Routes */}
                <Route element={<RequireAccess module="fsa" />}>
                  <Route path="analysis" element={<AnalysisProjectList />} />
                  <Route path="analysis/:projectId" element={<AnalysisWorkbench />} />
                </Route>

                {/* Verification Routes */}
                <Route element={<RequireAccess module="verification" />}>
                  <Route path="verification" element={<VerificationProjectList />} />
                  <Route path="verification/:projectId" element={<VerificationDashboard />} />
                </Route>

                {/* WQ Routes */}
                <Route element={<RequireAccess module="wq" />}>
                  <Route path="wq" element={<WQProjectList />} />
                </Route>

                {/* Admin Routes */}
                <Route element={<RequireAccess module="admin" />}>
                  <Route path="admin/users" element={<UserManagement />} />
                </Route>
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App;
