import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, type VueWrapper } from '@vue/test-utils';
import type { Router } from 'vue-router';
import { CanceledError } from 'axios';
import type { ProgramState } from '@/service/api/programs';
import type { ChatEvent, ChatRequest } from '@/service/api/chat';
import { CONTEXT_EVENT, textEvent } from '../../helpers/sse';
import { mountView } from '../../helpers/mount';

const getProgramsMock = vi.fn<() => Promise<ProgramState[]>>();
vi.mock('@/service/api/programs', () => ({
  getPrograms: () => getProgramsMock()
}));

const askMock = vi.fn<(input: ChatRequest, signal?: AbortSignal) => AsyncGenerator<ChatEvent, void, undefined>>();
vi.mock('@/service/api/chat', () => ({
  ask: (input: ChatRequest, signal?: AbortSignal) => askMock(input, signal)
}));

import ChatPage from '@/views/chat/ChatPage.vue';

const CODEX_ONLY: ProgramState[] = [
  { program: 'claude-code', state: 'not logged in' },
  { program: 'codex', state: 'logged in' }
];
const BOTH: ProgramState[] = [
  { program: 'claude-code', state: 'logged in' },
  { program: 'codex', state: 'logged in' }
];

/** An answer the test feeds one event at a time; `stop` ends it as a stop by the user would. */
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
let router: Router;

beforeEach(() => {
  getProgramsMock.mockReset();
  askMock.mockReset();
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
});

async function open(states: ProgramState[], path = '/?lang=en'): Promise<VueWrapper> {
  getProgramsMock.mockResolvedValue(states);
  ({ wrapper, router } = await mountView(ChatPage, { path }));
  await flushPromises();
  return wrapper;
}

async function typeAndSend(page: VueWrapper, question: string): Promise<void> {
  // The prompt puts the attribute on its textarea; the textarea's form sends the question.
  await page.find('textarea[data-test="question-box"]').setValue(question);
  await page.find('form').trigger('submit');
  await flushPromises();
}

