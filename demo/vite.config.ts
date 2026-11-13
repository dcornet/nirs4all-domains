import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import { browserWasm } from './scripts/browser-wasm';

export default defineConfig({
  base: '/nirs4all-domains/', plugins: [react(), browserWasm()],
  worker: { format: 'es', plugins: () => [browserWasm()] },
  build: { target: 'es2022', sourcemap: false, chunkSizeWarningLimit: 700 },
  server: { host: '127.0.0.1' }, preview: { host: '127.0.0.1' },
});
