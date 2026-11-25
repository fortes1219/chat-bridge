<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import type { Holding, Valuation } from '@/service/api/strategy';

const props = defineProps<{ valuation: Valuation; holdings: ReadonlyMap<string, Holding> }>();

const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();

interface Slice {
  name: string;
  share: number;
}

// Each valued holding's and cash's share of the total, as the service computed it; a holding left
// out for a missing price has no slice.
const slices = computed<Slice[]>(() =>
  props.valuation.holdings.flatMap(row =>
    row.weight === null
      ? []
      : [{ name: props.holdings.get(row.symbol)?.names[locale.value] ?? row.symbol, share: Number(row.weight) }]
  )
);

// One series: each slice's share. The total is on the cards: Nuxt UI's center slot re-renders the
// chart after every render of it, which never settles.
const categories = computed(() => [{ key: 'share' as const, label: t('strategy.donut.share') }]);

/** A slice's share as the tooltip shows it. */
function shareLabel(value: number): string {
  return `${value}%`;
}
</script>

<template>
  <section class="flex flex-col gap-2" data-test="allocation">
    <h3 class="font-semibold">{{ t('strategy.donut.title') }}</h3>
    <UChart
      type="donut"
      :data="slices"
      index="name"
      :categories="categories"
      :format="shareLabel"
      :height="220"
      :aria-label="t('strategy.donut.title')"
    />
  </section>
</template>
