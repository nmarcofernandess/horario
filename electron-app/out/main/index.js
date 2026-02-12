import { app, BrowserWindow } from "electron";
import path from "path";
import { spawn } from "child_process";
import { fileURLToPath } from "url";
import __cjs_mod__ from "node:module";
const __filename = import.meta.filename;
const __dirname = import.meta.dirname;
const require2 = __cjs_mod__.createRequire(import.meta.url);
const __dirname$1 = path.dirname(fileURLToPath(import.meta.url));
let pythonProcess = null;
const API_PORT = 8e3;
async function startPythonAPI() {
  if (pythonProcess) return;
  const projectRoot = path.resolve(__dirname$1, "../../..");
  const pythonCmd = process.platform === "win32" ? "python" : "python3";
  pythonProcess = spawn(pythonCmd, ["-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", String(API_PORT)], {
    cwd: projectRoot,
    env: { ...process.env, PYTHONPATH: projectRoot },
    stdio: "pipe"
  });
  pythonProcess.on("error", (err) => {
    console.error("Python API spawn error:", err);
  });
  pythonProcess.on("exit", (code) => {
    pythonProcess = null;
  });
  const maxAttempts = 30;
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise((r) => setTimeout(r, 500));
    try {
      const res = await fetch(`http://127.0.0.1:${API_PORT}/health`);
      if (res.ok) return;
    } catch {
    }
  }
}
function stopPythonAPI() {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
}
let win = null;
function createWindow() {
  win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "../preload/index.mjs"),
      contextIsolation: true
    }
  });
  if (process.env.ELECTRON_RENDERER_URL) {
    win.loadURL(process.env.ELECTRON_RENDERER_URL);
  } else {
    win.loadFile(path.join(__dirname, "../renderer/index.html"));
  }
}
app.on("window-all-closed", () => {
  stopPythonAPI();
  if (process.platform !== "darwin") {
    app.quit();
    win = null;
  }
});
app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
app.on("quit", () => {
  stopPythonAPI();
});
app.whenReady().then(async () => {
  await startPythonAPI();
  createWindow();
});
