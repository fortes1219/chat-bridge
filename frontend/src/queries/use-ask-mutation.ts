import { useMutation } from '@tanstack/vue-query';
import { ask, type ChatEvent, type ChatRequest } from '@/service/api/chat';
import type { AppError } from '@/service/error';

export interface AskVariables {
  input: ChatRequest;
  /** The caller's stop. A mutation has no signal of its own, so the caller owns this one. */
  signal: AbortSignal;
  /** Called with each event as it arrives, so the answer is drawn while it is written. */
  onEvent: (event: ChatEvent) => void;
}

async function askUntilDone({ input, signal, onEvent }: AskVariables): Promise<void> {
  for await (const event of ask(input, signal)) {
    onEvent(event);
  }
}

/**
 * Asking a question, as a mutation: it is pending while the answer streams, and fails with the
 * AppError that ended it. A stopped question rejects with the cancellation itself.
 */
export function useAskMutation() {
  return useMutation<void, AppError, AskVariables>({
    mutationFn: askUntilDone
  });
}
