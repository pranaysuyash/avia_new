const { app, BrowserWindow, Menu, dialog, shell, ipcMain, protocol } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const Store = require('electron-store');
const { autoUpdater } = require('electron-updater');
const log = require('electron-log');
const findFreePort = require('find-free-port');
const NativeIntegrations = require('./native-integrations');

// Initialize electron store for app settings
const store = new Store();

// Configure logging
log.transports.file.level = 'info';
autoUpdater.logger = log;

let mainWindow;
let pythonProcess;
let fastApiProcess;
let streamlitPort = 8501;
let nativeIntegrations;

// Check if running in development
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

function createWindow() {
  // Get window bounds from store or use defaults
  const windowBounds = store.get('windowBounds', {
    width: 1400,
    height: 900,
    x: undefined,
    y: undefined
  });

  // Create the browser window
  mainWindow = new BrowserWindow({
    ...windowBounds,
    minWidth: 1200,
    minHeight: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: !isDev
    },
    icon: path.join(__dirname, '../assets/icon.png'),
    show: false, // Don't show until ready
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    backgroundColor: '#ffffff'
  });

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Focus window on creation
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
    
    // Initialize native integrations only if not already initialized
    if (!nativeIntegrations) {
      nativeIntegrations = new NativeIntegrations(mainWindow);
    }
  });

  // Save window bounds when closed
  mainWindow.on('close', () => {
    store.set('windowBounds', mainWindow.getBounds());
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Prevent navigation to external URLs
  mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);

    if (parsedUrl.origin !== 'http://localhost:3000') {
      event.preventDefault();
      shell.openExternal(navigationUrl);
    }
  });

  // Handle new window requests
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Load the React app
  loadReactApp();
}

async function findAvailablePort() {
  try {
    const ports = await findFreePort(8501, 8510);
    return ports[0];
  } catch (error) {
    log.error('Failed to find available port:', error);
    return 8501;
  }
}

async function checkExistingStreamlit() {
  const axios = require('axios');
  try {
    await axios.get(`http://localhost:8501`);
    log.info('Found existing Streamlit server on port 8501');
    return 8501;
  } catch {
    return null;
  }
}

async function startReactApp() {
  if (isDev) {
    // In development, start React dev server
    try {
      const reactPath = path.join(__dirname, 'renderer');
      log.info(`Starting React development server from ${reactPath}`);
      
      pythonProcess = spawn('npm', ['start'], {
        cwd: reactPath,
        env: { 
          ...process.env,
          BROWSER: 'none',
          PORT: '3000'
        }
      });

      pythonProcess.stdout.on('data', (data) => {
        log.info(`React stdout: ${data}`);
      });

      pythonProcess.stderr.on('data', (data) => {
        log.error(`React stderr: ${data}`);
      });

      pythonProcess.on('close', (code) => {
        log.info(`React process exited with code ${code}`);
      });

      pythonProcess.on('error', (error) => {
        log.error('Failed to start React process:', error);
        showReactError();
      });

      // Wait for React to start
      await waitForReact();
      
    } catch (error) {
      log.error('Failed to start React app:', error);
      showReactError();
    }
  } else {
    // In production, load built React app
    streamlitPort = 3000; // React will be served on port 3000
  }
}

async function startFastApiBackend() {
  try {
    // Find the project root (2 levels up from desktop_app/src)
    const projectRoot = path.join(__dirname, '../../');
    log.info(`Starting FastAPI backend from ${projectRoot}`);
    
    // Start FastAPI server using the run_api.py script
    // Use the venv Python to ensure all dependencies are available
    const venvPython = path.join(projectRoot, 'venv', 'bin', 'python');
    fastApiProcess = spawn(venvPython, ['run_api.py'], {
      cwd: projectRoot,
      env: {
        ...process.env,
        API_HOST: '127.0.0.1',
        API_PORT: '8000',
        API_RELOAD: 'true'
      },
      stdio: ['pipe', 'pipe', 'pipe']
    });

    fastApiProcess.stdout.on('data', (data) => {
      log.info(`FastAPI: ${data.toString()}`);
    });

    fastApiProcess.stderr.on('data', (data) => {
      log.error(`FastAPI Error: ${data.toString()}`);
    });

    fastApiProcess.on('close', (code) => {
      log.info(`FastAPI process closed with code ${code}`);
    });

    // Wait for FastAPI to start
    await waitForFastApi();
    
  } catch (error) {
    log.error('Failed to start FastAPI backend:', error);
    throw error;
  }
}

function waitForFastApi() {
  return new Promise((resolve, reject) => {
    const axios = require('axios');
    let attempts = 0;
    const maxAttempts = 30;

    const checkFastApi = async () => {
      try {
        await axios.get('http://localhost:8000/api/health');
        log.info('FastAPI server is ready');
        resolve();
      } catch (error) {
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(checkFastApi, 1000);
        } else {
          log.error('FastAPI server failed to start within timeout');
          reject(new Error('FastAPI server timeout'));
        }
      }
    };

    checkFastApi();
  });
}

function waitForReact() {
  return new Promise((resolve, reject) => {
    const axios = require('axios');
    let attempts = 0;
    const maxAttempts = 30;

    const checkReact = async () => {
      try {
        await axios.get('http://localhost:3000');
        log.info('React server is ready');
        resolve();
      } catch (error) {
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(checkReact, 1000);
        } else {
          log.error('React server failed to start within timeout');
          reject(new Error('React server timeout'));
        }
      }
    };

    checkReact();
  });
}

