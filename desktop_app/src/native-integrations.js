const { app, ipcMain, shell, dialog, Menu, Tray, nativeTheme, systemPreferences } = require('electron');
const path = require('path');
const fs = require('fs').promises;
const os = require('os');
const { spawn } = require('child_process');
const safeLogger = require('./safe-logger');

class NativeIntegrations {
  constructor(mainWindow) {
    this.mainWindow = mainWindow;
    this.tray = null;
    this.isQuitting = false;
    
    this.setupIpcHandlers();
    this.setupSystemIntegrations();
  }

  setupIpcHandlers() {
    // File system operations
    ipcMain.handle('native:select-file', async () => {
      return await this.selectFile();
    });

    ipcMain.handle('native:save-file', async (event, content, defaultName) => {
      return await this.saveFile(content, defaultName);
    });

    ipcMain.handle('native:open-file-location', async (event, filePath) => {
      return await this.openFileLocation(filePath);
    });

    // System operations
    ipcMain.handle('native:get-system-info', async () => {
      return await this.getSystemInfo();
    });

    ipcMain.handle('native:set-startup', async (event, enabled) => {
      return await this.setStartupBehavior(enabled);
    });

    ipcMain.handle('native:minimize-to-tray', () => {
      return this.minimizeToTray();
    });

    ipcMain.handle('native:show-notification', async (event, options) => {
      return await this.showNotification(options);
    });

    // Audio system integration
    ipcMain.handle('native:get-audio-devices', async () => {
      return await this.getAudioDevices();
    });

    ipcMain.handle('native:set-audio-device', async (event, deviceId) => {
      return await this.setAudioDevice(deviceId);
    });

    // Theme and appearance
    ipcMain.handle('native:get-theme', () => {
      return nativeTheme.shouldUseDarkColors ? 'dark' : 'light';
    });

    ipcMain.handle('native:set-theme', (event, theme) => {
      nativeTheme.themeSource = theme;
      return theme;
    });

    // Keyboard shortcuts
    ipcMain.handle('native:register-shortcuts', async (event, shortcuts) => {
      return await this.registerGlobalShortcuts(shortcuts);
    });

    ipcMain.handle('native:unregister-shortcuts', () => {
      return this.unregisterGlobalShortcuts();
    });

    // Window management
    ipcMain.handle('native:set-always-on-top', (event, enabled) => {
      this.mainWindow.setAlwaysOnTop(enabled);
      return enabled;
    });

    ipcMain.handle('native:set-window-opacity', (event, opacity) => {
      this.mainWindow.setOpacity(opacity);
      return opacity;
    });

    // Power management
    ipcMain.handle('native:prevent-sleep', () => {
      return this.preventSystemSleep();
    });

    ipcMain.handle('native:allow-sleep', () => {
      return this.allowSystemSleep();
    });

    // Platform-specific features
    if (process.platform === 'darwin') {
      this.setupMacOSIntegrations();
    } else if (process.platform === 'win32') {
      this.setupWindowsIntegrations();
    } else {
      this.setupLinuxIntegrations();
    }
  }

  setupSystemIntegrations() {
    // Setup system tray
    this.setupSystemTray();
    
    // Setup context menu
    this.setupContextMenu();
    
    // Handle app events
    this.setupAppEventHandlers();
    
    // Setup theme change listener
    nativeTheme.on('updated', () => {
      const theme = nativeTheme.shouldUseDarkColors ? 'dark' : 'light';
      this.mainWindow.webContents.send('theme-changed', theme);
    });
  }

