/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_WS_URL: string
  readonly VITE_ENVIRONMENT: string
  readonly VITE_VERSION: string
  readonly VITE_SENTRY_DSN?: string
  // Add more env vars as needed
  [key: string]: any
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}