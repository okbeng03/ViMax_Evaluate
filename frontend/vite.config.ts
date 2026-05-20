import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'
import type { Plugin } from 'vite'

const COMFYUI_OUTPUT_DIR = 'D:\\ComfyUI\\output'
const IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp']

function findFileWithExtension(basePath: string): string | null {
  if (fs.existsSync(basePath) && fs.statSync(basePath).isFile()) {
    return basePath
  }
  for (const ext of IMAGE_EXTENSIONS) {
    const withExt = basePath + ext
    if (fs.existsSync(withExt) && fs.statSync(withExt).isFile()) {
      return withExt
    }
  }
  return null
}

function comfyuiOutputProxyPlugin(): Plugin {
  return {
    name: 'comfyui-output-proxy',
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const url = req.url || ''
        if (url.startsWith('/comfyui-output')) {
          const filePath = url.replace('/comfyui-output', '')
          const absolutePath = findFileWithExtension(path.join(COMFYUI_OUTPUT_DIR, filePath))
          if (absolutePath) {
            const ext = path.extname(absolutePath).toLowerCase()
            const mimeTypes: Record<string, string> = {
              '.png': 'image/png',
              '.jpg': 'image/jpeg',
              '.jpeg': 'image/jpeg',
              '.gif': 'image/gif',
              '.webp': 'image/webp',
            }
            res.setHeader('Access-Control-Allow-Origin', '*')
            res.setHeader('Content-Type', mimeTypes[ext] || 'application/octet-stream')
            fs.createReadStream(absolutePath).pipe(res)
          } else {
            res.statusCode = 404
            res.end('File not found')
          }
        } else {
          next()
        }
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), comfyuiOutputProxyPlugin()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          antd: ['antd', '@ant-design/icons'],
        },
      },
    },
    chunkSizeWarningLimit: 500,
  },
})