function loadReactApp() {
  const reactUrl = 'http://localhost:3000';
  
  mainWindow.loadURL(reactUrl).catch((error) => {
    log.error('Failed to load React app:', error);
    
    // Show error page
    mainWindow.loadFile(path.join(__dirname, 'error.html'));
  });
}

function showReactError() {
  if (mainWindow) {
    mainWindow.loadFile(path.join(__dirname, 'react-error.html'));
  }
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Transcription',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow.webContents.executeJavaScript(`
              window.location.reload();
            `);
          }
        },
        {
          label: 'Open Recent',
          submenu: [
            {
              label: 'Clear Recent',
              click: () => {
                store.delete('recentFiles');
              }
            }
          ]
        },
        { type: 'separator' },
        {
          label: 'Preferences',
          accelerator: 'CmdOrCtrl+,',
          click: () => {
            // Open preferences in Streamlit app
            mainWindow.webContents.executeJavaScript(`
              // Navigate to settings if available
              console.log('Opening preferences...');
            `);
          }
        },
        { type: 'separator' },
        {
          label: 'Quit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectall' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Tools',
      submenu: [
        {
          label: 'AI Customization',
          click: () => {
            // Navigate to AI customization in Streamlit
            mainWindow.webContents.executeJavaScript(`
              // Enable AI customization feature if available
              console.log('Opening AI customization...');
            `);
          }
        },
        {
          label: 'Batch Processing',
          click: () => {
            // Navigate to batch processing
            mainWindow.webContents.executeJavaScript(`
              console.log('Opening batch processing...');
            `);
          }
        },
        { type: 'separator' },
        {
          label: 'Export Data',
          click: async () => {
            const result = await dialog.showSaveDialog(mainWindow, {
              title: 'Export Transcription Data',
              defaultPath: 'transcription-export.json',
              filters: [
                { name: 'JSON Files', extensions: ['json'] },
                { name: 'All Files', extensions: ['*'] }
              ]
            });

            if (!result.canceled) {
              // Trigger export in Streamlit app
              mainWindow.webContents.executeJavaScript(`
                console.log('Exporting to: ${result.filePath}');
              `);
            }
          }
        }
      ]
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'close' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Transcription App',
              message: 'Transcription App v1.0.0',
              detail: 'AI-powered audio and video transcription with entity extraction.'
            });
          }
        },
        {
          label: 'Documentation',
          click: () => {
            shell.openExternal('https://github.com/your-repo/transcription-app');
          }
        },
        {
          label: 'Report Issue',
          click: () => {
            shell.openExternal('https://github.com/your-repo/transcription-app/issues');
          }
        }
      ]
    }
  ];

  // macOS specific menu adjustments
  if (process.platform === 'darwin') {
    template.unshift({
      label: app.getName(),
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideothers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    });

    // Window menu
    template[5].submenu = [
      { role: 'close' },
      { role: 'minimize' },
      { role: 'zoom' },
      { type: 'separator' },
      { role: 'front' }
    ];
  }

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// App event handlers
app.whenReady().then(async () => {
  try {
    // Start FastAPI backend first
    log.info('Starting FastAPI backend...');
    await startFastApiBackend();
    
    // Then start React app
    log.info('Starting React frontend...');
    await startReactApp();
    
    // Create main window
    createWindow();
    
    // Create application menu
    createMenu();
    
    // Check for updates (in production)
    if (!isDev) {
      autoUpdater.checkForUpdatesAndNotify();
    }
  } catch (error) {
    log.error('Failed to start application:', error);
    // Show error dialog
    dialog.showErrorBox('Startup Error', 'Failed to start the application. Please check the logs for more details.');
  }
});

app.on('window-all-closed', () => {
  // Quit React process
  if (pythonProcess) {
    pythonProcess.kill();
  }
  
  // Quit FastAPI process
  if (fastApiProcess) {
    fastApiProcess.kill();
  }
  
  // On macOS, keep app running even when all windows are closed
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On macOS, re-create window when dock icon is clicked
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  // Clean up React process
  if (pythonProcess) {
    log.info('Terminating React process...');
    pythonProcess.kill();
  }
  
  // Clean up FastAPI process
  if (fastApiProcess) {
    log.info('Terminating FastAPI process...');
    fastApiProcess.kill();
  }
});

// IPC handlers
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('show-save-dialog', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, options);
  return result;
});

ipcMain.handle('show-open-dialog', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, options);
  return result;
});

ipcMain.handle('open-external', async (event, url) => {
  shell.openExternal(url);
});

// Auto-updater events
autoUpdater.on('checking-for-update', () => {
  log.info('Checking for update...');
});

autoUpdater.on('update-available', (info) => {
  log.info('Update available.');
});

autoUpdater.on('update-not-available', (info) => {
  log.info('Update not available.');
});

autoUpdater.on('error', (err) => {
  log.error('Error in auto-updater. ' + err);
});

autoUpdater.on('download-progress', (progressObj) => {
  let log_message = "Download speed: " + progressObj.bytesPerSecond;
  log_message = log_message + ' - Downloaded ' + progressObj.percent + '%';
  log_message = log_message + ' (' + progressObj.transferred + "/" + progressObj.total + ')';
  log.info(log_message);
});

autoUpdater.on('update-downloaded', (info) => {
  log.info('Update downloaded');
  autoUpdater.quitAndInstall();
});