<script setup lang="ts">
import { computed } from 'vue'
import type { Locale } from '../effects/data.ts'

const props = defineProps<{ locale: Locale; step: number }>()

const passages = {
  A: { 'zh-TW': '利率趨勢摘要', en: 'Rate trend summary' },
  B: { 'zh-TW': '聯準會聲明', en: 'Fed statement' },
  C: { 'zh-TW': '前次會議紀錄', en: 'Prior meeting minutes' },
  D: { 'zh-TW': 'Fed 關鍵字索引', en: 'Fed keyword entry' },
}
type Passage = keyof typeof passages
const lanes = {
  vector: ['A', 'B', 'C'],
  text: ['B', 'C', 'D'],
} satisfies Record<string, Passage[]>
const firstOrder: Passage[] = ['A', 'B', 'C', 'D']
const rankConstant = 60
const example: Passage = 'B'

function ranks(passage: Passage) {
  return Object.values(lanes).map(lane => lane.indexOf(passage) + 1)
}

function reciprocalRank(rank: number) {
  return rank === 0 ? 0 : 1 / (rankConstant + rank)
}

function score(passage: Passage) {
  return ranks(passage).reduce((total, rank) => total + reciprocalRank(rank), 0)
}

const exampleFormula = ranks(example).map(rank => `1/(${rankConstant}+${rank})`).join(' + ')
const merged = computed(() => props.step === 2
  ? [...firstOrder].sort((left, right) => score(right) - score(left))
  : firstOrder)

const labels = {
  'zh-TW': { vector: '向量名次', text: '全文名次', result: '合併後', waiting: '合併重複的段落', note: '名次為示例', example: 'B 的分數' },
  en: { vector: 'Vector ranks', text: 'Full-text ranks', result: 'Fused ranks', waiting: 'Merge matching passages', note: 'Illustrative ranks', example: 'Score for B' },
}
</script>

<template>
  <figure class="diagram fusion-diagram" :data-step="step">
    <div v-for="(ranking, key) in lanes" :key="key" class="fusion-lane">
      <span class="diagram-label">{{ labels[locale][key] }}</span>
      <ol>
        <li v-for="(passage, index) in ranking" :key="passage">
          <span class="fusion-rank">{{ index + 1 }}</span>
          <span class="fusion-id" :data-passage="passage">{{ passage }}</span>
          {{ passages[passage][locale] }}
        </li>
      </ol>
    </div>
    <div class="fusion-lane fusion-result">
      <span class="diagram-label">{{ labels[locale].result }}</span>
      <p v-if="step === 0" class="diagram-note">{{ labels[locale].waiting }}</p>
      <TransitionGroup v-else name="fusion-list" tag="ol">
        <li v-for="(passage, index) in merged" :key="passage">
          <span class="fusion-rank">{{ step === 2 ? index + 1 : '–' }}</span>
          <span class="fusion-id" :data-passage="passage">{{ passage }}</span>
          {{ passages[passage][locale] }}
        </li>
      </TransitionGroup>
    </div>
    <figcaption class="diagram-foot">
      <span>{{ labels[locale].note }} · RRF k = {{ rankConstant }}</span>
      <strong v-if="step === 2" class="fusion-formula">{{ labels[locale].example }} = {{ exampleFormula }} ≈ {{ score(example).toFixed(5) }}</strong>
    </figcaption>
  </figure>
</template>
