<script setup lang="ts">
import { computed } from 'vue'
import { allocationExamples, type Locale } from '../effects/data.ts'
import type { SlideEffectStrategy } from '../effects/strategies.ts'

const props = defineProps<{
  strategy: Extract<SlideEffectStrategy, { effect: 'allocation-compare' }>
  locale: Locale
  still: boolean
}>()

const rows = computed(() => allocationExamples[props.strategy.example])
const labels = {
  'zh-TW': { symbol: '標的', current: '目前', proposed: '提案', change: '差異', note: '配置差異示意', cash: '現金', unit: '百分點' },
  en: { symbol: 'Asset', current: 'Current', proposed: 'Proposal', change: 'Change', note: 'Illustrative allocation', cash: 'Cash', unit: ' pp' },
}

function change(current: number, proposed: number) {
  const delta = proposed - current
  if (delta === 0)
    return '—'
  return delta > 0 ? `+${delta}` : `−${Math.abs(delta)}`
}
</script>

<template>
  <figure class="allocation-figure" :class="{ 'allocation-still': still }">
    <table>
      <thead>
        <tr>
          <th scope="col">{{ labels[locale].symbol }}</th>
          <th scope="col">{{ labels[locale].current }}</th>
          <th scope="col">{{ labels[locale].proposed }}</th>
          <th scope="col">{{ labels[locale].change }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.symbol">
          <th scope="row">{{ row.symbol === 'CASH' ? labels[locale].cash : row.symbol }}</th>
          <td>{{ row.current }}%</td>
          <td>{{ row.proposed }}%</td>
          <td :class="{ 'allocation-change': row.current !== row.proposed }">
            {{ change(row.current, row.proposed) }}{{ row.current === row.proposed ? '' : labels[locale].unit }}
          </td>
        </tr>
      </tbody>
    </table>
    <figcaption class="figure-note">{{ labels[locale].note }}</figcaption>
  </figure>
</template>
