import { computed, ref, type ComputedRef, type Ref } from 'vue';
import { LOCALES, type Locale } from '@/i18n';
import { useSaveHoldings } from '@/queries/use-strategy-mutations';
import type { Holding, HoldingInput, HoldingsInput } from '@/service/api/strategy';
import type { AppError } from '@/service/error';
import { CASH } from '../constants';

/** A new holding: empty, so the person types its symbol, name, quantity and cost. */
const NEW_HOLDING: HoldingInput = { symbol: '', names: { 'zh-TW': '', en: '' }, quantity: '', average_cost: '' };

export interface UseHoldingsEditor {
  editing: Ref<boolean>;
  /** The holdings being edited, cash apart: a copy of the saved ones, sent only on save. */
  draft: Ref<HoldingsInput>;
  /** Whether the draft differs from the saved holdings; an unchanged draft is not sent. */
  changed: ComputedRef<boolean>;
  saving: ComputedRef<boolean>;
  saveError: ComputedRef<AppError | null>;
  start(): void;
  cancel(): void;
  add(): void;
  remove(index: number): void;
  setSymbol(index: number, symbol: string): void;
  /**
   * The name in the page's language. A language whose name was the same, as both are empty in a
   * new holding, follows it, so a holding typed in one language has a name in both.
   */
  setName(index: number, locale: Locale, name: string): void;
  setQuantity(index: number, quantity: string): void;
  setCost(index: number, cost: string): void;
  setCash(cash: string): void;
  save(): void;
}

/** The saved holdings as the page sends them: no market or currency, which the service works out. */
function inputOf(holdings: readonly Holding[]): HoldingsInput {
  const cash = holdings.find(holding => holding.symbol === CASH);
  return {
    holdings: holdings
      .filter(holding => holding.symbol !== CASH)
      .map(({ symbol, names, quantity, average_cost }) => ({ symbol, names: { ...names }, quantity, average_cost })),
    cash: cash?.quantity ?? '0'
  };
}

/**
 * Editing the person's holdings, as the rules are edited: the draft is copied from the saved
 * holdings when editing starts, so a new price does not undo what the person is typing, and the
 * saved holdings change only when the service accepts the draft. Amounts stay text, so a decimal
 * is sent as typed.
 */
export function useHoldingsEditor(saved: () => readonly Holding[] | null): UseHoldingsEditor {
  const mutation = useSaveHoldings();
  const editing = ref(false);
  const draft = ref<HoldingsInput>({ holdings: [], cash: '0' });

  const savedInput = computed(() => inputOf(saved() ?? []));
  const changed = computed(() => JSON.stringify(draft.value) !== JSON.stringify(savedInput.value));

  function start(): void {
    mutation.reset();
    draft.value = structuredClone(savedInput.value);
    editing.value = true;
  }

  function cancel(): void {
    mutation.reset();
    editing.value = false;
  }

  function add(): void {
    draft.value.holdings.push(structuredClone(NEW_HOLDING));
  }

  function remove(index: number): void {
    draft.value.holdings.splice(index, 1);
  }

  function setSymbol(index: number, symbol: string): void {
    const holding = draft.value.holdings[index];
    if (!holding) return;
    holding.symbol = symbol.trim().toUpperCase();
  }

  function setName(index: number, locale: Locale, name: string): void {
    const holding = draft.value.holdings[index];
    if (!holding) return;
    const before = holding.names[locale];
    holding.names[locale] = name;
    for (const other of LOCALES) {
      if (other !== locale && holding.names[other] === before) holding.names[other] = name;
    }
  }

  function setQuantity(index: number, quantity: string): void {
    const holding = draft.value.holdings[index];
    if (!holding) return;
    holding.quantity = quantity.trim();
  }

  function setCost(index: number, cost: string): void {
    const holding = draft.value.holdings[index];
    if (!holding) return;
    holding.average_cost = cost.trim();
  }

  function setCash(cash: string): void {
    draft.value.cash = cash.trim();
  }

  function save(): void {
    if (!changed.value || mutation.isPending.value) return;
    mutation.mutate(draft.value, {
      onSuccess: () => {
        editing.value = false;
      }
    });
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
    setSymbol,
    setName,
    setQuantity,
    setCost,
    setCash,
    save
  };
}
