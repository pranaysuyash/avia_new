#!/usr/bin/env node

/**
 * Desktop App Launcher
 * Handles setup, dependency checking, and app startup
 */

const fs = require('fs');
const path = require('path');
const { spawn, exec } = require('child_process');
const os = require('os');

class AppLauncher {
  constructor() {
    this.pythonBackendPath = path.join(__dirname, '..');
    this.requiredPythonVersion = '3.8.0';
    this.isWindows = os.platform() === 'win32';
    this.pythonCommand = this.isWindows ? 'python' : 'python3';
  }

  async start() {
    console.log('🚀 Starting Transcription Desktop App...\n');
    
    try {
      await this.checkSystem();
      await this.checkPython();
      await this.checkDependencies();
      await this.startElectron();
    } catch (error) {
      console.error('❌ Failed to start application:', error.message);
      process.exit(1);
    }
  }

  async checkSystem() {
    console.log('📋 Checking system requirements...');
    
    // Check Node.js version
    const nodeVersion = process.version;
    console.log(`   Node.js: ${nodeVersion} ✓`);
    
    // Check platform
    console.log(`   Platform: ${os.platform()} ${os.arch()} ✓`);
    
    // Check available memory
    const totalMem = Math.round(os.totalmem() / 1024 / 1024 / 1024);
    console.log(`   Memory: ${totalMem}GB ${totalMem >= 4 ? '✓' : '⚠️'}`);
    
    if (totalMem < 4) {
      console.log('   ⚠️  Warning: Less than 4GB RAM detected. Performance may be affected.');
    }
    
    console.log();
  }

  async checkPython() {
    console.log('🐍 Checking Python installation...');
    
    return new Promise((resolve, reject) => {
      exec(`${this.pythonCommand} --version`, (error, stdout, stderr) => {
        if (error) {
          console.log('   ❌ Python not found or not accessible');
          console.log('\n   📥 Please install Python 3.8+ from:');
          console.log('   https://www.python.org/downloads/\n');
          reject(new Error('Python not found'));
          return;
        }
        
        const versionMatch = stdout.match(/Python (\d+\.\d+\.\d+)/);
        if (versionMatch) {
          const version = versionMatch[1];
          console.log(`   Python: ${version} ✓`);
          
          if (this.compareVersions(version, this.requiredPythonVersion) < 0) {
            console.log(`   ❌ Python ${this.requiredPythonVersion}+ required`);
            reject(new Error('Python version too old'));
            return;
          }
        }
        
        console.log();
        resolve();
      });
    });
  }

  async checkDependencies() {
    console.log('📦 Checking Python dependencies...');
    
    const requirementsPath = path.join(this.pythonBackendPath, 'requirements.txt');
    
    if (!fs.existsSync(requirementsPath)) {
      console.log('   ❌ requirements.txt not found');
      throw new Error('Requirements file missing');
    }
    
    return new Promise((resolve, reject) => {
      const child = spawn(this.pythonCommand, ['-m', 'pip', 'check'], {
        cwd: this.pythonBackendPath,
        stdio: 'pipe'
      });
      
      let hasErrors = false;
      
      child.stderr.on('data', (data) => {
        const error = data.toString();
        if (error.includes('has requirement') || error.includes('incompatible')) {
          hasErrors = true;
          console.log('   ⚠️  Dependency issues detected');
        }
      });
      
      child.on('close', (code) => {
        if (code === 0 && !hasErrors) {
          console.log('   Dependencies: ✓');
          console.log();
          resolve();
        } else {
          console.log('   ❌ Installing missing dependencies...');
          this.installDependencies()
            .then(resolve)
            .catch(reject);
        }
      });
      
      child.on('error', (error) => {
        console.log('   ⚠️  Could not check dependencies, attempting install...');
        this.installDependencies()
          .then(resolve)
          .catch(reject);
      });
    });
  }

  async installDependencies() {
    console.log('   📥 Installing Python dependencies...');
    
    return new Promise((resolve, reject) => {
      const child = spawn(this.pythonCommand, ['-m', 'pip', 'install', '-r', 'requirements.txt'], {
        cwd: this.pythonBackendPath,
        stdio: 'inherit'
      });
      
      child.on('close', (code) => {
        if (code === 0) {
          console.log('   Dependencies installed: ✓\n');
          resolve();
        } else {
          console.log('   ❌ Failed to install dependencies');
          reject(new Error('Dependency installation failed'));
        }
      });
      
      child.on('error', (error) => {
        console.log('   ❌ Error installing dependencies:', error.message);
        reject(error);
      });
    });
  }

  async startElectron() {
    console.log('⚡ Starting Electron application...\n');
    
    const electronPath = path.join(__dirname, 'node_modules', '.bin', 'electron');
    const mainPath = path.join(__dirname, 'src', 'main.js');
    
    // Set environment variables
    process.env.NODE_ENV = process.env.NODE_ENV || 'production';
    
    // Start Electron
    const child = spawn(electronPath, [mainPath], {
      stdio: 'inherit',
      env: process.env
    });
    
    child.on('close', (code) => {
      console.log(`\n📱 Application closed with code ${code}`);
      process.exit(code);
    });
    
    child.on('error', (error) => {
      console.error('❌ Failed to start Electron:', error.message);
      process.exit(1);
    });
    
    // Handle process termination
    process.on('SIGINT', () => {
      console.log('\n🛑 Shutting down...');
      child.kill('SIGINT');
    });
    
    process.on('SIGTERM', () => {
      child.kill('SIGTERM');
    });
  }

  compareVersions(version1, version2) {
    const v1parts = version1.split('.').map(Number);
    const v2parts = version2.split('.').map(Number);
    
    for (let i = 0; i < Math.max(v1parts.length, v2parts.length); i++) {
      const v1part = v1parts[i] || 0;
      const v2part = v2parts[i] || 0;
      
      if (v1part < v2part) return -1;
      if (v1part > v2part) return 1;
    }
    
    return 0;
  }
}

// Run launcher if called directly
if (require.main === module) {
  const launcher = new AppLauncher();
  launcher.start().catch((error) => {
    console.error('Failed to start application:', error);
    process.exit(1);
  });
}

module.exports = AppLauncher;