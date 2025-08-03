import { StyleSheet, Platform } from 'react-native';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingVertical: 40,
  },
  
  // Logo Section
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  appName: {
    fontSize: 28,
    fontWeight: '700',
    color: '#333333',
    marginTop: 12,
  },
  
  // Form Container
  formContainer: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 20,
    padding: 24,
    borderRadius: 16,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  
  title: {
    fontSize: 24,
    fontWeight: '600',
    color: '#333333',
    marginBottom: 8,
    textAlign: 'center',
  },
  
  subtitle: {
    fontSize: 16,
    color: '#666666',
    marginBottom: 24,
    textAlign: 'center',
  },
  
  // Input Styles
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8F8F8',
    borderRadius: 12,
    paddingHorizontal: 16,
    marginBottom: 16,
    height: 50,
  },
  
  inputIcon: {
    marginRight: 12,
  },
  
  input: {
    flex: 1,
    fontSize: 16,
    color: '#333333',
  },
  
  passwordToggle: {
    padding: 8,
  },
  
  // Options Row
  optionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  
  rememberMe: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  
  rememberMeText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#666666',
  },
  
  forgotPassword: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
  
  // Buttons
  loginButton: {
    backgroundColor: '#007AFF',
    height: 50,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  
  loginButtonDisabled: {
    opacity: 0.6,
  },
  
  loginButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  
  // Divider
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#E0E0E0',
  },
  
  dividerText: {
    marginHorizontal: 16,
    fontSize: 14,
    color: '#999999',
  },
  
  // Social Buttons
  socialButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 50,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    backgroundColor: '#FFFFFF',
    marginBottom: 12,
  },
  
  socialButtonText: {
    marginLeft: 12,
    fontSize: 16,
    color: '#333333',
    fontWeight: '500',
  },
  
  // Register Section
  registerContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 16,
  },
  
  registerText: {
    fontSize: 14,
    color: '#666666',
  },
  
  registerLink: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  
  // Error Message
  errorContainer: {
    backgroundColor: '#FFF5F5',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
  },
  
  errorText: {
    flex: 1,
    marginLeft: 8,
    fontSize: 14,
    color: '#E53E3E',
  },
  
  // Password Strength
  passwordStrengthContainer: {
    marginTop: 8,
    marginBottom: 16,
  },
  
  passwordStrengthBar: {
    height: 4,
    backgroundColor: '#E0E0E0',
    borderRadius: 2,
    overflow: 'hidden',
  },
  
  passwordStrengthFill: {
    height: '100%',
    borderRadius: 2,
  },
  
  passwordRequirements: {
    marginTop: 8,
  },
  
  requirementRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  
  requirementText: {
    marginLeft: 8,
    fontSize: 12,
    color: '#666666',
  },
  
  requirementMet: {
    color: '#48BB78',
  },
  
  // Terms Checkbox
  termsContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  
  termsCheckbox: {
    marginTop: 2,
  },
  
  termsText: {
    flex: 1,
    marginLeft: 8,
    fontSize: 14,
    color: '#666666',
    lineHeight: 20,
  },
  
  termsLink: {
    color: '#007AFF',
    textDecorationLine: 'underline',
  },
  
  // Success Message
  successContainer: {
    backgroundColor: '#F0FFF4',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  
  successIcon: {
    marginBottom: 12,
  },
  
  successTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#22543D',
    marginBottom: 8,
  },
  
  successText: {
    fontSize: 14,
    color: '#2F855A',
    textAlign: 'center',
    marginBottom: 16,
  },
  
  successButton: {
    backgroundColor: '#48BB78',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  
  successButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default styles;