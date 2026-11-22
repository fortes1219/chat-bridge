// @vitest-environment node
// The transport runs on the platform's own fetch, Response and ReadableStream, which happy-dom
// replaces with versions axios does not take as streamable; Node's are the ones browsers have.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { request } from '@/service/request';

// Node has no page to resolve a relative address against, so the tests use the service's own.
const SERVICE = 'http://127.0.0.1:8000';
const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function json(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

describe('request', () => {
  it('returns a 2xx JSON body', async () => {
    fetchMock.mockResolvedValue(json([{ program: 'codex', state: 'logged in' }], 200));
    await expect(request({ url: `${SERVICE}/chat/programs`, method: 'GET' })).resolves.toEqual([
      { program: 'codex', state: 'logged in' }
    ]);
  });

  it('returns a 2xx stream body as a stream', async () => {
    fetchMock.mockResolvedValue(new Response('data: {}\n\n', { status: 200 }));
    const body = await request<ReadableStream<Uint8Array>>({
      url: `${SERVICE}/chat/stream`,
      method: 'POST',
      data: { question: 'q' },
      responseType: 'stream'
    });
    expect(body).toBeInstanceOf(ReadableStream);
  });

  it('reads the error body of a refused stream request into the service’s message', async () => {
    fetchMock.mockResolvedValue(json({ detail: 'the knowledge base is empty' }, 503));
    await expect(
      request({ url: `${SERVICE}/chat/stream`, method: 'POST', data: { question: 'q' }, responseType: 'stream' })
    ).rejects.toMatchObject({
      source: 'backend',
      code: 'rejected',
      message: 'the knowledge base is empty',
      status: 503
    });
  });

  it('calls a failed connection a network error', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'));
    await expect(request({ url: `${SERVICE}/chat/programs`, method: 'GET' })).rejects.toMatchObject({
      source: 'network',
      code: 'network_error'
    });
  });

  it('rethrows a stop by the caller as a cancellation, not an error to show', async () => {
    fetchMock.mockImplementation((input, init) => {
      // axios may pass a Request that carries the signal, or the signal in the options.
      const signal = input instanceof Request ? input.signal : init?.signal;
      return new Promise((_resolve, reject) => {
        signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')));
      });
    });
    const controller = new AbortController();
    const pending = request({ url: `${SERVICE}/chat/programs`, method: 'GET', signal: controller.signal });
    controller.abort();
    await expect(pending).rejects.toMatchObject({ code: 'ERR_CANCELED' });
  });
});
