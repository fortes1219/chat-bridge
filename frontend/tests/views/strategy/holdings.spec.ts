import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, ref } from 'vue';
import { flushPromises, type VueWrapper } from '@vue/test-utils';
import type { HoldingsInput, Strategy } from '@/service/api/strategy';
import type { AppError } from '@/service/error';
import { STRATEGY } from '../../helpers/strategy';
import { mountView } from '../../helpers/mount';

const getStrategyMock = vi.fn<() => Promise<Strategy>>();
const saveHoldingsMock = vi.fn<(input: HoldingsInput) => Promise<Strategy>>();
vi.mock('@/service/api/strategy', () => ({
  getStrategy: () => getStrategyMock(),
  decideProposal: vi.fn(),
  saveRules: vi.fn(),
  saveHoldings: (input: HoldingsInput) => saveHoldingsMock(input)
}));

import StrategyPanel from '@/views/strategy/StrategyPanel.vue';
import { provideStrategyEditors } from '@/views/strategy/composables/useStrategyEditors';

/** The fixture's holdings as the page sends them: no market or currency, cash apart. */
const SAVED: HoldingsInput = {
  holdings: STRATEGY.holdings
    .filter(holding => holding.symbol !== 'CASH')
    .map(({ symbol, names, quantity, average_cost }) => ({ symbol, names, quantity, average_cost })),
  cash: STRATEGY.holdings.find(holding => holding.symbol === 'CASH')!.quantity
};

let wrapper: VueWrapper | undefined;

beforeEach(() => {
  getStrategyMock.mockReset().mockResolvedValue(STRATEGY);
  saveHoldingsMock.mockReset();
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
  document.body.innerHTML = '';
});

// Mounted on its own, the panel is in the page's default language, Traditional Chinese.
async function openEditor(): Promise<VueWrapper> {
  ({ wrapper } = await mountView(StrategyPanel));
  await flushPromises();
  await wrapper.find('[data-test="holdings-edit"]').trigger('click');
  return wrapper;
}

async function type(page: VueWrapper, test: string, value: string): Promise<void> {
  await page.find(`[data-test="${test}"]`).setValue(value);
}

function saveButton(page: VueWrapper) {
  return page.find('[data-test="holdings-save"]');
}

describe('the holdings editor', () => {
  it('lists each holding but cash, with the cash apart, and sends nothing unchanged', async () => {
    const page = await openEditor();

    expect(page.findAll('[data-test^="holding-row-"]')).toHaveLength(SAVED.holdings.length);
    expect((page.find('[data-test="holding-cash"]').element as HTMLInputElement).value).toBe(SAVED.cash);
    expect(saveButton(page).attributes('disabled')).toBeDefined();
  });

  it('adds a holding named in one language for both, removes one, sets the cash and saves', async () => {
    saveHoldingsMock.mockResolvedValue(STRATEGY);
    const page = await openEditor();
    const added = SAVED.holdings.length;

    await page.find('[data-test="holding-add"]').trigger('click');
    await type(page, `holding-symbol-${added}`, ' aapl ');
    await type(page, `holding-name-${added}`, '蘋果');
    await type(page, `holding-quantity-${added}`, '5');
    await type(page, `holding-cost-${added}`, '180.25');
    await page.find('[data-test="holding-remove-0"]').trigger('click');
    await type(page, 'holding-cash', '123456.78');
    await saveButton(page).trigger('click');
    await flushPromises();

    expect(saveHoldingsMock).toHaveBeenCalledTimes(1);
    expect(saveHoldingsMock).toHaveBeenCalledWith({
      holdings: [
        ...SAVED.holdings.slice(1),
        { symbol: 'AAPL', names: { 'zh-TW': '蘋果', en: '蘋果' }, quantity: '5', average_cost: '180.25' }
      ],
      cash: '123456.78'
    });
    expect(page.find('[data-test="holdings-editor"]').exists()).toBe(false);
  });

  it('changes only the shown language’s name of a holding named in both', async () => {
    saveHoldingsMock.mockResolvedValue(STRATEGY);
    const page = await openEditor();

    await type(page, 'holding-name-0', '台灣積體電路');
    await saveButton(page).trigger('click');
    await flushPromises();

    const sent = saveHoldingsMock.mock.calls[0]![0];
    expect(sent.holdings[0]!.names).toEqual({ ...SAVED.holdings[0]!.names, 'zh-TW': '台灣積體電路' });
  });

  it('stays open with the person’s changes and says why when the service refuses them', async () => {
    const refused: AppError = {
      source: 'backend',
      code: 'rejected',
      reason: 'holding_symbol',
      item: 1,
      message: "holding 1: '0700.HK' is not a Taiwan listing",
      status: 422
    };
    saveHoldingsMock.mockRejectedValue(refused);
    const page = await openEditor();

    await type(page, 'holding-symbol-0', '0700.HK');
    await saveButton(page).trigger('click');
    await flushPromises();

    const error = page.find('[data-test="holdings-error"]');
    expect(error.text()).toContain('第 1 檔：');
    expect(error.text()).toContain('.TW');
    expect(error.text()).not.toContain('is not');
    expect(page.find('[data-test="holding-row-0"]').classes()).toContain('border-error');
    expect(page.find('[data-test="holding-row-1"]').classes()).not.toContain('border-error');
    expect(page.find('[data-test="holdings-editor"]').exists()).toBe(true);
  });

  it('leaves the holdings as they were when the person cancels', async () => {
    const page = await openEditor();

    await type(page, 'holding-quantity-0', '1');
    await page.find('[data-test="holdings-cancel"]').trigger('click');
    await page.find('[data-test="holdings-edit"]').trigger('click');
    await flushPromises();

    expect(saveHoldingsMock).not.toHaveBeenCalled();
    expect(saveButton(page).attributes('disabled')).toBeDefined();
  });
});

describe('a draft', () => {
  it('outlives the panel being drawn again, as when the window crosses the narrow width', async () => {
    // As the chat page does: it keeps the editors and draws the panel in one of two places.
    const shown = ref(true);
    const Page = defineComponent({
      setup() {
        provideStrategyEditors();
        return () => (shown.value ? h(StrategyPanel) : null);
      }
    });
    ({ wrapper } = await mountView(Page));
    await flushPromises();
    await wrapper.find('[data-test="holdings-edit"]').trigger('click');
    await type(wrapper, 'holding-quantity-0', '1234');
    await wrapper.find('[data-test="rules-edit"]').trigger('click');

    shown.value = false;
    await flushPromises();
    shown.value = true;
    await flushPromises();

    expect((wrapper.find('[data-test="holding-quantity-0"]').element as HTMLInputElement).value).toBe('1234');
    expect(wrapper.find('[data-test="rule-editor"]').exists()).toBe(true);
    expect(saveButton(wrapper).attributes('disabled')).toBeUndefined();
  });
});

describe('the targets’ total', () => {
  it('is said only when it is not 100%', async () => {
    getStrategyMock.mockResolvedValue({ ...STRATEGY, targets_total: 92 });
    ({ wrapper } = await mountView(StrategyPanel));
    await flushPromises();

    expect(wrapper.find('[data-test="targets-total"]').text()).toContain('92%');
  });

  it('is not said when it is 100%', async () => {
    ({ wrapper } = await mountView(StrategyPanel));
    await flushPromises();

    expect(wrapper.find('[data-test="targets-total"]').exists()).toBe(false);
  });
});
