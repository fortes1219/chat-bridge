import js from '@eslint/js';
import eslintConfigPrettier from 'eslint-config-prettier';
import pluginVue from 'eslint-plugin-vue';
import globals from 'globals';
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript';

export default defineConfigWithVueTs(
  {
    // The two declaration files are written by Nuxt UI's build plugin.
    ignores: ['dist/**', 'coverage/**', 'node_modules/**', 'auto-imports.d.ts', 'components.d.ts']
  },
  js.configs.recommended,
  pluginVue.configs['flat/essential'],
  vueTsConfigs.recommended,
  {
    languageOptions: {
      globals: globals.browser
    }
  },
  eslintConfigPrettier
);
