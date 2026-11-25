<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import type { Holding, Valuation } from '@/service/api/strategy';
import { useStrategyFormat } from '../composables/useStrategyFormat';

const props = defineProps<{ valuation: Valuation; holdings: ReadonlyMap<string, Holding> }>();

const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();
const format = useStrategyFormat();

interface Card {
  key: string;
  icon: string;
  title: string;
  value: string;
  /** The same change in percent, beside the amount. */
  badge: string | null;
}

const cards = computed<Card[]>(() => {
  const valuation = props.valuation;
  return [
    {
      key: 'total',
      icon: 'i-lucide-wallet',
      title: t('strategy.cards.total'),
      value: format.money(valuation.total_value),
      badge: null
    },
    {
      key: 'change',
      icon: 'i-lucide-activity',
      title: t('strategy.cards.change'),
      value: format.money(valuation.change),
      badge: valuation.change_percent === null ? null : format.percent(valuation.change_percent, true)
    },
    {
      key: 'profit',
      icon: 'i-lucide-trending-up',
      title: t('strategy.cards.profit'),
      value: format.money(valuation.profit),
      badge: valuation.profit_percent === null ? null : format.percent(valuation.profit_percent, true)
    },
    {
      key: 'prices-at',
      icon: 'i-lucide-clock',
      title: t('strategy.cards.pricesAt'),
      value: format.priceTime(valuation.prices_at),
      badge: null
    }
  ];
});

// The holdings with no price or exchange rate, by name, so the person knows what the totals leave out.
// Holdings by name, so the person knows what a total leaves out.
function names(symbols: string[]): string {
  return symbols.map(symbol => props.holdings.get(symbol)?.names[locale.value] ?? symbol).join(', ');
}
const leftOut = computed(() => names(props.valuation.left_out));
const changeLeftOut = computed(() => names(props.valuation.change_left_out));
</script>

<template>
  <section class="flex flex-col gap-2" data-test="summary-cards">
    <!-- Two by two in the side panel, whatever the window's width. -->
    <UPageGrid class="grid-cols-2 gap-2 sm:grid-cols-2 lg:grid-cols-2">
      <UPageCard
        v-for="card in cards"
        :key="card.key"
        :data-test="`card-${card.key}`"
        :icon="card.icon"
        :title="card.title"
        variant="subtle"
        :ui="{
          container: 'gap-y-1 p-3 sm:p-3',
          wrapper: 'items-start',
          leading: 'p-2 rounded-full bg-primary/10 ring ring-inset ring-primary/25',
          title: 'font-normal text-muted text-xs'
        }"
      >
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-highlighted text-lg font-semibold" data-test="card-value">{{ card.value }}</span>
          <UBadge v-if="card.badge" color="neutral" variant="subtle" class="text-xs">{{ card.badge }}</UBadge>
        </div>
      </UPageCard>
    </UPageGrid>
    <UAlert
      v-if="valuation.left_out.length"
      data-test="left-out"
      color="warning"
      variant="subtle"
      icon="i-lucide-circle-alert"
      :description="t('strategy.cards.leftOut', { names: leftOut })"
    />
    <UAlert
      v-if="valuation.change_left_out.length"
      data-test="change-left-out"
      color="warning"
      variant="subtle"
      icon="i-lucide-circle-alert"
      :description="t('strategy.cards.changeLeftOut', { names: changeLeftOut })"
    />
    <p class="text-muted text-xs" data-test="change-note">{{ t('strategy.cards.changeNote') }}</p>
  </section>
</template>
