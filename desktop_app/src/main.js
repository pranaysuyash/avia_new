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
let streamlitPort = 8501;
let nativeIntegrations;

// Check if running in development
const isDev = process.env.NODE_ENV === 'development';

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
    
    // Initialize native integrations
    nativeIntegrations = new NativeIntegrations(mainWindow);
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

    if (parsedUrl.origin !== `http://localhost:${streamlitPort}`) {
      event.preventDefault();
      shell.openExternal(navigationUrl);
    }
  });

  // Handle new window requests
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Load the Streamlit app
  loadStreamlitApp();
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

async function startPythonBackend() {
  try {
    // Check if Streamlit is already running
    const existingPort = await checkExistingStreamlit();
    if (existingPort) {
      streamlitPort = existingPort;
      log.info(`Using existing Streamlit server on port ${streamlitPort}`);
      return;
    }

    // Find available port
    streamlitPort = await findAvailablePort();
    log.info(`Starting Python backend on port ${streamlitPort}`);

    // Determine Python backend path
    let pythonBackendPath;
    if (isDev) {
      pythonBackendPath = path.join(__dirname, '../../');
    } else {
      pythonBackendPath = path.join(process.resourcesPath, 'python-backend');
    }

    // Check if Python is available - try python first, then python3
    const pythonCommand = process.platform === 'win32' ? 'python' : 'python';
    
    // Start Streamlit server
    pythonProcess = spawn(pythonCommand, [
      '-m', 'streamlit', 'run', 'app.py',
      '--server.port', streamlitPort.toString(),
      '--server.headless', 'true',
      '--server.enableCORS', 'false',
      '--server.enableXsrfProtection', 'false'
    ], {
      cwd: pythonBackendPath,
      env: { 
        ...process.env,
        PYTHONPATH: pythonBackendPath,
        ELECTRON_APP: 'true'
      }
    });

    pythonProcess.stdout.on('data', (data) => {
      log.info(`Python stdout: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
      log.error(`Python stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
      log.info(`Python process exited with code ${code}`);
    });

    pythonProcess.on('error', (error) => {
      log.error('Failed to start Python process:', error);
      showPythonError();
    });

    // Wait for Streamlit to start
    await waitForStreamlit();
    
  } catch (error) {
    log.error('Failed to start Python backend:', error);
    showPythonError();
  }
}

function waitForStreamlit() {
  return new Promise((resolve, reject) => {
    const axios = require('axios');
    let attempts = 0;
    const maxAttempts = 30;

    const checkStreamlit = async () => {
      try {
        await axios.get(`http://localhost:${streamlitPort}`);
        log.info('Streamlit server is ready');
        resolve();
      } catch (error) {
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(checkStreamlit, 1000);
        } else {
          log.error('Streamlit server failed to start within timeout');
          reject(new Error('Streamlit server timeout'));
        }
      }
    };

    checkStreamlit();
  });
}

function loadStreamlitApp() {
  const streamlitUrl = `http://localhost:${streamlitPort}`;
  
  mainWindow.loadURL(streamlitUrl).catch((error) => {
    log.error('Failed to load Streamlit app:', error);
    
    // Show error page
    mainWindow.loadFile(path.join(__dirname, 'error.html'));
  });
}

function showPythonError() {
  if (mainWindow) {
    mainWindow.loadFile(path.join(__dirname, 'python-error.html'));
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
  // Start Python backend first
  await startPythonBackend();
  
  // Create main window
  createWindow();
  
  // Create application menu
  createMenu();
  
  // Check for updates (in production)
  if (!isDev) {
    autoUpdater.checkForUpdatesAndNotify();
  }
});

app.on('window-all-closed', () => {
  // Quit Python process
  if (pythonProcess) {
    pythonProcess.kill();
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
  // Clean up Python process
  if (pythonProcess) {
    log.info('Terminating Python process...');
    pythonProcess.kill();
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