import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config.ts';

// The tests build components with the page's own Vite settings, Nuxt UI and its icon bundling
// included, so a view renders in a test as it does in the page.
export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'happy-dom'
    }
  })
);
