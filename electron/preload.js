const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  startEyeTracking: () => ipcRenderer.invoke('eye-tracking-start'),
  stopEyeTracking: () => ipcRenderer.invoke('eye-tracking-stop'),
  getWindowPosition: () => ipcRenderer.invoke('get-window-position'),
  getDisplayScaleFactor: () => ipcRenderer.invoke('get-display-scale-factor'),
});

