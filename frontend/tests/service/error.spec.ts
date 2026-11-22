import { CanceledError } from 'axios';
import { describe, expect, it } from 'vitest';
import {
  isCancellation,
  normalizeHttpError,
  normalizeStreamReadError,
  parseContract,
  parseInput,
  parseJsonContract
} from '@/service/error';
import { ProgramStateSchema } from '@/service/schema/program';

function axiosError(status?: number, data?: unknown): unknown {
  return {
    isAxiosError: true,
    message: 'request failed',
    config: { url: '/chat/stream' },
    response: status === undefined ? undefined : { status, data }
  };
}

describe('normalizeHttpError', () => {
  it('keeps the service’s message and status', () => {
    expect(normalizeHttpError(axiosError(503, { detail: 'the knowledge base is empty' }))).toMatchObject({
      source: 'backend',
      code: 'rejected',
      message: 'the knowledge base is empty',
      status: 503
    });
  });

  it('calls a request without a response a network error', () => {
    expect(normalizeHttpError(axiosError())).toMatchObject({ source: 'network', code: 'network_error' });
  });

  it('calls a status with a body that is not the service’s a contract error', () => {
    expect(normalizeHttpError(axiosError(400, 'Invalid host header'))).toMatchObject({
      source: 'contract',
      code: 'contract_error'
    });
  });

  it('rethrows a cancellation instead of making it an error', () => {
    const error = new CanceledError('canceled');
    expect(() => normalizeHttpError(error)).toThrow(error);
  });

  it('calls anything else unknown', () => {
    expect(normalizeHttpError(new Error('x'))).toMatchObject({ source: 'unknown', code: 'unknown_error' });
  });
});

describe('parseContract and parseJsonContract', () => {
  it('report a drifted body as a contract error', () => {
    expect(() => parseContract(ProgramStateSchema, { program: 'codex' })).toThrowError(
      expect.objectContaining({ source: 'contract', code: 'contract_error' })
    );
  });

  it('report event data that is not JSON as a contract error', () => {
    expect(() => parseJsonContract(ProgramStateSchema, '{not json')).toThrowError(
      expect.objectContaining({ code: 'contract_error' })
    );
  });
});

describe('parseInput', () => {
  it('reports a request the page should not send as an input error', () => {
    expect(() => parseInput(ProgramStateSchema, { program: 'gemini', state: 'logged in' })).toThrowError(
      expect.objectContaining({ source: 'input', code: 'invalid_input' })
    );
  });
});

describe('normalizeStreamReadError', () => {
  it('turns the reader’s own stop into the same cancellation a stop before the response gives', () => {
    const controller = new AbortController();
    controller.abort();
    let thrown: unknown;
    try {
      normalizeStreamReadError(new DOMException('aborted', 'AbortError'), controller.signal);
    } catch (error) {
      thrown = error;
    }
    expect(isCancellation(thrown)).toBe(true);
    expect(isCancellation(new CanceledError('canceled'))).toBe(true);
  });

  it('calls a stream that broke off a network error', () => {
    expect(normalizeStreamReadError(new TypeError('network error'))).toMatchObject({
      source: 'network',
      code: 'network_error'
    });
  });
});
