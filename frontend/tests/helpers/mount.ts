import { mount } from '@vue/test-utils';
import { defineComponent, h, Suspense, type Component } from 'vue';
import { createMemoryHistory, createRouter, type Router } from 'vue-router';
import ui from '@nuxt/ui/vue-plugin';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { createPageI18n } from '@/i18n';
import { createQueryClient } from '@/queries/query-client';

/**
 * Mounts a view at an address, with the plugins the page installs: Nuxt UI, i18n, the query client
 * and a router, under Suspense as the page's root is. The page takes its language from the address,
 * so the default address is English.
 */
export async function mountView(component: Component, { path = '/?lang=en' }: { path?: string } = {}) {
  const router: Router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: { template: '<div />' } }]
  });
  await router.push(path);
  await router.isReady();
  const root = defineComponent({ render: () => h(Suspense, null, { default: () => h(component) }) });
  const wrapper = mount(root, {
    attachTo: document.body,
    global: {
      plugins: [ui, createPageI18n(), [VueQueryPlugin, { queryClient: createQueryClient() }], router]
    }
  });
  return { wrapper, router };
}
