<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import type { AppError } from '@/service/error';
import { useStrategy } from './composables/useStrategy';
import { useStrategySocket } from './composables/useStrategySocket';
import { useStrategyEditors } from './composables/useStrategyEditors';
import SummaryCards from './components/SummaryCards.vue';
import AllocationDonut from './components/AllocationDonut.vue';
import HoldingsTable from './components/HoldingsTable.vue';
import HoldingsEditor from './components/HoldingsEditor.vue';
import QuotesColumn from './components/QuotesColumn.vue';
import ProposalDiff from './components/ProposalDiff.vue';
import RuleChecks from './components/RuleChecks.vue';
import RuleEditor from './components/RuleEditor.vue';

/** `headless` leaves the title to a slide-over that already shows it. */
defineProps<{ headless?: boolean }>();

const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();
const { strategy, holdings, loading, error, deciding, decisionError, decide } = useStrategy();
// While the panel is shown, each new price brings the strategy the service recomputed from it.
const { connectionState, invalidUpdates } = useStrategySocket();
// Kept by the page, so a draft outlives this panel when the window crosses the narrow width.
const { holdings: holdingsEditor, rules: ruleEditor } = useStrategyEditors();

/** The page's own words for an error: the service's reason when it gave one, else the page's code. */
function errorKey(appError: AppError): keyof MessageSchema['errors'] {
  return appError.reason ?? appError.code;
}
const shownError = computed(() => decisionError.value ?? error.value);
</script>

<template>
  <div class="flex flex-col gap-4 p-4" data-test="strategy">
    <h2 v-if="!headless" class="text-lg font-semibold">{{ t('strategy.title') }}</h2>
    <p v-if="loading" class="text-muted text-sm" data-test="strategy-loading">{{ t('strategy.loading') }}</p>
    <UAlert
      v-if="shownError"
      data-test="strategy-error"
      color="error"
      variant="subtle"
      icon="i-lucide-circle-alert"
      :title="t(`errors.${errorKey(shownError)}.title`)"
      :description="t(`errors.${errorKey(shownError)}.description`)"
    />
    <template v-if="strategy">
      <UAlert
        data-test="sample-notice"
        color="neutral"
        variant="subtle"
        icon="i-lucide-info"
        :description="strategy.notice[locale]"
      />
      <SummaryCards :valuation="strategy.valuation" :holdings="holdings" />
      <ProposalDiff
        v-if="strategy.proposal"
        :proposal="strategy.proposal"
        :before="strategy.rule_checks"
        :holdings="holdings"
        :deciding="deciding"
        @decide="decide"
      />
      <AllocationDonut :valuation="strategy.valuation" :holdings="holdings" />
      <HoldingsEditor
        v-if="holdingsEditor.editing.value"
        :draft="holdingsEditor.draft.value"
        :changed="holdingsEditor.changed.value"
        :saving="holdingsEditor.saving.value"
        :error="holdingsEditor.saveError.value"
        @symbol="holdingsEditor.setSymbol"
        @name="holdingsEditor.setName"
        @quantity="holdingsEditor.setQuantity"
        @cost="holdingsEditor.setCost"
        @cash="holdingsEditor.setCash"
        @remove="holdingsEditor.remove"
        @add="holdingsEditor.add"
        @save="holdingsEditor.save"
        @cancel="holdingsEditor.cancel"
      />
      <HoldingsTable v-else :strategy="strategy" :holdings="holdings" @edit="holdingsEditor.start" />
      <RuleEditor
        v-if="ruleEditor.editing.value"
        :rules="ruleEditor.draft.value"
        :changed="ruleEditor.changed.value"
        :saving="ruleEditor.saving.value"
        :error="ruleEditor.saveError.value"
        @kind="ruleEditor.setKind"
        @limit="ruleEditor.setLimit"
        @market="ruleEditor.setMarket"
        @enabled="ruleEditor.setEnabled"
        @remove="ruleEditor.remove"
        @add="ruleEditor.add"
        @save="ruleEditor.save"
        @cancel="ruleEditor.cancel"
      />
      <RuleChecks v-else :checks="strategy.rule_checks" :holdings="holdings" @edit="ruleEditor.start" />
      <QuotesColumn :valuation="strategy.valuation" :connection="connectionState" :invalid-updates="invalidUpdates" />
    </template>
  </div>
</template>
