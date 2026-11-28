import type { ChatEvent } from '@/service/api/chat';

/** A response body that arrives in the given pieces, as the service's stream does. */
export function streamOf(...pieces: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const piece of pieces) {
        controller.enqueue(encoder.encode(piece));
      }
      controller.close();
    }
  });
}

/** One Server-Sent Event as FastAPI writes it: an optional name, then the data as JSON. */
export function sseEvent(data: unknown, name?: string): string {
  const head = name ? `event: ${name}\n` : '';
  return `${head}data: ${JSON.stringify(data)}\n\n`;
}

export const CONTEXT_EVENT: Extract<ChatEvent, { type: 'response.context' }> = {
  type: 'response.context',
  delta: null,
  context: {
    sources: [
      {
        number: 1,
        file: 'data/truth/a.md',
        title: 'T',
        heading: '影響股市證據',
        heading_localizations: { 'zh-TW': '影響股市證據', en: 'Evidence of market impact' },
        event_date: '2026-09-17'
      },
      {
        number: 2,
        file: 'data/truth/b.md',
        title: 'T2',
        heading: 'My own heading',
        heading_localizations: null,
        event_date: null
      }
    ],
    data_latest_date: '2026-09-17',
    disclaimer: { 'zh-TW': '聲明', en: 'notice' },
    program: 'codex',
    split_failed: false,
    proposal_expected: false,
    prices: null
  },
  proposal: null,
  usage: null
};

/** Prices looked up for a question: one Taiwan ETF read with a FinMind day, one US share not read. */
export const PRICES: NonNullable<(typeof CONTEXT_EVENT)['context']['prices']> = {
  lookups: [
    {
      symbol: '006208.TW',
      name: '富邦台50 006208',
      start_date: '2026-09-17',
      end_date: '2026-09-18',
      read_at: '2026-11-28T10:00:00+08:00',
      stored: false,
      sources: ['yahoo', 'finmind'],
      trend: {
        first_day: '2026-09-17',
        first_close: 118,
        last_day: '2026-09-18',
        last_close: 119,
        change: 0.85,
        high_day: '2026-09-18',
        high: 119,
        low_day: '2026-09-17',
        low: 118,
        largest_fall: 0,
        fall_from: null,
        fall_to: null
      },
      days: [
        { day: '2026-09-17', previous_close: 121, close: 118, change: -2.48 },
        { day: '2026-09-18', previous_close: 118, close: 119, change: 0.85 }
      ],
      not_read: null
    },
    {
      symbol: 'NVDA',
      name: 'NVDA',
      start_date: '2026-09-17',
      end_date: '2026-09-18',
      read_at: null,
      stored: false,
      sources: ['yahoo'],
      trend: null,
      days: [],
      not_read: { source: 'yahoo', reason: 'unreadable' }
    }
  ],
  events: [
    {
      file: '2026-09-16-fomc-raises-rate.md',
      event_date: '2026-09-16',
      source_numbers: [1],
      rows: [
        {
          symbol: '006208.TW',
          aligned: '2026-09-17',
          d0: '2026-09-17',
          previous_close: 121,
          close: 118,
          day_change: -2.48,
          next_change: 0.85,
          fifth_change: 1.7,
          notes: { during: false, missing: [], filled: ['2026-09-17'], dividends: [] }
        }
      ],
      same_as: null
    },
    {
      file: '2026-09-16-cbc.md',
      event_date: '2026-09-16',
      source_numbers: [2],
      rows: [],
      same_as: '2026-09-16-fomc-raises-rate.md'
    }
  ],
  days_left_out: 0,
  events_left_out: 3,
  period_events_left_out: 0,
  source: { name: 'Yahoo Finance', terms_url: 'https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html' }
};

export function textEvent(delta: string): Extract<ChatEvent, { type: 'response.output_text.delta' }> {
  return { type: 'response.output_text.delta', delta, context: null, proposal: null, usage: null };
}

/** The last event of an answer that ended: the question's tokens. */
export function completedEvent(
  usage: Partial<Extract<ChatEvent, { type: 'response.completed' }>['usage']> = {}
): Extract<ChatEvent, { type: 'response.completed' }> {
  return {
    type: 'response.completed',
    delta: null,
    context: null,
    proposal: null,
    usage: {
      input_tokens: 93_000,
      cached_input_tokens: 60_800,
      output_tokens: 2_050,
      total_tokens: 95_050,
      unreported_runs: 0,
      ...usage
    }
  };
}
