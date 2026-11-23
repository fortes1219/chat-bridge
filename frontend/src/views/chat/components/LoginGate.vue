<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { ProgramState } from '@/service/api/programs';
import type { MessageSchema } from '@/i18n';
import type { GateStatus } from '../composables/useLoginGate';
import ProgramLoginRow from './ProgramLoginRow.vue';

type ClosedStatus = Exclude<GateStatus, 'open'>;

const props = defineProps<{
  status: ClosedStatus;
  states: ProgramState[];
  checking: boolean;
}>();
const emit = defineEmits<{ checkAgain: [] }>();

const { t } = useI18n<{ message: MessageSchema }>();

type LoginKey = keyof MessageSchema['login'];
const HEADINGS: Record<ClosedStatus, { title: LoginKey; description?: LoginKey; icon: string }> = {
  reading: { title: 'reading', icon: 'i-lucide-loader-circle' },
  locked: { title: 'title', description: 'description', icon: 'i-lucide-log-in' },
  unreachable: { title: 'unreachableTitle', description: 'unreachable', icon: 'i-lucide-unplug' }
};

const heading = computed(() => HEADINGS[props.status]);
</script>

<template>
  <UEmpty
    data-test="login-gate"
    :icon="heading.icon"
    :loading="status === 'reading'"
    :title="t(`login.${heading.title}`)"
    :description="heading.description ? t(`login.${heading.description}`) : undefined"
    class="m-auto w-full max-w-xl"
  >
    <!-- While the first read is out there is nothing to retry yet. -->
    <template v-if="status !== 'reading'" #body>
      <ul v-if="status === 'locked'" class="w-full space-y-3 text-left">
        <ProgramLoginRow v-for="program in states" :key="program.program" :program="program" />
      </ul>
      <UButton
        data-test="check-again"
        icon="i-lucide-refresh-cw"
        :label="t('login.checkAgain')"
        :loading="checking"
        :disabled="checking"
        @click="emit('checkAgain')"
      />
    </template>
  </UEmpty>
</template>
