export interface ElectronAPI {
  getDisplayScaleFactor?: () => Promise<number>
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI
  }
}

export {}
