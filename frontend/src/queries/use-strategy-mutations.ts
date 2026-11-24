import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { strategyKeys } from '@/queries/keys';
import { decideProposal, type DecideInput, type Strategy } from '@/service/api/strategy';
import type { AppError } from '@/service/error';

/**
 * Accepting or rejecting the open proposal. The service answers with the strategy after the
 * decision, which replaces the cached one; a decision is not retried, since the proposal may
 * already be closed.
 */
export function useDecideProposal() {
  const queryClient = useQueryClient();
  return useMutation<Strategy, AppError, DecideInput>({
    mutationFn: input => decideProposal(input),
    retry: false,
    onSuccess: strategy => {
      queryClient.setQueryData(strategyKeys.current(), strategy);
    }
  });
}
