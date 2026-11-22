import { z } from 'zod';

/**
 * The service's body for a request it refuses: FastAPI's `{ detail }` with one message, as in the
 * 503 the chat endpoint answers when its search cannot run.
 */
export const ErrorBodySchema = z
  .object({
    detail: z.string()
  })
  .strict();
export type ErrorBody = z.infer<typeof ErrorBodySchema>;
