import { computed, ref, type ComputedRef, type Ref } from 'vue';
import { useSaveRules } from '@/queries/use-strategy-mutations';
import type { Market, Rule, RuleChecks, RuleKind } from '@/service/api/strategy';
import type { AppError } from '@/service/error';

/** Whether each kind is about a market, and so names one; the others name none. */
export const NAMES_A_MARKET: Record<RuleKind, boolean> = {
  max_holding_weight: false,
  min_holding_weight: false,
  max_market_weight: true
};

/** The markets a market rule can name, in the order the select lists them. */
export const MARKETS: readonly Market[] = ['TW', 'US'];

/**
 * A new rule is the most any one holding may weigh, at 100%: a limit that rules nothing out, so
 * adding it changes no result until the person sets the limit.
 */
const NEW_RULE: Rule = { kind: 'max_holding_weight', limit_percent: 100, market: null, enabled: true };

export interface UseRuleEditor {
  editing: Ref<boolean>;
  /** The rules being edited: a copy of the saved ones, sent only when the person saves. */
  draft: Ref<Rule[]>;
  /** Whether the draft differs from the saved rules; an unchanged draft is not sent. */
  changed: ComputedRef<boolean>;
  saving: ComputedRef<boolean>;
  saveError: ComputedRef<AppError | null>;
  start(): void;
  cancel(): void;
  add(): void;
  remove(index: number): void;
  setKind(index: number, kind: RuleKind): void;
  /** An emptied limit keeps the one before, so a rule never goes out without a limit. */
  setLimit(index: number, limit: number | null): void;
  setMarket(index: number, market: Market): void;
  setEnabled(index: number, enabled: boolean): void;
  save(): void;
}

/** The setting of a rule, without the result the service computed for it. */
function settingOf({ kind, limit_percent, market, enabled }: Rule): Rule {
  return { kind, limit_percent, market, enabled };
}

/**
 * Editing the person's rules. The draft is copied from the saved rules when editing starts, so a
 * new price, which brings the strategy again, does not undo what the person is typing. The saved
 * rules change only when the service accepts the draft; it answers with the checks recomputed.
 */
export function useRuleEditor(saved: () => RuleChecks | null): UseRuleEditor {
  const mutation = useSaveRules();
  const editing = ref(false);
  const draft = ref<Rule[]>([]);

  const savedRules = computed(() => (saved()?.rules ?? []).map(settingOf));
  const changed = computed(() => JSON.stringify(draft.value) !== JSON.stringify(savedRules.value));

  function start(): void {
    mutation.reset();
    draft.value = savedRules.value.map(rule => ({ ...rule }));
    editing.value = true;
  }

  function cancel(): void {
    mutation.reset();
    editing.value = false;
    draft.value = [];
  }

  function add(): void {
    draft.value.push({ ...NEW_RULE });
  }

  function remove(index: number): void {
    draft.value.splice(index, 1);
  }

  function setKind(index: number, kind: RuleKind): void {
    const rule = draft.value[index];
    if (!rule) return;
    rule.kind = kind;
    rule.market = NAMES_A_MARKET[kind] ? (rule.market ?? MARKETS[0] ?? null) : null;
  }

  function setLimit(index: number, limit: number | null): void {
    const rule = draft.value[index];
    if (!rule || limit === null) return;
    rule.limit_percent = limit;
  }

  function setMarket(index: number, market: Market): void {
    const rule = draft.value[index];
    if (!rule) return;
    rule.market = market;
  }

  function setEnabled(index: number, enabled: boolean): void {
    const rule = draft.value[index];
    if (!rule) return;
    rule.enabled = enabled;
  }

  function save(): void {
    if (!changed.value || mutation.isPending.value) return;
    mutation.mutate(
      { rules: draft.value.map(settingOf) },
      {
        onSuccess: () => {
          editing.value = false;
        }
      }
    );
  }

  return {
    editing,
    draft,
    changed,
    saving: computed(() => mutation.isPending.value),
    saveError: computed(() => mutation.error.value ?? null),
    start,
    cancel,
    add,
    remove,
    setKind,
    setLimit,
    setMarket,
    setEnabled,
    save
  };
}
