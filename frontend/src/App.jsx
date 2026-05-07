import { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Lazy load components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Conversations = lazy(() => import('./pages/Conversations'));
const BotStudio = lazy(() => import('./pages/BotStudio'));
const SettingsView = lazy(() => import('./pages/studio/SettingsView'));
const KnowledgeView = lazy(() => import('./pages/studio/KnowledgeView'));
const ProviderView = lazy(() => import('./pages/studio/ProviderView'));
const AnalyticsView = lazy(() => import('./pages/studio/AnalyticsView'));
const TelegramView = lazy(() => import('./pages/studio/TelegramView'));
const Login = lazy(() => import('./pages/Login'));
const Signup = lazy(() => import('./pages/Signup'));
const UpgradePlanPage = lazy(() => import('./pages/UpgradePlanPage'));
const AdminProviderConfig = lazy(() => import('./pages/AdminProviderConfig'));

// Loading component
const LoadingSpinner = () => (
  <div className="flex items-center justify-center h-screen bg-[#0a0a0a]">
    <div className="w-8 h-8 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin"></div>
  </div>
);

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('access_token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <div className="bg-[#0a0a0a] text-white font-sans selection:bg-emerald-500/30 min-h-screen">
      {/* Background Glow */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] bg-emerald-500/10 blur-[150px] rounded-full" />
        <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] bg-blue-500/10 blur-[150px] rounded-full" />
      </div>
      <div className="relative z-10">
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/upgrade-plan" element={<ProtectedRoute><UpgradePlanPage /></ProtectedRoute>} />
            <Route path="/admin/providers" element={<ProtectedRoute><AdminProviderConfig /></ProtectedRoute>} />
            
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/conversations" element={<ProtectedRoute><Conversations /></ProtectedRoute>} />
            <Route path="/bot/:botId" element={<ProtectedRoute><BotStudio /></ProtectedRoute>}>
              <Route index element={<Navigate to="settings" replace />} />
              <Route path="settings" element={<SettingsView />} />
              <Route path="knowledge" element={<KnowledgeView />} />
              <Route path="provider" element={<ProviderView />} />
              <Route path="analytics" element={<AnalyticsView />} />
              <Route path="telegram" element={<TelegramView />} />
            </Route>
          </Routes>
        </Suspense>
      </div>
    </div>
  );
}

export default App;