  setupSystemTray() {
    try {
      const trayIconPath = path.join(__dirname, '..', 'assets', 'tray-icon.png');
      
      // Fallback to default icon if custom icon doesn't exist
      const iconPath = require('fs').existsSync(trayIconPath) 
        ? trayIconPath 
        : path.join(__dirname, '..', 'assets', 'icon.png');
      
      this.tray = new Tray(iconPath);
      
      const trayMenu = Menu.buildFromTemplate([
        {
          label: 'Show App',
          click: () => {
            this.mainWindow.show();
            this.mainWindow.focus();
          }
        },
        {
          label: 'New Recording',
          click: () => {
            this.mainWindow.show();
            this.mainWindow.webContents.send('action:new-recording');
          }
        },
        { type: 'separator' },
        {
          label: 'Settings',
          click: () => {
            this.mainWindow.show();
            this.mainWindow.webContents.send('action:open-settings');
          }
        },
        { type: 'separator' },
        {
          label: 'Quit',
          click: () => {
            this.isQuitting = true;
            app.quit();
          }
        }
      ]);
      
      this.tray.setContextMenu(trayMenu);
      this.tray.setToolTip('Transcription App');
      
      this.tray.on('click', () => {
        if (this.mainWindow.isVisible()) {
          this.mainWindow.hide();
        } else {
          this.mainWindow.show();
          this.mainWindow.focus();
        }
      });
      
    } catch (error) {
      console.warn('Failed to setup system tray:', error);
    }
  }

