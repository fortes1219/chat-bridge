<script setup lang="ts">
import { computed, defineAsyncComponent, onErrorCaptured, onMounted, ref, watch } from 'vue'
import { retrievalExamples, type Locale } from '../effects/data.ts'
import type { SlideEffectStrategy } from '../effects/strategies.ts'

const props = defineProps<{
  strategy: Extract<SlideEffectStrategy, { effect: 'retrieval-3d' }>
  locale: Locale
  step: number
  still: boolean
}>()

const emit = defineEmits<{ stepChange: [step: number] }>()
const Scene = defineAsyncComponent(() => import('./RetrievalScene.vue'))
const canRender = ref(false)
const mounted = ref(false)

onMounted(() => { mounted.value = true })
watch([mounted, () => props.still], ([isMounted, still]) => {
  canRender.value = false
  if (!isMounted || still)
    return

  try {
    const context = document.createElement('canvas').getContext('webgl2')
    canRender.value = Boolean(context)
    context?.getExtension('WEBGL_lose_context')?.loseContext()
  }
  catch {
    canRender.value = false
  }
})
onErrorCaptured(() => {
  canRender.value = false
  return false
})
const example = computed(() => retrievalExamples[props.strategy.example])
const interactive = computed(() => canRender.value && !props.still)
const baseline = computed(() => props.strategy.view === 'baseline')
const expanded = computed(() => !baseline.value && props.step >= 1)
const focused = computed(() => !baseline.value || props.step >= 1)
const labels = {
  'zh-TW': {
    original: '整題查詢', split: '拆題後', rate: '利率政策來源',
    caption: '檢索流程示意', top: '整題取回的段落',
  },
  en: {
    original: 'Original query', split: 'Split queries', rate: 'Rate-policy sources',
    caption: 'Retrieval schematic', top: 'Passages in the original result',
  },
}
</script>

<template>
  <figure class="retrieval-figure" :data-render="interactive ? '3d' : 'static'" :data-step="step" :data-view="strategy.view">
    <div class="retrieval-scene" aria-hidden="true">
      <Scene
        v-if="interactive"
        :expanded="expanded"
        :focused="focused"
        :recovered="example.recovered"
        :expected="example.expected"
      />
      <div v-else class="retrieval-static">
        <span
          v-for="number in example.expected"
          :key="number"
          :class="{ 'dot-hit': expanded && number <= example.recovered }"
        ></span>
      </div>
      <div class="retrieval-topics">
        <span v-for="topic in example.topics[locale]" :key="topic">{{ topic }}</span>
      </div>
    </div>
    <figcaption>
      <div v-if="baseline" class="retrieval-baseline">
        <span>{{ labels[locale].top }}</span>
        <div class="retrieval-passage-slots" :class="{ 'slots-filled': focused }" :aria-label="String(example.originalTopK)">
          <span v-for="number in example.originalTopK" :key="number" :style="{ '--slot-index': number }" aria-hidden="true"></span>
        </div>
      </div>
      <div v-else-if="interactive" class="retrieval-switch">
        <button type="button" :aria-pressed="!expanded" @click="emit('stepChange', 0)">{{ labels[locale].original }}</button>
        <button type="button" :aria-pressed="expanded" @click="emit('stepChange', 1)">{{ labels[locale].split }}</button>
      </div>
      <p class="retrieval-count" aria-live="polite">
        {{ labels[locale].rate }}
        <strong v-if="baseline || interactive">{{ expanded ? example.recovered : example.original }}/{{ example.expected }}</strong>
        <strong v-else>{{ example.original }}/{{ example.expected }} → {{ example.recovered }}/{{ example.expected }}</strong>
      </p>
      <p class="figure-note">{{ labels[locale].caption }}</p>
    </figcaption>
  </figure>
</template>
