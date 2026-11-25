<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { TableColumn } from '@nuxt/ui';
import type { Locale, MessageSchema } from '@/i18n';
import type { Decision, Holding, Proposal, RuleCheck, RuleChecks } from '@/service/api/strategy';
import { PROGRAM_NAMES } from '../constants';
import { RULE_STATUS_COLORS, ruleStatus, useRuleText } from '../composables/useRuleText';

/** `before` is the rules checked on the current targets; the proposal carries them on its own. */
const props = defineProps<{
  proposal: Proposal;
  before: RuleChecks;
  holdings: ReadonlyMap<string, Holding>;
  deciding: boolean;
}>();
const emit = defineEmits<{ decide: [decision: Decision] }>();

const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();
const ruleText = useRuleText();

interface RuleRow {
  rule: string;
  before: RuleCheck;
  after: RuleCheck;
}
/** The two result columns, current then proposed. */
const RULE_SIDES = ['before', 'after'] as const;

// Both lists check the same rules in the same order; the results are the service's.
const ruleRows = computed<RuleRow[]>(() =>
  props.proposal.rule_checks.rules.flatMap((after, index) => {
    const before = props.before.rules[index];
    return before ? [{ rule: ruleText.describe(after), before, after }] : [];
  })
);

interface Row {
  symbol: string;
  name: string;
  current: string;
  proposed: string;
  change: number;
}

// The numbers are the service's; the page only formats them.
const rows = computed<Row[]>(() =>
  props.proposal.rows.map(row => ({
    symbol: row.symbol,
    name: props.holdings.get(row.symbol)?.names[locale.value] ?? row.symbol,
    current: `${row.current}%`,
    proposed: `${row.proposed}%`,
    change: row.change
  }))
);

const signed = computed(() => new Intl.NumberFormat(locale.value, { signDisplay: 'exceptZero' }));

/** The color of a change, by its sign. */
const CHANGE_COLORS: Record<'up' | 'down' | 'none', string> = {
  up: 'text-success',
  down: 'text-error',
  none: 'text-muted'
};
function changeColor(change: number): string {
  if (change > 0) return CHANGE_COLORS.up;
  if (change < 0) return CHANGE_COLORS.down;
  return CHANGE_COLORS.none;
}

const END = { class: { td: 'text-end', th: 'text-end' } };
const columns = computed<TableColumn<Row>[]>(() => [
  { accessorKey: 'name', header: t('strategy.holding') },
  { accessorKey: 'current', header: t('strategy.current'), meta: END },
  { accessorKey: 'proposed', header: t('strategy.proposed'), meta: END },
  { accessorKey: 'change', header: t('strategy.change'), meta: END }
]);
const ruleColumns = computed<TableColumn<RuleRow>[]>(() => [
  { accessorKey: 'rule', header: t('rules.title') },
  { id: 'before', header: t('rules.before'), meta: END },
  { id: 'after', header: t('rules.after'), meta: END }
]);

const sourceOf = computed(() => new Map(props.proposal.sources.map(source => [source.number, source] as const)));

/** The decision buttons, as data: accept first, the way a person reads them. */
const DECISIONS: { decision: Decision; color: 'primary' | 'neutral'; variant: 'solid' | 'outline' }[] = [
  { decision: 'accept', color: 'primary', variant: 'solid' },
  { decision: 'reject', color: 'neutral', variant: 'outline' }
];
</script>

<template>
  <section class="flex flex-col gap-3" data-test="proposal-diff">
    <div>
      <h3 class="font-semibold">{{ t('strategy.proposalTitle') }}</h3>
      <p class="text-muted text-sm" data-test="proposed-by">
        {{ t('strategy.proposedBy', { program: PROGRAM_NAMES[proposal.program], question: proposal.question }) }}
      </p>
    </div>
    <UTable :data="rows" :columns="columns" data-test="diff-table">
      <template #change-cell="{ row }">
        <span :class="changeColor(row.original.change)" :data-test="`change-${row.original.symbol}`">
          {{ signed.format(row.original.change) }}
        </span>
      </template>
    </UTable>
    <div v-if="ruleRows.length" class="flex flex-col gap-1" data-test="rule-diff">
      <p class="text-sm font-medium">{{ t('rules.proposalTitle') }}</p>
      <p class="text-muted text-xs" data-test="rule-diff-summary">
        {{ t('rules.before') }} {{ t('rules.summary', { met: before.met, enabled: before.enabled }) }}・{{
          t('rules.after')
        }}
        {{ t('rules.summary', { met: proposal.rule_checks.met, enabled: proposal.rule_checks.enabled }) }}
      </p>
      <UTable :data="ruleRows" :columns="ruleColumns" data-test="rule-diff-table">
        <template v-for="side in RULE_SIDES" :key="side" #[`${side}-cell`]="{ row }">
          <UBadge
            :color="RULE_STATUS_COLORS[ruleStatus(row.original[side])]"
            variant="subtle"
            :data-test="`rule-${side}-${row.index}`"
          >
            {{ ruleText.status(row.original[side]) }}
          </UBadge>
        </template>
      </UTable>
    </div>
    <div class="text-sm">
      <p class="font-medium">{{ t('strategy.reasons') }}</p>
      <ul class="list-disc ps-5" data-test="reasons">
        <li v-for="(reason, index) in proposal.reasons" :key="index">
          {{ reason.text }}
          <span class="text-muted">{{ reason.sources.map(number => `[${number}]`).join('') }}</span>
        </li>
      </ul>
    </div>
    <div class="text-sm">
      <p class="font-medium">{{ t('strategy.sources') }}</p>
      <ul class="text-muted" data-test="proposal-sources">
        <li v-for="number in sourceOf.keys()" :key="number">
          [{{ number }}] {{ sourceOf.get(number)?.title }}
          <template v-if="sourceOf.get(number)?.event_date">({{ sourceOf.get(number)?.event_date }})</template>
        </li>
      </ul>
    </div>
    <p class="text-muted text-xs" data-test="no-trade">{{ t('strategy.noTrade') }}</p>
    <div class="flex gap-2">
      <UButton
        v-for="button in DECISIONS"
        :key="button.decision"
        :data-test="button.decision"
        :color="button.color"
        :variant="button.variant"
        :label="t(`strategy.${button.decision}`)"
        :loading="deciding"
        :disabled="deciding"
        @click="emit('decide', button.decision)"
      />
    </div>
  </section>
</template>
