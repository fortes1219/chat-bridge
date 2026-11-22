<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { MessageSchema } from '@/i18n';
import type { Exchange } from '../composables/useAsk';
import SourceList from './SourceList.vue';
import AnswerMarkdown from './AnswerMarkdown';

defineProps<{ exchange: Exchange; streaming: boolean }>();

const { t } = useI18n<{ message: MessageSchema }>();
</script>

<template>
  <div class="flex flex-col gap-3" :data-test="`answer-${exchange.id}`">
    <SourceList v-if="exchange.context" :context="exchange.context" />
    <AnswerMarkdown data-test="answer-text" :value="exchange.answer" :streaming="streaming" />
    <p v-if="exchange.stopped" class="text-muted text-sm" data-test="answer-stopped">{{ t('chat.stopped') }}</p>
    <UAlert
      v-if="exchange.error"
      data-test="answer-error"
      color="error"
      variant="subtle"
      icon="i-lucide-circle-alert"
      :title="t('chat.failed')"
      :description="exchange.error.message"
    />
    <p v-if="exchange.context" class="text-muted text-xs" data-test="notice">{{ exchange.context.disclaimer }}</p>
  </div>
</template>
