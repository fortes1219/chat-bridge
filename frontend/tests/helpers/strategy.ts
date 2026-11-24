import type { Proposal, Strategy } from '@/service/api/strategy';

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
  proposal: null,
  notice: { 'zh-TW': '模擬範例', en: 'simulated sample' }
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
