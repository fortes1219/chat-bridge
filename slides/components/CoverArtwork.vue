<script setup lang="ts">
import portfolioArtwork from '../assets/portfolio-observatory.png'

defineProps<{ still: boolean }>()
</script>

<template>
  <figure class="cover-art" :class="{ 'cover-still': still }" aria-hidden="true">
    <img :src="portfolioArtwork" alt="" draggable="false">
    <span v-if="!still" class="cover-reflection"></span>
  </figure>
</template>
