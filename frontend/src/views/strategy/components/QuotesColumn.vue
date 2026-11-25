<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import type { Quote, Valuation } from '@/service/api/strategy';
import type { SocketConnectionState } from '@/stores/strategy-socket';
import { useStrategyFormat } from '../composables/useStrategyFormat';

const props = defineProps<{
  valuation: Valuation;
  connection: SocketConnectionState;
  /** Updates the page received that did not match the strategy's format and were not drawn. */
  invalidUpdates: number;
}>();

const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();
const format = useStrategyFormat();

/**
 * Whether prices are following, from the two connections they come through: the service's to the
 * price source, and the page's to the service. Each state's words and color.
 */
type Following = 'updating' | 'sourceDown' | 'connecting' | 'disconnected';
const FOLLOWING: Record<Following, { key: Following; color: 'success' | 'warning' | 'neutral' }> = {
  updating: { key: 'updating', color: 'success' },
  sourceDown: { key: 'sourceDown', color: 'warning' },
  connecting: { key: 'connecting', color: 'warning' },
  disconnected: { key: 'disconnected', color: 'neutral' }
};
const PAGE_CONNECTION: Record<SocketConnectionState, Following> = {
  connected: 'updating',
  connecting: 'connecting',
  disconnected: 'disconnected'
};

/**
 * The previous closes of Taiwan holdings also come from FinMind and the exchanges' open data. One
 * line names them and links the open data's license; the full attribution, in the form the
 * license's annex asks for, is in the README.
 */
const OPEN_DATA_LICENSE_URL = 'https://data.gov.tw/license';

/** The source's stated delay, in words. */
function delay(quote: Quote): string {
  if (quote.delay_minutes === null) return t('strategy.quotes.delayUnstated');
  if (quote.delay_minutes === 0) return t('strategy.quotes.realTime');
  return t('strategy.quotes.delayed', { minutes: quote.delay_minutes });
}

const rows = computed(() =>
  props.valuation.quotes.map(quote => ({
    symbol: quote.symbol,
    name: quote.names[locale.value],
    price: format.price(quote.price),
    // No change is shown without a previous close.
    change: quote.change_percent === null ? '' : format.percent(quote.change_percent, true),
    // A missing price has no time to show.
    when: quote.at === null ? '' : format.priceTime(quote.at),
    delay: delay(quote)
  }))
);
const following = computed(() => {
  const state = PAGE_CONNECTION[props.connection];
  return FOLLOWING[state === 'updating' && !props.valuation.live ? 'sourceDown' : state];
});
</script>

<template>
  <section class="flex flex-col gap-2" data-test="quotes">
    <div class="flex items-center justify-between gap-2">
      <h3 class="font-semibold">{{ t('strategy.quotes.title') }}</h3>
      <UBadge data-test="connection" :color="following.color" variant="subtle" class="text-xs">
        {{ t(`strategy.quotes.${following.key}`) }}
      </UBadge>
    </div>
    <UAlert
      v-if="invalidUpdates > 0"
      data-test="invalid-updates"
      color="warning"
      variant="subtle"
      icon="i-lucide-circle-alert"
      :description="t('strategy.quotes.invalid', { count: invalidUpdates })"
    />
    <ul class="divide-default divide-y">
      <li
        v-for="row in rows"
        :key="row.symbol"
        class="flex items-start justify-between gap-3 py-2"
        :data-test="`quote-${row.symbol}`"
      >
        <div class="min-w-0">
          <p class="truncate">{{ row.name }}</p>
          <p class="text-muted text-xs">{{ row.symbol }} · {{ row.delay }}</p>
        </div>
        <div class="text-end">
          <p data-test="quote-price">
            {{ row.price }} <span v-if="row.change" class="text-muted text-xs">{{ row.change }}</span>
          </p>
          <p v-if="row.when" class="text-muted text-xs" data-test="quote-time">{{ row.when }}</p>
        </div>
      </li>
    </ul>
    <p class="text-muted text-xs" data-test="price-source">
      {{ t('strategy.quotes.source', { name: valuation.source.name }) }}
      <ULink :to="valuation.source.terms_url" target="_blank" rel="noopener noreferrer" class="underline">
        {{ t('strategy.quotes.terms') }}
      </ULink>
    </p>
    <p class="text-muted text-xs" data-test="close-sources">
      {{ t('strategy.quotes.closeSources') }}
      <ULink :to="OPEN_DATA_LICENSE_URL" target="_blank" rel="noopener noreferrer" class="underline">
        {{ t('strategy.quotes.openDataLicense') }}
      </ULink>
    </p>
  </section>
</template>
