<script setup lang="ts">
import { shallowRef } from 'vue'
import { TresCanvas, type TresContextWithClock } from '@tresjs/core'
import { MathUtils, type Group, type PerspectiveCamera } from 'three'

const props = defineProps<{ expanded: boolean; focused: boolean; recovered: number; expected: number }>()
const camera = shallowRef<PerspectiveCamera>()
const rateHits = shallowRef<Group>()

// The flanking boards give context to the rate-policy experiment. Their slots are illustrative.
const lanes = [
  { x: -3.05, accent: '#78b2ff', base: '#142c4d' },
  { x: 0, accent: '#78f2cd', base: '#174444' },
  { x: 3.05, accent: '#b4b8fb', base: '#2e3057' },
]
const hitInterval = 0.105
const hitDuration = 0.42
let revealTime = 0
let yaw = props.focused ? -0.34 : 0.21
let distance = props.focused ? 9 : 11.5
let elevation = props.focused ? 4.8 : 6.6

function slotPosition(index: number): [number, number, number] {
  const i = index - 1
  return [(i % 3 - 1) * 0.61, 0.02, (Math.floor(i / 3) - 1) * 0.61]
}

function captureRateHits(node: unknown) {
  rateHits.value = (node as Group | null) ?? undefined
}

function animate({ delta, elapsed }: TresContextWithClock) {
  const step = Math.min(delta, 0.05)
  yaw = MathUtils.damp(yaw, (props.focused ? -0.34 : 0.21) + Math.sin(elapsed * 0.8) * 0.14, 3.1, step)
  distance = MathUtils.damp(distance, props.focused ? 9 : 11.5, 3.1, step)
  elevation = MathUtils.damp(elevation, props.focused ? 4.8 : 6.6, 3.1, step)
  if (camera.value) {
    camera.value.position.set(Math.sin(yaw) * distance, elevation, Math.cos(yaw) * distance)
    camera.value.lookAt(0, 0.07, -0.1)
  }

  const end = Math.max(0, props.recovered - 1) * hitInterval + hitDuration
  revealTime = MathUtils.clamp(revealTime + (props.expanded ? step : -2 * step), 0, end)
  rateHits.value?.children.forEach((node, index) => {
    const progress = MathUtils.smoothstep(revealTime - index * hitInterval, 0, hitDuration)
    node.visible = progress > 0
    node.scale.y = progress
  })
}
</script>

<template>
  <TresCanvas render-mode="always" :dpr="1.5" clear-color="#0a1726" @before-loop="animate">
    <TresPerspectiveCamera ref="camera" :position="[2.4, 6.6, 11.25]" :fov="36" />
    <TresAmbientLight :intensity="1.4" />
    <TresDirectionalLight :position="[2, 7, 5]" color="#e8f6ff" :intensity="2.3" />
    <TresDirectionalLight :position="[-5, 3, -3]" color="#538dff" :intensity="1.8" />
    <TresGridHelper :args="[22, 22, '#254258', '#172b3d']" :position="[0, -0.42, 0]" />

    <TresGroup v-for="lane in lanes" :key="lane.x" :position="[lane.x, 0, 0]">
      <TresMesh :position="[0, -0.31, 0]">
        <TresBoxGeometry :args="[2.53, 0.19, 2.63]" />
        <TresMeshStandardMaterial :color="lane.base" :roughness="0.72" />
      </TresMesh>
      <TresMesh :position="[0, -0.2, 0]">
        <TresBoxGeometry :args="[2.39, 0.04, 2.48]" />
        <TresMeshBasicMaterial :color="lane.accent" />
      </TresMesh>
      <TresMesh :position="[0, -0.11, 0]">
        <TresBoxGeometry :args="[2.31, 0.15, 2.4]" />
        <TresMeshStandardMaterial :color="lane.base" :roughness="0.72" />
      </TresMesh>

      <TresGroup v-if="lane.x !== 0">
        <TresMesh v-for="index in 6" :key="index" :position="slotPosition(index)">
          <TresBoxGeometry :args="[0.46, 0.18 + (index % 4) * 0.15, 0.46]" />
          <TresMeshStandardMaterial :color="lane.accent" :roughness="0.5" />
        </TresMesh>
      </TresGroup>
      <TresGroup v-else>
        <TresMesh v-for="index in expected" :key="index" :position="slotPosition(index)">
          <TresBoxGeometry :args="[0.46, 0.10, 0.46]" />
          <TresMeshStandardMaterial color="#355266" :roughness="0.7" />
        </TresMesh>
        <TresGroup :ref="captureRateHits">
          <TresGroup
            v-for="index in recovered"
            :key="index"
            :position="slotPosition(index)"
            :visible="false"
          >
            <TresMesh :position="[0, 0.47, 0]">
              <TresBoxGeometry :args="[0.44, 0.94, 0.44]" />
              <TresMeshStandardMaterial color="#28c8a4" :roughness="0.42" :metalness="0.18" />
            </TresMesh>
            <TresMesh :position="[0, 0.95, 0]">
              <TresBoxGeometry :args="[0.46, 0.04, 0.46]" />
              <TresMeshBasicMaterial color="#a9ffe4" />
            </TresMesh>
          </TresGroup>
        </TresGroup>
      </TresGroup>
    </TresGroup>
  </TresCanvas>
</template>
