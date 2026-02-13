import { spawn, type ChildProcess } from 'child_process'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

let pythonProcess: ChildProcess | null = null
const API_PORT = 8000

export async function startPythonAPI(): Promise<void> {
  if (pythonProcess) return

  // projectRoot = horario/ (parent of apps/)
  const projectRoot = path.resolve(__dirname, '../../../..')
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3'

  pythonProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'apps.backend.main:app', '--host', '127.0.0.1', '--port', String(API_PORT)], {
    cwd: projectRoot,
    env: { ...process.env, PYTHONPATH: projectRoot },
    stdio: 'pipe',
  })

  pythonProcess.on('error', (err) => {
    console.error('Python API spawn error:', err)
  })

  pythonProcess.on('exit', () => {
    pythonProcess = null
  })

  // Wait for API to be ready (poll /health)
  const maxAttempts = 30
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise((r) => setTimeout(r, 500))
    try {
      const res = await fetch(`http://127.0.0.1:${API_PORT}/health`)
      if (res.ok) return
    } catch {
      // continue
    }
  }
}

export function stopPythonAPI(): void {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
}
