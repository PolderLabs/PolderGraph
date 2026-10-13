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
    // Build straight into the directory the Python package serves
    // (api/server.py: ASSET_DIR -> src/poldergraph/web/dist) and that hatch
    // packages as `src/poldergraph/web/dist`. Building to web/dist instead
    // left a second copy that nothing serves, and force-including web/dist
    // into poldergraph/web/dist could publish stale or mismatched asset
    // hashes, because index.html and assets/ then come from different builds.
    outDir: '../src/poldergraph/web/dist',
    emptyOutDir: true,
    target: 'es2022',
    sourcemap: false,
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks: {
          sigma: ['sigma'],
          // The layout moved to d3-force, so graphology-layout and
          // graphology-layout-forceatlas2 are no longer pulled in by anything
          // under web/src. Listing them here only reserved a chunk name for
          // modules that are never imported.
          graphology: ['graphology', 'graphology-types'],
        },
      },
    },
  },
});
