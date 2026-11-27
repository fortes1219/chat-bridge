import type { InferContractRouterInputs, InferContractRouterOutputs } from '@orpc/contract';
import { EventSourceParserStream, type EventSourceMessage } from 'eventsource-parser/stream';
import { request } from '@/service/request';
import { contractError, normalizeStreamReadError, parseInput, parseJsonContract, streamError } from '@/service/error';
import { ChatEventSchema, ChatRequestSchema, StreamErrorSchema } from '@/service/schema/chat';
import type { contract } from '@/service/contract';

type AskRoute = 'ask';
type EventOf<T> = T extends AsyncIteratorObject<infer TEvent, unknown, unknown> ? TEvent : never;

/** The question and, optionally, the program that should answer and its level, inferred from the contract. */
export type ChatRequest = InferContractRouterInputs<typeof contract>['chat'][AskRoute];
/** How hard the answering program thinks. */
export type Effort = NonNullable<ChatRequest['effort']>;
/** One event of the answer: the context first, then each piece. */
export type ChatEvent = EventOf<InferContractRouterOutputs<typeof contract>['chat'][AskRoute]>;
export type ChatContext = Extract<ChatEvent, { type: 'response.context' }>['context'];
export type Source = ChatContext['sources'][number];
/** What came of a revision question: the checked proposal, or why it was refused. */
export type ProposalOutcome = Extract<ChatEvent, { type: 'response.proposal' }>['proposal'];
/** The tokens a question used, sent once its answer ended. */
export type QuestionUsage = Extract<ChatEvent, { type: 'response.completed' }>['usage'];

/**
 * The stream ends when the service closes it, at its own time limit or when the user stops it,
 * so the client sets none.
 */
const NO_TIMEOUT = 0;

/**
 * How each event is read, by its name. An unnamed event is part of the answer; `error` ends the
 * stream with the service's message. Any other name is a contract error. A Map, so a name such as
 * `constructor` finds nothing instead of a function every object has.
 */
const EVENT_READERS = new Map<string, (data: string) => ChatEvent>([
  ['message', data => parseJsonContract(ChatEventSchema, data)],
  [
    'error',
    data => {
      const { code, message } = parseJsonContract(StreamErrorSchema, data);
      throw streamError(code, message, data);
    }
  ]
]);

function readEvent(event: EventSourceMessage): ChatEvent {
  const reader = EVENT_READERS.get(event.event ?? 'message');
  if (!reader) {
    throw contractError(`unknown event: ${event.event}`, event);
  }
  return reader(event.data);
}

/**
 * Asks a question. Yields the context first, then each piece of the answer, each checked against
 * its schema as it arrives. The input is checked before anything is sent; a refused request
 * rejects with an AppError; stopping `signal` ends the stream with a cancellation, before or
 * after the answer starts.
 */
export async function* ask(input: ChatRequest, signal?: AbortSignal): AsyncGenerator<ChatEvent, void, undefined> {
  const body = parseInput(ChatRequestSchema, input);
  const stream = await request<ReadableStream<Uint8Array>>({
    url: '/chat/stream',
    method: 'POST',
    headers: { Accept: 'text/event-stream' },
    data: body,
    signal,
    responseType: 'stream',
    timeout: NO_TIMEOUT
  });
  // TypeScript's DOM types give TextDecoderStream a writable side of BufferSource, wider than the
  // Uint8Array the body is, so it is narrowed here; the stream itself accepts both.
  const decoder = new TextDecoderStream() as ReadableWritablePair<string, Uint8Array>;
  const events = stream.pipeThrough(decoder).pipeThrough(new EventSourceParserStream()).getReader();
  try {
    while (true) {
      let next: ReadableStreamReadResult<EventSourceMessage>;
      try {
        next = await events.read();
      } catch (error) {
        throw normalizeStreamReadError(error, signal);
      }
      if (next.done) {
        return;
      }
      yield readEvent(next.value);
    }
  } finally {
    // A caller that stops reading early leaves the rest of the body unread; cancel it so the
    // connection closes and the service stops the answer.
    void events.cancel().catch(() => undefined);
  }
}
