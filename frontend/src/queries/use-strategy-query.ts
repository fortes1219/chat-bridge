import { useQuery, useQueryClient } from '@tanstack/vue-query';
import { strategyKeys } from '@/queries/keys';
import { getStrategy, type Proposal, type Strategy } from '@/service/api/strategy';
import type { AppError } from '@/service/error';

export interface StrategyQueryOptions {
  /**
   * False for a view that only follows the strategy the page already has, such as a proposal card
   * in the chat: its mounting does not read the strategy again. It is still read when there is
   * none yet, and again whenever it is invalidated.
   */
  refetchOnMount?: boolean;
}

/** The strategy as server state. A decision or a new proposal replaces it in the cache. */
export function useStrategyQuery({ refetchOnMount = true }: StrategyQueryOptions = {}) {
  return useQuery<Strategy, AppError>({
    queryKey: strategyKeys.current(),
    queryFn: ({ signal }) => getStrategy(signal),
    refetchOnMount
  });
}

/**
 * A proposal the service kept from a revision answer is the open one from then on: it goes into
 * the cached strategy at once, so no view shows an older proposal as open meanwhile, and the
 * strategy is read again.
 */
export function useProposalKept(): (proposal: Proposal) => void {
  const queryClient = useQueryClient();
  return proposal => {
    queryClient.setQueryData<Strategy>(strategyKeys.current(), current => current && { ...current, proposal });
    void queryClient.invalidateQueries({ queryKey: strategyKeys.current() });
  };
}
