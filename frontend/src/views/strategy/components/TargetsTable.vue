<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { TableColumn } from '@nuxt/ui';
import type { Locale, MessageSchema } from '@/i18n';
import type { Holding, Strategy } from '@/service/api/strategy';

const props = defineProps<{ targets: Strategy['targets']; holdings: ReadonlyMap<string, Holding> }>();

const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();

interface Row {
  symbol: string;
  name: string;
  market: string;
  target: string;
}

const rows = computed<Row[]>(() =>
  props.targets.map(row => {
    const holding = props.holdings.get(row.symbol);
    return {
      symbol: row.symbol,
      name: holding?.names[locale.value] ?? row.symbol,
      market: t(`markets.${holding?.market ?? 'cash'}`),
      target: `${row.current}%`
    };
  })
);

const columns = computed<TableColumn<Row>[]>(() => [
  { accessorKey: 'name', header: t('strategy.holding') },
  { accessorKey: 'market', header: t('strategy.market') },
  { accessorKey: 'target', header: t('strategy.target'), meta: { class: { td: 'text-end', th: 'text-end' } } }
]);
</script>

<template>
  <UTable data-test="targets-table" :data="rows" :columns="columns" />
</template>
