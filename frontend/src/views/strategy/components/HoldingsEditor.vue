<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import type { HoldingsInput } from '@/service/api/strategy';
import type { AppError } from '@/service/error';

defineProps<{ draft: HoldingsInput; changed: boolean; saving: boolean; error: AppError | null }>();
const emit = defineEmits<{
  symbol: [index: number, symbol: string];
  name: [index: number, locale: Locale, name: string];
  quantity: [index: number, quantity: string];
  cost: [index: number, cost: string];
  cash: [cash: string];
  remove: [index: number];
  add: [];
  save: [];
  cancel: [];
}>();

const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();

/** The page's own words for an error: the service's reason when it gave one, else the page's code. */
function errorKey(appError: AppError): keyof MessageSchema['errors'] {
  return appError.reason ?? appError.code;
}

/** The error's title, after which holding it is about when it names one; that row is outlined. */
function errorTitle(appError: AppError): string {
  const title = t(`errors.${errorKey(appError)}.title`);
  return appError.item === undefined ? title : t('holdings.which', { item: appError.item, title });
}
</script>

<template>
  <section class="flex flex-col gap-3" data-test="holdings-editor">
    <h3 class="font-semibold">{{ t('holdings.title') }}</h3>
    <ul class="flex flex-col gap-3">
      <li
        v-for="(holding, index) in draft.holdings"
        :key="index"
        class="flex flex-wrap items-end gap-2 rounded-md border p-2"
        :class="error?.item === index + 1 ? 'border-error' : 'border-default'"
        :data-test="`holding-row-${index}`"
      >
        <UFormField :label="t('holdings.symbol')">
          <UInput
            class="w-28"
            :data-test="`holding-symbol-${index}`"
            :model-value="holding.symbol"
            placeholder="2330.TW"
            @update:model-value="emit('symbol', index, String($event))"
          />
        </UFormField>
        <UFormField :label="t('holdings.name')" class="min-w-32 grow">
          <UInput
            class="w-full"
            :data-test="`holding-name-${index}`"
            :model-value="holding.names[locale]"
            @update:model-value="emit('name', index, locale, String($event))"
          />
        </UFormField>
        <UFormField :label="t('holdings.quantity')">
          <UInput
            class="w-28"
            inputmode="decimal"
            :data-test="`holding-quantity-${index}`"
            :model-value="holding.quantity"
            @update:model-value="emit('quantity', index, String($event))"
          />
        </UFormField>
        <UFormField :label="t('holdings.cost')">
          <UInput
            class="w-28"
            inputmode="decimal"
            :data-test="`holding-cost-${index}`"
            :model-value="holding.average_cost"
            @update:model-value="emit('cost', index, String($event))"
          />
        </UFormField>
        <UButton
          :data-test="`holding-remove-${index}`"
          color="neutral"
          variant="ghost"
          icon="i-lucide-trash-2"
          :aria-label="t('holdings.remove')"
          @click="emit('remove', index)"
        />
      </li>
    </ul>
    <UButton
      data-test="holding-add"
      class="self-start"
      color="neutral"
      variant="outline"
      icon="i-lucide-plus"
      :label="t('holdings.add')"
      @click="emit('add')"
    />
    <UFormField :label="t('holdings.cash')">
      <UInput
        class="w-40"
        inputmode="decimal"
        data-test="holding-cash"
        :model-value="draft.cash"
        @update:model-value="emit('cash', String($event))"
      />
    </UFormField>
    <UAlert
      v-if="error"
      data-test="holdings-error"
      color="error"
      variant="subtle"
      icon="i-lucide-circle-alert"
      :title="errorTitle(error)"
      :description="t(`errors.${errorKey(error)}.description`)"
    />
    <div class="flex gap-2">
      <UButton
        data-test="holdings-save"
        :label="t('holdings.save')"
        :loading="saving"
        :disabled="!changed || saving"
        @click="emit('save')"
      />
      <UButton
        data-test="holdings-cancel"
        color="neutral"
        variant="outline"
        :label="t('holdings.cancel')"
        :disabled="saving"
        @click="emit('cancel')"
      />
    </div>
    <p class="text-muted text-xs">{{ t('holdings.note') }}</p>
  </section>
</template>
