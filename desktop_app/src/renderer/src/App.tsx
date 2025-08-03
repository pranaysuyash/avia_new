import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { motion } from 'framer-motion';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import Dashboard from './screens/Dashboard';
import TranscriptionWorkspace from './screens/TranscriptionWorkspace';
import VisualSearch from './screens/VisualSearch';
import Recommendations from './screens/Recommendations';
import ContentAnalysis from './screens/ContentAnalysis';
import AdvancedSearch from './screens/AdvancedSearch';
import ProcessingQueue from './screens/ProcessingQueue';
import History from './screens/History';
import Settings from './screens/Settings';
import AdminPanel from './screens/AdminPanel';
import Login from './screens/Login';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import './styles/globals.css';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Login route - no layout */}
            <Route path="/login" element={<Login />} />
            
            {/* Main app routes with layout */}
            <Route path="/*" element={
              <ProtectedRoute>
                <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
                  {/* Sidebar */}
                  <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
                  
                  {/* Main Content */}
                  <div className={`flex-1 flex flex-col overflow-hidden transition-all duration-300 ${
                    sidebarOpen ? 'ml-64' : 'ml-16'
                  }`}>
                    {/* Header */}
                    <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
                    
                    {/* Page Content */}
                    <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 dark:bg-gray-900">
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        className="container mx-auto px-6 py-8"
                      >
                        <Routes>
                          <Route path="/" element={<Dashboard />} />
                          <Route path="/workspace" element={<TranscriptionWorkspace />} />
                          <Route path="/visual-search" element={<VisualSearch />} />
                          <Route path="/recommendations" element={<Recommendations />} />
                          <Route path="/content-analysis" element={<ContentAnalysis />} />
                          <Route path="/advanced-search" element={<AdvancedSearch />} />
                          <Route path="/queue" element={<ProcessingQueue />} />
                          <Route path="/history" element={<History />} />
                          <Route path="/admin" element={<AdminPanel />} />
                          <Route path="/settings" element={<Settings />} />
                        </Routes>
                      </motion.div>
                    </main>
                  </div>
                </div>
              </ProtectedRoute>
            } />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;