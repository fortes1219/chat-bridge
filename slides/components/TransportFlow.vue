<script setup lang="ts">
import type { Locale } from '../effects/data.ts'

defineProps<{ locale: Locale; step: number; still: boolean }>()
const emit = defineEmits<{ stepChange: [step: number] }>()

const lanes = [
  {
    protocol: 'HTTP SSE',
    action: { 'zh-TW': '送出問題', en: 'Ask a question' },
    stages: {
      'zh-TW': ['問題請求', '上下文與來源', '回答片段', '選用的配置提案'],
      en: ['Question request', 'Context and sources', 'Answer text', 'Optional proposal'],
    },
  },
  {
    protocol: 'Socket.IO',
    action: { 'zh-TW': '收到報價', en: 'Receive a quote' },
    stages: {
      'zh-TW': ['行情來源', '後端計算', '推送新狀態', '面板更新市值與損益'],
      en: ['Quote source', 'Backend calculations', 'State push', 'Panel value and P&L update'],
    },
  },
] as const
</script>

<template>
  <figure class="diagram transport-diagram" :data-step="step">
    <section
      v-for="(lane, index) in lanes"
      :key="lane.protocol"
      class="transport-lane"
      :class="{ 'transport-active': !still && step === index + 1 }"
    >
      <div class="transport-heading">
        <strong>{{ lane.protocol }}</strong>
        <button
          v-if="!still"
          type="button"
          :aria-pressed="step === index + 1"
          @click="emit('stepChange', step === index + 1 ? 0 : index + 1)"
        >{{ lane.action[locale] }}</button>
      </div>
      <div class="transport-track">
        <span
          v-for="(stage, stageIndex) in lane.stages[locale]"
          :key="stage"
          :style="{ '--stage-index': stageIndex }"
        >{{ stage }}</span>
      </div>
    </section>
  </figure>
</template>
