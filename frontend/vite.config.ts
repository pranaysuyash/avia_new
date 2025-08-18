import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3002,
    host: true,
    proxy: {
      // Proxy API requests to FastAPI backend
      '/api': {
        target: 'http://localhost:8005',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '~': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor libraries
          vendor: ['react', 'react-dom'],
          // UI libraries
          ui: ['@mui/material', '@mui/icons-material', '@mui/lab'],
          // Chart libraries
          charts: ['chart.js', 'react-chartjs-2', 'recharts'],
          // Query and state management
          query: ['@tanstack/react-query', '@apollo/client'],
          // Utility libraries
          utils: ['axios', 'date-fns', 'clsx', 'tailwind-merge'],
          // Communication libraries
          comms: ['socket.io-client', 'graphql', 'urql']
        }
      }
    },
    // Increase chunk size warning limit
    chunkSizeWarningLimit: 1000,
  },
  define: {
    // Define global constants
    global: 'globalThis',
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      '@mui/material',
      '@mui/icons-material',
      'chart.js',
      'react-chartjs-2',
      'socket.io-client'
    ],
    exclude: [
      // Exclude any problematic dependencies
    ]
  },
  css: {
    devSourcemap: true,
  },
  esbuild: {
    // Enable JSX in .js files
    loader: 'jsx',
    include: /src\/.*\.[jt]sx?$/,
    exclude: []
  }
})