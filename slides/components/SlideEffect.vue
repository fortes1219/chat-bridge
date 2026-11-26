<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { effectComponents } from '../effects/registry.ts'
import { effectSteps, type SlideEffectStrategy } from '../effects/strategies.ts'
import type { Locale } from '../effects/data.ts'

const props = defineProps<{
  strategy: SlideEffectStrategy
  locale: Locale
  step: number
  still: boolean
}>()

const emit = defineEmits<{ stepChange: [step: number] }>()

const reduceMotion = ref(false)
let preference: MediaQueryList | undefined

function updatePreference() {
  reduceMotion.value = preference?.matches ?? false
}

onMounted(() => {
  preference = window.matchMedia('(prefers-reduced-motion: reduce)')
  updatePreference()
  preference.addEventListener('change', updatePreference)
})
onUnmounted(() => preference?.removeEventListener('change', updatePreference))

const renderer = computed(() => effectComponents[props.strategy.effect])
const staticView = computed(() => props.still || reduceMotion.value)
const finalStep = computed(() => effectSteps[props.strategy.effect])
</script>

<template>
  <component
    :is="renderer"
    v-if="renderer"
    :class="{ 'diagram-still': staticView }"
    :strategy="strategy"
    :locale="locale"
    :step="staticView ? finalStep : Math.min(step, finalStep)"
    :still="staticView"
    @step-change="emit('stepChange', $event)"
  />
</template>
