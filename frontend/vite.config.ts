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
      // Nuxt UI's typography components, which the answer's Markdown renderer draws each tag
      // with; without them Tailwind's reset leaves lists without markers and paragraphs touching.
      prose: true,
      // The page is always dark, in VS Code's dark colors (src/assets/css/main.css), so it does
      // not follow the system's light or dark setting.
      colorMode: false,
      ui: {
        // VS Code's accent is blue and its greys are plain, not Nuxt UI's green and blue-tinted
        // defaults. The exact shades are set in main.css.
        colors: { primary: 'blue', neutral: 'neutral' }
      },
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
