<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import type { Market, Rule, RuleKind } from '@/service/api/strategy';
import type { AppError } from '@/service/error';
import { MARKETS, NAMES_A_MARKET } from '../composables/useRuleEditor';

defineProps<{ rules: readonly Rule[]; changed: boolean; saving: boolean; error: AppError | null }>();
const emit = defineEmits<{
  kind: [index: number, kind: RuleKind];
  limit: [index: number, limit: number | null];
  market: [index: number, market: Market];
  enabled: [index: number, enabled: boolean];
  remove: [index: number];
  add: [];
  save: [];
  cancel: [];
}>();

const { t } = useI18n<{ message: MessageSchema }, Locale>();

const KINDS = Object.keys(NAMES_A_MARKET) as RuleKind[];
const kindItems = computed(() => KINDS.map(kind => ({ label: t(`rules.${kind}.name`), value: kind })));
const marketItems = computed(() => MARKETS.map(market => ({ label: t(`markets.${market}`), value: market })));

/** The page's own words for an error: the service's reason when it gave one, else the page's code. */
function errorKey(appError: AppError): keyof MessageSchema['errors'] {
  return appError.reason ?? appError.code;
}
</script>

<template>
  <section class="flex flex-col gap-3" data-test="rule-editor">
    <h3 class="font-semibold">{{ t('rules.title') }}</h3>
    <ul class="flex flex-col gap-3">
      <li
        v-for="(rule, index) in rules"
        :key="index"
        class="border-default flex flex-wrap items-end gap-2 rounded-md border p-2"
        :data-test="`rule-row-${index}`"
      >
        <UFormField :label="t('rules.kind')" class="min-w-44 grow">
          <USelect
            class="w-full"
            :data-test="`rule-kind-${index}`"
            :items="kindItems"
            :model-value="rule.kind"
            @update:model-value="emit('kind', index, $event)"
          />
        </UFormField>
        <UFormField v-if="NAMES_A_MARKET[rule.kind]" :label="t('rules.market')">
          <USelect
            class="w-24"
            :data-test="`rule-market-${index}`"
            :items="marketItems"
            :model-value="rule.market ?? undefined"
            @update:model-value="emit('market', index, $event)"
          />
        </UFormField>
        <UFormField :label="t('rules.limit')">
          <UInputNumber
            class="w-28"
            :data-test="`rule-limit-${index}`"
            :min="0"
            :max="100"
            :model-value="rule.limit_percent"
            @update:model-value="emit('limit', index, $event)"
          />
        </UFormField>
        <USwitch
          :data-test="`rule-enabled-${index}`"
          :label="t('rules.enabled')"
          :model-value="rule.enabled"
          @update:model-value="emit('enabled', index, $event)"
        />
        <UButton
          :data-test="`rule-remove-${index}`"
          color="neutral"
          variant="ghost"
          icon="i-lucide-trash-2"
          :aria-label="t('rules.remove')"
          @click="emit('remove', index)"
        />
      </li>
    </ul>
    <UButton
      data-test="rule-add"
      class="self-start"
      color="neutral"
      variant="outline"
      icon="i-lucide-plus"
      :label="t('rules.add')"
      @click="emit('add')"
    />
    <UAlert
      v-if="error"
      data-test="rules-error"
      color="error"
      variant="subtle"
      icon="i-lucide-circle-alert"
      :title="t(`errors.${errorKey(error)}.title`)"
      :description="t(`errors.${errorKey(error)}.description`)"
    />
    <div class="flex gap-2">
      <UButton
        data-test="rules-save"
        :label="t('rules.save')"
        :loading="saving"
        :disabled="!changed || saving"
        @click="emit('save')"
      />
      <UButton
        data-test="rules-cancel"
        color="neutral"
        variant="outline"
        :label="t('rules.cancel')"
        :disabled="saving"
        @click="emit('cancel')"
      />
    </div>
    <p class="text-muted text-xs">{{ t('rules.note') }}</p>
  </section>
</template>
