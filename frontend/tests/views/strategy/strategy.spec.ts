import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, type VueWrapper } from '@vue/test-utils';
import type { ProgramState } from '@/service/api/programs';
import type { ChatEvent, ChatRequest } from '@/service/api/chat';
import type { DecideInput, Strategy } from '@/service/api/strategy';
import type { AppError } from '@/service/error';
import { CONTEXT_EVENT, textEvent } from '../../helpers/sse';
import { PROPOSAL, STRATEGY } from '../../helpers/strategy';
import { mountView } from '../../helpers/mount';

const getProgramsMock = vi.fn<() => Promise<ProgramState[]>>();
vi.mock('@/service/api/programs', () => ({
  getPrograms: () => getProgramsMock()
}));

const getStrategyMock = vi.fn<() => Promise<Strategy>>();
const decideMock = vi.fn<(input: DecideInput) => Promise<Strategy>>();
vi.mock('@/service/api/strategy', () => ({
  getStrategy: () => getStrategyMock(),
  decideProposal: (input: DecideInput) => decideMock(input)
}));

const askMock = vi.fn<(input: ChatRequest, signal?: AbortSignal) => AsyncGenerator<ChatEvent, void, undefined>>();
vi.mock('@/service/api/chat', () => ({
  ask: (input: ChatRequest, signal?: AbortSignal) => askMock(input, signal)
}));

import ChatPage from '@/views/chat/ChatPage.vue';
import StrategyPanel from '@/views/strategy/StrategyPanel.vue';

const CODEX: ProgramState[] = [
  { program: 'claude-code', state: 'not logged in' },
  { program: 'codex', state: 'logged in' }
];
const WITH_PROPOSAL: Strategy = { ...STRATEGY, proposal: PROPOSAL };
const ACCEPTED: Strategy = {
  ...STRATEGY,
  targets: PROPOSAL.rows.map(row => ({ symbol: row.symbol, current: row.proposed }))
};
const WIDE = 1280;
const NARROW = 800;

let wrapper: VueWrapper | undefined;

function setWidth(width: number): void {
  window.innerWidth = width;
  window.dispatchEvent(new Event('resize'));
}

beforeEach(() => {
  getProgramsMock.mockReset().mockResolvedValue(CODEX);
  getStrategyMock.mockReset();
  decideMock.mockReset();
  askMock.mockReset();
  setWidth(WIDE);
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
  document.body.innerHTML = '';
});

async function mountPanel(): Promise<VueWrapper> {
  ({ wrapper } = await mountView(StrategyPanel));
  await flushPromises();
  return wrapper;
}

