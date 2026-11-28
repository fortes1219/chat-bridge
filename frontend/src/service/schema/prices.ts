import { z } from 'zod';
import { PriceSourceSchema } from '@/service/schema/strategy';

/**
 * The prices the service looked up for a question, as the answering program was given them. Every
 * number is the service's: closes and changes in percent, each to two decimals.
 */

const day = z.iso.date();
const number = z.number();

/** A lookup's period: first and last trading day, the change, the extremes, the largest fall. */
export const PriceTrendSchema = z
  .object({
    first_day: day,
    first_close: number,
    last_day: day,
    last_close: number,
    change: number,
    high_day: day,
    high: number,
    low_day: day,
    low: number,
    largest_fall: number,
    fall_from: day.nullable(),
    fall_to: day.nullable()
  })
  .strict();

/** One trading day of a short period, with the trading day before's close and the change from it. */
export const PriceDaySchema = z
  .object({
    day,
    previous_close: number.nullable(),
    close: number.nullable(),
    change: number.nullable()
  })
  .strict();

/** What a row's notes say, for the page to word in its language. */
export const MoveNotesSchema = z
  .object({
    during: z.boolean(),
    missing: day.array(),
    filled: day.array(),
    dividends: day.array()
  })
  .strict();

/** A series on the trading day before an event's trading day (D0), on D0 and after; D0 is null when the data has none yet. */
export const PriceRowSchema = z
  .object({
    symbol: z.string(),
    aligned: day,
    d0: day.nullable(),
    previous_close: number.nullable(),
    close: number.nullable(),
    day_change: number.nullable(),
    next_change: number.nullable(),
    fifth_change: number.nullable(),
    notes: MoveNotesSchema
  })
  .strict();

const PriceSourceNameSchema = z.enum(['yahoo', 'finmind']);

/** Why a lookup was not read: the source, and whether it had no data or did not answer. */
export const NotReadSchema = z
  .object({
    source: PriceSourceNameSchema,
    reason: z.enum(['no_data', 'unreadable'])
  })
  .strict();

/** A lookup: its symbol and period, when it was read, and its trend, or why it was not read. */
export const PriceLookupSchema = z
  .object({
    symbol: z.string(),
    name: z.string(),
    start_date: day,
    end_date: day,
    read_at: z.iso.datetime({ offset: true }).nullable(),
    stored: z.boolean(),
    sources: PriceSourceNameSchema.array(),
    trend: PriceTrendSchema.nullable(),
    days: PriceDaySchema.array(),
    not_read: NotReadSchema.nullable()
  })
  .strict();

/** A found event's rows, by its file and the numbers of its sources; or the earlier event it shares them with. */
export const PriceEventSchema = z
  .object({
    file: z.string(),
    event_date: day,
    source_numbers: z.number().int().positive().array(),
    rows: PriceRowSchema.array(),
    same_as: z.string().nullable()
  })
  .strict();

export const PriceLookupsSchema = z
  .object({
    lookups: PriceLookupSchema.array(),
    events: PriceEventSchema.array(),
    days_left_out: z.number().int().nonnegative(),
    events_left_out: z.number().int().nonnegative(),
    /** The events of the days a short lookup asks about that were not given to the program. */
    period_events_left_out: z.number().int().nonnegative(),
    source: PriceSourceSchema
  })
  .strict();
