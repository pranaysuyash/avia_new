import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import styles from './styles';

interface ForgotPasswordProps {
  onSuccess?: () => void;
}

const ForgotPassword: React.FC<ForgotPasswordProps> = ({ onSuccess }) => {
  const navigation = useNavigation();
  
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const validateForm = () => {
    if (!email.trim()) {
      Alert.alert('Error', 'Please enter your email');
      return false;
    }
    
    if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      Alert.alert('Error', 'Please enter a valid email address');
      return false;
    }
    
    return true;
  };

  const handleResetPassword = async () => {
    if (!validateForm()) return;
    
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/auth/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setIsSuccess(true);
        if (onSuccess) {
          onSuccess();
        }
      } else {
        const errorData = await response.json();
        Alert.alert('Error', errorData.detail || 'Failed to send reset email. Please try again.');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to connect to server. Please try again.');
      console.error('Forgot password error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToLogin = () => {
    navigation.navigate('Login' as never);
  };

  if (isSuccess) {
    return (
      <View style={styles.container}>
        <View style={styles.successContainer}>
          <Icon
            name="check-circle"
            size={60}
            color="#48BB78"
            style={styles.successIcon}
          />
          <Text style={styles.successTitle}>Check your email</Text>
          <Text style={styles.successText}>
            We've sent a password reset link to:
          </Text>
          <Text style={[styles.successText, { fontWeight: '600' }]}>
            {email}
          </Text>
          <Text style={[styles.successText, { marginTop: 16 }]}>
            Didn't receive the email? Check your spam folder or try again.
          </Text>
          
          <TouchableOpacity
            style={styles.successButton}
            onPress={handleBackToLogin}
          >
            <Text style={styles.successButtonText}>Back to Sign In</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={{ marginTop: 16 }}
            onPress={() => setIsSuccess(false)}
          >
            <Text style={styles.registerLink}>Try different email</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContainer}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.formContainer}>
          <Icon name="lock-reset" size={60} color="#007AFF" style={{ alignSelf: 'center', marginBottom: 24 }} />
          
          <Text style={styles.title}>Forgot Password?</Text>
          <Text style={styles.subtitle}>
            No worries, we'll send you reset instructions.
          </Text>

          <View style={styles.inputContainer}>
            <Icon name="email" size={20} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Enter your email"
              placeholderTextColor="#999"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
            />
          </View>

          <TouchableOpacity
            style={[styles.loginButton, isLoading && styles.loginButtonDisabled]}
            onPress={handleResetPassword}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.loginButtonText}>Reset Password</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.registerContainer}
            onPress={handleBackToLogin}
          >
            <Icon name="arrow-back" size={20} color="#007AFF" />
            <Text style={[styles.registerLink, { marginLeft: 8 }]}>
              Back to Sign In
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

export default ForgotPassword;