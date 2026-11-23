import axios, { CanceledError } from 'axios';
import type { ZodType } from 'zod';
import { ErrorBodySchema, type ServiceErrorCode } from '@/service/schema/common';

/**
 * Where an error came from: the service, or the page's own network, contract check, input check
 * or unknown.
 */
export type AppErrorSource = 'backend' | 'network' | 'contract' | 'input' | 'unknown';

/**
 * `rejected`: the service refused the request with a status and a message.
 * `stream_error`: the answer failed after its stream started.
 */
export type BackendErrorCode = 'rejected' | 'stream_error';

/** Errors the page names itself, not the service. */
export type LocalErrorCode = 'network_error' | 'contract_error' | 'invalid_input' | 'unknown_error';

/**
 * The page's one error type. `reason` is the service's own reason for a backend error, which the
 * page words in its language. `message` and `raw` are for debugging only and are never drawn or
 * serialised into the page.
 */
export interface AppError {
  source: AppErrorSource;
  code: BackendErrorCode | LocalErrorCode;
  reason?: ServiceErrorCode;
  message: string;
  status?: number;
  raw?: unknown;
}

/** Narrows an unknown thrown value to an AppError. */
export function isAppError(value: unknown): value is AppError {
  return typeof value === 'object' && value !== null && 'source' in value && 'code' in value && 'message' in value;
}

function backendError(
  code: BackendErrorCode,
  reason: ServiceErrorCode,
  message: string,
  raw: unknown,
  status?: number
): AppError {
  return { source: 'backend', code, reason, message, status, raw };
}

function localError(
  source: Exclude<AppErrorSource, 'backend'>,
  code: LocalErrorCode,
  message: string,
  raw: unknown
): AppError {
  return { source, code, message, raw };
}

/**
 * Turns a rejected request into an AppError. It sees only what axios rejects; a 2xx body that
 * does not match its schema is caught by {@link parseContract}.
 *
 * A cancellation is rethrown as it is: it is not an error to show or retry.
 */
export function normalizeHttpError(error: unknown): AppError {
  if (axios.isCancel(error)) {
    throw error;
  }

  if (axios.isAxiosError(error)) {
    const response = error.response;

    // No response: the network failed or the request timed out.
    if (!response) {
      return localError('network', 'network_error', error.message || 'network error', error);
    }

    const { status, data } = response;
    const parsed = ErrorBodySchema.safeParse(data);
    if (parsed.success) {
      return backendError('rejected', parsed.data.detail.code, parsed.data.detail.message, error, status);
    }

    // A status with a body that is not the service's error body: the service drifted.
    return localError('contract', 'contract_error', `malformed error payload (status ${status})`, error);
  }

  return localError('unknown', 'unknown_error', 'unknown error', error);
}

/** The answer failed after its stream started; the service says why in the `error` event. */
export function streamError(reason: ServiceErrorCode, message: string, raw: unknown): AppError {
  return backendError('stream_error', reason, message, raw);
}

/** The service sent something the contract does not allow. */
export function contractError(message: string, raw: unknown): AppError {
  return localError('contract', 'contract_error', message, raw);
}

/**
 * Checks a 2xx body, or one streamed event, against its schema. A mismatch means the service
 * drifted from the contract, and the data is never returned.
 */
export function parseContract<T>(schema: ZodType<T>, payload: unknown): T {
  const result = schema.safeParse(payload);
  if (!result.success) {
    throw contractError('response did not match contract', result.error);
  }
  return result.data;
}

/** Checks what the page is about to send, so a request the service would refuse is never sent. */
export function parseInput<T>(schema: ZodType<T>, input: unknown): T {
  const result = schema.safeParse(input);
  if (!result.success) {
    throw localError('input', 'invalid_input', 'the request is not valid', result.error);
  }
  return result.data;
}

/** {@link parseContract} for a streamed event's data, which arrives as JSON text. */
export function parseJsonContract<T>(schema: ZodType<T>, text: string): T {
  let payload: unknown;
  try {
    payload = JSON.parse(text);
  } catch (error) {
    throw contractError('event data is not JSON', error);
  }
  return parseContract(schema, payload);
}

/**
 * Whether the caller stopped the request. A stop before the response and a stop while its body
 * streams both end up as this one kind, so a view needs one check.
 */
export function isCancellation(error: unknown): boolean {
  return axios.isCancel(error);
}

/**
 * A failure while reading a stream. The caller's own stop becomes the same cancellation a stop
 * before the response gives; anything else is a network error.
 */
export function normalizeStreamReadError(error: unknown, signal?: AbortSignal): AppError {
  if (signal?.aborted) {
    throw new CanceledError('canceled');
  }
  if (isAppError(error)) {
    return error;
  }
  return localError('network', 'network_error', 'the answer stopped arriving', error);
}
