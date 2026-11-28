<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import type { PriceLookups } from '@/service/api/chat';

const props = defineProps<{ prices: PriceLookups }>();

const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();

type Lookup = PriceLookups['lookups'][number];
type Row = PriceLookups['events'][number]['rows'][number];

/** A close as the service rounded it, with two decimals. */
function close(value: number | null): string {
  return value === null ? t('prices.noValue') : value.toFixed(2);
}

/** A change in percent, signed as the program reads it. */
function change(value: number | null): string {
  if (value === null) return t('prices.noValue');
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

/** The sources a lookup may fail at, by the service's code; Yahoo's name comes with the prices. */
const SOURCE_NAMES = computed<Record<NonNullable<Lookup['not_read']>['source'], string>>(() => ({
  yahoo: props.prices.source.name,
  finmind: 'FinMind'
}));
const REASON_KEYS = { no_data: 'prices.reasons.noData', unreadable: 'prices.reasons.unreadable' } as const;

const symbols = computed(() => new Set(props.prices.lookups.map(lookup => lookup.symbol)).size);
const sources = computed(() => {
  const name = props.prices.source.name;
  const filled = props.prices.lookups.some(lookup => lookup.sources.includes('finmind'));
  return filled ? t('prices.withFinmind', { name }) : name;
});
/** The latest read among the lookups: the prices are no newer than it. */
const readAt = computed(() => {
  const times = props.prices.lookups.flatMap(lookup => (lookup.read_at ? [Date.parse(lookup.read_at)] : []));
  if (!times.length) return t('prices.noValue');
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'short', timeStyle: 'short' }).format(Math.max(...times));
});

/** A lookup's line: its trend, or why it has none. */
function lookupLine(lookup: Lookup): string {
  const period = { symbol: lookup.symbol, start: lookup.start_date, end: lookup.end_date };
  const missing = lookup.not_read;
  if (missing !== null) {
    const reason = t(REASON_KEYS[missing.reason], { source: SOURCE_NAMES.value[missing.source] });
    return t('prices.notRead', { symbol: lookup.symbol, reason });
  }
  const found = lookup.trend;
  if (found === null) return t('prices.noTradingDay', period);
  // A fall is zero or below, so it has no sign of its own to show.
  const fallen = `${found.largest_fall.toFixed(2)}%`;
  const fall =
    found.fall_from === null
      ? fallen
      : t('prices.fallDays', { fall: fallen, from: found.fall_from, to: found.fall_to });
  return t('prices.trend', {
    ...period,
    firstDay: found.first_day,
    first: close(found.first_close),
    lastDay: found.last_day,
    last: close(found.last_close),
    change: change(found.change),
    highDay: found.high_day,
    high: close(found.high),
    lowDay: found.low_day,
    low: close(found.low),
    fall
  });
}

const days = computed(() =>
  props.prices.lookups.flatMap(lookup => lookup.days.map(day => ({ symbol: lookup.symbol, ...day })))
);

/** What a row's notes say, in the page's language. */
function notes(row: Row): string {
  if (row.d0 === null) return t('prices.notes.noDay');
  return [
    ...(row.notes.during ? [t('prices.notes.during')] : []),
    ...row.notes.missing.map(day => t('prices.notes.missing', { day })),
    ...row.notes.filled.map(day => t('prices.notes.filled', { day })),
    ...row.notes.dividends.map(day => t('prices.notes.dividend', { day }))
  ].join('; ');
}

const events = computed(() =>
  props.prices.events.map(event => ({
    ...event,
    title: t('prices.eventTitle', {
      file: event.file,
      date: event.event_date,
      numbers: event.source_numbers.map(number => `[${number}]`).join(' ')
    })
  }))
);
</script>

<template>
  <!-- Folded under the answer, as its sources are. Every value is drawn as plain text. -->
  <UCollapsible data-test="prices" class="text-sm">
    <UButton
      data-test="prices-toggle"
      variant="link"
      color="neutral"
      size="sm"
      class="px-0"
      trailing-icon="i-lucide-chevron-down"
      :label="t('prices.lookedUp', { count: symbols, sources, time: readAt }, symbols)"
    />
    <template #content>
      <div class="mt-1 flex flex-col gap-2" data-test="prices-content">
        <ul class="space-y-1">
          <li v-for="lookup in prices.lookups" :key="`${lookup.symbol}-${lookup.start_date}-${lookup.end_date}`">
            {{ lookupLine(lookup) }}
          </li>
        </ul>
        <table v-if="days.length" class="w-full text-start" data-test="prices-days">
          <thead>
            <tr>
              <th>{{ t('prices.columns.symbol') }}</th>
              <th>{{ t('prices.columns.day') }}</th>
              <th>{{ t('prices.columns.close') }}</th>
              <th>{{ t('prices.columns.change') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="day in days" :key="`${day.symbol}-${day.day}`">
              <td>{{ day.symbol }}</td>
              <td>{{ day.day }}</td>
              <td>{{ close(day.close) }}</td>
              <td>{{ change(day.change) }}</td>
            </tr>
          </tbody>
        </table>
        <section v-for="event in events" :key="event.file" :data-test="`prices-event-${event.file}`">
          <p class="font-medium">{{ event.title }}</p>
          <p v-if="event.same_as" class="text-muted">{{ t('prices.sameAs', { file: event.same_as }) }}</p>
          <table v-else class="w-full text-start">
            <thead>
              <tr>
                <th>{{ t('prices.columns.symbol') }}</th>
                <th>{{ t('prices.columns.d0') }}</th>
                <th>{{ t('prices.columns.d0Close') }}</th>
                <th>{{ t('prices.columns.change') }}</th>
                <th>{{ t('prices.columns.next') }}</th>
                <th>{{ t('prices.columns.fifth') }}</th>
                <th>{{ t('prices.columns.notes') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in event.rows" :key="row.symbol">
                <td>{{ row.symbol }}</td>
                <td>{{ row.d0 ?? t('prices.noValue') }}</td>
                <td>{{ close(row.close) }}</td>
                <td>{{ change(row.day_change) }}</td>
                <td>{{ change(row.next_change) }}</td>
                <td>{{ change(row.fifth_change) }}</td>
                <td>{{ notes(row) }}</td>
              </tr>
            </tbody>
          </table>
        </section>
        <p v-if="prices.days_left_out" class="text-muted" data-test="prices-days-left-out">
          {{ t('prices.daysLeftOut', { count: prices.days_left_out }, prices.days_left_out) }}
        </p>
        <p v-if="prices.events_left_out" class="text-muted" data-test="prices-left-out">
          {{ t('prices.leftOut', { count: prices.events_left_out }, prices.events_left_out) }}
        </p>
        <p class="text-muted text-xs">
          <ULink :to="prices.source.terms_url" target="_blank" rel="noopener noreferrer" class="underline">
            {{ t('prices.terms') }}
          </ULink>
        </p>
      </div>
    </template>
  </UCollapsible>
</template>
