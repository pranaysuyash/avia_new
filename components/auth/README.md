# Unified Authentication Components

A comprehensive set of accessible, cross-platform authentication components following WCAG 2.1 AA guidelines and the unified design system.

## Features

- ✅ **WCAG 2.1 AA Compliant**: Full accessibility support with screen readers, keyboard navigation, and proper ARIA attributes
- 🎨 **Unified Design System**: Consistent styling across all platforms using centralized design tokens
- 📱 **Cross-Platform**: React Web, React Native, Electron, and Streamlit implementations
- 🔐 **Comprehensive Authentication**: Login, registration, password reset, and OAuth support
- 🛡️ **Security-First**: Input validation, secure password handling, and CSRF protection
- 🌍 **Internationalization**: Built-in i18n support for global applications
- ⚡ **Performance Optimized**: Lazy loading, code splitting, and efficient rendering

## Components

### UnifiedLogin
Primary login component for web and desktop applications.

**Features:**
- Email/password authentication
- Real-time validation with accessibility announcements
- OAuth integration (Google, GitHub)
- Remember me functionality
- Forgot password integration
- Multiple variants (page, modal, inline)
- High contrast and reduced motion support

### UnifiedLoginNative
Optimized login component for React Native mobile applications.

**Features:**
- Touch-optimized interface with 44px minimum touch targets
- Biometric authentication support (TouchID/FaceID)
- Platform-specific keyboard handling
- Native animations and haptic feedback
- Offline capability indicators
- Safe area and keyboard avoidance

### UnifiedLoginStreamlit
Server-side login component for Streamlit applications.

**Features:**
- Server-side validation and session management
- Streamlit-optimized UI components
- Social login redirects
- Form state persistence
- Built-in error handling

## Quick Start

### Installation

```bash
npm install framer-motion react-icons
# For React Native
npm install react-native-vector-icons react-native-safe-area-context
```

### Basic Usage

#### React Web/Electron

```tsx
import { UnifiedLogin } from './components/auth';

const LoginPage = () => {
  const handleLogin = async (credentials) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      return response.ok;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  return (
    <UnifiedLogin
      onSubmit={handleLogin}
      onForgotPassword={() => navigate('/forgot-password')}
      onRegister={() => navigate('/register')}
      socialLogin={true}
      variant="page"
    />
  );
};
```

#### React Native

```tsx
import { UnifiedLoginNative } from './components/auth';
import { useNavigation } from '@react-navigation/native';

const LoginScreen = () => {
  const navigation = useNavigation();

  const handleLogin = async (credentials) => {
    // Your login logic here
    return true;
  };

  return (
    <UnifiedLoginNative
      onSubmit={handleLogin}
      onForgotPassword={() => navigation.navigate('ForgotPassword')}
      onRegister={() => navigation.navigate('Register')}
      biometricLogin={true}
    />
  );
};
```

#### Streamlit

```python
import streamlit as st
from components.auth.UnifiedLogin_streamlit import render_unified_login

def authenticate_user(credentials):
    # Your authentication logic
    if credentials.email == "user@example.com" and credentials.password == "password":
        return True
    return False

# Main app
def main():
    st.title("My App")
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        credentials = render_unified_login(
            on_submit=authenticate_user,
            show_social_login=True
        )
        
        if credentials:
            st.session_state.authenticated = True
            st.rerun()
    else:
        st.success("Welcome to the app!")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

if __name__ == "__main__":
    main()
```

## Props Reference

### UnifiedLogin (React Web/Electron)

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onSubmit` | `(credentials: LoginCredentials) => Promise<boolean>` | Required | Login submission handler |
| `onForgotPassword` | `() => void` | Optional | Forgot password callback |
| `onRegister` | `() => void` | Optional | Registration callback |
| `loading` | `boolean` | `false` | External loading state |
| `error` | `string` | `undefined` | External error message |
| `socialLogin` | `boolean` | `true` | Show social login options |
| `rememberMe` | `boolean` | `true` | Show remember me checkbox |
| `autoFocus` | `boolean` | `true` | Auto-focus email field |
| `variant` | `'modal' \| 'page' \| 'inline'` | `'page'` | Component layout variant |
| `platform` | `'web' \| 'mobile' \| 'desktop'` | `'web'` | Platform-specific optimizations |

### UnifiedLoginNative (React Native)

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onSubmit` | `(credentials: LoginCredentials) => Promise<boolean>` | Required | Login submission handler |
| `onForgotPassword` | `() => void` | Optional | Forgot password callback |
| `onRegister` | `() => void` | Optional | Registration callback |
| `loading` | `boolean` | `false` | External loading state |
| `error` | `string` | `undefined` | External error message |
| `biometricLogin` | `boolean` | `true` | Show biometric login option |
| `rememberMe` | `boolean` | `true` | Show remember me checkbox |
| `autoFocus` | `boolean` | `true` | Auto-focus email field |

