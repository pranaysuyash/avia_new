const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // App info
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // File dialogs
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  
  // External links
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  
  // Platform info
  platform: process.platform,
  
  // Custom transcription app methods
  transcription: {
    // Export functionality
    exportData: (data, format) => ipcRenderer.invoke('export-data', data, format),
    
    // File operations
    saveTranscription: (data) => ipcRenderer.invoke('save-transcription', data),
    loadTranscription: () => ipcRenderer.invoke('load-transcription'),
    
    // Settings
    getSettings: () => ipcRenderer.invoke('get-settings'),
    saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
    
    // Recent files
    getRecentFiles: () => ipcRenderer.invoke('get-recent-files'),
    addRecentFile: (file) => ipcRenderer.invoke('add-recent-file', file),
    
    // AI customization
    getCustomizations: () => ipcRenderer.invoke('get-customizations'),
    saveCustomizations: (customizations) => ipcRenderer.invoke('save-customizations', customizations),
  }
});

// Inject custom styles and JavaScript for better desktop integration
window.addEventListener('DOMContentLoaded', () => {
  // Add desktop-specific styling
  const style = document.createElement('style');
  style.textContent = `
    /* Desktop app specific styles */
    .main .block-container {
      padding-top: 2rem;
      padding-left: 2rem;
      padding-right: 2rem;
      max-width: none;
    }
    
    /* Hide Streamlit menu and footer for cleaner desktop experience */
    .stApp > header,
    .stApp > footer {
      display: none;
    }
    
    /* Improve sidebar appearance */
    .css-1d391kg {
      background-color: #f8f9fa;
      border-right: 1px solid #dee2e6;
    }
    
    /* Better file uploader styling */
    .stFileUploader {
      border: 2px dashed #6c757d;
      border-radius: 8px;
      padding: 2rem;
      text-align: center;
    }
    
    .stFileUploader:hover {
      border-color: #007bff;
      background-color: #f8f9ff;
    }
    
    /* Enhanced progress bars */
    .stProgress {
      height: 12px;
      border-radius: 6px;
    }
    
    /* Better button styling */
    .stButton > button {
      border-radius: 6px;
      font-weight: 500;
      transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Improved metrics display */
    .metric-container {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      padding: 1rem;
      margin: 0.5rem;
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
      .css-1d391kg {
        background-color: #2b2b2b;
        border-right-color: #444;
      }
      
      .metric-container {
        background: #333;
        color: white;
      }
    }
    
    /* Hide Streamlit branding */
    .stApp > footer,
    [data-testid="stToolbar"] {
      display: none !important;
    }
    
    /* Responsive design improvements */
    @media (max-width: 768px) {
      .main .block-container {
        padding: 1rem;
      }
    }
  `;
  document.head.appendChild(style);
  
  // Add desktop app identification
  document.body.classList.add('electron-app');
  
  // Disable context menu on production builds
  if (process.env.NODE_ENV === 'production') {
    document.addEventListener('contextmenu', (e) => {
      e.preventDefault();
    });
  }
  
  // Handle keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + R for refresh
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
      e.preventDefault();
      window.location.reload();
    }
    
    // Ctrl/Cmd + N for new transcription
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
      e.preventDefault();
      // Trigger new transcription in Streamlit
      const newButton = document.querySelector('[data-testid="stButton"]:first-of-type button');
      if (newButton) {
        newButton.click();
      }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
      // Close any open expanders or modals
      const closeButtons = document.querySelectorAll('[data-testid="stExpander"] button');
      closeButtons.forEach(button => {
        if (button.getAttribute('aria-expanded') === 'true') {
          button.click();
        }
      });
    }
  });
  
  // Enhance file drag and drop
  document.addEventListener('dragover', (e) => {
    e.preventDefault();
    document.body.classList.add('drag-over');
  });
  
  document.addEventListener('dragleave', (e) => {
    if (!document.body.contains(e.relatedTarget)) {
      document.body.classList.remove('drag-over');
    }
  });
  
  document.addEventListener('drop', (e) => {
    e.preventDefault();
    document.body.classList.remove('drag-over');
    
    // Handle dropped files
    const files = Array.from(e.dataTransfer.files);
    const audioVideoFiles = files.filter(file => 
      file.type.startsWith('audio/') || file.type.startsWith('video/')
    );
    
    if (audioVideoFiles.length > 0) {
      // Simulate file upload to Streamlit file uploader
      const fileUploader = document.querySelector('input[type="file"]');
      if (fileUploader) {
        // Create a new FileList-like object
        const dataTransfer = new DataTransfer();
        audioVideoFiles.forEach(file => dataTransfer.items.add(file));
        fileUploader.files = dataTransfer.files;
        
        // Trigger change event
        const event = new Event('change', { bubbles: true });
        fileUploader.dispatchEvent(event);
      }
    }
  });
  
  // Add drag-over styling
  const dragStyle = document.createElement('style');
  dragStyle.textContent = `
    .drag-over {
      background-color: rgba(0, 123, 255, 0.1);
    }
    
    .drag-over::after {
      content: "Drop files here to upload";
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: rgba(0, 123, 255, 0.9);
      color: white;
      padding: 2rem 3rem;
      border-radius: 8px;
      font-size: 1.5rem;
      font-weight: bold;
      z-index: 10000;
      pointer-events: none;
    }
  `;
  document.head.appendChild(dragStyle);
  
  // Periodically check for Streamlit updates and enhance UI
  setInterval(() => {
    // Add tooltips to buttons without titles
    const buttons = document.querySelectorAll('button:not([title])');
    buttons.forEach(button => {
      const text = button.textContent.trim();
      if (text && !button.title) {
        button.title = text;
      }
    });
    
    // Enhance file uploader appearance
    const fileUploaders = document.querySelectorAll('.stFileUploader');
    fileUploaders.forEach(uploader => {
      if (!uploader.classList.contains('enhanced')) {
        uploader.classList.add('enhanced');
        uploader.addEventListener('dragenter', () => {
          uploader.style.borderColor = '#007bff';
          uploader.style.backgroundColor = '#f8f9ff';
        });
        uploader.addEventListener('dragleave', () => {
          uploader.style.borderColor = '#6c757d';
          uploader.style.backgroundColor = 'transparent';
        });
      }
    });
  }, 2000);
});