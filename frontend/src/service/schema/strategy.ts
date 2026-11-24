import { z } from 'zod';
import { LocalizedSchema } from '@/service/schema/common';
import { ProgramSchema } from '@/service/schema/program';
import { SourceSchema } from '@/service/schema/source';

/** The market a holding is listed in; cash belongs to none. */
export const MarketSchema = z.enum(['TW', 'US']);

/** An exact amount, sent as text in plain notation so no float rounds it. */
const AmountSchema = z.string().regex(/^\d+(\.\d+)?$/);

/** A whole percent of a target weight. */
const PercentSchema = z.number().int().min(0).max(100);

/** One holding of the simulated profile; cash is the holding `CASH`. */
export const HoldingSchema = z
  .object({
    symbol: z.string(),
    names: LocalizedSchema,
    market: MarketSchema.nullable(),
    currency: z.string(),
    quantity: AmountSchema,
    average_cost: AmountSchema
  })
  .strict();

/** A holding's current target weight. */
export const TargetRowSchema = z
  .object({
    symbol: z.string(),
    current: PercentSchema
  })
  .strict();

/** One holding of a proposal: current, proposed and the change, all computed by the service. */
export const DiffRowSchema = z
  .object({
    symbol: z.string(),
    current: PercentSchema,
    proposed: PercentSchema,
    change: z.number().int().min(-100).max(100)
  })
  .strict();

/** A reason for a proposal, with the numbers of the sources it rests on. */
export const ReasonSchema = z
  .object({
    text: z.string(),
    sources: z.number().int().positive().array()
  })
  .strict();

export const ProposalStatusSchema = z.enum(['open', 'accepted', 'rejected', 'replaced']);

/** A revised strategy a program handed back and the service checked. */
export const ProposalSchema = z
  .object({
    id: z.number().int().positive(),
    created_at: z.iso.datetime({ offset: true }),
    question: z.string(),
    program: ProgramSchema,
    status: ProposalStatusSchema,
    rows: DiffRowSchema.array(),
    reasons: ReasonSchema.array(),
    sources: SourceSchema.array()
  })
  .strict();

/** `GET /strategy`: the profile, its current targets, the open proposal, and the sample notice. */
export const StrategySchema = z
  .object({
    holdings: HoldingSchema.array(),
    targets: TargetRowSchema.array(),
    proposal: ProposalSchema.nullable(),
    notice: LocalizedSchema
  })
  .strict();

export const DecisionSchema = z.enum(['accept', 'reject']);

/**
 * `POST /strategy/proposals/{id}/decision` body. A JSON body, so another web page cannot send a
 * decision without the browser asking the service first.
 */
export const DecisionRequestSchema = z
  .object({
    decision: DecisionSchema
  })
  .strict();

/** Why the service refused a proposal, for the page to say in its language. */
export const RefusalCodeSchema = z.enum([
  'not_the_shape',
  'unknown_holding',
  'repeated_holding',
  'missing_holding',
  'percent_out_of_range',
  'not_100',
  'unknown_source'
]);

/** A refusal: its reason, and the service's message, which is for logs and is never drawn. */
export const ProposalRefusalSchema = z
  .object({
    code: RefusalCodeSchema,
    message: z.string()
  })
  .strict();

/**
 * What came of a revision question: the checked proposal, or why it was refused. Both are null
 * when the program proposed nothing.
 */
export const ProposalOutcomeSchema = z
  .object({
    proposal: ProposalSchema.nullable(),
    refused: ProposalRefusalSchema.nullable()
  })
  .strict();
