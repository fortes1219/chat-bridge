<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { UI_LOCALES, type Locale } from '@/i18n';

const { locale } = useI18n<[unknown], Locale>({ useScope: 'global' });
</script>

<template>
  <!-- The answer's Markdown renderer parses in an async setup, which renders only under Suspense. -->
  <Suspense>
    <UApp :locale="UI_LOCALES[locale]">
      <RouterView />
    </UApp>
  </Suspense>
</template>
