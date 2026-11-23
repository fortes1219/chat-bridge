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
    split_failed: false
  }
};

export function textEvent(delta: string): Extract<ChatEvent, { type: 'response.output_text.delta' }> {
  return { type: 'response.output_text.delta', delta, context: null };
}
