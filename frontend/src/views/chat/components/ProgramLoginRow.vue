<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useClipboard } from '@vueuse/core';
import type { Program, ProgramState } from '@/service/api/programs';
import type { MessageSchema } from '@/i18n';
import { PROGRAM_NAMES, STATE_KEYS } from '../constants';

const props = defineProps<{ program: ProgramState }>();

const { t } = useI18n<{ message: MessageSchema }>();
const { copy, copied } = useClipboard();

/** The command each program logs in with; the page only shows it and never runs it. */
const LOGIN_COMMANDS: Record<Program, string> = {
  'claude-code': 'claude auth login',
  codex: 'codex login'
};

const name = computed(() => PROGRAM_NAMES[props.program.program]);
const stateKey = computed(() => STATE_KEYS[props.program.state]);
const command = computed(() => LOGIN_COMMANDS[props.program.program]);
</script>

<template>
  <li :data-test="`login-program-${program.program}`">
    <div class="flex items-center justify-between gap-2">
      <span class="font-medium">{{ name }}</span>
      <UBadge
        :label="t(`loginState.${stateKey}`)"
        :color="program.state === 'logged in' ? 'success' : 'neutral'"
        variant="subtle"
      />
    </div>
    <p class="text-muted mt-1 text-sm">{{ t(`loginNext.${stateKey}`, { program: name }) }}</p>
    <div v-if="program.state === 'not logged in'" class="mt-1 flex items-center gap-2">
      <code class="bg-elevated rounded px-2 py-1 text-sm" data-test="login-command">{{ command }}</code>
      <UButton
        size="xs"
        variant="ghost"
        data-test="copy-command"
        :icon="copied ? 'i-lucide-check' : 'i-lucide-copy'"
        :label="copied ? t('login.copied') : t('login.copy')"
        @click="copy(command)"
      />
    </div>
  </li>
</template>
