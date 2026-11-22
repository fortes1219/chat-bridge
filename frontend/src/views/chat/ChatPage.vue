<script setup lang="ts">
import { useLoginGate } from './composables/useLoginGate';
import { useAddressState } from './composables/useAddressState';
import { useAsk } from './composables/useAsk';
import LoginGate from './components/LoginGate.vue';
import ProgramPicker from './components/ProgramPicker.vue';
import ChatPanel from './components/ChatPanel.vue';

// Nothing of the chat or the strategy screen is drawn until a program is logged in.
const { states, status: gate, isChecking, checkAgain } = useLoginGate();
const { program, chooseProgram } = useAddressState(states);
const { exchanges, status, ask, stop } = useAsk(program);
</script>

<template>
  <main class="flex h-screen flex-col">
    <LoginGate
      v-if="gate !== 'open'"
      :status="gate"
      :states="states"
      :checking="isChecking"
      @check-again="checkAgain"
    />
    <!-- The place for the strategy screen beside the chat is drawn by the layout (T018). -->
    <section v-else data-test="chat-open" class="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col gap-4 p-4">
      <ProgramPicker :states="states" :program="program" @choose="chooseProgram" />
      <ChatPanel :exchanges="exchanges" :status="status" @ask="ask" @stop="stop" />
    </section>
  </main>
</template>
