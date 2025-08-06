import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Import screens
import Login from '../components/auth/Login';
import Register from '../components/auth/Register';
import MainDashboard from '../components/dashboard/MainDashboard';
import TranscriptionResults from '../components/transcription/TranscriptionResults';
import EnterpriseSales from '../screens/EnterpriseSales';
import CustomerSupport from '../screens/CustomerSupport';
import MarketingDashboard from '../screens/MarketingDashboard';
import DeveloperPortal from '../screens/DeveloperPortal';
import ComplianceDashboard from '../screens/ComplianceDashboard';
import Settings from '../components/settings/Settings';

// Import auth context
import { useAuth } from '../contexts/AuthContext';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

const AuthStack = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name="Login" component={Login} />
    <Stack.Screen name="Register" component={Register} />
  </Stack.Navigator>
);

const MainTabs = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      tabBarIcon: ({ focused, color, size }) => {
        let iconName: string;

        switch (route.name) {
          case 'Dashboard':
            iconName = 'dashboard';
            break;
          case 'Sales':
            iconName = 'trending-up';
            break;
          case 'Support':
            iconName = 'support-agent';
            break;
          case 'Marketing':
            iconName = 'campaign';
            break;
          case 'Settings':
            iconName = 'settings';
            break;
          default:
            iconName = 'circle';
        }

        return <Icon name={iconName} size={size} color={color} />;
      },
      tabBarActiveTintColor: '#3498db',
      tabBarInactiveTintColor: '#95a5a6',
      tabBarStyle: {
        backgroundColor: 'white',
        borderTopWidth: 1,
        borderTopColor: '#ecf0f1',
        paddingBottom: 5,
        height: 60,
      },
      tabBarLabelStyle: {
        fontSize: 12,
      },
      headerStyle: {
        backgroundColor: '#3498db',
      },
      headerTintColor: 'white',
      headerTitleStyle: {
        fontWeight: 'bold',
      },
    })}
  >
    <Tab.Screen 
      name="Dashboard" 
      component={MainDashboard}
      options={{
        title: 'Dashboard',
      }}
    />
    <Tab.Screen 
      name="Sales" 
      component={EnterpriseSales}
      options={{
        title: 'Sales',
      }}
    />
    <Tab.Screen 
      name="Support" 
      component={CustomerSupport}
      options={{
        title: 'Support',
      }}
    />
    <Tab.Screen 
      name="Marketing" 
      component={MarketingDashboard}
      options={{
        title: 'Marketing',
      }}
    />
    <Tab.Screen 
      name="Settings" 
      component={Settings}
      options={{
        title: 'Settings',
      }}
    />
  </Tab.Navigator>
);

const AppStack = () => (
  <Stack.Navigator>
    <Stack.Screen 
      name="Main" 
      component={MainTabs} 
      options={{ headerShown: false }}
    />
    <Stack.Screen 
      name="Transcription" 
      component={TranscriptionResults}
      options={{
        title: 'Transcription Details',
        headerStyle: {
          backgroundColor: '#3498db',
        },
        headerTintColor: 'white',
      }}
    />
    <Stack.Screen 
      name="DeveloperPortal" 
      component={DeveloperPortal}
      options={{
        title: 'Developer Portal',
        headerStyle: {
          backgroundColor: '#3498db',
        },
        headerTintColor: 'white',
      }}
    />
    <Stack.Screen 
      name="ComplianceDashboard" 
      component={ComplianceDashboard}
      options={{
        title: 'Compliance & Security',
        headerStyle: {
          backgroundColor: '#3498db',
        },
        headerTintColor: 'white',
      }}
    />
  </Stack.Navigator>
);

const AppNavigator = () => {
  const { isAuthenticated } = useAuth();

  return (
    <NavigationContainer>
      {isAuthenticated ? <AppStack /> : <AuthStack />}
    </NavigationContainer>
  );
};

export default AppNavigator;