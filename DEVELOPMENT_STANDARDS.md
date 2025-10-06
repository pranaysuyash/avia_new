# Development Standards and Guidelines

## Overview

This document establishes comprehensive development standards for the Backend-Frontend Integration Modernization project. These standards ensure consistency, maintainability, and quality across all platforms.

## Code Organization Standards

### File Size Limits

| File Type | Maximum Lines | Rationale |
|-----------|---------------|-----------|
| **API Routers** | 300 lines | Single responsibility, easy testing |
| **React Components** | 200 lines | Component reusability, maintainability |
| **Backend Modules** | 400 lines | Business logic separation |
| **Test Files** | 500 lines | Comprehensive test coverage |
| **Configuration Files** | 100 lines | Simple, focused configuration |

### Naming Conventions

#### Backend (Python)
```python
# Files
api_router_name.py          # API routers
service_name_service.py     # Service layer
model_name.py              # Data models
test_feature_name.py       # Test files

# Classes
class UserService:         # PascalCase for classes
class APIResponse:         # Acronyms in PascalCase

# Functions and variables
def process_audio_file():  # snake_case for functions
user_id = "123"           # snake_case for variables

# Constants
MAX_FILE_SIZE = 1024      # UPPER_SNAKE_CASE for constants
```

#### Frontend (TypeScript/React)
```typescript
// Files
ComponentName.tsx          // PascalCase for components
serviceName.ts            // camelCase for services
types.ts                  // lowercase for types
ComponentName.test.tsx    // Test files

// Components
export const UserProfile: React.FC = () => {}  // PascalCase

// Functions and variables
const handleSubmit = () => {}  // camelCase
const userId = "123"          // camelCase

// Types and interfaces
interface UserProfile {}     // PascalCase
type ApiResponse<T> = {}     // PascalCase

// Constants
const MAX_RETRY_ATTEMPTS = 3  // UPPER_SNAKE_CASE
```

## API Development Standards

### Standardized Response Format

```python
from typing import Generic, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standardized API response format"""
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PaginatedResponse(APIResponse[List[T]]):
    """Paginated response format"""
    pagination: PaginationInfo
    
class PaginationInfo(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool

# Usage examples
@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_users(page: int = 1, limit: int = 20):
    users, total = await user_service.get_users(page, limit)
    return PaginatedResponse(
        success=True,
        data=users,
        pagination=PaginationInfo(
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit,
            has_next=page * limit < total,
            has_prev=page > 1
        )
    )
```

### Error Handling Standards

```python
from enum import Enum
from fastapi import HTTPException

class ErrorCode(str, Enum):
    # Authentication errors
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Validation errors
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    
    # Business logic errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    
    # System errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

class APIError(HTTPException):
    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.details = details or {}
        
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code.value,
                "message": message,
                "details": self.details,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Usage
@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await user_service.get_user(user_id)
    if not user:
        raise APIError(
            status_code=404,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"User with ID {user_id} not found",
            details={"user_id": user_id}
        )
    return APIResponse(success=True, data=user)
```

### Authentication Standards

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

security = HTTPBearer()

class AuthLevel(str, Enum):
    PUBLIC = "public"           # No authentication required
    AUTHENTICATED = "authenticated"  # Valid token required
    ADMIN = "admin"            # Admin role required
    OWNER = "owner"            # Resource owner or admin

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise APIError(
                status_code=401,
                error_code=ErrorCode.AUTHENTICATION_FAILED,
                message="Invalid token"
            )
        user = await user_service.get_user(user_id)
        if user is None:
            raise APIError(
                status_code=401,
                error_code=ErrorCode.AUTHENTICATION_FAILED,
                message="User not found"
            )
        return user
    except JWTError:
        raise APIError(
            status_code=401,
            error_code=ErrorCode.AUTHENTICATION_FAILED,
            message="Invalid token"
        )

