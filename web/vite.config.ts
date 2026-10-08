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
    // Hatch's force-include copies web/dist into the Python package for both
    // wheels and source distributions. Keeping the build output here also lets
    // the package's build hooks find the documented dashboard artifact.
    outDir: './dist',
    emptyOutDir: true,
    target: 'es2022',
    sourcemap: false,
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks: {
          sigma: ['sigma'],
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
