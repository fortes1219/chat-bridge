import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CONTEXT_EVENT, sseEvent, streamOf, textEvent } from '../helpers/sse';

const requestMock = vi.fn();
vi.mock('@/service/request', () => ({
  request: (...args: unknown[]) => requestMock(...args)
}));

import { contract } from '@/service/contract';
import { getPrograms } from '@/service/api/programs';
import { ask, type ChatEvent } from '@/service/api/chat';
import { isCancellation } from '@/service/error';

beforeEach(() => {
  requestMock.mockReset();
});

async function collect(events: AsyncIterable<ChatEvent>): Promise<{ events: ChatEvent[]; error: unknown }> {
  const seen: ChatEvent[] = [];
  try {
    for await (const event of events) {
      seen.push(event);
    }
  } catch (error) {
    return { events: seen, error };
  }
  return { events: seen, error: undefined };
}

describe('getPrograms', () => {
  it('calls the contract’s method and path and returns the checked states', async () => {
    const states = [
      { program: 'claude-code', state: 'not logged in' },
      { program: 'codex', state: 'logged in' }
    ];
    requestMock.mockResolvedValue(states);

    const result = await getPrograms();

    const { method, path } = contract.programs.getPrograms['~orpc'].route;
    expect(requestMock).toHaveBeenCalledWith(expect.objectContaining({ url: path, method }));
    expect(result).toEqual(states);
  });

  it('throws a contract error on a drifted response and returns nothing', async () => {
    requestMock.mockResolvedValue([{ program: 'codex', state: 'logged in', detail: 'account' }]);
    await expect(getPrograms()).rejects.toMatchObject({ source: 'contract', code: 'contract_error' });
  });

  it('passes the signal through', async () => {
    requestMock.mockResolvedValue([]);
    const controller = new AbortController();
    await getPrograms(controller.signal);
    expect(requestMock).toHaveBeenCalledWith(expect.objectContaining({ signal: controller.signal }));
  });
});

describe('ask', () => {
  it('checks the question before anything is sent, and says so with an AppError', async () => {
    const { error } = await collect(ask({ question: '' }));
    expect(error).toMatchObject({ source: 'input', code: 'invalid_input' });
    expect(requestMock).not.toHaveBeenCalled();
  });

  it('posts to the contract’s path as a stream with no client time limit', async () => {
    requestMock.mockResolvedValue(streamOf());
    const controller = new AbortController();

    await collect(ask({ question: 'q', program: 'codex' }, controller.signal));

    const { method, path } = contract.chat.ask['~orpc'].route;
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        url: path,
        method,
        data: { question: 'q', program: 'codex' },
        responseType: 'stream',
        timeout: 0,
        signal: controller.signal
      })
    );
  });

  it('yields the context, then each piece, even when an event is split across chunks', async () => {
    const piece = sseEvent(textEvent('降息。'));
    requestMock.mockResolvedValue(
      streamOf(sseEvent(CONTEXT_EVENT), sseEvent(textEvent('聯準會')), piece.slice(0, 12), piece.slice(12))
    );

    const { events, error } = await collect(ask({ question: 'q' }));

    expect(error).toBeUndefined();
    expect(events.map(event => event.type)).toEqual([
      'response.context',
      'response.output_text.delta',
      'response.output_text.delta'
    ]);
    expect(events.slice(1).map(event => event.delta)).toEqual(['聯準會', '降息。']);
  });

  it('ends with the service’s reason and message when an error event arrives', async () => {
    requestMock.mockResolvedValue(
      streamOf(sseEvent(CONTEXT_EVENT), sseEvent({ code: 'answer_failed', message: 'the program stopped' }, 'error'))
    );

    const { events, error } = await collect(ask({ question: 'q' }));

    expect(events).toHaveLength(1);
    expect(error).toMatchObject({
      source: 'backend',
      code: 'stream_error',
      reason: 'answer_failed',
      message: 'the program stopped'
    });
  });

  it('never yields an event that does not match its schema', async () => {
    requestMock.mockResolvedValue(
      streamOf(sseEvent(CONTEXT_EVENT), sseEvent({ type: 'response.output_text.delta', delta: '<b>x</b>' }))
    );

    const { events, error } = await collect(ask({ question: 'q' }));

    expect(events).toHaveLength(1);
    expect(error).toMatchObject({ code: 'contract_error' });
  });

  it.each(['progress', 'constructor', 'toString', '__proto__'])(
    'treats the event name %s, which the contract does not have, as a contract error',
    async name => {
      requestMock.mockResolvedValue(streamOf(sseEvent({ note: 'x' }, name)));
      const { events, error } = await collect(ask({ question: 'q' }));
      expect(events).toEqual([]);
      expect(error).toMatchObject({ code: 'contract_error' });
    }
  );

  it('ends with a cancellation when the caller stops while the answer streams', async () => {
    const controller = new AbortController();
    const body = new ReadableStream<Uint8Array>({
      start(stream) {
        stream.enqueue(new TextEncoder().encode(sseEvent(CONTEXT_EVENT)));
        controller.signal.addEventListener('abort', () => stream.error(new DOMException('aborted', 'AbortError')));
      }
    });
    requestMock.mockResolvedValue(body);

    const seen: ChatEvent[] = [];
    let stopped: unknown;
    try {
      for await (const event of ask({ question: 'q' }, controller.signal)) {
        seen.push(event);
        controller.abort();
      }
    } catch (error) {
      stopped = error;
    }

    expect(seen).toHaveLength(1);
    expect(isCancellation(stopped)).toBe(true);
  });

  it('ignores the keep-alive comments the service sends while it waits', async () => {
    requestMock.mockResolvedValue(streamOf(': ping\n\n', sseEvent(CONTEXT_EVENT)));
    const { events, error } = await collect(ask({ question: 'q' }));
    expect(error).toBeUndefined();
    expect(events).toHaveLength(1);
  });
});
