import { StrategySchema } from '@/service/schema/strategy';
import type { Strategy } from '@/service/api/strategy';

/** The event the service sends with the strategy, once on connecting and after each price. */
export const STRATEGY_EVENT = 'strategy';

/** The event's strategy, checked as a response is; null when it does not match, so it is not drawn. */
export function parseStrategyEvent(raw: unknown): Strategy | null {
  const parsed = StrategySchema.safeParse(raw);
  return parsed.success ? parsed.data : null;
}
