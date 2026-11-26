<script setup lang="ts">
import type { Locale } from '../effects/data.ts'

defineProps<{ locale: Locale; still: boolean }>()

const labels = {
  'zh-TW': [
    { label: '市場事件', title: '聯準會利率決策', detail: '事件日期與來源' },
    { label: '引用回答', title: '利率政策與台積電', detail: '回到文件核對段落' },
    { label: '配置對照', title: '目前權重與提案', detail: '確認後才更新' },
  ],
  en: [
    { label: 'Market event', title: 'Fed rate decision', detail: 'Event date and source' },
    { label: 'Cited answer', title: 'Rate policy and TSMC', detail: 'Inspect the original passage' },
    { label: 'Allocation comparison', title: 'Current and proposed weights', detail: 'Apply after confirmation' },
  ],
}
</script>

<template>
  <figure class="cover-art" :class="{ 'cover-still': still }" aria-hidden="true">
    <div v-for="panel in labels[locale]" :key="panel.label" class="cover-sheet">
      <span class="sheet-label">{{ panel.label }}</span>
      <span class="sheet-title">{{ panel.title }}</span>
      <span class="sheet-detail">{{ panel.detail }}</span>
    </div>
  </figure>
</template>
