<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Program, ProgramState } from '@/service/api/programs';
import type { MessageSchema } from '@/i18n';
import { PROGRAM_NAMES, STATE_KEYS } from '../constants';

const props = defineProps<{ states: ProgramState[]; program: Program | null }>();
const emit = defineEmits<{ choose: [program: Program] }>();

const { t } = useI18n<{ message: MessageSchema }>();

// Both programs are listed with their states; only a logged-in one can be chosen.
const items = computed(() =>
  props.states.map(state => ({
    label: PROGRAM_NAMES[state.program],
    description: t(`loginState.${STATE_KEYS[state.state]}`),
    value: state.program,
    disabled: state.state !== 'logged in'
  }))
);

function onChoose(value: unknown): void {
  const chosen = props.states.find(state => state.program === value);
  if (chosen) emit('choose', chosen.program);
}
</script>

<template>
  <URadioGroup
    data-test="program-picker"
    orientation="horizontal"
    :legend="t('chat.answerWith')"
    :items="items"
    :model-value="program ?? undefined"
    @update:model-value="onChoose"
  />
</template>
