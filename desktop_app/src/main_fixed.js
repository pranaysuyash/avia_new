/**
 * Enhanced Electron Main Process with Cross-Platform Support
 * Fixes EPIPE errors and improves platform compatibility
 */

const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) {
  app.quit();
}

// Enhanced logging to handle EPIPE errors
class SafeLogger {
  constructor() {
    this.consoleAvailable = true;
  }
  
  log(...args) {
    if (this.consoleAvailable) {
      try {
        console.log(...args);
      } catch (error) {
        if (error.code === 'EPIPE') {
          this.consoleAvailable = false;
          this.fallbackLog('INFO', ...args);
        }
      }
    } else {
      this.fallbackLog('INFO', ...args);
    }
  }
  
  warn(...args) {
    if (this.consoleAvailable) {
      try {
        console.warn(...args);
      } catch (error) {
        if (error.code === 'EPIPE') {
          this.consoleAvailable = false;
          this.fallbackLog('WARN', ...args);
        }
      }
    } else {
      this.fallbackLog('WARN', ...args);
    }
  }
  
  error(...args) {
    if (this.consoleAvailable) {
      try {
        console.error(...args);
      } catch (error) {
        if (error.code === 'EPIPE') {
          this.consoleAvailable = false;
          this.fallbackLog('ERROR', ...args);
        }
      }
    } else {
      this.fallbackLog('ERROR', ...args);
    }
  }
  
  fallbackLog(level, ...args) {
    try {
      // Write to file log
      const logDir = path.join(app.getPath('logs'), 'transcription-desktop');
      if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
      }
      
      const logFile = path.join(logDir, 'main.log');
      const timestamp = new Date().toISOString();
      const logEntry = `[${timestamp}] ${level}: ${args.join(' ')}\n`;
      
      fs.appendFileSync(logFile, logEntry);
    } catch (logError) {
      // Silent fail - can't log the log error
    }
  }
}

const logger = new SafeLogger();

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow;

const createWindow = () => {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      // Enable web security in production
      webSecurity: process.env.NODE_ENV !== 'development',
    },
  });

  // Determine the URL to load
  const isDev = process.env.NODE_ENV === 'development';
  
  if (isDev) {
    // In development, load from the development server
    const devServerURL = process.env.ELECTRON_WEBPACK_DEV_SERVER_URL;
    if (devServerURL) {
      mainWindow.loadURL(devServerURL);
    } else {
      // Fallback to localhost:3000
      mainWindow.loadURL('http://localhost:3000');
    }
  } else {
    // In production, load the built React app
    mainWindow.loadFile(path.join(__dirname, '../build/index.html')).catch(err => {
      logger.error('Failed to load built React app:', err);
      // Fallback to loading error page
      mainWindow.loadFile(path.join(__dirname, 'react-error.html')).catch(fallbackErr => {
        logger.error('Failed to load error page:', fallbackErr);
        // Last resort - show error in window
        mainWindow.webContents.executeJavaScript(`
          document.body.innerHTML = '<div style="padding: 20px; font-family: Arial;"><h2>Error Loading Application</h2><p>Could not load the application files.</p><p>Please restart the application.</p></div>';
        `);
      });
    });
  }

  // Open the DevTools in development mode
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  // Handle window close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
};

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', () => {
  logger.log('Electron app is ready');
  createWindow();
  
  // Handle EPIPE errors globally
  process.on('uncaughtException', (error) => {
    if (error.code === 'EPIPE') {
      logger.warn('Caught EPIPE error, continuing...');
      return; // Don't exit on EPIPE
    }
    logger.error('Uncaught exception:', error);
    // Don't exit in production for non-EPIPE errors
    if (process.env.NODE_ENV === 'development') {
      process.exit(1);
    }
  });
  
  process.on('unhandledRejection', (reason, promise) => {
    logger.error('Unhandled rejection at:', promise, 'reason:', reason);
    // Don't exit in production
    if (process.env.NODE_ENV === 'development') {
      process.exit(1);
    }
  });
});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handlers for desktop-specific functionality
ipcMain.handle('get-app-version', async () => {
  return app.getVersion();
});

ipcMain.handle('show-save-dialog', async (event, options) => {
  if (!mainWindow) return { canceled: true };
  
  try {
    const result = await dialog.showSaveDialog(mainWindow, {
      title: 'Save File',
      defaultPath: options.defaultPath || os.homedir(),
      filters: options.filters || [],
      ...options
    });
    return result;
  } catch (error) {
    logger.error('Save dialog error:', error);
    return { canceled: true, error: error.message };
  }
});

ipcMain.handle('show-open-dialog', async (event, options) => {
  if (!mainWindow) return { canceled: true };
  
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      title: 'Open File',
      defaultPath: options.defaultPath || os.homedir(),
      filters: options.filters || [],
      properties: options.properties || ['openFile'],
      ...options
    });
    return result;
  } catch (error) {
    logger.error('Open dialog error:', error);
    return { canceled: true, error: error.message };
  }
});

