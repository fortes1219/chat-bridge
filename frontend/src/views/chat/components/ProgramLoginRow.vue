<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { ProgramState } from '@/service/api/programs';
import type { MessageSchema } from '@/i18n';
import { INSTALL_COMMANDS, LOGIN_COMMANDS, PROGRAM_NAMES, STATE_KEYS } from '../constants';
import CommandLine from './CommandLine.vue';

const props = defineProps<{ program: ProgramState }>();

const { t } = useI18n<{ message: MessageSchema }>();

const name = computed(() => PROGRAM_NAMES[props.program.program]);
const stateKey = computed(() => STATE_KEYS[props.program.state]);
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
    <template v-if="program.state === 'not installed'">
      <CommandLine
        v-for="install in INSTALL_COMMANDS[program.program]"
        :key="install.command"
        :label="install.system"
        :command="install.command"
      />
      <CommandLine :command="LOGIN_COMMANDS[program.program]" />
    </template>
    <CommandLine v-else-if="program.state === 'not logged in'" :command="LOGIN_COMMANDS[program.program]" />
  </li>
</template>
