import { CanceledError } from 'axios';
import { describe, expect, it } from 'vitest';
import { queryClient, shouldRetryQuery } from '@/queries/query-client';
import type { AppError } from '@/service/error';

function appError(partial: Partial<AppError>): AppError {
  return { source: 'unknown', code: 'unknown_error', message: 'x', ...partial };
}

describe('shouldRetryQuery', () => {
  it('retries a network error twice, then stops', () => {
    const error = appError({ source: 'network', code: 'network_error' });
    expect(shouldRetryQuery(0, error)).toBe(true);
    expect(shouldRetryQuery(1, error)).toBe(true);
    expect(shouldRetryQuery(2, error)).toBe(false);
  });

  it('retries a 5xx twice, then stops', () => {
    const error = appError({ source: 'backend', code: 'rejected', status: 503 });
    expect(shouldRetryQuery(0, error)).toBe(true);
    expect(shouldRetryQuery(2, error)).toBe(false);
  });

  it('never retries a 4xx, a contract error, an unknown error or a cancellation', () => {
    expect(shouldRetryQuery(0, appError({ source: 'backend', code: 'rejected', status: 422 }))).toBe(false);
    expect(shouldRetryQuery(0, appError({ source: 'contract', code: 'contract_error' }))).toBe(false);
    expect(shouldRetryQuery(0, appError({}))).toBe(false);
    expect(shouldRetryQuery(0, new CanceledError('canceled'))).toBe(false);
  });
});

describe('queryClient', () => {
  it('never refetches on focus or reconnect and never retries a mutation', () => {
    const { queries, mutations } = queryClient.getDefaultOptions();
    expect(queries?.refetchOnWindowFocus).toBe(false);
    expect(queries?.refetchOnReconnect).toBe(false);
    expect(mutations?.retry).toBe(false);
  });
});
