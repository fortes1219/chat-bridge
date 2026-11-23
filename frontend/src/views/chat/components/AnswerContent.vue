<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import type { Exchange } from '../composables/useAsk';
import { PROGRAM_NAMES } from '../constants';
import { useTypedText } from '../composables/useTypedText';
import { useCitedSources } from '../composables/useCitedSources';
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

const sources = computed(() => props.exchange.context?.sources ?? []);
// Read from the text on screen, so a source is listed under the answer once its mark is shown.
const cited = useCitedSources(shown, sources);
const answerDone = computed(() => !props.streaming && !typing.value && props.exchange.answer !== '');

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

/**
 * Which of the page's own error texts to show: the service's reason when it gave one, else the
 * page's own code. The service's message is never drawn: it is in one language and written for
 * logs.
 */
const errorKey = computed<keyof MessageSchema['errors'] | null>(() => {
  const error = props.exchange.error;
  return error ? (error.reason ?? error.code) : null;
});
</script>

<template>
  <div class="flex flex-col gap-3" :data-test="`answer-${exchange.id}`">
    <!-- What the search found, before any answer text: how many sources, with the whole list one
         click away. The model was given all of them, so they stay reachable whatever it cites. -->
    <UCollapsible v-if="sources.length" data-test="all-sources" class="text-sm">
      <UButton
        data-test="all-sources-toggle"
        variant="link"
        color="neutral"
        size="sm"
        class="px-0"
        trailing-icon="i-lucide-chevron-down"
        :label="t('chat.allSources', { count: sources.length }, sources.length)"
      />
      <template #content>
        <SourceList :sources="sources" class="mt-1" data-test="all-sources-list" />
      </template>
    </UCollapsible>
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
    <!-- Under the answer, only what it cites, as numbered in its text. -->
    <section v-if="sources.length" data-test="sources" class="text-sm">
      <template v-if="cited.length">
        <p class="font-medium">{{ t('chat.citedSources') }}</p>
        <SourceList :sources="cited" data-test="cited-sources" />
      </template>
      <p v-else-if="answerDone" class="text-muted" data-test="none-cited">{{ t('chat.noneCited') }}</p>
      <p class="text-muted mt-1" data-test="latest-date">
        {{
          exchange.context?.data_latest_date
            ? t('chat.latestDate', { date: exchange.context.data_latest_date })
            : t('chat.noLatestDate')
        }}
      </p>
      <!-- A failed split is said, so it never looks like one that worked. -->
      <p v-if="exchange.context?.split_failed" class="text-muted mt-1" data-test="split-failed">
        {{ t('chat.splitFailed') }}
      </p>
    </section>
    <p v-if="exchange.context" class="text-muted text-xs" data-test="notice">
      {{ exchange.context.disclaimer[locale] }}
    </p>
  </div>
</template>
