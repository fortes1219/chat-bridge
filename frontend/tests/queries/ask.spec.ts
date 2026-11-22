import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { defineComponent, h } from 'vue';
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';
import type { ChatEvent } from '@/service/api/chat';
import { CONTEXT_EVENT, textEvent } from '../helpers/sse';

const askMock = vi.fn();
vi.mock('@/service/api/chat', () => ({
  ask: (...args: unknown[]) => askMock(...args)
}));

import { useAskMutation } from '@/queries/use-ask-mutation';

beforeEach(() => {
  askMock.mockReset();
});

function mountMutation() {
  let mutation!: ReturnType<typeof useAskMutation>;
  const Probe = defineComponent({
    setup() {
      mutation = useAskMutation();
      return () => h('div');
    }
  });
  const queryClient = new QueryClient();
  mount(Probe, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } });
  return mutation;
}

describe('useAskMutation', () => {
  it('hands each event over as it arrives and resolves when the answer ends', async () => {
    askMock.mockImplementation(async function* () {
      yield CONTEXT_EVENT;
      yield textEvent('聯準會');
    });
    const mutation = mountMutation();
    const seen: ChatEvent[] = [];
    const controller = new AbortController();

    await mutation.mutateAsync({
      input: { question: 'q' },
      signal: controller.signal,
      onEvent: event => seen.push(event)
    });

    expect(askMock).toHaveBeenCalledWith({ question: 'q' }, controller.signal);
    expect(seen.map(event => event.type)).toEqual(['response.context', 'response.output_text.delta']);
  });

  it('fails with the error that ended the answer, once, without a retry', async () => {
    const failure = { source: 'backend', code: 'stream_error', message: 'the program stopped' };
    askMock.mockImplementation(async function* () {
      yield CONTEXT_EVENT;
      throw failure;
    });
    const mutation = mountMutation();

    await expect(
      mutation.mutateAsync({ input: { question: 'q' }, signal: new AbortController().signal, onEvent: () => {} })
    ).rejects.toBe(failure);
    expect(askMock).toHaveBeenCalledTimes(1);
    // Vue hands the error back through a reactive proxy, so its content is compared.
    await vi.waitFor(() => expect(mutation.error.value).toStrictEqual(failure));
  });
});
