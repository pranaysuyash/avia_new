# Vite Migration Plan

## Overview
Migrating the React transcription frontend from react-scripts 5.0.1 to Vite for improved performance, faster development, and modern tooling.

## Current State Analysis
- **Build Tool**: react-scripts 5.0.1 with CRACO overrides
- **Framework**: React 18.2.0 with TypeScript
- **Dependencies**: 62 production dependencies, 16 dev dependencies
- **Key Features**: Material-UI, Chart.js, WebSocket support, file uploads
- **Proxy Setup**: API requests proxied to http://localhost:8001

## Migration Benefits
- **⚡ 10-100x faster development server** startup and HMR
- **📦 Faster production builds** with Rollup
- **🔥 Instant hot module replacement**
- **🛠️ Better TypeScript support** and error reporting
- **📱 Modern ES modules** and tree-shaking
- **🎯 Simplified configuration** without CRACO

## Step-by-Step Migration Plan

### Phase 1: Preparation & Backup
1. **Backup current configuration**
   - Save working react-scripts setup
   - Document current proxy configuration
   - Note environment variables usage

2. **Analyze dependencies**
   - Identify Vite compatibility issues
   - Check for webpack-specific dependencies
   - Plan necessary replacements

### Phase 2: Vite Installation & Configuration
3. **Install Vite and essential plugins**
   ```bash
   npm install --save-dev vite @vitejs/plugin-react-swc
   npm install --save-dev @types/node
   ```

4. **Create Vite configuration**
   - Setup vite.config.ts
   - Configure proxy for API requests
   - Setup TypeScript paths
   - Configure build optimizations

5. **Update package.json scripts**
   - Replace react-scripts commands with Vite
   - Update build and dev scripts
   - Configure preview script

### Phase 3: Code & Asset Migration
6. **Migrate index.html**
   - Move from public/ to root
   - Update script references
   - Add Vite-specific script tag

7. **Update environment variables**
   - Change from REACT_APP_ to VITE_
   - Update .env files
   - Update code references

8. **Fix import paths**
   - Update absolute imports
   - Fix public asset references
   - Update CSS imports

### Phase 4: Testing & Optimization
9. **Test functionality**
   - Verify all components load
   - Test API proxy
   - Validate TypeScript compilation
   - Check hot module replacement

10. **Optimize configuration**
    - Configure chunk splitting
    - Setup build optimizations
    - Configure dev server settings

### Phase 5: Cleanup
11. **Remove deprecated dependencies**
    - Uninstall react-scripts
    - Remove CRACO
    - Clean up unnecessary webpack-related packages

## Key Configuration Files

### vite.config.ts
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3002,
    proxy: {
      '/api': 'http://localhost:8001'
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@mui/material', '@mui/icons-material'],
          charts: ['chart.js', 'react-chartjs-2']
        }
      }
    }
  }
})
```

### Environment Variables Migration
- `REACT_APP_API_URL` → `VITE_API_URL`
- `REACT_APP_WEBSOCKET_URL` → `VITE_WEBSOCKET_URL`
- All environment variables need VITE_ prefix

### Import Updates
- Public assets: `/assets/logo.png` → `/logo.png`
- Environment: `process.env.REACT_APP_*` → `import.meta.env.VITE_*`

## Risk Mitigation
- **Backup Strategy**: Keep react-scripts as fallback during migration
- **Testing**: Comprehensive testing after each phase
- **Rollback Plan**: Document exact steps to revert if needed

## Success Criteria
- ✅ Development server starts in <1 second
- ✅ Hot module replacement works instantly
- ✅ All existing functionality preserved
- ✅ Build time reduced by 50%+
- ✅ Bundle size optimized
- ✅ TypeScript compilation faster

## Timeline
- **Preparation**: 5 minutes
- **Installation**: 5 minutes  
- **Configuration**: 10 minutes
- **Migration**: 15 minutes
- **Testing**: 10 minutes
- **Total**: ~45 minutes

## Post-Migration Benefits
- Faster development experience
- Better debugging with source maps
- Modern build optimizations
- Simplified maintenance
- Future-proof tooling