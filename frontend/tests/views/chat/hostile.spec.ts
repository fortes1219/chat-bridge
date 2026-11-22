import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, type DOMWrapper, type VueWrapper } from '@vue/test-utils';
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

/** What a hostile document can make an answer say, quoted or steered. */
const HOSTILE_ANSWER = [
  'The Fed cut rates [1].',
  '',
  `<img src=x onerror="alert('img')">`,
  `<script>alert('script')</script>`,
  `[click me](javascript:alert('link'))`,
  '[data link](data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==)',
  '<iframe src="https://evil.example/frame"></iframe>',
  '<object data="https://evil.example/o"></object><embed src="https://evil.example/e">',
  '<link rel="stylesheet" href="https://evil.example/s.css">',
  '<style>body { background: url(https://evil.example/b.png) }</style>',
  '![pixel](https://evil.example/pixel.png?leak=1)',
  '![inline](data:image/png;base64,iVBORw0KGgo=)',
  '<div style="background:url(https://evil.example/c.png)">styled</div>',
  `<a href="https://example.com" onclick="alert('a')">site</a>`,
  ':icon{name="i-mdi-home"}',
  '',
  '[a source page](https://example.com/page) and **bold**.'
].join('\n');

const HOSTILE_CONTEXT: ChatEvent = {
  ...CONTEXT_EVENT,
  context: {
    ...CONTEXT_EVENT.context,
    sources: [
      {
        number: 1,
        file: 'data/truth/<b>x</b>.md',
        title: `<script>alert('title')</script>`,
        heading: `<img src=x onerror="alert('heading')">`,
        event_date: null
      }
    ],
    disclaimer: `<img src=x onerror="alert('notice')">`
  }
};

const EXECUTABLE_OR_LOADING = 'script, iframe, object, embed, link, style, img, form, base, meta, svg, video, audio';

let wrapper: VueWrapper | undefined;
const alertSpy = vi.fn();
const fetchSpy = vi.fn();

beforeEach(() => {
  getProgramsMock.mockReset().mockResolvedValue([
    { program: 'claude-code', state: 'not logged in' },
    { program: 'codex', state: 'logged in' }
  ]);
  askMock.mockReset().mockImplementation(async function* () {
    yield HOSTILE_CONTEXT;
    yield textEvent(HOSTILE_ANSWER);
  });
  alertSpy.mockReset();
  fetchSpy.mockReset();
  vi.stubGlobal('alert', alertSpy);
  vi.stubGlobal('confirm', alertSpy);
  vi.stubGlobal('prompt', alertSpy);
  vi.stubGlobal('fetch', fetchSpy);
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
  vi.unstubAllGlobals();
});

async function askHostile(): Promise<VueWrapper> {
  ({ wrapper } = await mountView(ChatPage));
  await flushPromises();
  await wrapper.find('textarea[data-test="question-box"]').setValue('q');
  await wrapper.find('form').trigger('submit');
  await flushPromises();
  return wrapper;
}

/** Every attribute name in a subtree, for the event handler check. */
function attributeNames(root: DOMWrapper<Element>): string[] {
  return [root.element, ...root.element.querySelectorAll('*')].flatMap(element => element.getAttributeNames());
}

describe('hostile content in an answer and its sources', () => {
  it('runs nothing, opens no dialog and loads nothing', async () => {
    const page = await askHostile();

    expect(alertSpy).not.toHaveBeenCalled();
    expect(fetchSpy).not.toHaveBeenCalled();
    for (const part of ['answer-text', 'sources', 'notice']) {
      const area = page.find(`[data-test="${part}"]`);
      expect(area.exists()).toBe(true);
      expect(area.findAll(EXECUTABLE_OR_LOADING)).toHaveLength(0);
      expect(attributeNames(area).filter(name => name.toLowerCase().startsWith('on'))).toEqual([]);
      expect(attributeNames(area)).not.toContain('style');
    }
  });

  it('keeps only https and mailto links, so no link in an answer runs code', async () => {
    const page = await askHostile();

    // The raw <a onclick> stays text; only the Markdown link with an https address is a link.
    const hrefs = page.findAll('[data-test="answer-text"] a').map(link => link.attributes('href') ?? '');
    expect(hrefs).toEqual(['https://example.com/page']);
  });

  it('shows the hostile HTML of the sources and the notice as text', async () => {
    const page = await askHostile();

    expect(page.find('[data-test="source-1"]').text()).toBe(
      `[1] data/truth/<b>x</b>.md · <img src=x onerror="alert('heading')"> · No date`
    );
    expect(page.find('[data-test="notice"]').text()).toBe(`<img src=x onerror="alert('notice')">`);
  });

  it('still formats ordinary Markdown and keeps citations as written', async () => {
    const page = await askHostile();

    const answer = page.find('[data-test="answer-text"]');
    expect(answer.text()).toContain('The Fed cut rates [1].');
    expect(answer.find('strong').text()).toBe('bold');
    expect(answer.text()).toContain(`<script>alert('script')</script>`);
  });

  it('draws lists and tables the model writes, not their raw symbols', async () => {
    askMock.mockImplementation(async function* () {
      yield CONTEXT_EVENT;
      const lines = [
        '- first',
        '- second',
        '',
        '1. one',
        '2. two',
        '',
        '| Index | Change |',
        '|---|---|',
        '| SOX | -3% |'
      ];
      yield textEvent(lines.join('\n'));
    });
    const page = await askHostile();

    const answer = page.find('[data-test="answer-text"]');
    expect(answer.findAll('ul li').map(item => item.text())).toEqual(['first', 'second']);
    expect(answer.findAll('ol li').map(item => item.text())).toEqual(['one', 'two']);
    expect(answer.findAll('table th').map(cell => cell.text())).toEqual(['Index', 'Change']);
    expect(answer.findAll('table td').map(cell => cell.text())).toEqual(['SOX', '-3%']);
    expect(answer.text()).not.toContain('|---|');
  });
});