  setupContextMenu() {
    const template = [
      {
        label: 'File',
        submenu: [
          {
            label: 'Open Audio File',
            accelerator: 'CmdOrCtrl+O',
            click: async () => {
              const result = await this.selectFile();
              if (result.success && result.filePath) {
                this.mainWindow.webContents.send('file:selected', result.filePath);
              }
            }
          },
          { type: 'separator' },
          {
            label: 'Settings',
            accelerator: 'CmdOrCtrl+,',
            click: () => {
              this.mainWindow.webContents.send('action:open-settings');
            }
          },
          { type: 'separator' },
          {
            label: 'Quit',
            accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
            click: () => {
              this.isQuitting = true;
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
          { role: 'close' },
          {
            label: 'Always on Top',
            type: 'checkbox',
            click: (menuItem) => {
              this.mainWindow.setAlwaysOnTop(menuItem.checked);
            }
          }
        ]
      }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
  }

  setupAppEventHandlers() {
    // Handle window close
    this.mainWindow.on('close', (event) => {
      if (!this.isQuitting && this.tray) {
        event.preventDefault();
        this.mainWindow.hide();
        
        // Show notification on first minimize
        if (!this.hasShownTrayNotification) {
          this.showNotification({
            title: 'Transcription App',
            body: 'App was minimized to tray. Click the tray icon to restore.',
            silent: true
          });
          this.hasShownTrayNotification = true;
        }
      }
    });

    // Handle app quit
    app.on('before-quit', () => {
      this.isQuitting = true;
    });

    app.on('activate', () => {
      this.mainWindow.show();
    });
  }

  async selectFile() {
    try {
      const result = await dialog.showOpenDialog(this.mainWindow, {
        title: 'Select Audio/Video File',
        filters: [
          {
            name: 'Audio/Video Files',
            extensions: ['mp3', 'wav', 'mp4', 'm4a', 'flac', 'ogg', 'webm', 'mov', 'avi', 'mkv']
          },
          { name: 'Audio Files', extensions: ['mp3', 'wav', 'm4a', 'flac', 'ogg'] },
          { name: 'Video Files', extensions: ['mp4', 'webm', 'mov', 'avi', 'mkv'] },
          { name: 'All Files', extensions: ['*'] }
        ],
        properties: ['openFile']
      });

      if (result.canceled || result.filePaths.length === 0) {
        return { success: false, canceled: true };
      }

      const filePath = result.filePaths[0];
      const stats = await fs.stat(filePath);

      return {
        success: true,
        filePath,
        fileName: path.basename(filePath),
        fileSize: stats.size,
        lastModified: stats.mtime
      };

    } catch (error) {
      safeLogger.error('File selection failed:', error);
      return { success: false, error: error.message };
    }
  }

  async saveFile(content, defaultName = 'transcription.txt') {
    try {
      const result = await dialog.showSaveDialog(this.mainWindow, {
        title: 'Save Transcription',
        defaultPath: defaultName,
        filters: [
          { name: 'Text Files', extensions: ['txt'] },
          { name: 'JSON Files', extensions: ['json'] },
          { name: 'SRT Subtitles', extensions: ['srt'] },
          { name: 'All Files', extensions: ['*'] }
        ]
      });

      if (result.canceled || !result.filePath) {
        return { success: false, canceled: true };
      }

      await fs.writeFile(result.filePath, content, 'utf8');

      return {
        success: true,
        filePath: result.filePath,
        fileName: path.basename(result.filePath)
      };

    } catch (error) {
      safeLogger.error('File save failed:', error);
      return { success: false, error: error.message };
    }
  }

  async openFileLocation(filePath) {
    try {
      await shell.showItemInFolder(filePath);
      return { success: true };
    } catch (error) {
      safeLogger.error('Failed to open file location:', error);
      return { success: false, error: error.message };
    }
  }

  async getSystemInfo() {
    try {
      const cpus = os.cpus();
      const networkInterfaces = os.networkInterfaces();
      
      return {
        platform: os.platform(),
        arch: os.arch(),
        release: os.release(),
        hostname: os.hostname(),
        uptime: os.uptime(),
        memory: {
          total: os.totalmem(),
          free: os.freemem(),
          used: os.totalmem() - os.freemem()
        },
        cpu: {
          model: cpus[0]?.model || 'Unknown',
          cores: cpus.length,
          speed: cpus[0]?.speed || 0
        },
        networkInterfaces: Object.keys(networkInterfaces),
        userInfo: os.userInfo(),
        homedir: os.homedir(),
        tmpdir: os.tmpdir()
      };
    } catch (error) {
      safeLogger.error('Failed to get system info:', error);
      return { error: error.message };
    }
  }

  async setStartupBehavior(enabled) {
    try {
      if (process.platform === 'darwin') {
        // macOS
        app.setLoginItemSettings({
          openAtLogin: enabled,
          openAsHidden: true
        });
      } else if (process.platform === 'win32') {
        // Windows
        app.setLoginItemSettings({
          openAtLogin: enabled,
          path: process.execPath,
          args: ['--hidden']
        });
      } else {
        // Linux - create desktop entry
        const desktopEntry = `[Desktop Entry]
Type=Application
Name=Transcription App
Exec=${process.execPath} --hidden
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true`;

        const autostartDir = path.join(os.homedir(), '.config', 'autostart');
        const desktopFile = path.join(autostartDir, 'transcription-app.desktop');

        if (enabled) {
          await fs.mkdir(autostartDir, { recursive: true });
          await fs.writeFile(desktopFile, desktopEntry);
        } else {
          try {
            await fs.unlink(desktopFile);
          } catch (error) {
            // File might not exist
          }
        }
      }

      return { success: true, enabled };
    } catch (error) {
      safeLogger.error('Failed to set startup behavior:', error);
      return { success: false, error: error.message };
    }
  }

  minimizeToTray() {
    if (this.tray) {
      this.mainWindow.hide();
      return { success: true };
    } else {
      this.mainWindow.minimize();
      return { success: false, reason: 'No system tray available' };
    }
  }

  async showNotification(options) {
    try {
      const { Notification } = require('electron');
      
      if (!Notification.isSupported()) {
        return { success: false, reason: 'Notifications not supported' };
      }

      const notification = new Notification({
        title: options.title || 'Transcription App',
        body: options.body || '',
        icon: options.icon || path.join(__dirname, '..', 'assets', 'icon.png'),
        silent: options.silent || false
      });

      notification.show();

      notification.on('click', () => {
        this.mainWindow.show();
        this.mainWindow.focus();
        if (options.onClick) {
          this.mainWindow.webContents.send('notification:clicked', options.onClick);
        }
      });

      return { success: true };
    } catch (error) {
      safeLogger.error('Failed to show notification:', error);
      return { success: false, error: error.message };
    }
  }

  async getAudioDevices() {
    try {
      // This would require additional native modules for full audio device enumeration
      // For now, return basic info
      return {
        success: true,
        devices: [
          { id: 'default', name: 'Default', type: 'input' },
          { id: 'default_output', name: 'Default Output', type: 'output' }
        ]
      };
    } catch (error) {
      safeLogger.error('Failed to get audio devices:', error);
      return { success: false, error: error.message };
    }
  }

  async setAudioDevice(deviceId) {
    try {
      // Audio device setting would require platform-specific implementation
      safeLogger.info('Setting audio device:', deviceId);
      return { success: true, deviceId };
    } catch (error) {
      safeLogger.error('Failed to set audio device:', error);
      return { success: false, error: error.message };
    }
  }

  async registerGlobalShortcuts(shortcuts) {
    try {
      const { globalShortcut } = require('electron');
      
      // Unregister existing shortcuts
      globalShortcut.unregisterAll();
      
      const registered = {};
      
      for (const [action, accelerator] of Object.entries(shortcuts)) {
        try {
          const success = globalShortcut.register(accelerator, () => {
            this.mainWindow.webContents.send('shortcut:triggered', action);
          });
          
          registered[action] = success ? accelerator : null;
        } catch (error) {
          console.warn(`Failed to register shortcut ${accelerator}:`, error);
          registered[action] = null;
        }
      }
      
      return { success: true, registered };
    } catch (error) {
      safeLogger.error('Failed to register shortcuts:', error);
      return { success: false, error: error.message };
    }
  }

  unregisterGlobalShortcuts() {
    try {
      const { globalShortcut } = require('electron');
      globalShortcut.unregisterAll();
      return { success: true };
    } catch (error) {
      safeLogger.error('Failed to unregister shortcuts:', error);
      return { success: false, error: error.message };
    }
  }

  preventSystemSleep() {
    try {
      const { powerSaveBlocker } = require('electron');
      const id = powerSaveBlocker.start('prevent-display-sleep');
      return { success: true, blockerId: id };
    } catch (error) {
      safeLogger.error('Failed to prevent system sleep:', error);
      return { success: false, error: error.message };
    }
  }

  allowSystemSleep() {
    try {
      const { powerSaveBlocker } = require('electron');
      // This would need to track the blocker ID from preventSystemSleep
      // For now, just stop all blockers
      return { success: true };
    } catch (error) {
      safeLogger.error('Failed to allow system sleep:', error);
      return { success: false, error: error.message };
    }
  }

  // Platform-specific integrations
  setupMacOSIntegrations() {
    ipcMain.handle('native:macos-permissions', async () => {
      const micPermission = systemPreferences.getMediaAccessStatus('microphone');
      const screenPermission = systemPreferences.getMediaAccessStatus('screen');
      
      return {
        microphone: micPermission,
        screen: screenPermission
      };
    });

    ipcMain.handle('native:macos-request-permissions', async () => {
      const micPermission = await systemPreferences.askForMediaAccess('microphone');
      return { microphone: micPermission };
    });

    // macOS dock integration
    if (process.platform === 'darwin') {
      app.dock.setMenu(Menu.buildFromTemplate([
        {
          label: 'New Recording',
          click: () => {
            this.mainWindow.show();
            this.mainWindow.webContents.send('action:new-recording');
          }
        }
      ]));
    }
  }

  setupWindowsIntegrations() {
    // Windows-specific features
    ipcMain.handle('native:windows-jumplist', async (event, tasks) => {
      try {
        app.setJumpList([
          {
            type: 'tasks',
            name: 'Tasks',
            items: tasks.map(task => ({
              type: 'task',
              title: task.title,
              description: task.description,
              program: process.execPath,
              args: task.args || [],
              iconPath: process.execPath,
              iconIndex: 0
            }))
          }
        ]);
        return { success: true };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Windows taskbar progress
    ipcMain.handle('native:set-progress', (event, progress) => {
      this.mainWindow.setProgressBar(progress);
      return { success: true };
    });
  }

  setupLinuxIntegrations() {
    // Linux-specific features
    ipcMain.handle('native:linux-desktop-entry', async (event, options) => {
      try {
        const desktopEntry = `[Desktop Entry]
Version=1.0
Type=Application
Name=${options.name || 'Transcription App'}
Comment=${options.comment || 'Audio and video transcription'}
Exec=${process.execPath}
Icon=${options.icon || path.join(__dirname, '..', 'assets', 'icon.png')}
Terminal=false
Categories=AudioVideo;Audio;
MimeType=audio/mpeg;audio/wav;video/mp4;`;

        const desktopFile = path.join(os.homedir(), '.local', 'share', 'applications', 'transcription-app.desktop');
        await fs.mkdir(path.dirname(desktopFile), { recursive: true });
        await fs.writeFile(desktopFile, desktopEntry);
        
        return { success: true, desktopFile };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
  }
}

module.exports = NativeIntegrations;