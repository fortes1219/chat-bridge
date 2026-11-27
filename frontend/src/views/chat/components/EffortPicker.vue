<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Effort } from '@/service/api/chat';
import type { MessageSchema } from '@/i18n';
import { EFFORT_KEYS, EFFORT_ORDER } from '../constants';

defineProps<{ effort: Effort }>();
const emit = defineEmits<{ choose: [effort: Effort] }>();

const { t } = useI18n<{ message: MessageSchema }>();

const items = computed(() =>
  EFFORT_ORDER.map(level => ({ label: t(`chat.effort.${EFFORT_KEYS[level]}`), value: level }))
);

function onChoose(value: unknown): void {
  const chosen = EFFORT_ORDER.find(level => level === value);
  if (chosen) emit('choose', chosen);
}
</script>

<template>
  <USelect
    data-test="effort"
    class="w-32"
    size="sm"
    color="neutral"
    variant="ghost"
    icon="i-lucide-gauge"
    :aria-label="t('chat.effortLabel')"
    :items="items"
    :model-value="effort"
    @update:model-value="onChoose"
  />
</template>
