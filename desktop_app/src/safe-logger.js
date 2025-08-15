/**
 * Safe Logger Utility
 * Prevents EPIPE errors when logging in Electron app
 */

const log = require('electron-log');

class SafeLogger {
  constructor() {
    this.isConsoleAvailable = true;
    this.setupErrorHandlers();
  }

  setupErrorHandlers() {
    // Override console methods to catch EPIPE errors
    const originalConsoleLog = console.log;
    const originalConsoleInfo = console.info;
    const originalConsoleWarn = console.warn;
    const originalConsoleError = console.error;

    const safeLog = (originalMethod, level) => {
      return (...args) => {
        try {
          if (this.isConsoleAvailable) {
            originalMethod.apply(console, args);
          }
        } catch (error) {
          if (error?.code === 'EPIPE' || error?.message?.includes('EPIPE')) {
            // Console is broken, disable it and use file logging only
            this.isConsoleAvailable = false;
            log[level](...args);
          } else {
            // Re-throw other errors
            throw error;
          }
        }
      };
    };

    console.log = safeLog(originalConsoleLog, 'info');
    console.info = safeLog(originalConsoleInfo, 'info');
    console.warn = safeLog(originalConsoleWarn, 'warn');
    console.error = safeLog(originalConsoleError, 'error');
  }

  log(...args) {
    this.info(...args);
  }

  info(...args) {
    try {
      if (this.isConsoleAvailable) {
        console.info(...args);
      } else {
        log.info(...args);
      }
    } catch (error) {
      if (error?.code === 'EPIPE' || error?.message?.includes('EPIPE')) {
        this.isConsoleAvailable = false;
        log.info(...args);
      }
    }
  }

  warn(...args) {
    try {
      if (this.isConsoleAvailable) {
        console.warn(...args);
      } else {
        log.warn(...args);
      }
    } catch (error) {
      if (error?.code === 'EPIPE' || error?.message?.includes('EPIPE')) {
        this.isConsoleAvailable = false;
        log.warn(...args);
      }
    }
  }

  error(...args) {
    try {
      if (this.isConsoleAvailable) {
        console.error(...args);
      } else {
        log.error(...args);
      }
    } catch (error) {
      if (error?.code === 'EPIPE' || error?.message?.includes('EPIPE')) {
        this.isConsoleAvailable = false;
        log.error(...args);
      }
    }
  }

  debug(...args) {
    try {
      if (this.isConsoleAvailable && process.env.NODE_ENV === 'development') {
        console.log(...args);
      } else {
        log.debug(...args);
      }
    } catch (error) {
      if (error?.code === 'EPIPE' || error?.message?.includes('EPIPE')) {
        this.isConsoleAvailable = false;
        log.debug(...args);
      }
    }
  }
}

// Create singleton instance
const safeLogger = new SafeLogger();

// Export for use in other modules
module.exports = safeLogger;