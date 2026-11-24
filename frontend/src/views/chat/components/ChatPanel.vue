<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import type { MessageSchema } from '@/i18n';
import { MAX_QUESTION_LENGTH } from '@/service/schema/chat';
import type { AskStatus, Exchange } from '../composables/useAsk';
import AnswerContent from './AnswerContent.vue';
import SampleQuestions from './SampleQuestions.vue';

const props = defineProps<{ exchanges: Exchange[]; status: AskStatus }>();
const emit = defineEmits<{ ask: [question: string]; stop: []; openStrategy: [] }>();

const { t } = useI18n<{ message: MessageSchema }>();
const input = ref('');
/** Why the last question was not sent; cleared as soon as one is. */
const notSent = ref<'emptyQuestion' | 'longQuestion' | null>(null);

const QUESTION_SUFFIX = ':question';
const ANSWER_SUFFIX = ':answer';

// The question shows at once; its answer once the first event of it arrives. A message needs at
// least one part to be drawn, so the answer carries its text even while it is empty.
const messages = computed(() =>
  props.exchanges.flatMap(exchange => {
    const question = {
      id: exchange.id + QUESTION_SUFFIX,
      role: 'user' as const,
      parts: [{ type: 'text' as const, text: exchange.question }]
    };
    const started = exchange.context !== null || exchange.error !== null || exchange.stopped;
    if (!started) return [question];
    const answer = {
      id: exchange.id + ANSWER_SUFFIX,
      role: 'assistant' as const,
      parts: [{ type: 'text' as const, text: exchange.answer }]
    };
    return [question, answer];
  })
);

const exchangeOf = computed(() => new Map(props.exchanges.map(exchange => [exchange.id + ANSWER_SUFFIX, exchange])));

// The prompt itself drops an empty submit before `submit` is emitted, so pressing Enter or the
// send button on an empty box is caught here to say why nothing was sent. On Enter it reads the
// box itself: a question just sent clears the model before the box is redrawn.
function explainIfEmpty(event: Event): void {
  const typed = event.target instanceof HTMLTextAreaElement ? event.target.value : input.value;
  if (props.status === 'ready' && !typed.trim()) notSent.value = 'emptyQuestion';
}

// A question the service would refuse is not sent, and the page says why.
function onSubmit(): void {
  const question = input.value.trim();
  if (!question) {
    notSent.value = 'emptyQuestion';
    return;
  }
  if (question.length > MAX_QUESTION_LENGTH) {
    notSent.value = 'longQuestion';
    return;
  }
  notSent.value = null;
  input.value = '';
  emit('ask', question);
}
</script>

<template>
  <!-- `contents`, so the conversation and the question box are the page grid's two lower rows:
       the conversation scrolls in its row, the question box stays at the bottom. -->
  <div class="contents">
    <!-- The vertical padding is on the scrolling box itself: the list counts that box's padding
         when it places a new question at the top, and padding inside it would push the question
         under the top edge. -->
    <div class="flex min-h-0 flex-col overflow-y-auto px-4 py-6">
      <div class="mx-auto flex w-full max-w-3xl flex-1 flex-col">
        <SampleQuestions v-if="!exchanges.length" class="my-auto" @pick="input = $event" />
        <!-- With no footer, the scroll-to-bottom button stays at the bottom of this row and shows
             only while the reader has scrolled away from the end, so it never sits on the end. -->
        <UChatMessages
          v-else
          :messages="messages"
          :status="status"
          should-auto-scroll
          :ui="{ viewport: 'sticky top-auto bottom-4 h-0' }"
        >
          <!-- While the search runs, before the sources arrive. -->
          <template #indicator>
            <UChatShimmer data-test="searching" :text="t('chat.searching')" />
          </template>
          <template #content="{ message, streaming }">
            <AnswerContent
              v-if="exchangeOf.get(message.id)"
              :exchange="exchangeOf.get(message.id)!"
              :streaming="streaming"
              @open-strategy="emit('openStrategy')"
            />
            <p v-else class="whitespace-pre-wrap">{{ message.parts[0]?.text }}</p>
          </template>
        </UChatMessages>
      </div>
    </div>
    <footer class="border-default bg-muted border-t">
      <div class="mx-auto w-full max-w-3xl px-4 py-3">
        <UChatPrompt
          v-model="input"
          data-test="question-box"
          :status="status"
          :placeholder="t('chat.placeholder')"
          :ui="{ root: 'bg-accented ring-accented' }"
          @submit="onSubmit"
          @keydown.enter.exact="explainIfEmpty"
        >
          <UChatPromptSubmit data-test="send-or-stop" :status="status" @click="explainIfEmpty" @stop="emit('stop')" />
        </UChatPrompt>
        <p v-if="notSent" class="text-error mt-2 text-sm" data-test="not-sent">
          {{ t(`chat.${notSent}`, { limit: MAX_QUESTION_LENGTH.toLocaleString() }) }}
        </p>
      </div>
    </footer>
  </div>
</template>
