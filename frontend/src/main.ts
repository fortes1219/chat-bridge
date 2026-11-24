import './assets/css/main.css';
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import ui from '@nuxt/ui/vue-plugin';
import { VueQueryPlugin } from '@tanstack/vue-query';
import App from './App.vue';
import router from './router';
import { createPageI18n } from '@/i18n';
import { queryClient } from '@/queries/query-client';

createApp(App)
  .use(ui)
  .use(createPinia())
  .use(createPageI18n())
  .use(VueQueryPlugin, { queryClient })
  .use(router)
  .mount('#app');
