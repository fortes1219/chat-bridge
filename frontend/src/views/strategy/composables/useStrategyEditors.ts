import { inject, provide, type InjectionKey } from 'vue';
import { useStrategyQuery } from '@/queries/use-strategy-query';
import { useHoldingsEditor, type UseHoldingsEditor } from './useHoldingsEditor';
import { useRuleEditor, type UseRuleEditor } from './useRuleEditor';

export interface StrategyEditors {
  holdings: UseHoldingsEditor;
  rules: UseRuleEditor;
}

const STRATEGY_EDITORS: InjectionKey<StrategyEditors> = Symbol('strategy editors');

/** The editors, following the strategy the panel reads, without reading it themselves. */
function createStrategyEditors(): StrategyEditors {
  const query = useStrategyQuery({ refetchOnMount: false, enabled: false });
  return {
    holdings: useHoldingsEditor(() => query.data.value?.holdings ?? null),
    rules: useRuleEditor(() => query.data.value?.rule_checks ?? null)
  };
}

/**
 * Made by the page that holds the strategy panel. The page shows the panel beside the chat in a
 * wide window and in a slide-over in a narrow one, a different panel each; a draft kept here, not
 * in the panel, outlives the window crossing that width, and the person's typing is not lost.
 */
export function provideStrategyEditors(): void {
  provide(STRATEGY_EDITORS, createStrategyEditors());
}

/** The editors the page keeps; a panel mounted on its own, as in a test, makes its own. */
export function useStrategyEditors(): StrategyEditors {
  return inject(STRATEGY_EDITORS, createStrategyEditors, true);
}
