<script setup lang="ts">
import type { Locale } from '../effects/data.ts'

defineProps<{ locale: Locale; step: number }>()

const labels = {
  'zh-TW': {
    source: '原始 PDF · 第 3 頁', title: '聯準會利率決策', index: '可搜尋的段落',
    headings: ['決策摘要', '市場反應'], table: '當日與之後的行情', page: '第 3 頁',
    waiting: '依頁面與段落結構切分', attached: '附回同一事件的行情表',
    chunk: '每段最多 512 tokens', note: '文件與段落為流程示意',
  },
  en: {
    source: 'Source PDF · page 3', title: 'Fed rate decision', index: 'Searchable passages',
    headings: ['Decision summary', 'Market reaction'], table: 'Event-day prices and later moves', page: 'Page 3',
    waiting: 'Split at document boundaries', attached: 'Attach the table to the event',
    chunk: 'Up to 512 tokens per passage', note: 'Illustrative document and passages',
  },
}
</script>

<template>
  <figure class="diagram document-diagram" :data-step="step">
    <div class="document-paper">
      <span class="diagram-label">{{ labels[locale].source }}</span>
      <strong class="document-title">{{ labels[locale].title }}</strong>
      <div v-for="heading in labels[locale].headings" :key="heading" class="document-section">
        <span>{{ heading }}</span>
        <i aria-hidden="true"></i>
      </div>
      <div class="document-table">{{ labels[locale].table }}</div>
    </div>
    <div class="document-arrow" aria-hidden="true">→</div>
    <div class="document-index">
      <span class="diagram-label">{{ labels[locale].index }}</span>
      <p v-if="step === 0" class="diagram-note">{{ labels[locale].waiting }}</p>
      <div v-if="step >= 1" class="document-passage-list">
        <div v-for="(heading, index) in labels[locale].headings" :key="heading" class="document-passage" :style="{ '--row': index }">
          <strong>{{ heading }}</strong>
          <span>{{ labels[locale].page }} / {{ heading }}</span>
        </div>
      </div>
      <div v-if="step >= 2" class="document-attachment">
        <span>{{ labels[locale].table }}</span>
        <strong>{{ labels[locale].attached }}</strong>
      </div>
    </div>
    <figcaption class="diagram-foot">
      <span>{{ labels[locale].chunk }}</span>
      <span>{{ labels[locale].note }}</span>
    </figcaption>
  </figure>
</template>
