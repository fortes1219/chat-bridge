<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { MessageSchema } from '@/i18n';
import { SAMPLE_QUESTION_KEYS } from '../constants';

const emit = defineEmits<{ pick: [question: string] }>();

const { t } = useI18n<{ message: MessageSchema }>();
</script>

<template>
  <section data-test="sample-questions" class="flex flex-col items-center gap-3">
    <p class="text-muted text-sm">{{ t('chat.samplesTitle') }}</p>
    <div class="flex flex-wrap justify-center gap-2">
      <UButton
        v-for="key in SAMPLE_QUESTION_KEYS"
        :key="key"
        :label="t(`samples.${key}`)"
        :data-test="`sample-${key}`"
        color="neutral"
        variant="outline"
        size="sm"
        @click="emit('pick', t(`samples.${key}`))"
      />
    </div>
  </section>
</template>
