import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, type VueWrapper } from '@vue/test-utils';
import { useStrategySocketStore } from '@/stores/strategy-socket';
import type { Strategy, Valuation } from '@/service/api/strategy';
import { STRATEGY, VALUATION } from '../../helpers/strategy';
import { latestSocket } from '../../helpers/socket';
import { mountView } from '../../helpers/mount';

const getStrategyMock = vi.fn<() => Promise<Strategy>>();
vi.mock('@/service/api/strategy', () => ({
  getStrategy: () => getStrategyMock(),
  decideProposal: vi.fn()
}));

import StrategyPanel from '@/views/strategy/StrategyPanel.vue';
import AllocationDonut from '@/views/strategy/components/AllocationDonut.vue';

/** TSMC's price could not be had: it is left out, and the totals are of NVIDIA and cash. */
const TSMC_MISSING: Valuation = {
  ...VALUATION,
  total_value: '1464000.00',
  profit: '180960.00',
  profit_percent: '26.49',
  left_out: ['2330.TW'],
  holdings: [
    { symbol: '2330.TW', price: null, value: null, weight: null, profit: null, profit_percent: null },
    { ...VALUATION.holdings[1]!, weight: '59.02' },
    { ...VALUATION.holdings[2]!, weight: '40.98' }
  ],
  quotes: [{ ...VALUATION.quotes[0]!, price: null, change_percent: null, at: null }, ...VALUATION.quotes.slice(1)]
};

/** The same strategy after TSMC moved to 1,490. */
const TSMC_UP: Strategy = {
  ...STRATEGY,
  valuation: {
    ...VALUATION,
    total_value: '4444000.00',
    holdings: [
      { ...VALUATION.holdings[0]!, price: '1490', value: '2980000.00', weight: '67.06' },
      { ...VALUATION.holdings[1]!, weight: '19.44' },
      { ...VALUATION.holdings[2]!, weight: '13.50' }
    ]
  }
};

let wrapper: VueWrapper | undefined;

beforeEach(() => {
  getStrategyMock.mockReset();
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
  document.body.innerHTML = '';
});

async function mountPanel(strategy: Strategy): Promise<VueWrapper> {
  getStrategyMock.mockResolvedValue(strategy);
  ({ wrapper } = await mountView(StrategyPanel));
  await flushPromises();
  return wrapper;
}

function card(page: VueWrapper, key: string): string {
  return page.find(`[data-test="card-${key}"] [data-test="card-value"]`).text();
}

function donutShares(page: VueWrapper): unknown {
  return page.findComponent(AllocationDonut).findComponent({ name: 'Chart' }).props('data');
}

