<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import type { AppError } from '@/service/error';
import { useStrategy } from './composables/useStrategy';
import TargetsTable from './components/TargetsTable.vue';
import ProposalDiff from './components/ProposalDiff.vue';

/** `headless` leaves the title to a slide-over that already shows it. */
defineProps<{ headless?: boolean }>();

const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();
const { strategy, holdings, loading, error, deciding, decisionError, decide } = useStrategy();

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
      <ProposalDiff
        v-if="strategy.proposal"
        :proposal="strategy.proposal"
        :holdings="holdings"
        :deciding="deciding"
        @decide="decide"
      />
      <section v-else class="flex flex-col gap-2">
        <h3 class="font-semibold">{{ t('strategy.targetsTitle') }}</h3>
        <TargetsTable :targets="strategy.targets" :holdings="holdings" />
      </section>
    </template>
  </div>
</template>
