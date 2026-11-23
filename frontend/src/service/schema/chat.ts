import { z } from 'zod';
import { ProgramSchema } from '@/service/schema/program';
import { ErrorDetailSchema, LocalizedSchema } from '@/service/schema/common';

/** The service's own limit on a question, so a longer one is refused before it is sent. */
export const MAX_QUESTION_LENGTH = 10_240;

/** `POST /chat/stream` body. Without a program, the service picks the first one logged in. */
export const ChatRequestSchema = z
  .object({
    question: z.string().min(1).max(MAX_QUESTION_LENGTH),
    program: ProgramSchema.optional()
  })
  .strict();

/**
 * A section the answer may use, numbered as the model sees it. A section may have no event date.
 * `heading_localizations` is set only for the section names the sample news is written with; any
 * other heading is the document's own words and is shown as written.
 */
export const SourceSchema = z
  .object({
    number: z.number().int().positive(),
    file: z.string(),
    title: z.string(),
    heading: z.string(),
    heading_localizations: LocalizedSchema.nullable(),
    event_date: z.iso.date().nullable()
  })
  .strict();

/**
 * What the service, not the model, says about an answer. `program` is null when no program is
 * asked, as for a question the data has nothing on. `data_latest_date` is the knowledge base's
 * latest event date. `split_failed` says the question could not be split into parts, so only the
 * question as asked was searched.
 */
export const ChatContextSchema = z
  .object({
    sources: SourceSchema.array(),
    data_latest_date: z.iso.date().nullable(),
    disclaimer: LocalizedSchema,
    program: ProgramSchema.nullable(),
    split_failed: z.boolean()
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
export const StreamErrorSchema = ErrorDetailSchema;
