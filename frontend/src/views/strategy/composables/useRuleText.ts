import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import type { Holding, Rule, RuleCheck } from '@/service/api/strategy';

/** A rule's result: met, not met, or off and not checked. */
export type RuleStatus = 'met' | 'broken' | 'off';

/** The badge color of each result. */
export const RULE_STATUS_COLORS: Record<RuleStatus, 'success' | 'error' | 'neutral'> = {
  met: 'success',
  broken: 'error',
  off: 'neutral'
};

/** A check's result, as the service gave it: no result means the rule is off. */
export function ruleStatus(check: RuleCheck): RuleStatus {
  if (check.met === null) return 'off';
  return check.met ? 'met' : 'broken';
}

export interface RuleText {
  /** The rule in words, with its limit and, for a market rule, its market. */
  describe(rule: Rule): string;
  /** The weight the rule looked at; empty when it looked at none. */
  measured(check: RuleCheck): string;
  /** The holdings that break it, by name; empty when none do. */
  breaking(check: RuleCheck, holdings: ReadonlyMap<string, Holding>): string;
  /** The word for a result. */
  status(check: RuleCheck): string;
}

/** The rules and their results in the page's language; the numbers are the service's. */
export function useRuleText(): RuleText {
  const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();

  function describe(rule: Rule): string {
    const market = rule.market === null ? '' : t(`markets.${rule.market}`);
    return t(`rules.${rule.kind}.rule`, { limit: rule.limit_percent, market });
  }

  function measured(check: RuleCheck): string {
    if (check.measured === null) return '';
    return t(`rules.${check.kind}.measured`, { value: check.measured });
  }

  function breaking(check: RuleCheck, holdings: ReadonlyMap<string, Holding>): string {
    if (check.breaking.length === 0) return '';
    const names = check.breaking.map(symbol => holdings.get(symbol)?.names[locale.value] ?? symbol).join(', ');
    return t('rules.breaking', { names });
  }

  function status(check: RuleCheck): string {
    return t(`rules.${ruleStatus(check)}`);
  }

  return { describe, measured, breaking, status };
}
