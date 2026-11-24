<script setup lang="ts">
import { computed, h } from 'vue';
import { useI18n } from 'vue-i18n';
import type { TableColumn } from '@nuxt/ui';
import type { Locale, MessageSchema } from '@/i18n';
import type { Holding, Strategy } from '@/service/api/strategy';
import { useStrategyFormat } from '../composables/useStrategyFormat';
import { CASH, MISSING } from '../constants';

const props = defineProps<{ strategy: Strategy; holdings: ReadonlyMap<string, Holding> }>();

const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();
const format = useStrategyFormat();

interface Row {
  symbol: string;
  name: string;
  /** The symbol, quantity and average cost, under the name. */
  detail: string;
  value: string;
  weight: string;
  target: string;
  profit: string;
  profitPercent: string;
  price: string;
  priceTime: string;
}

// The holdings in the profile's order, each with its actual weight above its target. Five columns,
// so the side panel shows them all at its default width: quantity and cost, which do not move, sit
// under the name. Cash has no price, cost or profit.
const rows = computed<Row[]>(() => {
  const valuation = props.strategy.valuation;
  const values = new Map(valuation.holdings.map(row => [row.symbol, row] as const));
  const quotes = new Map(valuation.quotes.map(quote => [quote.symbol, quote] as const));
  const targets = new Map(props.strategy.targets.map(row => [row.symbol, row.current] as const));
  return props.strategy.holdings.map(holding => {
    const value = values.get(holding.symbol);
    const isCash = holding.symbol === CASH;
    const target = targets.get(holding.symbol);
    const at = quotes.get(holding.symbol)?.at ?? null;
    return {
      symbol: holding.symbol,
      name: holding.names[locale.value],
      detail: isCash
        ? ''
        : t('strategy.holdingsTable.detail', {
            symbol: holding.symbol,
            quantity: format.price(holding.quantity),
            cost: format.price(holding.average_cost)
          }),
      value: format.money(value?.value ?? null),
      weight: format.percent(value?.weight ?? null),
      target: t('strategy.holdingsTable.targetOf', { target: target === undefined ? MISSING : `${target}%` }),
      profit: format.money(value?.profit ?? null),
      profitPercent: value?.profit_percent == null ? '' : format.percent(value.profit_percent, true),
      price: isCash ? MISSING : format.price(value?.price ?? null),
      // A missing price has no time to show.
      priceTime: at === null ? '' : format.priceTimeShort(at)
    };
  });
});

// Numbers align right. A header stays on one line: a narrow Chinese header would otherwise break
// after every character.
const END = { class: { td: 'text-end', th: 'text-end whitespace-nowrap' } };

/** A cell of two lines: the value, and a smaller line below it. */
function twoLines(main: string, below: string) {
  return h('div', [h('span', main), below ? h('span', { class: 'text-muted block text-xs' }, below) : null]);
}

const columns = computed<TableColumn<Row>[]>(() => [
  {
    accessorKey: 'name',
    header: t('strategy.holding'),
    // The one column that wraps, so the table fits the panel once the panel has its own scroll
    // bar, as it has in a window of ordinary height. A price's time is kept short instead
    // (24-hour clock, month and day), so a date such as 11-21 is never split.
    meta: { class: { td: 'whitespace-normal min-w-28' } },
    cell: ({ row }) => twoLines(row.original.name, row.original.detail)
  },
  { accessorKey: 'value', header: t('strategy.holdingsTable.value'), meta: END },
  {
    accessorKey: 'weight',
    header: t('strategy.holdingsTable.weight'),
    meta: END,
    cell: ({ row }) => twoLines(row.original.weight, row.original.target)
  },
  {
    accessorKey: 'profit',
    header: t('strategy.holdingsTable.profit'),
    meta: END,
    cell: ({ row }) => twoLines(row.original.profit, row.original.profitPercent)
  },
  {
    accessorKey: 'price',
    header: t('strategy.holdingsTable.price'),
    meta: END,
    cell: ({ row }) => twoLines(row.original.price, row.original.priceTime)
  }
]);

// Narrower cells than the table's default, so five columns fit the side panel.
const TABLE_UI = { th: 'px-2 py-2', td: 'px-2 py-2' };
</script>

<template>
  <section class="flex flex-col gap-2">
    <h3 class="font-semibold">{{ t('strategy.holdingsTable.title') }}</h3>
    <UTable data-test="holdings-table" :data="rows" :columns="columns" :ui="TABLE_UI" />
    <p class="text-muted text-xs">{{ t('strategy.holdingsTable.note') }}</p>
  </section>
</template>
