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
        name: 'ButtonRow',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name === 'index.html') {
            return '[name][extname]'; // Outputs index.html directly to build/
          }
          return 'assets/[name][extname]';
        },
        globals: {
            'react': 'React',
            'react-dom': 'ReactDOM',
            'streamlit-component-lib': 'Streamlit'
          }
      }
    },
    assetsDir: ''
  }
});