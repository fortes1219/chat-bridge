import { QueryClient } from '@tanstack/vue-query';
import { isAppError } from '@/service/error';

/**
 * The most retries. TanStack Query counts failures from 0 and asks `retry(failureCount, error)`
 * before it adds one, so returning true while `failureCount < MAX_QUERY_RETRY` (0 and 1) stops
 * after the second failure: at most two retries.
 */
const MAX_QUERY_RETRY = 2;

function isServerError(status: number | undefined): boolean {
  return status !== undefined && status >= 500 && status <= 599;
}

/**
 * Which failed queries are tried again:
 * - a cancellation (rethrown, not an AppError), a contract error, an unknown error, a 4xx: never;
 * - a network error or a 5xx: at most twice.
 */
export function shouldRetryQuery(failureCount: number, error: unknown): boolean {
  if (failureCount >= MAX_QUERY_RETRY) return false;
  if (!isAppError(error)) return false;
  if (error.source === 'network') return true;
  if (error.source === 'backend') return isServerError(error.status);
  return false;
}

/**
 * A QueryClient with the page's rules; tests make their own with the same rules.
 * - Retries follow {@link shouldRetryQuery}; mutations are never retried, so a question is never
 *   sent twice.
 * - No refetch on window focus or reconnect: the login states are read when the page opens and
 *   when the user asks again, never behind their back.
 */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: shouldRetryQuery,
        refetchOnWindowFocus: false,
        refetchOnReconnect: false
      },
      mutations: {
        retry: false
      }
    }
  });
}

/** The page's one QueryClient. */
export const queryClient = createQueryClient();
