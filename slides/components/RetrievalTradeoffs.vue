<script setup lang="ts">
import type { Locale } from '../effects/data.ts'

defineProps<{ locale: Locale; step: number }>()

const comparisons = [
  {
    value: '52 → 56 → 61',
    title: { 'zh-TW': '直接多取段落', en: 'Retrieve more passages' },
    measure: { 'zh-TW': '取 20／30／50 段，命中的標註目標增加。', en: 'At 20, 30 and 50 passages, total target hits rose.' },
    cost: { 'zh-TW': '取到 50 段，利率面向仍是 0。', en: 'The rate-policy case still had zero hits at 50.' },
  },
  {
    value: '+36 s',
    title: { 'zh-TW': '加入重排模型', en: 'Add a reranker' },
    measure: { 'zh-TW': '兩款輕量模型各命中 43 筆新聞，直接取 20 段有 51 筆。', en: 'Two lighter rerankers kept 43 news hits each, versus 51 in the direct top 20.' },
    cost: { 'zh-TW': '較大的模型多命中 4 筆，每題約多 36 秒。', en: 'The larger model added four hits and about 36 seconds per query.' },
  },
  {
    value: '7 / 9',
    title: { 'zh-TW': '按面向各自檢索', en: 'Search each subtopic' },
    measure: { 'zh-TW': '補回 7 筆利率來源，保留原題命中的段落。', en: 'Recovered seven rate-policy sources and retained original hits.' },
    cost: { 'zh-TW': '多一次模型呼叫，送出的上下文也更多。', en: 'Adds one model call and more context.' },
  },
] as const
const sourceNote = {
  'zh-TW': '原型對照實驗。延遲是單機樣本，三欄各自標明量測口徑。',
  en: 'Prototype comparison. Timing comes from one machine. Each column labels its measure.',
}
</script>

<template>
  <figure class="diagram tradeoff-diagram" :data-step="step">
    <div class="tradeoff-grid">
      <section
        v-for="(entry, index) in comparisons"
        :key="entry.value"
        class="tradeoff-column"
        :class="{ 'tradeoff-selected': index === 2 && step > index }"
      >
        <h2>{{ entry.title[locale] }}</h2>
        <div v-if="step > index" class="tradeoff-details">
          <strong class="tradeoff-value">{{ entry.value }}</strong>
          <p>{{ entry.measure[locale] }}</p>
          <p class="tradeoff-cost">{{ entry.cost[locale] }}</p>
        </div>
      </section>
    </div>
    <figcaption class="diagram-foot">{{ sourceNote[locale] }}</figcaption>
  </figure>
</template>
