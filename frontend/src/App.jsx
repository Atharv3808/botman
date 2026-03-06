import { Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Conversations from './pages/Conversations';
import BotStudio from './pages/BotStudio';
import SettingsView from './pages/studio/SettingsView';
import KnowledgeView from './pages/studio/KnowledgeView';
import ProviderView from './pages/studio/ProviderView';
import AnalyticsView from './pages/studio/AnalyticsView';
import Login from './pages/Login';
import Signup from './pages/Signup';
import UpgradePlanPage from './pages/UpgradePlanPage';

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
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/upgrade-plan" element={<ProtectedRoute><UpgradePlanPage /></ProtectedRoute>} />
          
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/conversations" element={<ProtectedRoute><Conversations /></ProtectedRoute>} />
          <Route path="/bot/:botId" element={<ProtectedRoute><BotStudio /></ProtectedRoute>}>
            <Route index element={<Navigate to="settings" replace />} />
            <Route path="settings" element={<SettingsView />} />
            <Route path="knowledge" element={<KnowledgeView />} />
            <Route path="provider" element={<ProviderView />} />
            <Route path="analytics" element={<AnalyticsView />} />
          </Route>
        </Routes>
      </div>
    </div>
  );
}

export default App;
