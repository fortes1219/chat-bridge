import { createRouter, createWebHistory } from 'vue-router';

// The page has one address. The language and the chosen program are in its query, so a reload
// or a shared link opens the same view.
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'chat',
      component: () => import('@/views/chat/ChatPage.vue')
    }
  ]
});

export default router;
