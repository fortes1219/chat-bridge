import { computed, type ComputedRef } from 'vue';
import { useStrategyQuery } from '@/queries/use-strategy-query';
import { useDecideProposal } from '@/queries/use-strategy-mutations';
import type { Decision, Holding, Strategy } from '@/service/api/strategy';
import type { AppError } from '@/service/error';

export interface UseStrategy {
  strategy: ComputedRef<Strategy | null>;
  /** Each holding by its symbol, from the latest strategy, so a row names its holding. */
  holdings: ComputedRef<ReadonlyMap<string, Holding>>;
  loading: ComputedRef<boolean>;
  error: ComputedRef<AppError | null>;
  deciding: ComputedRef<boolean>;
  decisionError: ComputedRef<AppError | null>;
  decide(decision: Decision): void;
}

/**
 * The strategy and the decision on its open proposal. The proposal is read from the latest
 * strategy each time, never kept aside, so a decision goes to the proposal the screen shows.
 */
export function useStrategy(): UseStrategy {
  const query = useStrategyQuery();
  const mutation = useDecideProposal();

  const strategy = computed(() => query.data.value ?? null);
  const holdings = computed(
    () => new Map((strategy.value?.holdings ?? []).map(holding => [holding.symbol, holding] as const))
  );

  function decide(decision: Decision): void {
    const proposal = strategy.value?.proposal;
    if (!proposal || mutation.isPending.value) return;
    mutation.mutate({ params: { id: proposal.id }, body: { decision } });
  }

  return {
    strategy,
    holdings,
    loading: computed(() => query.isPending.value),
    error: computed(() => query.error.value ?? null),
    deciding: computed(() => mutation.isPending.value),
    decisionError: computed(() => mutation.error.value ?? null),
    decide
  };
}
