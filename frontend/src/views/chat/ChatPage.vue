<script setup lang="ts">
import { useI18n } from 'vue-i18n';
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
// A program that logged out since the page opened sends the page back to reading the states.
const { exchanges, status, ask, stop } = useAsk(program, { onLoggedOut: checkAgain });

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
  <!-- Three rows: the bar on top and the question box at the bottom stay where they are, and only
       the conversation between them scrolls. The chat panel draws the two lower rows. -->
  <main class="grid h-dvh grid-rows-[auto_minmax(0,1fr)_auto]">
    <header class="border-default bg-muted border-b">
      <div class="mx-auto flex w-full max-w-3xl items-center justify-between gap-4 px-4 py-2">
        <ProgramPicker v-if="gate === 'open'" :states="states" :program="program" @choose="chooseProgram" />
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
    <!-- The place for the strategy screen beside the chat is drawn by the layout (T018). -->
    <ChatPanel v-else data-test="chat-open" :exchanges="exchanges" :status="status" @ask="ask" @stop="stop" />
  </main>
</template>
