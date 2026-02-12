/// <reference types="electron-vite/node" />
import { app, BrowserWindow } from 'electron'
import path from 'path'
import { startPythonAPI, stopPythonAPI } from './python'

let win: BrowserWindow | null = null

function createWindow() {
  win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.mjs'),
      contextIsolation: true,
    },
  })

  if (process.env.ELECTRON_RENDERER_URL) {
    win.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    win.loadFile(path.join(__dirname, '../renderer/index.html'))
  }
}

app.on('window-all-closed', () => {
  stopPythonAPI()
  if (process.platform !== 'darwin') {
    app.quit()
    win = null
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

app.on('quit', () => {
  stopPythonAPI()
})

app.whenReady().then(async () => {
  await startPythonAPI()
  createWindow()
})
