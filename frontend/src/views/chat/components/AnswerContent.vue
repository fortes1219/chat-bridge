<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import type { Exchange } from '../composables/useAsk';
import { PROGRAM_NAMES } from '../constants';
import { useTypedText } from '../composables/useTypedText';
import SourceList from './SourceList.vue';
import AnswerMarkdown from './AnswerMarkdown';

const props = defineProps<{ exchange: Exchange; streaming: boolean }>();

const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();

// The answer is typed onto the screen at a steady pace, however it arrives; a stopped or failed
// answer shows what had arrived at once.
const { shown, typing } = useTypedText({
  text: () => props.exchange.answer,
  arriving: () => props.streaming,
  cutShort: () => props.exchange.stopped || props.exchange.error !== null
});

/**
 * Which of the page's own error texts to show: the service's reason when it gave one, else the
 * page's own code. The service's message is never drawn: it is in one language and written for
 * logs.
 */
/**
 * The sources are in and the program has not written its first words, which can take a while: the
 * answer's place says so until they come.
 */
const waitingFirstWords = computed(
  () => props.streaming && !props.exchange.answer && !props.exchange.stopped && props.exchange.error === null
);
const programName = computed(() => {
  const program = props.exchange.context?.program;
  return program ? PROGRAM_NAMES[program] : '';
});

const errorKey = computed<keyof MessageSchema['errors'] | null>(() => {
  const error = props.exchange.error;
  return error ? (error.reason ?? error.code) : null;
});
</script>

<template>
  <div class="flex flex-col gap-3" :data-test="`answer-${exchange.id}`">
    <SourceList v-if="exchange.context" :context="exchange.context" />
    <UChatShimmer v-if="waitingFirstWords" data-test="waiting" :text="t('chat.waiting', { program: programName })" />
    <AnswerMarkdown data-test="answer-text" :value="shown" :streaming="typing" :caret="typing" />
    <p v-if="exchange.stopped" class="text-muted text-sm" data-test="answer-stopped">{{ t('chat.stopped') }}</p>
    <UAlert
      v-if="exchange.error"
      data-test="answer-error"
      color="error"
      variant="subtle"
      icon="i-lucide-circle-alert"
      :title="t(`errors.${errorKey}.title`)"
      :description="t(`errors.${errorKey}.description`)"
    />
    <p v-if="exchange.context" class="text-muted text-xs" data-test="notice">
      {{ exchange.context.disclaimer[locale] }}
    </p>
  </div>
</template>
