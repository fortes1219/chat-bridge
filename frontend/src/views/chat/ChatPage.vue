<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { breakpointsTailwind, useBreakpoints } from '@vueuse/core';
import { useProposalKept } from '@/queries/use-strategy-query';
import StrategyPanel from '@/views/strategy/StrategyPanel.vue';
import { LOCALES, UI_LOCALES, type MessageSchema } from '@/i18n';
import { useLoginGate } from './composables/useLoginGate';
import { useAddressState } from './composables/useAddressState';
import { useAsk } from './composables/useAsk';
import LoginGate from './components/LoginGate.vue';
import ProgramPicker from './components/ProgramPicker.vue';
import ChatPanel from './components/ChatPanel.vue';

// Nothing of the chat or the strategy screen is drawn until a program is logged in.
const { states, status: gate, isChecking, checkAgain } = useLoginGate();
const { language, program, chooseLanguage, chooseProgram } = useAddressState(states);
// A program that logged out since the page opened sends the page back to reading the states; a
// proposal the service kept is now the open one of the strategy.
const { exchanges, status, ask, stop } = useAsk(program, {
  onLoggedOut: checkAgain,
  onProposal: useProposalKept()
});
const open = computed(() => gate.value === 'open');

// The strategy sits beside the chat in a wide window and in a slide-over in a narrow one, which the
// proposal card and the bar's button open.
const isNarrow = useBreakpoints(breakpointsTailwind).smaller('lg');
const strategyOpen = ref(false);
// The chat panel's share of a wide window, in percent; the strategy takes the rest.
const CHAT_PANEL = { defaultSize: 62, minSize: 45, maxSize: 75 } as const;

const { t } = useI18n<{ message: MessageSchema }>();
// Each language by its own name only: the flag emoji a locale select adds is drawn on Windows as
// two letters, which name no language.
const LANGUAGES = LOCALES.map(locale => ({ label: UI_LOCALES[locale].name, value: locale }));

function onChooseLanguage(value: string): void {
  const chosen = LOCALES.find(locale => locale === value);
  if (chosen) chooseLanguage(chosen);
}
</script>

<template>
  <UDashboardGroup unit="%" storage="local" storage-key="chat-bridge">
    <UDashboardPanel
      id="chat"
      :resizable="open && !isNarrow"
      :default-size="open && !isNarrow ? CHAT_PANEL.defaultSize : undefined"
      :min-size="CHAT_PANEL.minSize"
      :max-size="CHAT_PANEL.maxSize"
    >
      <!-- Three rows: the bar on top and the question box at the bottom stay where they are, and
           only the conversation between them scrolls. The chat panel draws the two lower rows. -->
      <main class="grid min-h-0 flex-1 grid-rows-[auto_minmax(0,1fr)_auto]">
        <header class="border-default bg-muted border-b">
          <div class="mx-auto flex w-full max-w-3xl items-center justify-between gap-4 px-4 py-2">
            <ProgramPicker v-if="open" :states="states" :program="program" @choose="chooseProgram" />
            <UButton
              v-if="open && isNarrow"
              data-test="open-strategy"
              color="neutral"
              variant="outline"
              size="sm"
              icon="i-lucide-chart-pie"
              :label="t('strategy.open')"
              @click="strategyOpen = true"
            />
            <USelect
              data-test="language"
              class="ms-auto w-36"
              size="sm"
              icon="i-lucide-languages"
              :aria-label="t('page.language')"
              :items="LANGUAGES"
              :model-value="language"
              @update:model-value="onChooseLanguage"
            />
          </div>
        </header>
        <div v-if="gate !== 'open'" class="flex min-h-0 overflow-y-auto p-4">
          <LoginGate :status="gate" :states="states" :checking="isChecking" @check-again="checkAgain" />
        </div>
        <ChatPanel
          v-else
          data-test="chat-open"
          :exchanges="exchanges"
          :status="status"
          @ask="ask"
          @stop="stop"
          @open-strategy="strategyOpen = true"
        />
      </main>
    </UDashboardPanel>
    <UDashboardPanel v-if="open && !isNarrow" id="strategy" data-test="strategy-panel">
      <div class="min-h-0 flex-1 overflow-y-auto">
        <StrategyPanel />
      </div>
    </UDashboardPanel>
    <USlideover
      v-if="open && isNarrow"
      v-model:open="strategyOpen"
      data-test="strategy-slideover"
      :title="t('strategy.title')"
    >
      <template #body>
        <StrategyPanel headless />
      </template>
    </USlideover>
  </UDashboardGroup>
</template>
