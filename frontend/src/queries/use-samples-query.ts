import { useQuery } from '@tanstack/vue-query';
import { sampleKeys } from '@/queries/keys';
import { getSampleQuestions, type SampleQuestion } from '@/service/api/samples';
import type { AppError } from '@/service/error';

/**
 * The sample questions as server state, read once a page opens: what the knowledge base holds
 * changes only when the person ingests from the terminal.
 */
export function useSamplesQuery() {
  return useQuery<SampleQuestion[], AppError>({
    queryKey: sampleKeys.questions(),
    queryFn: ({ signal }) => getSampleQuestions(signal),
    staleTime: Infinity
  });
}
