import { z } from 'zod';
import { LocalizedSchema } from '@/service/schema/common';
import { ProgramSchema } from '@/service/schema/program';
import { SourceSchema } from '@/service/schema/source';

/** The market a holding is listed in; cash belongs to none. */
export const MarketSchema = z.enum(['TW', 'US']);

/** An exact amount, sent as text in plain notation so no float rounds it. */
const AmountSchema = z.string().regex(/^\d+(\.\d+)?$/);

/** The same for an amount that can fall below zero: a loss, a change. */
const SignedAmountSchema = z.string().regex(/^-?\d+(\.\d+)?$/);

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

/**
 * The weight limits a person can set: the most any one holding may weigh, the least any held holding
 * may weigh, the most one market may weigh.
 */
export const RuleKindSchema = z.enum(['max_holding_weight', 'min_holding_weight', 'max_market_weight']);

/** A rule as the person sets it; a market rule names its market, the others none. */
export const RuleSchema = z
  .object({
    kind: RuleKindSchema,
    limit_percent: PercentSchema,
    market: MarketSchema.nullable(),
    enabled: z.boolean()
  })
  .strict();

/** A rule and its result on one set of target weights, computed by the service. */
export const RuleCheckSchema = RuleSchema.extend({
  /** Null when the rule is off. */
  met: z.boolean().nullable(),
  /** The weight the rule looks at; null when it is off or there is nothing to measure. */
  measured: PercentSchema.nullable(),
  /** The holdings that break it. */
  breaking: z.string().array()
}).strict();

/** Every rule checked on one set of target weights, and how many of those that are on are met. */
export const RuleChecksSchema = z
  .object({
    met: z.number().int().min(0),
    enabled: z.number().int().min(0),
    rules: RuleCheckSchema.array()
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
    /** The rules checked on the proposed targets. */
    rule_checks: RuleChecksSchema,
    reasons: ReasonSchema.array(),
    sources: SourceSchema.array()
  })
  .strict();

/** A live price from the stream, or the latest value of the daily series: the day's close once it has ended. */
export const BasisSchema = z.enum(['live', 'daily']);

/**
 * When a price is from: a live price's moment, or a daily value's trading day, which the exchange's
 * calendar names and the reader's time zone does not move.
 */
export const PriceTimeSchema = z
  .object({
    basis: BasisSchema,
    time: z.iso.datetime({ offset: true }).nullable(),
    day: z.iso.date().nullable()
  })
  .strict();

/** One series of the quotes column, in its own currency; null where the price could not be had. */
export const QuoteSchema = z
  .object({
    symbol: z.string(),
    names: LocalizedSchema,
    price: AmountSchema.nullable(),
    change_percent: SignedAmountSchema.nullable(),
    at: PriceTimeSchema.nullable(),
    /** The source's stated delay for the market; null when it states none. */
    delay_minutes: z.number().int().min(0).nullable()
  })
  .strict();

/** One holding at its latest price, money in Taiwan dollars; all null when it is left out. */
export const HoldingValueSchema = z
  .object({
    symbol: z.string(),
    price: AmountSchema.nullable(),
    value: AmountSchema.nullable(),
    weight: AmountSchema.nullable(),
    profit: SignedAmountSchema.nullable(),
    profit_percent: SignedAmountSchema.nullable()
  })
  .strict();

export const PriceSourceSchema = z
  .object({
    name: z.string(),
    terms_url: z.url({ protocol: /^https$/ })
  })
  .strict();

/** The numbers that follow the prices, all computed by the service. */
export const ValuationSchema = z
  .object({
    currency: z.literal('TWD'),
    /** Whether the service's live connection to the price source is open. */
    live: z.boolean(),
    total_value: AmountSchema,
    change: SignedAmountSchema.nullable(),
    change_percent: SignedAmountSchema.nullable(),
    profit: SignedAmountSchema.nullable(),
    profit_percent: SignedAmountSchema.nullable(),
    /** Valued holdings whose previous close is not known, left out of the change. */
    change_left_out: z.string().array(),
    /** Holdings without a price or exchange rate, left out of every total. */
    left_out: z.string().array(),
    prices_at: PriceTimeSchema.nullable(),
    holdings: HoldingValueSchema.array(),
    quotes: QuoteSchema.array(),
    source: PriceSourceSchema
  })
  .strict();

/**
 * `GET /strategy`, and each `strategy` event of the real-time connection: the profile, its current
 * targets, the open proposal, the sample notice, and the numbers that follow the prices.
 */
export const StrategySchema = z
  .object({
    holdings: HoldingSchema.array(),
    targets: TargetRowSchema.array(),
    /** The rules checked on the current targets; prices do not move them. */
    rule_checks: RuleChecksSchema,
    proposal: ProposalSchema.nullable(),
    notice: LocalizedSchema,
    valuation: ValuationSchema
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

/**
 * `PUT /strategy/rules` body: every rule, in the order the screen lists them, replacing the saved
 * ones. A JSON body, so another web page cannot send it without the browser asking the service first.
 */
export const RulesRequestSchema = z
  .object({
    rules: RuleSchema.array()
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
