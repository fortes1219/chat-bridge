import { z } from 'zod';
import { ProgramSchema } from '@/service/schema/program';

/** The service's own limit on a question, so a longer one is refused before it is sent. */
export const MAX_QUESTION_LENGTH = 10_240;

/** `POST /chat/stream` body. Without a program, the service picks the first one logged in. */
export const ChatRequestSchema = z
  .object({
    question: z.string().min(1).max(MAX_QUESTION_LENGTH),
    program: ProgramSchema.optional()
  })
  .strict();

/** A section the answer may use, numbered as the model sees it. A section may have no event date. */
export const SourceSchema = z
  .object({
    number: z.number().int().positive(),
    file: z.string(),
    title: z.string(),
    heading: z.string(),
    event_date: z.iso.date().nullable()
  })
  .strict();

/**
 * What the service, not the model, says about an answer. `program` is null when no program is
 * asked, as for a question the data has nothing on.
 */
export const ChatContextSchema = z
  .object({
    sources: SourceSchema.array(),
    data_latest_date: z.iso.date().nullable(),
    disclaimer: z.string(),
    program: ProgramSchema.nullable()
  })
  .strict();

/** The stream's first event: the sources and the notice, sent even when the answer is cut off. */
export const ContextEventSchema = z
  .object({
    type: z.literal('response.context'),
    delta: z.null(),
    context: ChatContextSchema
  })
  .strict();

/** Each later event: one piece of the answer. */
export const TextEventSchema = z
  .object({
    type: z.literal('response.output_text.delta'),
    delta: z.string(),
    context: z.null()
  })
  .strict();

/** An unnamed event of the stream. */
export const ChatEventSchema = z.discriminatedUnion('type', [ContextEventSchema, TextEventSchema]);

/** The event named `error` that ends a stream whose answer failed after it started. */
export const StreamErrorSchema = z
  .object({
    message: z.string()
  })
  .strict();
