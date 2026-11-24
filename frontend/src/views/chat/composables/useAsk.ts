import { computed, markRaw, onScopeDispose, reactive, ref, type ComputedRef, type Ref } from 'vue';
import { useAskMutation } from '@/queries/use-ask-mutation';
import { isAppError, isCancellation, type AppError } from '@/service/error';
import type { ChatContext, ChatEvent, ProposalOutcome } from '@/service/api/chat';
import type { Proposal } from '@/service/api/strategy';
import type { Program } from '@/service/api/programs';

/** One question and its answer. Exchanges are independent: none is sent with another. */
export interface Exchange {
  id: string;
  question: string;
  answer: string;
  context: ChatContext | null;
  /** What came of a revision question's proposal; null until its event arrives, or for any other question. */
  proposal: ProposalOutcome | null;
  error: AppError | null;
  stopped: boolean;
}

/** The states of `UChatMessages` and `UChatPrompt` this page uses. */
export type AskStatus = 'ready' | 'submitted' | 'streaming';

export interface UseAsk {
  exchanges: Ref<Exchange[]>;
  status: ComputedRef<AskStatus>;
  ask(question: string): Promise<void>;
  stop(): void;
}

type EventOf<T extends ChatEvent['type']> = Extract<ChatEvent, { type: T }>;

/** What each event does to the exchange it belongs to. */
const APPLY_EVENT: { [T in ChatEvent['type']]: (exchange: Exchange, event: EventOf<T>) => void } = {
  'response.context': (exchange, event) => {
    exchange.context = event.context;
  },
  'response.output_text.delta': (exchange, event) => {
    exchange.answer += event.delta;
  },
  'response.proposal': (exchange, event) => {
    exchange.proposal = event.proposal;
  }
};

function applyEvent(exchange: Exchange, event: ChatEvent): void {
  (APPLY_EVENT[event.type] as (exchange: Exchange, event: ChatEvent) => void)(exchange, event);
}

const UNKNOWN_ERROR: AppError = { source: 'unknown', code: 'unknown_error', message: 'unknown error' };

export interface UseAskOptions {
  /** Called when the answering program turned out to be logged out, so the page reads the states again. */
  onLoggedOut(): void;
  /** Called with a revision question's proposal once the service has checked and kept it. */
  onProposal(proposal: Proposal): void;
}

/**
 * Asking and stopping. Each question is one exchange kept for the visit; the answer grows as its
 * pieces arrive. Leaving the page stops an answer that is still being written.
 */
export function useAsk(program: Ref<Program | null>, { onLoggedOut, onProposal }: UseAskOptions): UseAsk {
  const mutation = useAskMutation();
  const exchanges = ref<Exchange[]>([]);
  let controller: AbortController | null = null;

  const status = computed<AskStatus>(() => {
    if (!mutation.isPending.value) return 'ready';
    const current = exchanges.value[exchanges.value.length - 1];
    return current?.context ? 'streaming' : 'submitted';
  });

  async function ask(question: string): Promise<void> {
    if (mutation.isPending.value) return;
    const exchange = reactive<Exchange>({
      id: crypto.randomUUID(),
      question,
      answer: '',
      context: null,
      proposal: null,
      error: null,
      stopped: false
    });
    exchanges.value.push(exchange);
    controller = new AbortController();
    try {
      await mutation.mutateAsync({
        input: { question, program: program.value ?? undefined },
        signal: controller.signal,
        onEvent: event => {
          applyEvent(exchange, event);
          if (event.type === 'response.proposal' && event.proposal.proposal) onProposal(event.proposal.proposal);
        }
      });
    } catch (error) {
      if (isCancellation(error)) {
        exchange.stopped = true;
        return;
      }
      // Kept as it is: its `raw` detail is for debugging and is not made reactive.
      exchange.error = markRaw(isAppError(error) ? error : { ...UNKNOWN_ERROR, raw: error });
      if (exchange.error.reason === 'not_logged_in') onLoggedOut();
    } finally {
      controller = null;
    }
  }

  function stop(): void {
    controller?.abort();
  }

  onScopeDispose(stop);

  return { exchanges, status, ask, stop };
}
