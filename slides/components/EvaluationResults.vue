<script setup lang="ts">
import { evaluation, type Locale } from '../effects/data.ts'

defineProps<{ locale: Locale; step: number }>()

const heldOut = evaluation[1]
const relatedSets = [evaluation[0], evaluation[2]]
const baselineWidth = `${100 * heldOut.before / heldOut.total}%`
const addedWidth = `${100 * (heldOut.after - heldOut.before) / heldOut.total}%`
const beforePercent = Math.round(100 * heldOut.before / heldOut.total)
const afterPercent = Math.round(100 * heldOut.after / heldOut.total)

const labels = {
  'zh-TW': { before: '原題前 8 段', after: '加上拆題結果', added: '補回的證據', denominator: '分母為標註的證據目標' },
  en: { before: 'Original top eight', after: 'With split queries', added: 'Recovered evidence', denominator: 'Denominator: labeled evidence targets' },
}
</script>

<template>
  <figure class="diagram recall-diagram" :data-step="step">
    <div class="recall-heading">
      <strong>{{ heldOut.label[locale] }}</strong>
      <span class="diagram-label">{{ labels[locale].denominator }}</span>
    </div>
    <div class="recall-row">
      <span>{{ labels[locale].before }}</span>
      <div class="recall-track">
        <span class="recall-base" :style="{ width: baselineWidth }"></span>
      </div>
      <strong>{{ heldOut.before }}/{{ heldOut.total }} <small>{{ beforePercent }}%</small></strong>
    </div>
    <div class="recall-row">
      <span>{{ labels[locale].after }}</span>
      <div class="recall-track">
        <span class="recall-base" :style="{ width: baselineWidth }"></span>
        <span class="recall-added" :style="{ width: step >= 1 ? addedWidth : '0%' }"></span>
      </div>
      <strong v-if="step >= 1">{{ heldOut.after }}/{{ heldOut.total }} <small>{{ afterPercent }}%</small></strong>
    </div>
    <p v-if="step >= 1" class="recall-increase"><strong>+{{ heldOut.after - heldOut.before }}</strong> {{ labels[locale].added }}</p>
    <div v-if="step >= 2" class="recall-related">
      <div v-for="row in relatedSets" :key="row.id">
        <span>{{ row.label[locale] }}</span>
        <strong>{{ row.before }}/{{ row.total }} → {{ row.after }}/{{ row.total }}</strong>
      </div>
    </div>
  </figure>
</template>
