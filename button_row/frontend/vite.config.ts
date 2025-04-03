import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'build',
    rollupOptions: {
      input: 'src/index.html',
      output: {
        entryFileNames: 'ButtonRow.js',
        format: 'iife',
        name: 'ButtonRow'
      }
    }
  }
});