// Mounted on its own, the panel is in the page's default language, Traditional Chinese.
describe('the strategy panel', () => {
  it('lists each holding’s current target and says the profile is a simulated sample', async () => {
    getStrategyMock.mockResolvedValue(STRATEGY);

    const page = await mountPanel();

    const table = page.find('[data-test="holdings-table"]');
    expect(table.text()).toContain('台積電');
    expect(table.text()).toContain('50%');
    expect(table.text()).toContain('現金');
    expect(page.find('[data-test="sample-notice"]').text()).toContain('模擬範例');
    expect(page.find('[data-test="proposal-diff"]').exists()).toBe(false);
  });

  it('shows the open proposal as current, proposed and change, with its reasons and sources', async () => {
    getStrategyMock.mockResolvedValue(WITH_PROPOSAL);

    const page = await mountPanel();

    const diff = page.find('[data-test="diff-table"]');
    expect(diff.text()).toContain('50%');
    expect(diff.text()).toContain('40%');
    expect(page.find('[data-test="change-2330.TW"]').text()).toBe('-10');
    expect(page.find('[data-test="change-CASH"]').text()).toBe('+10');
    expect(page.find('[data-test="change-NVDA"]').text()).toBe('0');
    expect(page.find('[data-test="reasons"]').text()).toContain('The Fed raised rates. [1]');
    expect(page.find('[data-test="proposal-sources"]').text()).toContain('[1] Fed raises rates');
    expect(page.find('[data-test="proposed-by"]').text()).toContain('Codex');
    expect(page.find('[data-test="no-trade"]').exists()).toBe(true);
    // The holdings stay, with the current targets the proposal would change.
    expect(page.find('[data-test="holdings-table"]').text()).toContain('50%');
  });

  it('accepts once, sends the proposal’s number, and shows the strategy the service returns', async () => {
    getStrategyMock.mockResolvedValue(WITH_PROPOSAL);
    let resolve: (strategy: Strategy) => void = () => {};
    decideMock.mockReturnValue(new Promise(done => (resolve = done)));

    const page = await mountPanel();
    await page.find('[data-test="accept"]').trigger('click');
    await page.find('[data-test="accept"]').trigger('click');
    await page.find('[data-test="reject"]').trigger('click');
    resolve(ACCEPTED);
    await flushPromises();

    expect(decideMock).toHaveBeenCalledTimes(1);
    expect(decideMock).toHaveBeenCalledWith({ params: { id: 5 }, body: { decision: 'accept' } });
    expect(page.find('[data-test="proposal-diff"]').exists()).toBe(false);
    expect(page.find('[data-test="holdings-table"]').text()).toContain('40%');
  });

  it('rejects with the proposal’s number and shows the strategy unchanged', async () => {
    getStrategyMock.mockResolvedValue(WITH_PROPOSAL);
    decideMock.mockResolvedValue(STRATEGY);

    const page = await mountPanel();
    await page.find('[data-test="reject"]').trigger('click');
    await flushPromises();

    expect(decideMock).toHaveBeenCalledWith({ params: { id: 5 }, body: { decision: 'reject' } });
    expect(page.find('[data-test="holdings-table"]').text()).toContain('50%');
  });

  it('says so in the page’s words when the proposal was already decided', async () => {
    getStrategyMock.mockResolvedValue(WITH_PROPOSAL);
    const closed: AppError = {
      source: 'backend',
      code: 'rejected',
      reason: 'proposal_not_open',
      message: 'proposal 5 is accepted, not open',
      status: 409
    };
    decideMock.mockRejectedValue(closed);

    const page = await mountPanel();
    await page.find('[data-test="accept"]').trigger('click');
    await flushPromises();

    const error = page.find('[data-test="strategy-error"]');
    expect(error.text()).toContain('已經接受、否決，或被新的取代');
    expect(error.text()).not.toContain('proposal 5 is accepted');
  });
});

/** An answer whose events are all ready at once. */
function answerOf(...events: ChatEvent[]) {
  return async function* (): AsyncGenerator<ChatEvent, void, undefined> {
    for (const event of events) yield event;
  };
}

const REVISION_CONTEXT: ChatEvent = {
  ...CONTEXT_EVENT,
  context: { ...CONTEXT_EVENT.context, proposal_expected: true }
};

async function askOnPage(...events: ChatEvent[]): Promise<VueWrapper> {
  askMock.mockImplementation(answerOf(...events));
  ({ wrapper } = await mountView(ChatPage));
  await flushPromises();
  await wrapper.find('textarea[data-test="question-box"]').setValue('Lower my risk');
  await wrapper.find('form').trigger('submit');
  await flushPromises();
  return wrapper;
}

