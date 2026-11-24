<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { MessageSchema } from '@/i18n';
import { useStrategyQuery } from '@/queries/use-strategy-query';
import type { ProposalOutcome } from '@/service/api/chat';

const props = defineProps<{ outcome: ProposalOutcome }>();
const emit = defineEmits<{ openStrategy: [] }>();

const { t } = useI18n<{ message: MessageSchema }>();

// The refusal's reason in the page's language; the service's message is for logs and is not drawn.
const refusedReason = computed(() => (props.outcome.refused ? t(`refusals.${props.outcome.refused.code}`) : ''));

// A kept proposal waits for the person only while it is the strategy's open one. Once it is
// accepted, rejected or replaced, the card says so and has no button: the strategy screen no
// longer shows it. Read from the strategy the page already has; the card reads nothing new.
const strategy = useStrategyQuery({ refetchOnMount: false });
const isClosed = computed(() => {
  const proposal = props.outcome.proposal;
  const current = strategy.data.value;
  if (!proposal || !current) return false;
  return current.proposal?.id !== proposal.id;
});
</script>

<template>
  <UAlert
    v-if="outcome.proposal && isClosed"
    data-test="proposal-closed"
    color="neutral"
    variant="subtle"
    icon="i-lucide-check"
    :title="t('chat.proposalClosed')"
  />
  <UAlert
    v-else-if="outcome.proposal"
    data-test="proposal-card"
    color="primary"
    variant="subtle"
    icon="i-lucide-git-compare"
    :title="t('chat.proposalReady')"
    :actions="[
      { label: t('chat.viewProposal'), color: 'primary', variant: 'solid', onClick: () => emit('openStrategy') }
    ]"
  />
  <UAlert
    v-else-if="outcome.refused"
    data-test="proposal-refused"
    color="warning"
    variant="subtle"
    icon="i-lucide-circle-alert"
    :title="t('chat.proposalRefused', { reason: refusedReason })"
  />
  <p v-else class="text-muted text-sm" data-test="no-proposal">{{ t('chat.noProposal') }}</p>
</template>
