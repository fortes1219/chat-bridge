import type { Proposal, RuleChecks, Strategy, Valuation } from '@/service/api/strategy';

const LIVE = { basis: 'live', time: '2026-11-24T01:30:00Z', day: null } as const;

/**
 * The holdings below at TSMC 1,480 (live), NVIDIA 180 (the US close of 2026-11-21) and 32 Taiwan
 * dollars a US dollar, as the service computes them; the Philadelphia index has no price.
 */
export const VALUATION: Valuation = {
  currency: 'TWD',
  live: true,
  total_value: '4424000.00',
  change: '-6000.00',
  change_percent: '-0.14',
  profit: '-819040.00',
  profit_percent: '-17.64',
  change_left_out: [],
  left_out: [],
  prices_at: LIVE,
  holdings: [
    {
      symbol: '2330.TW',
      price: '1480',
      value: '2960000.00',
      weight: '66.91',
      profit: '-1000000.00',
      profit_percent: '-25.25'
    },
    { symbol: 'NVDA', price: '180', value: '864000.00', weight: '19.53', profit: '180960.00', profit_percent: '26.49' },
    { symbol: 'CASH', price: null, value: '600000.00', weight: '13.56', profit: null, profit_percent: null }
  ],
  quotes: [
    {
      symbol: '2330.TW',
      names: { 'zh-TW': '台積電', en: 'TSMC' },
      price: '1480',
      change_percent: '-1.00',
      at: LIVE,
      delay_minutes: 20
    },
    {
      symbol: 'NVDA',
      names: { 'zh-TW': '輝達', en: 'NVIDIA' },
      price: '180',
      change_percent: '2.86',
      at: { basis: 'daily', time: null, day: '2026-11-21' },
      delay_minutes: 0
    },
    {
      symbol: '^SOX',
      names: { 'zh-TW': '費城半導體指數', en: 'PHLX Semiconductor Index' },
      price: null,
      change_percent: null,
      at: null,
      delay_minutes: 0
    },
    {
      symbol: 'TWD=X',
      names: { 'zh-TW': '美元兌新台幣', en: 'US dollar in Taiwan dollars' },
      price: '32',
      change_percent: '0.31',
      at: LIVE,
      delay_minutes: 0
    }
  ],
  source: { name: 'Yahoo Finance', terms_url: 'https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html' }
};

/**
 * Three rules on the current targets below (TSMC 50, NVIDIA 30, cash 20), as the service checks
 * them: TSMC breaks the most per holding; the least per held holding and the US limit are met.
 */
export const RULE_CHECKS: RuleChecks = {
  met: 2,
  enabled: 3,
  rules: [
    {
      kind: 'max_holding_weight',
      limit_percent: 40,
      market: null,
      enabled: true,
      met: false,
      measured: 50,
      breaking: ['2330.TW']
    },
    {
      kind: 'min_holding_weight',
      limit_percent: 10,
      market: null,
      enabled: true,
      met: true,
      measured: 30,
      breaking: []
    },
    {
      kind: 'max_market_weight',
      limit_percent: 30,
      market: 'US',
      enabled: true,
      met: true,
      measured: 30,
      breaking: []
    }
  ]
};

/** The same rules on the proposal's targets (TSMC 40, NVIDIA 30, cash 30): all three are met. */
export const PROPOSED_RULE_CHECKS: RuleChecks = {
  met: 3,
  enabled: 3,
  rules: RULE_CHECKS.rules.map((check, index) =>
    index === 0 ? { ...check, met: true, measured: 40, breaking: [] } : check
  )
};

/** A strategy as the service sends it: two holdings and cash, no proposal. */
export const STRATEGY: Strategy = {
  holdings: [
    {
      symbol: '2330.TW',
      names: { 'zh-TW': '台積電', en: 'TSMC' },
      market: 'TW',
      currency: 'TWD',
      quantity: '2000',
      average_cost: '1980'
    },
    {
      symbol: 'NVDA',
      names: { 'zh-TW': '輝達', en: 'NVIDIA' },
      market: 'US',
      currency: 'USD',
      quantity: '150',
      average_cost: '142.3'
    },
    {
      symbol: 'CASH',
      names: { 'zh-TW': '現金', en: 'Cash' },
      market: null,
      currency: 'TWD',
      quantity: '600000',
      average_cost: '1'
    }
  ],
  targets: [
    { symbol: '2330.TW', current: 50 },
    { symbol: 'NVDA', current: 30 },
    { symbol: 'CASH', current: 20 }
  ],
  targets_total: 100,
  rule_checks: RULE_CHECKS,
  proposal: null,
  notice: { 'zh-TW': '模擬範例', en: 'simulated sample' },
  valuation: VALUATION
};

/** A checked proposal that moves ten points from TSMC to cash. */
export const PROPOSAL: Proposal = {
  id: 5,
  created_at: '2026-11-24T02:00:00Z',
  question: 'Lower my risk',
  program: 'codex',
  status: 'open',
  rows: [
    { symbol: '2330.TW', current: 50, proposed: 40, change: -10 },
    { symbol: 'NVDA', current: 30, proposed: 30, change: 0 },
    { symbol: 'CASH', current: 20, proposed: 30, change: 10 }
  ],
  rule_checks: PROPOSED_RULE_CHECKS,
  reasons: [{ text: 'The Fed raised rates.', sources: [1] }],
  sources: [
    {
      number: 1,
      file: 'data/truth/a.md',
      title: 'Fed raises rates',
      heading: '事件發生',
      heading_localizations: null,
      event_date: '2026-09-16'
    }
  ]
};
