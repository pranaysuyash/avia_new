// Global Electron API declaration for TypeScript
export interface ElectronAPI {
  // App info
  getAppVersion: () => Promise<string>;
  
  // File dialogs
  showSaveDialog: (options: any) => Promise<{ filePath?: string; canceled: boolean }>;
  showOpenDialog: (options: any) => Promise<{ filePaths?: string[]; canceled: boolean }>;
  
  // External links
  openExternal: (url: string) => Promise<void>;
  
  // Platform info
  platform: string;
  
  // Notifications
  showNotification: (title: string, body: string) => void;
  
  // System info
  getSystemInfo: () => Promise<any>;
  
  // Command execution
  executeCommand: (command: string) => Promise<{ stdout: string; stderr: string }>;
  
  // File operations
  readSystemLogs: (logFile: string) => Promise<string>;
  openPath: (path: string) => Promise<void>;
  showItemInFolder: (path: string) => Promise<void>;
  saveDialog: (options: any) => Promise<{ filePath?: string; canceled: boolean }>;
  saveFile: (filePath: string, data: Buffer) => Promise<void>;
  showMessageBox: (options: any) => Promise<any>;
  relaunch: () => void;
  setAlwaysOnTop: (flag: boolean) => void;
  toggleFullScreen: () => void;
  exportData: (data: any, format: string) => Promise<boolean>;
  showContextMenu: (options: any) => Promise<any>;
  readFile: (filePath: string) => Promise<Buffer>;
  writeFile: (filePath: string, data: Buffer) => Promise<void>;
  
  // Custom transcription app methods
  transcription: {
    // Export functionality
    exportData: (data: any, format: string) => Promise<boolean>;
    
    // File operations
    saveTranscription: (data: any) => Promise<boolean>;
    loadTranscription: () => Promise<any>;
    
    // Settings
    getSettings: () => Promise<any>;
    saveSettings: (settings: any) => Promise<boolean>;
    
    // Recent files
    getRecentFiles: () => Promise<any[]>;
    addRecentFile: (file: any) => Promise<boolean>;
    
    // AI customization
    getCustomizations: () => Promise<any>;
    saveCustomizations: (customizations: any) => Promise<boolean>;
  };
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
    electron?: {
      ipcRenderer: {
        invoke: (channel: string, ...args: any[]) => Promise<any>;
      };
    };
  }
}