/**
 * Unified Authentication Components
 * Cross-platform accessible authentication components
 * 
 * @fileoverview Exports unified auth components for all platforms
 * @version 1.0.0
 */

// Platform detection
const isReactNative = typeof window === 'undefined' && typeof global !== 'undefined';

// Export the appropriate component based on platform
export { UnifiedLogin } from './UnifiedLogin';

// Export React Native component specifically
export { UnifiedLoginNative } from './UnifiedLogin.native';

// Export types and interfaces
export type {
  LoginProps,
  LoginCredentials,
  FormValidation
} from './UnifiedLogin';

// Platform-specific exports
export const PlatformLogin = isReactNative 
  ? require('./UnifiedLogin.native').UnifiedLoginNative
  : require('./UnifiedLogin').UnifiedLogin;

/**
 * Component Usage Examples:
 * 
 * React Web/Electron:
 * ```tsx
 * import { UnifiedLogin } from './components/auth';
 * 
 * const App = () => {
 *   const handleLogin = async (credentials) => {
 *     // Handle login logic
 *     return true; // or false
 *   };
 * 
 *   return (
 *     <UnifiedLogin
 *       onSubmit={handleLogin}
 *       onForgotPassword={() => navigate('/forgot-password')}
 *       onRegister={() => navigate('/register')}
 *       socialLogin={true}
 *       variant="page"
 *       platform="web"
 *     />
 *   );
 * };
 * ```
 * 
 * React Native:
 * ```tsx
 * import { UnifiedLoginNative } from './components/auth';
 * 
 * const LoginScreen = () => {
 *   const handleLogin = async (credentials) => {
 *     // Handle login logic
 *     return true; // or false
 *   };
 * 
 *   return (
 *     <UnifiedLoginNative
 *       onSubmit={handleLogin}
 *       onForgotPassword={() => navigation.navigate('ForgotPassword')}
 *       onRegister={() => navigation.navigate('Register')}
 *       biometricLogin={true}
 *     />
 *   );
 * };
 * ```
 * 
 * Streamlit:
 * ```python
 * from components.auth.UnifiedLogin_streamlit import render_unified_login
 * 
 * def handle_login(credentials):
 *     # Handle login logic
 *     return True  # or False
 * 
 * # In your Streamlit app
 * credentials = render_unified_login(
 *     on_submit=handle_login,
 *     show_social_login=True,
 *     show_remember_me=True
 * )
 * 
 * if credentials:
 *     st.success("Login successful!")
 * ```
 */