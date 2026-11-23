<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { ChatContext } from '@/service/api/chat';
import type { Locale, MessageSchema } from '@/i18n';

defineProps<{ context: ChatContext }>();

const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();
</script>

<template>
  <!-- Every field is drawn as plain text: it comes from the documents. A section name the sample
       news is written with comes in both languages and is shown in the page's. -->
  <section data-test="sources" class="text-sm">
    <ol v-if="context.sources.length" class="space-y-1">
      <li v-for="source in context.sources" :key="source.number" :data-test="`source-${source.number}`">
        <span class="font-medium">[{{ source.number }}]</span>
        {{ source.file }} · {{ source.heading_localizations?.[locale] ?? source.heading }} ·
        {{ source.event_date ?? t('chat.noDate') }}
      </li>
    </ol>
    <p v-if="context.sources.length" class="text-muted mt-1" data-test="latest-date">
      {{ context.data_latest_date ? t('chat.latestDate', { date: context.data_latest_date }) : t('chat.noLatestDate') }}
    </p>
  </section>
</template>
