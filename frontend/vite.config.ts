import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import ui from '@nuxt/ui/vite';

// While developing, the page is served by Vite and its requests go to the chat service on its
// fixed local address. The built page is served by the service itself, so no proxy is needed there.
const DEV_SERVICE_TARGET = 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [
    vue(),
    ui({
      // Every icon the page names is built into it. Nuxt UI still asks the Iconify API for an icon
      // that is not, and has no switch to stop that, so the scan also reads .ts files, where
      // icon names in lookup tables live; the default scan skips them.
      icon: {
        clientBundle: {
          scan: {
            globInclude: ['**/*.{vue,ts}']
          }
        }
      }
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      '/chat': { target: DEV_SERVICE_TARGET, changeOrigin: true }
    }
  }
});
