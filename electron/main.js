const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../assets/icon.png')
  });

  // Load the Vue.js app
  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
  
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startPythonBackend() {
  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
  
  if (isDev) {
    // In development, backend is started separately via npm script
    return;
  }

  // In production, start Python backend
  const pythonPath = path.join(__dirname, '../backend/venv/Scripts/python.exe');
  const scriptPath = path.join(__dirname, '../backend/main.py');
  
  pythonProcess = spawn(pythonPath, ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000']);
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });
}

app.whenReady().then(() => {
  createWindow();
  startPythonBackend();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

// IPC handlers for communication between frontend and backend
ipcMain.handle('eye-tracking-start', async () => {
  // This will communicate with Python backend
  return { success: true };
});

ipcMain.handle('eye-tracking-stop', async () => {
  return { success: true };
});

ipcMain.handle('get-window-position', async () => {
  if (mainWindow) {
    const position = mainWindow.getPosition();
    const bounds = mainWindow.getBounds();
    return {
      x: position[0],
      y: position[1],
      width: bounds.width,
      height: bounds.height,
    };
  }
  return { x: 0, y: 0, width: 0, height: 0 };
});

ipcMain.handle('get-display-scale-factor', async () => {
  if (mainWindow) {
    const display = screen.getDisplayMatching(mainWindow.getBounds());
    
    // Try multiple methods to get accurate scale factor
    // Method 1: Use display.scaleFactor (should work on most platforms)
    if (display.scaleFactor && display.scaleFactor > 0) {
      console.log('Scale factor from display.scaleFactor:', display.scaleFactor);
      return display.scaleFactor;
    }
    
    // Method 2: Calculate from bounds vs workArea (Windows fallback)
    // Physical size vs logical size
    if (display.bounds && display.workArea) {
      const scaleX = display.bounds.width / display.workArea.width;
      const scaleY = display.bounds.height / display.workArea.height;
      const calculatedScale = (scaleX + scaleY) / 2;
      if (calculatedScale > 0 && calculatedScale !== 1.0) {
        console.log('Scale factor calculated from bounds:', calculatedScale);
        return calculatedScale;
      }
    }
    
    // Method 3: Try webContents zoom factor
    const zoomFactor = mainWindow.webContents.getZoomFactor();
    if (zoomFactor && zoomFactor > 0 && zoomFactor !== 1.0) {
      console.log('Scale factor from zoom factor:', zoomFactor);
      return zoomFactor;
    }
    
    console.log('Using default scale factor 1.0');
    return 1.0;
  }
  
  // Fallback to primary display
  const primaryDisplay = screen.getPrimaryDisplay();
  if (primaryDisplay.scaleFactor && primaryDisplay.scaleFactor > 0) {
    console.log('Scale factor from primary display:', primaryDisplay.scaleFactor);
    return primaryDisplay.scaleFactor;
  }
  
  console.log('Using default scale factor 1.0 (fallback)');
  return 1.0;
});

