<script setup lang="ts">
import { clickCountFor, effectFor } from '../effects/strategies.ts'
</script>

<template>
  <section
    class="slidev-layout research"
    :class="{
      'research-ink': $frontmatter.appearance === 'ink',
      'research-cover': $frontmatter.composition === 'cover',
      'research-scene': $frontmatter.composition === 'scene',
      'research-diagram': $frontmatter.composition === 'diagram',
    }"
    :lang="$frontmatter.locale"
  >
    <header class="research-header">
      <span>chat-bridge</span>
      <a
        class="language-link"
        :href="$frontmatter.locale === 'en' ? '/' : '/en/'"
        :lang="$frontmatter.locale === 'en' ? 'zh-TW' : 'en'"
      >{{ $frontmatter.locale === 'en' ? '繁體中文' : 'English' }}</a>
    </header>
    <div
      class="research-main"
      :class="{ 'research-with-effect': effectFor($frontmatter.slideId)?.effect !== 'none' }"
    >
      <div class="research-copy">
        <slot />
        <a v-if="$frontmatter.composition === 'cover' && $renderContext === 'slide'" class="cover-start" href="#/2">
          {{ $frontmatter.locale === 'en' ? 'Start presentation' : '開始簡報' }}
          <span aria-hidden="true">→</span>
        </a>
      </div>
      <aside v-if="effectFor($frontmatter.slideId)?.effect !== 'none'" class="research-aside">
        <span
          v-if="clickCountFor($frontmatter.slideId)"
          v-click="clickCountFor($frontmatter.slideId)"
          aria-hidden="true"
          hidden
        />
        <SlideEffect
          v-if="effectFor($frontmatter.slideId)"
          :strategy="effectFor($frontmatter.slideId)!"
          :locale="$frontmatter.locale"
          :step="$clicks"
          :still="$page !== $nav.currentPage || ($renderContext !== 'slide' && $renderContext !== 'presenter')"
          @step-change="$nav.go($page, $event)"
        />
      </aside>
    </div>
  </section>
</template>
