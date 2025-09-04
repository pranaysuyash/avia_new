/**
 * Unified Login Component - React Native
 * Accessible, responsive login form optimized for mobile
 * Follows WCAG 2.1 AA guidelines and unified design system
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  AccessibilityInfo,
  Animated,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { ThemeProvider } from '../../shared/theme';
import { logUxEvent } from '../shared/uxTelemetry';

// Interfaces
interface LoginProps {
  onSubmit: (credentials: LoginCredentials) => Promise<boolean>;
  onForgotPassword?: () => void;
  onRegister?: () => void;
  loading?: boolean;
  error?: string;
  biometricLogin?: boolean;
  rememberMe?: boolean;
  autoFocus?: boolean;
}

interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

interface FormValidation {
  email: {
    isValid: boolean;
    message: string;
  };
  password: {
    isValid: boolean;
    message: string;
  };
}

// Get screen dimensions
const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

// Accessibility helpers
const announceToScreenReader = (message: string) => {
  AccessibilityInfo.announceForAccessibility(message);
};

const validateEmail = (email: string): { isValid: boolean; message: string } => {
  if (!email) {
    return { isValid: false, message: 'Email is required' };
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return { isValid: false, message: 'Please enter a valid email address' };
  }
  
  return { isValid: true, message: '' };
};

const validatePassword = (password: string): { isValid: boolean; message: string } => {
  if (!password) {
    return { isValid: false, message: 'Password is required' };
  }
  
  if (password.length < 6) {
    return { isValid: false, message: 'Password must be at least 6 characters' };
  }
  
  return { isValid: true, message: '' };
};

export const UnifiedLoginNative: React.FC<LoginProps> = ({
  onSubmit,
  onForgotPassword,
  onRegister,
  loading = false,
  error,
  biometricLogin = true,
  rememberMe = true,
  autoFocus = true,
}) => {
  // Theme
  const theme = ThemeProvider.mobile;
  
  // State management
  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: '',
    rememberMe: false
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [validation, setValidation] = useState<FormValidation>({
    email: { isValid: true, message: '' },
    password: { isValid: true, message: '' }
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  
  // Refs
  const emailRef = useRef<TextInput>(null);
  const passwordRef = useRef<TextInput>(null);
  
  // Animations
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  
  // Component mount animation
  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 500,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }),
    ]).start();
  }, [fadeAnim, slideAnim]);
  
  // Auto-focus email field
  useEffect(() => {
    if (autoFocus) {
      const timer = setTimeout(() => {
        emailRef.current?.focus();
      }, 600); // After animation
      
      return () => clearTimeout(timer);
    }
  }, [autoFocus]);
  
  // Announce errors to screen readers
  useEffect(() => {
    if (error) {
      announceToScreenReader(`Login error: ${error}`);
    }
  }, [error]);
  
  // Real-time validation
  const validateField = useCallback((field: 'email' | 'password', value: string) => {
    let validationResult;
    
    switch (field) {
      case 'email':
        validationResult = validateEmail(value);
        break;
      case 'password':
        validationResult = validatePassword(value);
        break;
      default:
        return;
    }
    
    setValidation(prev => ({
      ...prev,
      [field]: validationResult
    }));
  }, []);
  
  // Handle input changes
  const handleInputChange = useCallback((field: keyof LoginCredentials, value: string | boolean) => {
    setCredentials(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Validate on change for better UX
    if (typeof value === 'string' && (field === 'email' || field === 'password')) {
      validateField(field, value);
    }
  }, [validateField]);
  
  // Handle form submission
  const handleSubmit = useCallback(async () => {
    // Prevent double submission
    if (isSubmitting || loading) return;
    
    // Validate all fields
    const emailValidation = validateEmail(credentials.email);
    const passwordValidation = validatePassword(credentials.password);
    
    setValidation({
      email: emailValidation,
      password: passwordValidation
    });
    
    // Check if form is valid
    if (!emailValidation.isValid || !passwordValidation.isValid) {
      announceToScreenReader('Please correct the errors in the form');
      
      // Focus first invalid field
      if (!emailValidation.isValid) {
        emailRef.current?.focus();
      } else if (!passwordValidation.isValid) {
        passwordRef.current?.focus();
      }
      
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      await logUxEvent('login_submit', { email_present: !!credentials.email });
      const success = await onSubmit(credentials);
      
      if (success) {
        await logUxEvent('login_success');
        announceToScreenReader('Login successful');
      } else {
        await logUxEvent('login_failed', { reason: 'invalid_credentials' });
        announceToScreenReader('Login failed. Please check your credentials.');
      }
    } catch (err) {
      console.error('Login error:', err);
      await logUxEvent('login_failed', { error: String(err) });
      announceToScreenReader('An error occurred during login');
    } finally {
      setIsSubmitting(false);
    }
  }, [credentials, isSubmitting, loading, onSubmit]);
  
  // Handle biometric authentication
  const handleBiometricLogin = useCallback(async () => {
    // Implementation would depend on biometric library
    // For now, just show an alert
    await logUxEvent('login_biometric_initiated');
    Alert.alert(
      'Biometric Login',
      'Biometric authentication would be implemented here',
      [{ text: 'OK' }]
    );
  }, []);
  
  // Dynamic styles
  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.backgroundPrimary,
    },
    scrollContainer: {
      flexGrow: 1,
      justifyContent: 'center',
      paddingHorizontal: theme.spacing.lg,
      paddingVertical: theme.spacing.xl,
    },
    animatedContainer: {
      transform: [{ translateY: slideAnim }],
      opacity: fadeAnim,
    },
    logoContainer: {
      alignItems: 'center',
      marginBottom: theme.spacing.xl * 2,
    },
    appName: {
      fontSize: theme.typography.h2.fontSize,
      fontWeight: theme.typography.h2.fontWeight,
      color: theme.colors.textPrimary,
      marginTop: theme.spacing.md,
      textAlign: 'center',
    },
    tagline: {
      fontSize: theme.typography.body2.fontSize,
      color: theme.colors.textSecondary,
      marginTop: theme.spacing.sm,
      textAlign: 'center',
    },
    formContainer: {
      marginBottom: theme.spacing.xl,
    },
    inputContainer: {
      marginBottom: theme.spacing.lg,
    },
    inputWrapper: {
      flexDirection: 'row',
      alignItems: 'center',
      borderWidth: 1,
      borderRadius: theme.borderRadius.md,
      backgroundColor: theme.colors.surface,
      minHeight: theme.accessibility.minTouchTarget,
    },
    inputWrapperFocused: {
      borderColor: theme.colors.primary,
      borderWidth: 2,
    },
    inputWrapperError: {
      borderColor: theme.colors.error,
    },
    inputIcon: {
      paddingHorizontal: theme.spacing.md,
    },
    textInput: {
      flex: 1,
      fontSize: theme.typography.body1.fontSize,
      color: theme.colors.textPrimary,
      paddingVertical: theme.spacing.md,
      paddingRight: theme.spacing.md,
      minHeight: theme.accessibility.minTouchTarget,
    },
    passwordToggle: {
      padding: theme.spacing.md,
      minWidth: theme.accessibility.minTouchTarget,
      minHeight: theme.accessibility.minTouchTarget,
      justifyContent: 'center',
      alignItems: 'center',
    },
    errorText: {
      color: theme.colors.error,
      fontSize: theme.typography.caption.fontSize,
      marginTop: theme.spacing.xs,
      marginLeft: theme.spacing.sm,
    },
    rememberMeContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: theme.spacing.lg,
    },
    checkboxContainer: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    checkbox: {
      width: 24,
      height: 24,
      borderWidth: 2,
      borderColor: theme.colors.border,
      borderRadius: 4,
      marginRight: theme.spacing.sm,
      justifyContent: 'center',
      alignItems: 'center',
    },
    checkboxChecked: {
      backgroundColor: theme.colors.primary,
      borderColor: theme.colors.primary,
    },
    checkboxLabel: {
      fontSize: theme.typography.body2.fontSize,
      color: theme.colors.textPrimary,
    },
    forgotPassword: {
      fontSize: theme.typography.body2.fontSize,
      color: theme.colors.primary,
      fontWeight: theme.typography.body2.fontWeight,
    },
    submitButton: {
      backgroundColor: theme.colors.primary,
      borderRadius: theme.borderRadius.md,
      paddingVertical: theme.spacing.md,
      paddingHorizontal: theme.spacing.lg,
      minHeight: theme.accessibility.minTouchTarget,
      flexDirection: 'row',
      justifyContent: 'center',
      alignItems: 'center',
      marginBottom: theme.spacing.lg,
    },
    submitButtonDisabled: {
      backgroundColor: theme.colors.border,
    },
    submitButtonText: {
      color: theme.colors.surface,
      fontSize: theme.typography.body1.fontSize,
      fontWeight: theme.typography.h6.fontWeight,
      marginLeft: theme.spacing.sm,
    },
    biometricButton: {
      backgroundColor: theme.colors.secondary,
      borderRadius: theme.borderRadius.md,
      paddingVertical: theme.spacing.md,
      paddingHorizontal: theme.spacing.lg,
      minHeight: theme.accessibility.minTouchTarget,
      flexDirection: 'row',
      justifyContent: 'center',
      alignItems: 'center',
      marginBottom: theme.spacing.lg,
    },
    biometricButtonText: {
      color: theme.colors.surface,
      fontSize: theme.typography.body1.fontSize,
      fontWeight: theme.typography.h6.fontWeight,
      marginLeft: theme.spacing.sm,
    },
    errorContainer: {
      backgroundColor: theme.colors.errorBackground,
      borderRadius: theme.borderRadius.md,
      padding: theme.spacing.md,
      marginBottom: theme.spacing.lg,
      flexDirection: 'row',
      alignItems: 'center',
    },
    errorIcon: {
      marginRight: theme.spacing.sm,
    },
    errorMessage: {
      flex: 1,
      color: theme.colors.error,
      fontSize: theme.typography.body2.fontSize,
    },
    footer: {
      flexDirection: 'row',
      justifyContent: 'center',
      alignItems: 'center',
      marginTop: theme.spacing.xl,
    },
    footerText: {
      fontSize: theme.typography.body2.fontSize,
      color: theme.colors.textSecondary,
    },
    signupLink: {
      fontSize: theme.typography.body2.fontSize,
      color: theme.colors.primary,
      fontWeight: theme.typography.h6.fontWeight,
    },
  });
  
  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContainer}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <Animated.View style={[styles.animatedContainer]}>
            {/* Logo and Header */}
            <View style={styles.logoContainer}>
              <Icon 
                name="transcribe" 
                size={80} 
                color={theme.colors.primary}
                accessible={true}
                accessibilityLabel="App logo"
              />
              <Text style={styles.appName}>NER Platform</Text>
              <Text style={styles.tagline}>Advanced Video Transcription & Analytics</Text>
            </View>
            
            {/* Error Display */}
            {error && (
              <View 
                style={styles.errorContainer}
                accessible={true}
                accessibilityRole="alert"
                accessibilityLiveRegion="assertive"
              >
                <Icon 
                  name="error-outline" 
                  size={20} 
                  color={theme.colors.error} 
                  style={styles.errorIcon}
                />
                <Text style={styles.errorMessage}>{error}</Text>
              </View>
            )}
            
            {/* Form */}
            <View style={styles.formContainer}>
              {/* Email Field */}
              <View style={styles.inputContainer}>
                <View style={[
                  styles.inputWrapper,
                  !validation.email.isValid && styles.inputWrapperError
                ]}>
                  <Icon 
                    name="email" 
                    size={20} 
                    color={theme.colors.textSecondary} 
                    style={styles.inputIcon}
                  />
                  <TextInput
                    ref={emailRef}
                    style={styles.textInput}
                    placeholder="Email address"
                    placeholderTextColor={theme.colors.textSecondary}
                    value={credentials.email}
                    onChangeText={(text) => handleInputChange('email', text)}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoCorrect={false}
                    returnKeyType="next"
                    onSubmitEditing={() => passwordRef.current?.focus()}
                    accessible={true}
                    accessibilityLabel="Email address"
                    accessibilityHint="Enter your email address to sign in"
                    accessibilityRole="text"
                    accessibilityRequired={true}
                  />
                </View>
                {validation.email.message ? (
                  <Text 
                    style={styles.errorText}
                    accessible={true}
                    accessibilityRole="text"
                    accessibilityLiveRegion="polite"
                  >
                    {validation.email.message}
                  </Text>
                ) : null}
              </View>
              
              {/* Password Field */}
              <View style={styles.inputContainer}>
                <View style={[
                  styles.inputWrapper,
                  !validation.password.isValid && styles.inputWrapperError
                ]}>
                  <Icon 
                    name="lock" 
                    size={20} 
                    color={theme.colors.textSecondary} 
                    style={styles.inputIcon}
                  />
                  <TextInput
                    ref={passwordRef}
                    style={styles.textInput}
                    placeholder="Password"
                    placeholderTextColor={theme.colors.textSecondary}
                    value={credentials.password}
                    onChangeText={(text) => handleInputChange('password', text)}
                    secureTextEntry={!showPassword}
                    returnKeyType="done"
                    onSubmitEditing={handleSubmit}
                    accessible={true}
                    accessibilityLabel="Password"
                    accessibilityHint="Enter your password. Must be at least 6 characters."
                    accessibilityRole="text"
                    accessibilityRequired={true}
                  />
                  <TouchableOpacity
                    style={styles.passwordToggle}
                    onPress={() => setShowPassword(!showPassword)}
                    accessible={true}
                    accessibilityRole="button"
                    accessibilityLabel={showPassword ? "Hide password" : "Show password"}
                    accessibilityHint="Toggle password visibility"
                  >
                    <Icon
                      name={showPassword ? 'visibility-off' : 'visibility'}
                      size={20}
                      color={theme.colors.textSecondary}
                    />
                  </TouchableOpacity>
                </View>
                {validation.password.message ? (
                  <Text 
                    style={styles.errorText}
                    accessible={true}
                    accessibilityRole="text"
                    accessibilityLiveRegion="polite"
                  >
                    {validation.password.message}
                  </Text>
                ) : null}
              </View>
              
              {/* Remember Me & Forgot Password */}
              <View style={styles.rememberMeContainer}>
                {rememberMe && (
                  <TouchableOpacity 
                    style={styles.checkboxContainer}
                    onPress={() => handleInputChange('rememberMe', !credentials.rememberMe)}
                    accessible={true}
                    accessibilityRole="checkbox"
                    accessibilityState={{ checked: credentials.rememberMe }}
                    accessibilityLabel="Remember me"
                    accessibilityHint="Keep me signed in on this device"
                  >
                    <View style={[
                      styles.checkbox,
                      credentials.rememberMe && styles.checkboxChecked
                    ]}>
                      {credentials.rememberMe && (
                        <Icon name="check" size={16} color={theme.colors.surface} />
                      )}
                    </View>
                    <Text style={styles.checkboxLabel}>Remember me</Text>
                  </TouchableOpacity>
                )}
                
                {onForgotPassword && (
                  <TouchableOpacity
                    onPress={onForgotPassword}
                    accessible={true}
                    accessibilityRole="button"
                    accessibilityLabel="Forgot your password?"
                    accessibilityHint="Reset your password"
                  >
                    <Text style={styles.forgotPassword}>Forgot password?</Text>
                  </TouchableOpacity>
                )}
              </View>
              
              {/* Submit Button */}
              <TouchableOpacity
                style={[
                  styles.submitButton,
                  (loading || isSubmitting) && styles.submitButtonDisabled
                ]}
                onPress={handleSubmit}
                disabled={loading || isSubmitting}
                accessible={true}
                accessibilityRole="button"
                accessibilityLabel="Sign in"
                accessibilityHint="Sign in with your email and password"
                accessibilityState={{ disabled: loading || isSubmitting }}
              >
                {(loading || isSubmitting) ? (
                  <Icon name="refresh" size={20} color={theme.colors.surface} />
                ) : (
                  <Icon name="login" size={20} color={theme.colors.surface} />
                )}
                <Text style={styles.submitButtonText}>
                  {(loading || isSubmitting) ? 'Signing in...' : 'Sign in'}
                </Text>
              </TouchableOpacity>
              
              {/* Biometric Login */}
              {biometricLogin && (
                <TouchableOpacity
                  style={styles.biometricButton}
                  onPress={handleBiometricLogin}
                  accessible={true}
                  accessibilityRole="button"
                  accessibilityLabel="Sign in with biometrics"
                  accessibilityHint="Use fingerprint or face recognition to sign in"
                >
                  <Icon name="fingerprint" size={20} color={theme.colors.surface} />
                  <Text style={styles.biometricButtonText}>Use Biometrics</Text>
                </TouchableOpacity>
              )}
            </View>
            
            {/* Footer */}
            {onRegister && (
              <View style={styles.footer}>
                <Text style={styles.footerText}>Don't have an account? </Text>
                <TouchableOpacity
                  onPress={onRegister}
                  accessible={true}
                  accessibilityRole="button"
                  accessibilityLabel="Create new account"
                  accessibilityHint="Go to registration screen"
                >
                  <Text style={styles.signupLink}>Sign Up</Text>
                </TouchableOpacity>
              </View>
            )}
          </Animated.View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

export default UnifiedLoginNative;
