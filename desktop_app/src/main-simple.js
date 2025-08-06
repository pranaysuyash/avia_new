const { app, BrowserWindow, Menu, dialog, shell, ipcMain } = require('electron');
const path = require('path');
const Store = require('electron-store');
const log = require('electron-log');

// Initialize electron store for app settings
const store = new Store();

// Configure logging
log.transports.file.level = 'info';

let mainWindow;

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

    if (parsedUrl.origin !== 'http://localhost:3000' && parsedUrl.origin !== 'file://') {
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

function loadReactApp() {
  if (isDev) {
    // In development, wait for React dev server
    const reactUrl = 'http://localhost:3000';
    
    // Try to load immediately, React dev server might already be running
    mainWindow.loadURL(reactUrl).catch((error) => {
      log.error('Failed to load React app:', error);
      
      // Show error page
      mainWindow.loadFile(path.join(__dirname, 'error.html')).catch(() => {
        // If error.html doesn't exist, show a simple error
        mainWindow.loadURL(`data:text/html,
          <html>
            <head>
              <style>
                body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
                h1 { color: #e74c3c; }
                p { color: #666; margin: 20px 0; }
                code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
              </style>
            </head>
            <body>
              <h1>React Dev Server Not Running</h1>
              <p>Please start the React development server:</p>
              <code>cd desktop_app/src/renderer && npm start</code>
              <p>Then reload this window (Cmd+R or Ctrl+R)</p>
            </body>
          </html>
        `);
      });
    });
  } else {
    // In production, serve the built React app
    const indexPath = path.join(__dirname, 'renderer/build/index.html');
    mainWindow.loadFile(indexPath).catch((error) => {
      log.error('Failed to load built React app:', error);
      mainWindow.loadURL(`data:text/html,
        <html>
          <body style="font-family: Arial; padding: 40px; text-align: center;">
            <h1>Production Build Not Found</h1>
            <p>Please build the React app first:</p>
            <code>cd desktop_app/src/renderer && npm run build</code>
          </body>
        </html>
      `);
    });
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
            mainWindow.webContents.reload();
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
    template[4].submenu = [
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
app.whenReady().then(() => {
  log.info('Electron app ready, creating window...');
  
  // Create main window
  createWindow();
  
  // Create application menu
  createMenu();
});

app.on('window-all-closed', () => {
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

log.info('Electron main process initialized');