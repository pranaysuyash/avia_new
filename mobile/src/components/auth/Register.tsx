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

interface RegisterProps {
  onSuccess?: () => void;
}

const Register: React.FC<RegisterProps> = ({ onSuccess }) => {
  const navigation = useNavigation();
  
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  const checkPasswordStrength = (pass: string) => {
    let strength = 0;
    if (pass.length >= 8) strength++;
    if (pass.match(/[a-z]/) && pass.match(/[A-Z]/)) strength++;
    if (pass.match(/\d/)) strength++;
    if (pass.match(/[^a-zA-Z\d]/)) strength++;
    setPasswordStrength(strength);
  };

  const handlePasswordChange = (text: string) => {
    setPassword(text);
    checkPasswordStrength(text);
  };

  const validateForm = () => {
    if (!fullName.trim()) {
      Alert.alert('Error', 'Please enter your full name');
      return false;
    }
    
    if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      Alert.alert('Error', 'Please enter a valid email address');
      return false;
    }
    
    if (password.length < 8) {
      Alert.alert('Error', 'Password must be at least 8 characters long');
      return false;
    }
    
    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return false;
    }
    
    if (!acceptTerms) {
      Alert.alert('Error', 'Please accept the terms and conditions');
      return false;
    }
    
    return true;
  };

  const handleRegister = async () => {
    if (!validateForm()) return;
    
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name: fullName,
          email: email,
          password: password,
        }),
      });

      if (response.ok) {
        Alert.alert(
          'Success',
          'Your account has been created successfully. Please check your email to verify your account.',
          [
            {
              text: 'OK',
              onPress: () => {
                if (onSuccess) {
                  onSuccess();
                } else {
                  navigation.navigate('Login' as never);
                }
              },
            },
          ]
        );
      } else {
        const errorData = await response.json();
        Alert.alert('Registration Failed', errorData.detail || 'Please try again.');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to connect to server. Please try again.');
      console.error('Registration error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getPasswordStrengthColor = () => {
    switch (passwordStrength) {
      case 0:
      case 1:
        return '#EF4444';
      case 2:
        return '#F59E0B';
      case 3:
        return '#3B82F6';
      case 4:
        return '#10B981';
      default:
        return '#E5E7EB';
    }
  };

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
          <Text style={styles.title}>Create Account</Text>
          <Text style={styles.subtitle}>Sign up to get started</Text>

          <View style={styles.inputContainer}>
            <Icon name="person" size={20} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Full Name"
              placeholderTextColor="#999"
              value={fullName}
              onChangeText={setFullName}
              autoComplete="name"
            />
          </View>

          <View style={styles.inputContainer}>
            <Icon name="email" size={20} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Email address"
              placeholderTextColor="#999"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
            />
          </View>

          <View style={styles.inputContainer}>
            <Icon name="lock" size={20} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Password"
              placeholderTextColor="#999"
              value={password}
              onChangeText={handlePasswordChange}
              secureTextEntry={!showPassword}
              autoComplete="password-new"
            />
            <TouchableOpacity
              onPress={() => setShowPassword(!showPassword)}
              style={styles.passwordToggle}
            >
              <Icon
                name={showPassword ? 'visibility-off' : 'visibility'}
                size={20}
                color="#666"
              />
            </TouchableOpacity>
          </View>

          {password.length > 0 && (
            <View style={styles.passwordStrengthContainer}>
              <View style={styles.passwordStrengthBar}>
                <View
                  style={[
                    styles.passwordStrengthFill,
                    {
                      width: `${(passwordStrength / 4) * 100}%`,
                      backgroundColor: getPasswordStrengthColor(),
                    },
                  ]}
                />
              </View>
              <View style={styles.passwordRequirements}>
                <View style={styles.requirementRow}>
                  <Icon
                    name="check-circle"
                    size={16}
                    color={password.length >= 8 ? '#10B981' : '#D1D5DB'}
                  />
                  <Text
                    style={[
                      styles.requirementText,
                      password.length >= 8 && styles.requirementMet,
                    ]}
                  >
                    At least 8 characters
                  </Text>
                </View>
                <View style={styles.requirementRow}>
                  <Icon
                    name="check-circle"
                    size={16}
                    color={
                      password.match(/[a-z]/) && password.match(/[A-Z]/)
                        ? '#10B981'
                        : '#D1D5DB'
                    }
                  />
                  <Text
                    style={[
                      styles.requirementText,
                      password.match(/[a-z]/) &&
                        password.match(/[A-Z]/) &&
                        styles.requirementMet,
                    ]}
                  >
                    Upper and lowercase letters
                  </Text>
                </View>
                <View style={styles.requirementRow}>
                  <Icon
                    name="check-circle"
                    size={16}
                    color={password.match(/\d/) ? '#10B981' : '#D1D5DB'}
                  />
                  <Text
                    style={[
                      styles.requirementText,
                      password.match(/\d/) && styles.requirementMet,
                    ]}
                  >
                    At least one number
                  </Text>
                </View>
                <View style={styles.requirementRow}>
                  <Icon
                    name="check-circle"
                    size={16}
                    color={password.match(/[^a-zA-Z\d]/) ? '#10B981' : '#D1D5DB'}
                  />
                  <Text
                    style={[
                      styles.requirementText,
                      password.match(/[^a-zA-Z\d]/) && styles.requirementMet,
                    ]}
                  >
                    At least one special character
                  </Text>
                </View>
              </View>
            </View>
          )}

          <View style={styles.inputContainer}>
            <Icon name="lock" size={20} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Confirm Password"
              placeholderTextColor="#999"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry={!showConfirmPassword}
              autoComplete="password-new"
            />
            <TouchableOpacity
              onPress={() => setShowConfirmPassword(!showConfirmPassword)}
              style={styles.passwordToggle}
            >
              <Icon
                name={showConfirmPassword ? 'visibility-off' : 'visibility'}
                size={20}
                color="#666"
              />
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={styles.termsContainer}
            onPress={() => setAcceptTerms(!acceptTerms)}
          >
            <Icon
              name={acceptTerms ? 'check-box' : 'check-box-outline-blank'}
              size={20}
              color={acceptTerms ? '#007AFF' : '#666'}
              style={styles.termsCheckbox}
            />
            <Text style={styles.termsText}>
              I agree to the{' '}
              <Text style={styles.termsLink}>Terms and Conditions</Text> and{' '}
              <Text style={styles.termsLink}>Privacy Policy</Text>
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.loginButton,
              (!acceptTerms || isLoading) && styles.loginButtonDisabled,
            ]}
            onPress={handleRegister}
            disabled={!acceptTerms || isLoading}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.loginButtonText}>Create Account</Text>
            )}
          </TouchableOpacity>

          <View style={styles.registerContainer}>
            <Text style={styles.registerText}>Already have an account? </Text>
            <TouchableOpacity onPress={() => navigation.navigate('Login' as never)}>
              <Text style={styles.registerLink}>Sign In</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

export default Register;