def require_auth(auth_level: AuthLevel = AuthLevel.AUTHENTICATED):
    """Decorator for endpoint authentication"""
    def decorator(func):
        if auth_level == AuthLevel.PUBLIC:
            return func
        elif auth_level == AuthLevel.AUTHENTICATED:
            return Depends(get_current_user)(func)
        # Add other auth levels as needed
    return decorator
```

## React Component Standards

### Component Structure Template

```typescript
import React, { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// Types
interface ComponentProps {
  id: string;
  className?: string;
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
}

interface ComponentState {
  isLoading: boolean;
  error: string | null;
  data: any | null;
}

// Component
export const ComponentName: React.FC<ComponentProps> = ({
  id,
  className = '',
  onSuccess,
  onError
}) => {
  // State
  const [localState, setLocalState] = useState<ComponentState>({
    isLoading: false,
    error: null,
    data: null
  });

  // API calls
  const { data, isLoading, error } = useQuery({
    queryKey: ['component-data', id],
    queryFn: () => apiClient.get(`/api/component/${id}`),
    enabled: !!id
  });

  const mutation = useMutation({
    mutationFn: (data: any) => apiClient.post('/api/component', data),
    onSuccess: (data) => {
      onSuccess?.(data);
    },
    onError: (error) => {
      onError?.(error as Error);
    }
  });

  // Event handlers
  const handleSubmit = useCallback(async (formData: any) => {
    try {
      await mutation.mutateAsync(formData);
    } catch (error) {
      console.error('Submit failed:', error);
    }
  }, [mutation]);

  // Effects
  useEffect(() => {
    if (error) {
      setLocalState(prev => ({ ...prev, error: error.message }));
    }
  }, [error]);

  // Loading state
  if (isLoading) {
    return <LoadingSpinner />;
  }

  // Error state
  if (error) {
    return (
      <div className="error-container">
        <p>Error: {error.message}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  // Main render
  return (
    <ErrorBoundary>
      <div className={`component-container ${className}`}>
        {/* Component content */}
      </div>
    </ErrorBoundary>
  );
};

// Default props
ComponentName.displayName = 'ComponentName';

export default ComponentName;
```

### State Management Standards

```typescript
// Use React Query for server state
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Use React hooks for local state
import { useState, useReducer, useContext } from 'react';

// Use Context for shared application state
interface AppContextType {
  user: User | null;
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
}

const AppContext = React.createContext<AppContextType | undefined>(undefined);

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};
```

### Error Handling Standards

```typescript
import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Send to error reporting service
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false })}>
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook for error handling
export const useErrorHandler = () => {
  const handleError = useCallback((error: Error, context?: string) => {
    console.error(`Error${context ? ` in ${context}` : ''}:`, error);
    
    // Show user-friendly error message
    toast.error(error.message || 'An unexpected error occurred');
    
    // Report to error tracking service
    errorReporting.captureException(error, { context });
  }, []);

  return { handleError };
};
```

## Testing Standards

### Backend Testing

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app import app

client = TestClient(app)

class TestUserAPI:
    """Test user API endpoints"""
    
    def test_create_user_success(self):
        """Test successful user creation"""
        user_data = {
            "email": "test@example.com",
            "password": "securepassword",
            "name": "Test User"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["user"]["email"] == user_data["email"]
    
    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email"""
        user_data = {
            "email": "existing@example.com",
            "password": "securepassword",
            "name": "Test User"
        }
        
        # Create first user
        client.post("/api/auth/register", json=user_data)
        
        # Try to create duplicate
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error_code"] == "RESOURCE_ALREADY_EXISTS"
    
    @patch('services.user_service.UserService.get_user')
    def test_get_user_not_found(self, mock_get_user):
        """Test getting non-existent user"""
        mock_get_user.return_value = None
        
        response = client.get("/api/users/999")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "RESOURCE_NOT_FOUND"
```

### Frontend Testing

