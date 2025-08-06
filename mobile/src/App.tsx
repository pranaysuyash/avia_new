import React from 'react';
import { StatusBar } from 'react-native';
import { AuthProvider } from './contexts/AuthContext';
import { UsageProvider } from './contexts/UsageContext';
import AppNavigator from './navigation/AppNavigator';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <UsageProvider>
        <StatusBar barStyle="light-content" backgroundColor="#3498db" />
        <AppNavigator />
      </UsageProvider>
    </AuthProvider>
  );
};

export default App;