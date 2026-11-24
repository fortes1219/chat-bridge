<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import type { Holding, RuleChecks } from '@/service/api/strategy';
import { RULE_STATUS_COLORS, ruleStatus, useRuleText } from '../composables/useRuleText';

defineProps<{ checks: RuleChecks; holdings: ReadonlyMap<string, Holding> }>();
const emit = defineEmits<{ edit: [] }>();

const { t } = useI18n<{ message: MessageSchema }, Locale>();
const text = useRuleText();
</script>

<template>
  <section class="flex flex-col gap-3" data-test="rule-checks">
    <div class="flex items-center justify-between gap-2">
      <h3 class="font-semibold">{{ t('rules.title') }}</h3>
      <UButton
        data-test="rules-edit"
        size="sm"
        color="neutral"
        variant="outline"
        icon="i-lucide-pencil"
        :label="t('rules.edit')"
        @click="emit('edit')"
      />
    </div>
    <p class="text-sm font-medium" data-test="rules-summary">
      {{ checks.enabled ? t('rules.summary', { met: checks.met, enabled: checks.enabled }) : t('rules.noneOn') }}
    </p>
    <ul class="flex flex-col gap-2 text-sm" data-test="rules-list">
      <li
        v-for="(check, index) in checks.rules"
        :key="index"
        class="flex items-start justify-between gap-2"
        :data-test="`rule-${index}`"
      >
        <div>
          <p>{{ text.describe(check) }}</p>
          <p v-if="text.measured(check)" class="text-muted text-xs">{{ text.measured(check) }}</p>
          <p v-if="text.breaking(check, holdings)" class="text-error text-xs" :data-test="`rule-breaking-${index}`">
            {{ text.breaking(check, holdings) }}
          </p>
        </div>
        <UBadge
          :color="RULE_STATUS_COLORS[ruleStatus(check)]"
          variant="subtle"
          class="shrink-0"
          :data-test="`rule-status-${index}`"
        >
          {{ text.status(check) }}
        </UBadge>
      </li>
    </ul>
    <p class="text-muted text-xs" data-test="rules-note">{{ t('rules.note') }}</p>
  </section>
</template>