```typescript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { ComponentName } from './ComponentName';
import { apiClient } from '@/lib/api-client';

// Mock API client
vi.mock('@/lib/api-client');
const mockApiClient = vi.mocked(apiClient);

// Test wrapper with providers
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('ComponentName', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    mockApiClient.get.mockImplementation(() => new Promise(() => {}));
    
    render(<ComponentName id="test-id" />, { wrapper: createWrapper() });
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders data when loaded successfully', async () => {
    const mockData = { id: 'test-id', name: 'Test Item' };
    mockApiClient.get.mockResolvedValue({ data: mockData });
    
    render(<ComponentName id="test-id" />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Item')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    const mockError = new Error('API Error');
    mockApiClient.get.mockRejectedValue(mockError);
    
    render(<ComponentName id="test-id" />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText(/Error: API Error/)).toBeInTheDocument();
    });
  });

  it('calls onSuccess callback when mutation succeeds', async () => {
    const onSuccess = vi.fn();
    const mockResponse = { success: true };
    mockApiClient.post.mockResolvedValue(mockResponse);
    
    render(<ComponentName id="test-id" onSuccess={onSuccess} />, { 
      wrapper: createWrapper() 
    });
    
    const submitButton = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith(mockResponse);
    });
  });
});
```

## Code Quality Tools

### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.36.0
    hooks:
      - id: eslint
        files: \.(js|jsx|ts|tsx)$
        types: [file]

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0-alpha.6
    hooks:
      - id: prettier
        files: \.(js|jsx|ts|tsx|json|css|md)$
```

### ESLint Configuration

```json
{
  "extends": [
    "@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint", "react", "react-hooks"],
  "rules": {
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",
    "@typescript-eslint/explicit-function-return-type": "off",
    "@typescript-eslint/explicit-module-boundary-types": "off",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "prefer-const": "error",
    "no-var": "error"
  },
  "settings": {
    "react": {
      "version": "detect"
    }
  }
}
```

### TypeScript Configuration

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["DOM", "DOM.Iterable", "ES6"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "ESNext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@/components/*": ["src/components/*"],
      "@/hooks/*": ["src/hooks/*"],
      "@/lib/*": ["src/lib/*"],
      "@/types/*": ["src/types/*"]
    }
  },
  "include": [
    "src/**/*"
  ],
  "exclude": [
    "node_modules",
    "dist",
    "build"
  ]
}
```

## Documentation Standards

### API Documentation

```python
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/users", tags=["Users"])

class UserCreate(BaseModel):
    """User creation request model"""
    email: str = Field(..., description="User email address", example="user@example.com")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    name: str = Field(..., description="User full name", example="John Doe")

@router.post("/", response_model=APIResponse[UserResponse])
async def create_user(user: UserCreate):
    """
    Create a new user account.
    
    This endpoint creates a new user account with the provided information.
    The password will be hashed before storage.
    
    Args:
        user: User creation data
        
    Returns:
        APIResponse containing the created user data and access token
        
    Raises:
        APIError: If email already exists or validation fails
        
    Example:
        ```python
        response = await create_user({
            "email": "user@example.com",
            "password": "securepassword",
            "name": "John Doe"
        })
        ```
    """
    # Implementation here
    pass
```

### Component Documentation

```typescript
/**
 * UserProfile component displays and allows editing of user profile information.
 * 
 * @example
 * ```tsx
 * <UserProfile 
 *   userId="123"
 *   onUpdate={(user) => console.log('Updated:', user)}
 *   editable={true}
 * />
 * ```
 */
interface UserProfileProps {
  /** User ID to display profile for */
  userId: string;
  /** Whether the profile can be edited */
  editable?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Callback when user profile is updated */
  onUpdate?: (user: User) => void;
  /** Callback when an error occurs */
  onError?: (error: Error) => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({
  userId,
  editable = false,
  className = '',
  onUpdate,
  onError
}) => {
  // Component implementation
};
```

These development standards provide a solid foundation for consistent, maintainable, and high-quality code across the entire platform. All team members should follow these guidelines to ensure seamless collaboration and code quality.