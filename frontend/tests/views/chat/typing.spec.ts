import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, type VueWrapper } from '@vue/test-utils';
import { CanceledError } from 'axios';
import type { ProgramState } from '@/service/api/programs';
import type { ChatEvent, ChatRequest } from '@/service/api/chat';
import { CONTEXT_EVENT, textEvent } from '../../helpers/sse';
import { mountView } from '../../helpers/mount';

const getProgramsMock = vi.fn<() => Promise<ProgramState[]>>();
// The strategy beside the chat reads a fixed strategy, so no test reaches the network for it.
vi.mock('@/service/api/strategy', async () => {
  const { STRATEGY } = await import('../../helpers/strategy');
  return { getStrategy: () => Promise.resolve(STRATEGY), decideProposal: () => Promise.resolve(STRATEGY) };
});

vi.mock('@/service/api/programs', () => ({
  getPrograms: () => getProgramsMock()
}));

const askMock = vi.fn<(input: ChatRequest, signal?: AbortSignal) => AsyncGenerator<ChatEvent, void, undefined>>();
vi.mock('@/service/api/chat', () => ({
  ask: (input: ChatRequest, signal?: AbortSignal) => askMock(input, signal)
}));

import ChatPage from '@/views/chat/ChatPage.vue';

/** A whole answer arriving in one piece, as Codex sends it. */
const LONG_ANSWER = '聯準會降息一碼，台股隔天收高。'.repeat(40);

interface HappyDomWindow {
  happyDOM: { settings: { device: { prefersReducedMotion: 'reduce' | 'no-preference' } } };
}

function setReducedMotion(value: 'reduce' | 'no-preference'): void {
  (window as unknown as HappyDomWindow).happyDOM.settings.device.prefersReducedMotion = value;
}

/** An answer the test feeds; `fail` ends it with an error, a stop by the user ends it as a stop. */
function controlledAnswer() {
  const queue: ChatEvent[] = [];
  let wake: () => void = () => {};
  let ended = false;
  let failure: unknown;
  async function* events(_input: ChatRequest, signal?: AbortSignal): AsyncGenerator<ChatEvent, void, undefined> {
    signal?.addEventListener('abort', () => {
      failure = new CanceledError('canceled');
      wake();
    });
    while (true) {
      if (failure) throw failure;
      const next = queue.shift();
      if (next) {
        yield next;
        continue;
      }
      if (ended) return;
      await new Promise<void>(resolve => (wake = resolve));
    }
  }
  return {
    events,
    send(event: ChatEvent) {
      queue.push(event);
      wake();
    },
    fail(error: unknown) {
      failure = error;
      wake();
    },
    end() {
      ended = true;
      wake();
    }
  };
}

let wrapper: VueWrapper | undefined;

beforeEach(() => {
  setReducedMotion('no-preference');
  getProgramsMock.mockReset().mockResolvedValue([
    { program: 'claude-code', state: 'not logged in' },
    { program: 'codex', state: 'logged in' }
  ]);
  askMock.mockReset();
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
  setReducedMotion('reduce');
});

async function askWith(answer: ReturnType<typeof controlledAnswer>): Promise<VueWrapper> {
  askMock.mockImplementation(answer.events);
  ({ wrapper } = await mountView(ChatPage));
  await flushPromises();
  await wrapper.find('textarea[data-test="question-box"]').setValue('q');
  await wrapper.find('form').trigger('submit');
  await flushPromises();
  return wrapper;
}

const answerText = (page: VueWrapper) => page.find('[data-test="answer-text"]');
// Comark's caret is the one element in an answer with an inline style.
const caret = (page: VueWrapper) => answerText(page).find('span[style]');

describe('typing the answer', () => {
  it('types a whole answer that arrives at once, with a caret, and ends with exactly what arrived', async () => {
    const answer = controlledAnswer();
    const page = await askWith(answer);
    answer.send(CONTEXT_EVENT);
    answer.send(textEvent(LONG_ANSWER));
    answer.end();
    await flushPromises();

    // The sources and the notice are not typed: they are on screen before the answer.
    expect(page.find('[data-test="sources"]').exists()).toBe(true);
    expect(page.find('[data-test="notice"]').text()).toBe('notice');
    expect(answerText(page).text().length).toBeLessThan(LONG_ANSWER.length);

    await vi.waitFor(() => expect(answerText(page).text()).toBe(LONG_ANSWER), { timeout: 2000 });
    expect(caret(page).exists()).toBe(false);
  });

  it('shows the caret while the answer is still arriving', async () => {
    const answer = controlledAnswer();
    const page = await askWith(answer);
    answer.send(CONTEXT_EVENT);
    answer.send(textEvent('聯準會'));
    await flushPromises();

    await vi.waitFor(() => expect(answerText(page).text()).toBe('聯準會'));
    expect(caret(page).exists()).toBe(true);
    answer.end();
  });

  it('shows everything that had arrived at once when the user stops', async () => {
    const answer = controlledAnswer();
    const page = await askWith(answer);
    answer.send(CONTEXT_EVENT);
    answer.send(textEvent(LONG_ANSWER));
    await flushPromises();
    expect(answerText(page).text().length).toBeLessThan(LONG_ANSWER.length);

    await page.find('[data-test="send-or-stop"]').trigger('click');
    await flushPromises();

    expect(answerText(page).text()).toBe(LONG_ANSWER);
    expect(page.find('[data-test="answer-stopped"]').exists()).toBe(true);
    expect(caret(page).exists()).toBe(false);
  });

  it('shows everything that had arrived at once when the answer fails', async () => {
    const answer = controlledAnswer();
    const page = await askWith(answer);
    answer.send(CONTEXT_EVENT);
    answer.send(textEvent(LONG_ANSWER));
    await flushPromises();

    answer.fail({ source: 'backend', code: 'stream_error', reason: 'answer_failed', message: 'x' });
    await flushPromises();

    expect(answerText(page).text()).toBe(LONG_ANSWER);
    expect(page.find('[data-test="answer-error"]').exists()).toBe(true);
  });
});
