import { defineConfig } from 'electron-vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  main: {},
  preload: {},
  renderer: {
    root: 'src/renderer',
    publicDir: path.resolve(__dirname, 'public'),
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src/renderer'),
      },
    },
    plugins: [react(), tailwindcss()],
  },
})
