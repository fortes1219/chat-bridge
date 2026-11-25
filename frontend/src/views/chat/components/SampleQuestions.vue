<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import { useSamplesQuery } from '@/queries/use-samples-query';

const emit = defineEmits<{ pick: [question: string] }>();

const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();
const query = useSamplesQuery();

// The questions the service offers, in the page's language. None while it has not answered, or
// when the knowledge base does not hold the documents they are about.
const questions = computed(() => (query.data.value ?? []).map(question => question[locale.value]));
</script>

<template>
  <section v-if="questions.length" data-test="sample-questions" class="flex flex-col items-center gap-3">
    <p class="text-muted text-sm">{{ t('chat.samplesTitle') }}</p>
    <div class="flex flex-wrap justify-center gap-2">
      <UButton
        v-for="(question, index) in questions"
        :key="index"
        :label="question"
        :data-test="`sample-${index}`"
        color="neutral"
        variant="outline"
        size="sm"
        @click="emit('pick', question)"
      />
    </div>
  </section>
</template>
