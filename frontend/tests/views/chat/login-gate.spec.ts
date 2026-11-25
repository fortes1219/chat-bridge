import { afterEach, beforeEach, describe, expect, it, onTestFinished, vi } from 'vitest';
import { flushPromises, type VueWrapper } from '@vue/test-utils';
import type { ProgramState } from '@/service/api/programs';
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

import ChatPage from '@/views/chat/ChatPage.vue';

const NEITHER: ProgramState[] = [
  { program: 'claude-code', state: 'not installed' },
  { program: 'codex', state: 'not logged in' }
];
const CODEX_IN: ProgramState[] = [
  { program: 'claude-code', state: 'unknown' },
  { program: 'codex', state: 'logged in' }
];

let wrapper: VueWrapper | undefined;

beforeEach(() => {
  getProgramsMock.mockReset();
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
});

async function open(language: 'en' | 'zh-TW' = 'en'): Promise<VueWrapper> {
  wrapper = (await mountView(ChatPage, { path: `/?lang=${language}` })).wrapper;
  await flushPromises();
  return wrapper;
}

function checkAgainButton(page: VueWrapper) {
  const button = page.find('[data-test="check-again"]');
  return button.exists() ? button : undefined;
}

describe('the login screen', () => {
  it('draws neither the chat nor the strategy screen while the states are being read', async () => {
    getProgramsMock.mockReturnValue(new Promise(() => {}));
    const page = await open();

    expect(page.find('[data-test="login-gate"]').text()).toContain('Checking whether Claude Code and Codex');
    expect(page.find('[data-test="chat-open"]').exists()).toBe(false);
    expect(checkAgainButton(page)).toBeUndefined();
  });

  it('with neither logged in, shows each program’s state and next step, and nothing else', async () => {
    getProgramsMock.mockResolvedValue(NEITHER);
    const page = await open();

    const claude = page.find('[data-test="login-program-claude-code"]').text();
    expect(claude).toContain('Not installed');
    expect(claude).toContain('Install Claude Code with a command below');
    const claudeCommands = page.findAll('[data-test="login-program-claude-code"] [data-test="command"]');
    expect(claudeCommands.map(command => command.text())).toEqual([
      'irm https://claude.ai/install.ps1 | iex',
      'curl -fsSL https://claude.ai/install.sh | bash',
      'claude auth login'
    ]);

    const codex = page.find('[data-test="login-program-codex"]');
    expect(codex.text()).toContain('Not logged in');
    expect(codex.findAll('[data-test="command"]').map(command => command.text())).toEqual(['codex login']);

    expect(checkAgainButton(page)).toBeDefined();
    expect(page.find('[data-test="chat-open"]').exists()).toBe(false);
  });

  it('never takes a state it could not read for a login', async () => {
    getProgramsMock.mockResolvedValue([
      { program: 'claude-code', state: 'unknown' },
      { program: 'codex', state: 'unknown' }
    ]);
    const page = await open();

    expect(page.find('[data-test="login-program-codex"]').text()).toContain('Could not be read');
    expect(page.find('[data-test="chat-open"]').exists()).toBe(false);
  });

  it('opens the page when one program is logged in', async () => {
    getProgramsMock.mockResolvedValue(CODEX_IN);
    const page = await open();

    expect(page.find('[data-test="login-gate"]').exists()).toBe(false);
    expect(page.find('[data-test="chat-open"]').exists()).toBe(true);
  });

  it('opens after a login and one press of the button, without a reload', async () => {
    getProgramsMock.mockResolvedValueOnce(NEITHER);
    const page = await open();
    let answer!: (states: ProgramState[]) => void;
    getProgramsMock.mockReturnValueOnce(new Promise(resolve => (answer = resolve)));

    await checkAgainButton(page)!.trigger('click');
    await flushPromises();
    // While it checks, the button is disabled and spins.
    expect(checkAgainButton(page)!.attributes('disabled')).toBeDefined();

    answer(CODEX_IN);
    await flushPromises();

    expect(getProgramsMock).toHaveBeenCalledTimes(2);
    expect(page.find('[data-test="chat-open"]').exists()).toBe(true);
  });

  it('does not check by itself when the window regains focus or comes back online', async () => {
    getProgramsMock.mockResolvedValue(NEITHER);
    await open();

    window.dispatchEvent(new Event('focus'));
    window.dispatchEvent(new Event('online'));
    document.dispatchEvent(new Event('visibilitychange'));
    await flushPromises();

    expect(getProgramsMock).toHaveBeenCalledTimes(1);
  });

  it('says the service cannot be reached when the states cannot be read, and offers the same button', async () => {
    // A contract error is not retried, so the screen shows it at once; a network error shows it
    // after the shared client's two retries.
    getProgramsMock.mockRejectedValue({ source: 'contract', code: 'contract_error', message: 'x' });
    const page = await open();

    expect(page.find('[data-test="login-gate"]').text()).toContain('The chat service cannot be reached');
    expect(checkAgainButton(page)).toBeDefined();
    expect(page.find('[data-test="chat-open"]').exists()).toBe(false);
  });

  it('with the service down, keeps reading through two retries, then says it cannot be reached', async () => {
    vi.useFakeTimers();
    onTestFinished(() => {
      vi.useRealTimers();
    });
    getProgramsMock.mockRejectedValue({ source: 'network', code: 'network_error', message: 'x' });
    const page = (await mountView(ChatPage)).wrapper;
    wrapper = page;
    await vi.advanceTimersByTimeAsync(0);

    expect(page.find('[data-test="login-gate"]').text()).toContain('Checking whether');

    // TanStack Query waits 1 s, then 2 s, between tries.
    await vi.advanceTimersByTimeAsync(3_100);

    expect(getProgramsMock).toHaveBeenCalledTimes(3);
    expect(page.find('[data-test="login-gate"]').text()).toContain('The chat service cannot be reached');
  });

  it('copies a login command and never runs it', async () => {
    // As a browser that lets the page write to the clipboard; removed again after the test.
    const written: ClipboardItem[] = [];
    const write = vi.fn(async (items: ClipboardItem[]) => void written.push(...items));
    const permission = Object.assign(new EventTarget(), { state: 'granted' });
    Object.defineProperty(window.navigator, 'clipboard', { value: { write }, configurable: true });
    Object.defineProperty(window.navigator, 'permissions', {
      value: { query: async () => permission },
      configurable: true
    });
    onTestFinished(() => {
      Reflect.deleteProperty(window.navigator, 'clipboard');
      Reflect.deleteProperty(window.navigator, 'permissions');
    });
    getProgramsMock.mockResolvedValue(NEITHER);
    const page = await open();

    await page.find('[data-test="login-program-codex"] [data-test="copy-command"]').trigger('click');
    await flushPromises();

    expect(write).toHaveBeenCalledTimes(1);
    const copied = await (await written[0]!.getType('text/plain')).text();
    expect(copied).toBe('codex login');
    expect(getProgramsMock).toHaveBeenCalledTimes(1);
  });

  it('is drawn in Traditional Chinese too', async () => {
    getProgramsMock.mockResolvedValue(NEITHER);
    const page = await open('zh-TW');

    expect(page.find('[data-test="login-gate"]').text()).toContain('請先登入 Claude Code 或 Codex');
    expect(page.find('[data-test="login-program-codex"]').text()).toContain('未登入');
  });

  it('switches its language from the bar on top, before anyone has logged in', async () => {
    getProgramsMock.mockResolvedValue(NEITHER);
    const page = await open('zh-TW');

    page.findComponent({ name: 'Select' }).vm.$emit('update:modelValue', 'en');
    await flushPromises();

    expect(page.find('[data-test="login-gate"]').text()).toContain('Log in to Claude Code or Codex');
  });
});
