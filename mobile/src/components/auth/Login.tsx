import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { Input, Button } from 'react-native-elements';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigation } from '@react-navigation/native';
import { logUxEvent } from '../../utils/uxTelemetry';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const { login } = useAuth();
  const navigation = useNavigation();

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please enter both email and password');
      await logUxEvent('login_failed', { reason: 'missing_fields' });
      return;
    }

    try {
      setLoading(true);
      await logUxEvent('login_submit', { email_present: !!email });
      await login(email, password);
      await logUxEvent('login_success');
    } catch (error: any) {
      Alert.alert('Login Failed', error.message || 'Invalid credentials');
      await logUxEvent('login_failed', { error: String(error?.message || error) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView 
        contentContainerStyle={styles.scrollContainer}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.logoContainer}>
          <Icon name="transcribe" size={80} color="#3498db" />
          <Text style={styles.appName}>NER Platform</Text>
          <Text style={styles.tagline}>Advanced Video Transcription & Analytics</Text>
        </View>

        <View style={styles.formContainer}>
          <Input
            placeholder="Email"
            leftIcon={<Icon name="email" size={20} color="#95a5a6" />}
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            containerStyle={styles.inputContainer}
            inputStyle={styles.input}
          />

          <Input
            placeholder="Password"
            leftIcon={<Icon name="lock" size={20} color="#95a5a6" />}
            rightIcon={
              <Icon 
                name={showPassword ? 'visibility-off' : 'visibility'} 
                size={20} 
                color="#95a5a6"
                onPress={() => setShowPassword(!showPassword)}
              />
            }
            value={password}
            onChangeText={setPassword}
            secureTextEntry={!showPassword}
            containerStyle={styles.inputContainer}
            inputStyle={styles.input}
          />

          <Button
            title="Login"
            loading={loading}
            buttonStyle={styles.loginButton}
            titleStyle={styles.loginButtonText}
            onPress={handleLogin}
          />

          <View style={styles.footer}>
            <Text style={styles.footerText}>Don't have an account? </Text>
            <Text 
              style={styles.signupLink}
              onPress={() => navigation.navigate('Register' as never)}
            >
              Sign Up
            </Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 50,
  },
  appName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginTop: 15,
  },
  tagline: {
    fontSize: 14,
    color: '#7f8c8d',
    marginTop: 5,
  },
  formContainer: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  inputContainer: {
    marginBottom: 15,
  },
  input: {
    fontSize: 16,
  },
  loginButton: {
    backgroundColor: '#3498db',
    borderRadius: 25,
    paddingVertical: 15,
    marginTop: 10,
  },
  loginButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 20,
  },
  footerText: {
    color: '#7f8c8d',
    fontSize: 14,
  },
  signupLink: {
    color: '#3498db',
    fontSize: 14,
    fontWeight: 'bold',
  },
});

export default Login;
