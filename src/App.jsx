import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import Conversations from './pages/Conversations';
import BotStudio from './pages/BotStudio';
import SettingsView from './pages/studio/SettingsView';
import KnowledgeView from './pages/studio/KnowledgeView';
import ProviderView from './pages/studio/ProviderView';
import AnalyticsView from './pages/studio/AnalyticsView';
import TelegramView from './pages/studio/TelegramView';
import Login from './pages/Login';
import Signup from './pages/Signup';
import UpgradePlanPage from './pages/UpgradePlanPage';

import './App.css';

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
    <BrowserRouter>
      <div className="min-h-screen bg-[#050505] text-white selection:bg-accent-blue/30">
        <Routes>
          {/* Public Landing Page */}
          <Route path="/" element={<LandingPage />} />
          
          {/* Auth Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          
          {/* Protected App Routes */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/conversations" 
            element={
              <ProtectedRoute>
                <Conversations />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/upgrade-plan" 
            element={
              <ProtectedRoute>
                <UpgradePlanPage />
              </ProtectedRoute>
            } 
          />

          <Route 
            path="/bot/:botId" 
            element={
              <ProtectedRoute>
                <BotStudio />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="settings" replace />} />
            <Route path="settings" element={<SettingsView />} />
            <Route path="knowledge" element={<KnowledgeView />} />
            <Route path="provider" element={<ProviderView />} />
            <Route path="analytics" element={<AnalyticsView />} />
            <Route path="telegram" element={<TelegramView />} />
          </Route>

          {/* Catch-all - redirect to landing */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
