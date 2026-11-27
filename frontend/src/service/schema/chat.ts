import { z } from 'zod';
import { ProgramSchema } from '@/service/schema/program';
import { ErrorDetailSchema, LocalizedSchema } from '@/service/schema/common';
import { SourceSchema } from '@/service/schema/source';
import { ProposalOutcomeSchema } from '@/service/schema/strategy';

export { SourceSchema };

/** The service's own limit on a question, so a longer one is refused before it is sent. */
export const MAX_QUESTION_LENGTH = 10_240;

/** How hard the answering program thinks; the service takes only these three. */
export const EffortSchema = z.enum(['low', 'medium', 'high']);

/**
 * `POST /chat/stream` body. Without a program, the service picks the first one logged in; without
 * a level, it answers at `medium`.
 */
export const ChatRequestSchema = z
  .object({
    question: z.string().min(1).max(MAX_QUESTION_LENGTH),
    program: ProgramSchema.optional(),
    effort: EffortSchema.optional()
  })
  .strict();

/**
 * What the service, not the model, says about an answer. `program` is null when no program is
 * asked, as for a question the data has nothing on. `data_latest_date` is the knowledge base's
 * latest event date. `split_failed` says the question could not be split into parts, so only the
 * question as asked was searched. `proposal_expected` says the question asks to revise the
 * strategy: the answer comes whole, then a proposal event.
 */
export const ChatContextSchema = z
  .object({
    sources: SourceSchema.array(),
    data_latest_date: z.iso.date().nullable(),
    disclaimer: LocalizedSchema,
    program: ProgramSchema.nullable(),
    split_failed: z.boolean(),
    proposal_expected: z.boolean()
  })
  .strict();

/** The stream's first event: the sources and the notice, sent even when the answer is cut off. */
export const ContextEventSchema = z
  .object({
    type: z.literal('response.context'),
    delta: z.null(),
    context: ChatContextSchema,
    proposal: z.null(),
    usage: z.null()
  })
  .strict();

/** Each later event: one piece of the answer. */
export const TextEventSchema = z
  .object({
    type: z.literal('response.output_text.delta'),
    delta: z.string(),
    context: z.null(),
    proposal: z.null(),
    usage: z.null()
  })
  .strict();

/** A revision question's event after its answer: what came of its proposal. */
export const ProposalEventSchema = z
  .object({
    type: z.literal('response.proposal'),
    delta: z.null(),
    context: z.null(),
    proposal: ProposalOutcomeSchema,
    usage: z.null()
  })
  .strict();

const tokens = z.number().int().nonnegative();

/**
 * The tokens of every model run of the question, added up. The input counts all of it, the part
 * read from the cache included; `unreported_runs` runs reported none and are left out.
 */
export const QuestionUsageSchema = z
  .object({
    input_tokens: tokens,
    cached_input_tokens: tokens,
    output_tokens: tokens,
    total_tokens: tokens,
    unreported_runs: tokens
  })
  .strict();

/** The last event of an answer that ended: the question's tokens. */
export const CompletedEventSchema = z
  .object({
    type: z.literal('response.completed'),
    delta: z.null(),
    context: z.null(),
    proposal: z.null(),
    usage: QuestionUsageSchema
  })
  .strict();

/** An unnamed event of the stream. */
export const ChatEventSchema = z.discriminatedUnion('type', [
  ContextEventSchema,
  TextEventSchema,
  ProposalEventSchema,
  CompletedEventSchema
]);

/** The event named `error` that ends a stream whose answer failed after it started. */
export const StreamErrorSchema = ErrorDetailSchema;
