import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const API_TARGET = process.env.POLDERGRAPH_API ?? 'http://127.0.0.1:7432';

export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    port: 5273,
    strictPort: false,
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: false,
        // SSE must stream; never buffer.
        configure(proxy) {
          proxy.on('proxyRes', (proxyRes) => {
            if (proxyRes.headers['content-type']?.includes('text/event-stream')) {
              proxyRes.headers['cache-control'] = 'no-cache, no-transform';
            }
          });
        },
      },
    },
  },
  worker: {
    format: 'es',
  },
  build: {
    // Keep the production bundle inside the Python package so Hatch includes it
    // in both wheels and source distributions without a Node build at install time.
    outDir: '../src/poldergraph/web/dist',
    emptyOutDir: true,
    target: 'es2022',
    sourcemap: false,
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks: {
          sigma: ['sigma', '@sigma/node-border'],
          graphology: [
            'graphology',
            'graphology-types',
            'graphology-layout',
            'graphology-layout-forceatlas2',
          ],
        },
      },
    },
  },
});