describe('asking a question', () => {
  it('shows sample questions first; picking one fills the box and sends nothing', async () => {
    const page = await open(CODEX_ONLY);

    await page.find('[data-test="sample-fed"]').trigger('click');

    const box = page.find('textarea[data-test="question-box"]').element as HTMLTextAreaElement;
    expect(box.value).toBe('Which of the Fed’s moves over the past half year shook the stock market?');
    expect(askMock).not.toHaveBeenCalled();
  });

  it('does not send an empty question or one longer than the service takes, and says why', async () => {
    const page = await open(CODEX_ONLY);

    await page.find('textarea[data-test="question-box"]').setValue('   ');
    await page.find('textarea[data-test="question-box"]').trigger('keydown', { key: 'Enter' });
    expect(page.find('[data-test="not-sent"]').text()).toBe('Type a question first.');
    await page.find('[data-test="send-or-stop"]').trigger('click');
    expect(page.find('[data-test="not-sent"]').text()).toBe('Type a question first.');

    await typeAndSend(page, 'x'.repeat(10_241));
    expect(page.find('[data-test="not-sent"]').text()).toBe('A question can be at most 10,240 characters.');

    expect(askMock).not.toHaveBeenCalled();
    expect(page.find('[data-test="sample-questions"]').exists()).toBe(true);
  });

  it('sends a question on Enter without saying it was empty', async () => {
    askMock.mockImplementation(controlledAnswer().events);
    const page = await open(CODEX_ONLY);
    const box = page.find('textarea[data-test="question-box"]');

    await box.setValue('Fed?');
    await box.trigger('keydown', { key: 'Enter' });
    await flushPromises();

    expect(askMock).toHaveBeenCalledWith({ question: 'Fed?', program: 'codex' }, expect.any(AbortSignal));
    expect(page.find('[data-test="not-sent"]').exists()).toBe(false);
  });

  it('shows the sources first, then the answer as it grows, with the notice', async () => {
    const answer = controlledAnswer();
    askMock.mockImplementation(answer.events);
    const page = await open(CODEX_ONLY);

    await typeAndSend(page, 'Fed?');
    expect(askMock).toHaveBeenCalledWith({ question: 'Fed?', program: 'codex' }, expect.any(AbortSignal));

    answer.send(CONTEXT_EVENT);
    await flushPromises();
    expect(page.find('[data-test="source-1"]').text()).toBe('[1] data/truth/a.md · H · 2026-09-17');
    expect(page.find('[data-test="source-2"]').text()).toBe('[2] data/truth/b.md · H2 · No date');
    expect(page.find('[data-test="latest-date"]').text()).toBe('The sources reach 2026-09-17.');
    expect(page.find('[data-test="notice"]').text()).toBe('notice');
    expect(page.find('[data-test="answer-text"]').text()).toBe('');

    answer.send(textEvent('The Fed '));
    await flushPromises();
    expect(page.find('[data-test="answer-text"]').text()).toBe('The Fed');
    answer.send(textEvent('cut rates [1].'));
    await flushPromises();
    expect(page.find('[data-test="answer-text"]').text()).toBe('The Fed cut rates [1].');

    answer.end();
    await flushPromises();
    expect(page.find('[data-test="sample-questions"]').exists()).toBe(false);
  });

  it('stops an answer being written and is ready for another question', async () => {
    const first = controlledAnswer();
    askMock.mockImplementationOnce(first.events);
    const page = await open(CODEX_ONLY);
    await typeAndSend(page, 'first');
    first.send(CONTEXT_EVENT);
    first.send(textEvent('partial'));
    await flushPromises();

    await page.find('[data-test="send-or-stop"]').trigger('click');
    await flushPromises();

    expect(page.find('[data-test="answer-text"]').text()).toBe('partial');
    expect(page.find('[data-test="answer-stopped"]').exists()).toBe(true);

    const second = controlledAnswer();
    askMock.mockImplementationOnce(second.events);
    await typeAndSend(page, 'second');
    expect(askMock).toHaveBeenLastCalledWith({ question: 'second', program: 'codex' }, expect.any(AbortSignal));
  });

  it('keeps the text so far and shows the error under it when the answer breaks off', async () => {
    const answer = controlledAnswer();
    askMock.mockImplementation(answer.events);
    const page = await open(CODEX_ONLY);
    await typeAndSend(page, 'q');
    answer.send(CONTEXT_EVENT);
    answer.send(textEvent('so far'));
    await flushPromises();

    answer.fail({ source: 'backend', code: 'stream_error', message: 'the program stopped' });
    await flushPromises();

    expect(page.find('[data-test="answer-text"]').text()).toBe('so far');
    expect(page.find('[data-test="answer-error"]').text()).toContain('the program stopped');
  });

  it('sends each question on its own and keeps earlier exchanges on screen', async () => {
    const first = controlledAnswer();
    askMock.mockImplementationOnce(first.events);
    const page = await open(CODEX_ONLY);
    await typeAndSend(page, 'first');
    first.send(CONTEXT_EVENT);
    first.send(textEvent('one'));
    first.end();
    await flushPromises();

    const second = controlledAnswer();
    askMock.mockImplementationOnce(second.events);
    await typeAndSend(page, 'second');
    second.send(CONTEXT_EVENT);
    second.send(textEvent('two'));
    second.end();
    await flushPromises();

    expect(askMock).toHaveBeenLastCalledWith({ question: 'second', program: 'codex' }, expect.any(AbortSignal));
    expect(page.findAll('[data-test="answer-text"]').map(text => text.text())).toEqual(['one', 'two']);
  });
});

describe('which program answers', () => {
  it('with one logged in, names it in the address and offers only it', async () => {
    const page = await open(CODEX_ONLY);

    expect(router.currentRoute.value.query.program).toBe('codex');
    const picker = page.find('[data-test="program-picker"]');
    expect(picker.text()).toContain('Claude Code');
    expect(picker.text()).toContain('Not logged in');
    expect(picker.findAll('button[disabled], input[disabled]').length).toBeGreaterThan(0);
  });

  it('with both logged in, lets the user choose, keeps the choice in the address and answers with it', async () => {
    askMock.mockImplementation(controlledAnswer().events);
    const page = await open(BOTH);
    expect(router.currentRoute.value.query.program).toBe('claude-code');

    await router.push({ query: { ...router.currentRoute.value.query, program: 'codex' } });
    await flushPromises();
    await typeAndSend(page, 'q');

    expect(askMock).toHaveBeenCalledWith({ question: 'q', program: 'codex' }, expect.any(AbortSignal));
  });

  it('corrects an address naming a program that is not logged in', async () => {
    await open(CODEX_ONLY, '/?lang=en&program=claude-code');
    expect(router.currentRoute.value.query.program).toBe('codex');
  });
});

describe('the language in the address', () => {
  it('opens in the language the address names, and writes the default when it names none', async () => {
    const page = await open(CODEX_ONLY, '/');
    expect(router.currentRoute.value.query.lang).toBe('zh-TW');
    expect(page.find('[data-test="sample-questions"]').text()).toContain('聯準會在這近半年的動向哪些行為導致股市動盪');
  });
});
