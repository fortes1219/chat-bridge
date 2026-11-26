export type Locale = 'zh-TW' | 'en'

export const retrievalExamples = {
  'multi-topic-query': {
    originalTopK: 8,
    original: 0,
    recovered: 7,
    expected: 9,
    topics: {
      'zh-TW': ['AI 資本支出', '利率政策', 'ETF 行情'],
      en: ['AI spending', 'Rate policy', 'ETF moves'],
    },
  },
} as const

export const allocationExamples = {
  'sample-profile': [
    { symbol: '0050', current: 40, proposed: 35 },
    { symbol: '2330', current: 25, proposed: 25 },
    { symbol: 'MSFT', current: 20, proposed: 20 },
    { symbol: 'CASH', current: 15, proposed: 20 },
  ],
} as const

export const evaluation = [
  { id: 'development', label: { 'zh-TW': '開發題 · 20 題', en: 'Development set · 20 questions' }, before: 45, after: 59, total: 63 },
  { id: 'held-out', label: { 'zh-TW': '保留題 · 7 題', en: 'Held-out set · 7 questions' }, before: 20, after: 26, total: 28 },
  { id: 'reviewed', label: { 'zh-TW': '保留題 · 複核標註', en: 'Held-out set · reviewed labels' }, before: 19, after: 25, total: 27 },
] as const
