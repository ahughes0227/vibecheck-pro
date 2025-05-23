const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const express = require('express');
const expressApp = express();
const multer = require('multer');
const upload = multer({ dest: app.getPath('temp') });
const fs = require('fs');
const { spawn } = require('child_process');
const { autoUpdater } = require('electron-updater');
const axios = require('axios');
const FormData = require('form-data');
const Store = require('electron-store');

const store = new Store();

let mainWindow;
let flaskProcess;

// Configure auto-updater
autoUpdater.autoDownload = false;
autoUpdater.autoInstallOnAppQuit = true;

function getPythonPath() {
  const isDev = process.env.NODE_ENV === 'development';
  if (isDev) {
    return process.platform === 'win32' ? 'python' : 'python3';
  }

  const resourcesPath = process.resourcesPath;
  if (!resourcesPath) {
    throw new Error('Resources path not found');
  }

  const pythonPath =
    process.platform === 'win32'
      ? path.join(resourcesPath, 'python', 'Scripts', 'python.exe')
      : path.join(resourcesPath, 'python', 'bin', 'python3');

  if (!fs.existsSync(pythonPath)) {
    throw new Error(`Python executable not found at: ${pythonPath}`);
  }

  return pythonPath;
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    icon: path.join(__dirname, 'vc_analyzer_icon.png'),
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#f8fafc'
  });

  mainWindow.loadFile('index.html');

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  // Start Flask server
  startFlaskServer();

  // Check for updates
  checkForUpdates();
}

function startFlaskServer() {
  try {
    const pythonPath = getPythonPath();
    const flaskScript = path.join(__dirname, 'flask_server.py');

    console.log('Starting Flask server with Python:', pythonPath);
    console.log('Flask script path:', flaskScript);

    flaskProcess = spawn(pythonPath, [flaskScript], {
      env: {
        ...process.env,
        PYTHONPATH: path.join(__dirname),
      },
    });

    flaskProcess.stdout.on('data', (data) => {
      console.log(`Flask server: ${data}`);
    });

    flaskProcess.stderr.on('data', (data) => {
      console.error(`Flask server error: ${data}`);
    });

    flaskProcess.on('error', (err) => {
      console.error('Failed to start Flask server:', err);
      dialog.showErrorBox('Server Error', `Failed to start server: ${err.message}`);
    });
  } catch (error) {
    console.error('Error starting Flask server:', error);
    dialog.showErrorBox('Server Error', `Failed to start server: ${error.message}`);
  }
}

// Auto-update handlers
function checkForUpdates() {
  autoUpdater.checkForUpdates().catch((err) => {
    console.error('Error checking for updates:', err);
  });
}

autoUpdater.on('update-available', (info) => {
  dialog
    .showMessageBox(mainWindow, {
      type: 'info',
      title: 'Update Available',
      message: `Version ${info.version} is available. Would you like to download it now?`,
      buttons: ['Yes', 'No'],
    })
    .then((result) => {
      if (result.response === 0) {
        autoUpdater.downloadUpdate();
      }
    });
});

autoUpdater.on('update-downloaded', (info) => {
  dialog
    .showMessageBox(mainWindow, {
      type: 'info',
      title: 'Update Ready',
      message: `Version ${info.version} has been downloaded. Would you like to install it now?`,
      buttons: ['Yes', 'No'],
    })
    .then((result) => {
      if (result.response === 0) {
        autoUpdater.quitAndInstall();
      }
    });
});

autoUpdater.on('error', (err) => {
  dialog.showErrorBox('Update Error', err.message);
});

// Handle file selection
ipcMain.handle('select-file', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'IDE Files', extensions: ['ide'] }
    ]
  });

  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  return null;
});

// Get file info
ipcMain.handle('get-file-info', async (event, filePath) => {
  try {
    const stats = await fs.promises.stat(filePath);
    return {
      name: path.basename(filePath),
      size: stats.size,
      lastModified: stats.mtime
    };
  } catch (error) {
    console.error('Error getting file info:', error);
    throw error;
  }
});

// Handle file analysis
ipcMain.handle('analyze-file', async (event, filePath) => {
  try {
    const formData = new FormData();
    formData.append('file', fs.createReadStream(filePath));

    const response = await axios.post('http://localhost:5000/analyze', formData, {
      headers: {
        ...formData.getHeaders()
      }
    });

    if (response.data.success) {
      return {
        success: true,
        path: response.data.reportPath
      };
    } else {
      return {
        success: false,
        error: response.data.error || 'Analysis failed'
      };
    }
  } catch (error) {
    console.error('Analysis error:', error);
    return {
      success: false,
      error: error.message || 'Failed to analyze file'
    };
  }
});

// Handle app updates
autoUpdater.on('checking-for-update', () => {
  mainWindow.webContents.send('update-status', 'Checking for updates...');
});

autoUpdater.on('update-available', (info) => {
  mainWindow.webContents.send('update-status', 'Update available. Downloading...');
});

autoUpdater.on('update-not-available', (info) => {
  mainWindow.webContents.send('update-status', 'No updates available');
});

autoUpdater.on('error', (err) => {
  mainWindow.webContents.send('update-status', 'Error checking for updates');
});

autoUpdater.on('download-progress', (progressObj) => {
  mainWindow.webContents.send('update-progress', progressObj);
});

autoUpdater.on('update-downloaded', (info) => {
  mainWindow.webContents.send('update-status', 'Update downloaded. Restarting...');
  autoUpdater.quitAndInstall();
});

// Check for updates periodically
setInterval(() => {
  autoUpdater.checkForUpdates();
}, 1000 * 60 * 60); // Check every hour

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  if (flaskProcess) {
    flaskProcess.kill();
  }
});