ipcMain.handle('open-external', async (event, url) => {
  try {
    await shell.openExternal(url);
    return { success: true };
  } catch (error) {
    logger.error('Open external error:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('export-data', async (event, data, format) => {
  try {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    let defaultPath = `export-${timestamp}`;
    
    switch (format.toLowerCase()) {
      case 'json':
        defaultPath += '.json';
        break;
      case 'csv':
        defaultPath += '.csv';
        break;
      case 'txt':
        defaultPath += '.txt';
        break;
      default:
        defaultPath += `.${format}`;
    }
    
    const result = await dialog.showSaveDialog(mainWindow, {
      title: 'Export Data',
      defaultPath,
      filters: [
        { name: `${format.toUpperCase()} Files`, extensions: [format.toLowerCase()] },
        { name: 'All Files', extensions: ['*'] }
      ]
    });
    
    if (!result.canceled && result.filePath) {
      let content = data;
      
      // Convert data to appropriate format if needed
      if (format.toLowerCase() === 'json' && typeof data !== 'string') {
        content = JSON.stringify(data, null, 2);
      } else if (format.toLowerCase() === 'csv' && Array.isArray(data)) {
        // Simple CSV conversion
        content = data.map(row => 
          Array.isArray(row) ? row.join(',') : 
          typeof row === 'object' ? Object.values(row).join(',') : 
          String(row)
        ).join('\n');
      }
      
      await fs.promises.writeFile(result.filePath, content, 'utf8');
      return { success: true, filePath: result.filePath };
    }
    
    return { canceled: true };
  } catch (error) {
    logger.error('Export data error:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('save-transcription', async (event, data) => {
  try {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const defaultPath = `transcription-${timestamp}.json`;
    
    const result = await dialog.showSaveDialog(mainWindow, {
      title: 'Save Transcription',
      defaultPath,
      filters: [
        { name: 'JSON Files', extensions: ['json'] },
        { name: 'Text Files', extensions: ['txt'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    });
    
    if (!result.canceled && result.filePath) {
      const content = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
      await fs.promises.writeFile(result.filePath, content, 'utf8');
      return { success: true, filePath: result.filePath };
    }
    
    return { canceled: true };
  } catch (error) {
    logger.error('Save transcription error:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('load-transcription', async () => {
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      title: 'Load Transcription',
      filters: [
        { name: 'JSON Files', extensions: ['json'] },
        { name: 'Text Files', extensions: ['txt'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      properties: ['openFile']
    });
    
    if (!result.canceled && result.filePaths && result.filePaths.length > 0) {
      const filePath = result.filePaths[0];
      const content = await fs.promises.readFile(filePath, 'utf8');
      
      let data;
      try {
        data = JSON.parse(content);
      } catch (parseError) {
        // If not JSON, treat as plain text
        data = content;
      }
      
      return { success: true, data, filePath };
    }
    
    return { canceled: true };
  } catch (error) {
    logger.error('Load transcription error:', error);
    return { success: false, error: error.message };
  }
});

// Desktop auth handlers
ipcMain.handle('get-desktop-auth', async () => {
  try {
    // Try to read from secure storage or config file
    const configPath = path.join(app.getPath('userData'), 'desktop-auth.json');
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(await fs.promises.readFile(configPath, 'utf8'));
      return config;
    }
    return null;
  } catch (error) {
    logger.error('Get desktop auth error:', error);
    return null;
  }
});

ipcMain.handle('save-desktop-auth', async (event, authData) => {
  try {
    const configPath = path.join(app.getPath('userData'), 'desktop-auth.json');
    await fs.promises.writeFile(configPath, JSON.stringify(authData), 'utf8');
    return { success: true };
  } catch (error) {
    logger.error('Save desktop auth error:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('clear-desktop-auth', async () => {
  try {
    const configPath = path.join(app.getPath('userData'), 'desktop-auth.json');
    if (fs.existsSync(configPath)) {
      await fs.promises.unlink(configPath);
    }
    return { success: true };
  } catch (error) {
    logger.error('Clear desktop auth error:', error);
    return { success: false, error: error.message };
  }
});

// Graceful shutdown handling
app.on('before-quit', (event) => {
  logger.log('Application before-quit event');
  // Allow async operations to complete
});

app.on('will-quit', () => {
  logger.log('Application will-quit event');
});

process.on('exit', (code) => {
  logger.log(`Application exiting with code ${code}`);
});

// Handle SIGTERM and SIGINT gracefully
process.on('SIGTERM', () => {
  logger.log('Received SIGTERM signal');
  app.quit();
});

process.on('SIGINT', () => {
  logger.log('Received SIGINT signal');
  app.quit();
});

logger.log('Electron main process initialized');