// Mounted on its own, the panel is in the page's default language, Traditional Chinese.
describe('the strategy panel with prices', () => {
  it('shows the cards, the allocation, the holdings with profit and loss, and the quotes with their times', async () => {
    const page = await mountPanel(STRATEGY);

    expect(card(page, 'total')).toBe('$4,424,000');
    expect(page.find('[data-test="card-change"]').text()).toContain('-0.14%');
    expect(card(page, 'profit')).toBe('-$819,040');
    expect(page.find('[data-test="card-profit"]').text()).toContain('-17.64%');
    expect(donutShares(page)).toEqual([
      { name: '台積電', share: 66.91 },
      { name: '輝達', share: 19.53 },
      { name: '現金', share: 13.56 }
    ]);
    const table = page.find('[data-test="holdings-table"]').text();
    for (const shown of ['1,480', '$2,960,000', '66.91%', '50%', '-$1,000,000', '-25.25%', '+26.49%']) {
      expect(table).toContain(shown);
    }
    expect(page.find('[data-test="quote-NVDA"]').text()).toContain('2026-11-21 日線');
    expect(page.find('[data-test="quote-2330.TW"]').text()).toContain('延遲 20 分鐘');
    expect(page.find('[data-test="quote-NVDA"]').text()).toContain('即時');
    expect(page.find('[data-test="quote-TWD=X"]').text()).toContain('即時');
    const source = page.find('[data-test="price-source"]');
    expect(source.text()).toContain('價格來自 Yahoo Finance，不是交易所官方的資料');
    expect(source.find('a').attributes('href')).toBe(VALUATION.source.terms_url);
  });

  it('draws a missing price as missing, not zero, and names what the totals leave out', async () => {
    const page = await mountPanel({ ...STRATEGY, valuation: TSMC_MISSING });

    expect(page.find('[data-test="left-out"]').text()).toContain('台積電');
    expect(page.find('[data-test="quote-^SOX"] [data-test="quote-price"]').text()).toBe('--');
    expect(page.find('[data-test="quote-2330.TW"] [data-test="quote-price"]').text()).toBe('--');
    const tsmc = page.find('[data-test="holdings-table"] tbody tr').text();
    expect(tsmc).toContain('--');
    expect(tsmc).not.toMatch(/\$0\b/);
    expect(donutShares(page)).toEqual([
      { name: '輝達', share: 59.02 },
      { name: '現金', share: 40.98 }
    ]);
  });

  it('updates the cards, the donut and the holdings from a strategy event, without asking again', async () => {
    const page = await mountPanel(STRATEGY);

    latestSocket().receive('strategy', TSMC_UP);
    await flushPromises();

    expect(card(page, 'total')).toBe('$4,444,000');
    expect(donutShares(page)).toContainEqual({ name: '台積電', share: 67.06 });
    expect(page.find('[data-test="holdings-table"]').text()).toContain('1,490');
    expect(getStrategyMock).toHaveBeenCalledTimes(1);
  });

  it('does not draw an event that does not match the strategy, and counts it', async () => {
    const page = await mountPanel(STRATEGY);

    latestSocket().receive('strategy', { ...TSMC_UP, valuation: { ...TSMC_UP.valuation, total_value: 'lots' } });
    await flushPromises();

    expect(card(page, 'total')).toBe('$4,424,000');
    expect(useStrategySocketStore().invalidPayloadCount).toBe(1);
    // Said on the screen, so a failed update does not look like a quiet market.
    expect(page.find('[data-test="invalid-updates"]').text()).toContain('1 次更新');
  });

  it('says whether prices are updating as the connection comes and goes', async () => {
    const page = await mountPanel(STRATEGY);
    const connection = () => page.find('[data-test="connection"]').text();

    expect(connection()).toBe('連線中…');
    latestSocket().receive('connect');
    await flushPromises();
    expect(connection()).toBe('更新中');
    latestSocket().receive('disconnect');
    await flushPromises();
    expect(connection()).toBe('連線中…');
  });

  it('says when the service is not connected to the price source, though the page is', async () => {
    const page = await mountPanel({ ...STRATEGY, valuation: { ...VALUATION, live: false } });

    latestSocket().receive('connect');
    await flushPromises();

    expect(page.find('[data-test="connection"]').text()).toBe('沒有連上行情來源，價格停在顯示的時間');
  });

  it('names a holding left out of the change and says what the change is', async () => {
    const page = await mountPanel({
      ...STRATEGY,
      valuation: { ...VALUATION, change: '-30000.00', change_percent: '-0.84', change_left_out: ['NVDA'] }
    });

    expect(page.find('[data-test="change-left-out"]').text()).toContain('輝達');
    expect(page.find('[data-test="change-note"]').text()).toContain('自己市場的前一個收盤');
    expect(page.find('[data-test="card-change"]').text()).toContain('-0.84%');
  });

  it('closes the connection when the panel goes away', async () => {
    const page = await mountPanel(STRATEGY);
    const socket = latestSocket();

    page.unmount();
    wrapper = undefined;

    expect(socket.disconnects).toBe(1);
    expect(socket.listeners('strategy')).toBe(0);
    expect(useStrategySocketStore().connectionState).toBe('disconnected');
  });
});
