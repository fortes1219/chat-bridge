import { eventIterator, oc } from '@orpc/contract';
import { ChatEventSchema, ChatRequestSchema } from '@/service/schema/chat';

/**
 * The chat answer as Server-Sent Events (oRPC, types only: nothing calls it at run time). An
 * error after the stream starts is an event named `error`, outside this event schema.
 */
export const chatContract = {
  ask: oc
    .route({
      method: 'POST',
      path: '/chat/stream',
      summary: 'Answer a question from the knowledge base, streamed as Server-Sent Events'
    })
    .input(ChatRequestSchema)
    .output(eventIterator(ChatEventSchema))
};
