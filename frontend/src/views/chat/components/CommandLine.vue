<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useClipboard } from '@vueuse/core';
import type { MessageSchema } from '@/i18n';

defineProps<{ command: string; label?: string }>();

const { t } = useI18n<{ message: MessageSchema }>();
const { copy, copied } = useClipboard();
</script>

<template>
  <!-- A command the user runs in a terminal; the page only shows it and never runs it. -->
  <div class="mt-1 flex flex-wrap items-center gap-2">
    <span v-if="label" class="text-muted text-xs">{{ label }}</span>
    <code class="bg-elevated rounded px-2 py-1 text-sm" data-test="command">{{ command }}</code>
    <UButton
      size="xs"
      variant="ghost"
      data-test="copy-command"
      :icon="copied ? 'i-lucide-check' : 'i-lucide-copy'"
      :label="copied ? t('login.copied') : t('login.copy')"
      @click="copy(command)"
    />
  </div>
</template>