### render_unified_login (Streamlit)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `on_submit` | `Callable[[LoginCredentials], bool]` | Required | Login submission handler |
| `on_forgot_password` | `Callable` | `None` | Forgot password callback |
| `on_register` | `Callable` | `None` | Registration callback |
| `show_social_login` | `bool` | `True` | Show social login options |
| `show_remember_me` | `bool` | `True` | Show remember me checkbox |
| `form_key` | `str` | `"unified_login"` | Unique form identifier |

## Accessibility Features

### Keyboard Navigation
- Tab order follows logical flow
- Enter key submits form or moves to next field
- Escape key cancels modal dialogs
- Arrow keys for custom components

### Screen Reader Support
- Semantic HTML with proper roles
- ARIA labels and descriptions
- Live regions for dynamic content
- Form validation announcements

### Visual Accessibility
- WCAG 2.1 AA color contrast compliance
- Focus indicators with 2px outline
- High contrast mode support
- Reduced motion preferences respected

### Touch Accessibility
- Minimum 44px touch targets
- Sufficient spacing between interactive elements
- Haptic feedback on native platforms
- Gesture support where appropriate

## Customization

### Theme Integration

Components automatically use the unified design system. Customize by modifying the design tokens:

```typescript
// In your theme configuration
import { ThemeProvider } from '../shared/theme';

// Access theme values
const theme = ThemeProvider.web; // or .mobile
const primaryColor = theme.colors.primary.DEFAULT;
const spacing = theme.spacing.md;
```

### Platform-Specific Styling

```tsx
// Conditional styling based on platform
const getButtonStyle = () => {
  if (isElectron) {
    return 'electron-specific-class';
  }
  return 'web-specific-class';
};
```

### Custom Validation

```tsx
const customValidation = {
  email: (value: string) => ({
    isValid: value.includes('@company.com'),
    message: 'Please use your company email'
  }),
  password: (value: string) => ({
    isValid: value.length >= 8 && /[A-Z]/.test(value),
    message: 'Password must be 8+ characters with uppercase'
  })
};
```

## Testing

### Unit Tests

```tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UnifiedLogin } from './UnifiedLogin';

test('validates email format', async () => {
  const mockSubmit = jest.fn();
  render(<UnifiedLogin onSubmit={mockSubmit} />);
  
  const emailInput = screen.getByLabelText(/email/i);
  fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
  
  await waitFor(() => {
    expect(screen.getByText(/valid email address/i)).toBeInTheDocument();
  });
});
```

### Accessibility Tests

```tsx
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('should not have accessibility violations', async () => {
  const { container } = render(<UnifiedLogin onSubmit={() => Promise.resolve(true)} />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### E2E Tests

```typescript
// Playwright example
test('complete login flow', async ({ page }) => {
  await page.goto('/login');
  
  await page.fill('[aria-label="Email address"]', 'user@example.com');
  await page.fill('[aria-label="Password"]', 'password123');
  await page.click('button[type="submit"]');
  
  await expect(page).toHaveURL('/dashboard');
});
```

## Security Considerations

### Input Validation
- Client-side validation for UX
- Server-side validation for security
- XSS prevention with proper sanitization
- SQL injection protection with parameterized queries

### Password Security
- Secure password transmission (HTTPS)
- Password strength requirements
- Rate limiting for login attempts
- Account lockout mechanisms

### OAuth Security
- CSRF protection with state parameter
- Secure redirect URI validation
- Token validation and expiration
- Proper scope limitations

## Performance Optimization

### Bundle Size
- Tree-shaking for unused components
- Platform-specific builds
- Lazy loading for heavy components
- Dynamic imports for OAuth providers

### Runtime Performance
- Memoized validation functions
- Debounced input validation
- Optimized re-renders with React.memo
- Efficient animation libraries

### Mobile Performance
- Native component optimization
- Image compression and caching
- Offline capability indicators
- Battery usage optimization

## Troubleshooting

### Common Issues

**Component not rendering:**
- Check if design tokens are properly imported
- Verify theme provider is wrapped around components
- Ensure all required dependencies are installed

**Accessibility warnings:**
- Run axe-core tests to identify specific issues
- Check ARIA attributes are properly set
- Verify focus management in interactive flows

**OAuth not working:**
- Verify redirect URIs are configured correctly
- Check API endpoint availability
- Ensure proper CORS settings for web platforms

**Mobile issues:**
- Test on physical devices, not just simulators
- Verify SafeAreaProvider is properly configured
- Check platform-specific permission requirements

### Debug Mode

Enable debug mode for additional logging:

```tsx
const DEBUG_AUTH = process.env.NODE_ENV === 'development';

if (DEBUG_AUTH) {
  console.log('Auth component props:', props);
  console.log('Validation state:', validation);
}
```

## Contributing

When contributing to these components:

1. **Accessibility First**: Test with screen readers and keyboard navigation
2. **Cross-Platform**: Ensure changes work on all supported platforms
3. **Design System**: Use unified design tokens, don't hardcode values
4. **Documentation**: Update this README with any new features
5. **Testing**: Add tests for new functionality
6. **Performance**: Consider impact on bundle size and runtime performance

## License

MIT License - see LICENSE file for details.

---

*Built with ❤️ for accessible, cross-platform authentication*