describe('a revision question on the chat page', () => {
  it('reads the strategy again once the proposal is kept, so the panel shows the difference', async () => {
    getStrategyMock.mockResolvedValueOnce(STRATEGY).mockResolvedValue(WITH_PROPOSAL);

    const page = await askOnPage(REVISION_CONTEXT, textEvent('Raise cash [1].'), {
      type: 'response.proposal',
      delta: null,
      context: null,
      usage: null,
      proposal: { proposal: PROPOSAL, refused: null }
    });

    expect(page.find('[data-test="strategy-panel"]').exists()).toBe(true);
    expect(page.find('[data-test="proposal-card"]').text()).toContain('A revised strategy is ready');
    expect(getStrategyMock).toHaveBeenCalledTimes(2);
    expect(page.find('[data-test="strategy-panel"] [data-test="diff-table"]').exists()).toBe(true);
  });

  it('says why a refused proposal was not shown and reads the strategy only once', async () => {
    getStrategyMock.mockResolvedValue(STRATEGY);

    const page = await askOnPage(REVISION_CONTEXT, textEvent('Raise cash [1].'), {
      type: 'response.proposal',
      delta: null,
      context: null,
      usage: null,
      proposal: { proposal: null, refused: { code: 'not_100', message: 'the targets add up to 90%, not 100%' } }
    });

    const refused = page.find('[data-test="proposal-refused"]');
    expect(refused.text()).toContain('its targets do not add up to 100%');
    expect(refused.text()).not.toContain('90%');
    expect(getStrategyMock).toHaveBeenCalledTimes(1);
  });

  it('once the proposal is accepted, its card says it no longer waits and has no button', async () => {
    getStrategyMock.mockResolvedValueOnce(STRATEGY).mockResolvedValue(WITH_PROPOSAL);
    decideMock.mockResolvedValue(ACCEPTED);

    const page = await askOnPage(REVISION_CONTEXT, textEvent('Raise cash [1].'), {
      type: 'response.proposal',
      delta: null,
      context: null,
      usage: null,
      proposal: { proposal: PROPOSAL, refused: null }
    });
    expect(page.find('[data-test="proposal-card"] button').exists()).toBe(true);
    await page.find('[data-test="strategy-panel"] [data-test="accept"]').trigger('click');
    await flushPromises();

    expect(page.find('[data-test="proposal-card"]').exists()).toBe(false);
    const closed = page.find('[data-test="proposal-closed"]');
    expect(closed.text()).toContain('no longer waiting for you');
    expect(closed.find('button').exists()).toBe(false);
    expect(getStrategyMock).toHaveBeenCalledTimes(2);
  });

  it('when a new proposal replaces the open one, only the new one’s card opens the strategy', async () => {
    const replacing = { ...PROPOSAL, id: 6 };
    getStrategyMock
      .mockResolvedValueOnce(STRATEGY)
      .mockResolvedValueOnce(WITH_PROPOSAL)
      .mockResolvedValue({ ...STRATEGY, proposal: replacing });
    const page = await askOnPage(REVISION_CONTEXT, textEvent('Raise cash [1].'), {
      type: 'response.proposal',
      delta: null,
      context: null,
      usage: null,
      proposal: { proposal: PROPOSAL, refused: null }
    });

    askMock.mockImplementation(
      answerOf(REVISION_CONTEXT, textEvent('Raise cash more [1].'), {
        type: 'response.proposal',
        delta: null,
        context: null,
        usage: null,
        proposal: { proposal: replacing, refused: null }
      })
    );
    await page.find('textarea[data-test="question-box"]').setValue('Lower it more');
    await page.find('form').trigger('submit');
    await flushPromises();

    expect(page.findAll('[data-test="proposal-closed"]')).toHaveLength(1);
    expect(page.findAll('[data-test="proposal-card"]')).toHaveLength(1);
    expect(page.find('[data-test="proposal-closed"]').find('button').exists()).toBe(false);
  });

  it('says no change was proposed, shows no difference and reads the strategy only once', async () => {
    getStrategyMock.mockResolvedValue(STRATEGY);

    const page = await askOnPage(REVISION_CONTEXT, textEvent('No change is needed [1].'), {
      type: 'response.proposal',
      delta: null,
      context: null,
      usage: null,
      proposal: { proposal: null, refused: null }
    });

    expect(page.find('[data-test="no-proposal"]').text()).toContain('No change to the strategy was proposed');
    expect(page.find('[data-test="proposal-card"]').exists()).toBe(false);
    expect(page.find('[data-test="strategy-panel"] [data-test="diff-table"]').exists()).toBe(false);
    expect(getStrategyMock).toHaveBeenCalledTimes(1);
  });

  it('says the answer and a proposal are being written while a revision answer is awaited', async () => {
    getStrategyMock.mockResolvedValue(STRATEGY);
    let release: () => void = () => {};
    askMock.mockImplementation(async function* () {
      yield REVISION_CONTEXT;
      await new Promise<void>(done => (release = done));
    });
    ({ wrapper } = await mountView(ChatPage));
    await flushPromises();
    await wrapper.find('textarea[data-test="question-box"]').setValue('Lower my risk');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    expect(wrapper.find('[data-test="waiting"]').text()).toContain('writing the answer and a revised strategy');
    release();
  });

  it('in a narrow window keeps the strategy in a slide-over that the proposal card opens', async () => {
    setWidth(NARROW);
    getStrategyMock.mockResolvedValue(WITH_PROPOSAL);

    const page = await askOnPage(REVISION_CONTEXT, textEvent('Raise cash [1].'), {
      type: 'response.proposal',
      delta: null,
      context: null,
      usage: null,
      proposal: { proposal: PROPOSAL, refused: null }
    });

    expect(page.find('[data-test="strategy-panel"]').exists()).toBe(false);
    expect(document.body.querySelector('[data-test="diff-table"]')).toBeNull();
    await page.find('[data-test="proposal-card"] button').trigger('click');
    await flushPromises();

    expect(document.body.querySelector('[data-test="diff-table"]')).not.toBeNull();
  });
});
