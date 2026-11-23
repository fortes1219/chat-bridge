import { computed, type ComputedRef, type Ref } from 'vue';
import { useProgramsQuery } from '@/queries/use-programs-query';
import type { ProgramState } from '@/service/api/programs';

/**
 * - `reading`: the first read has not come back, so nothing else is drawn yet;
 * - `unreachable`: the states could not be read;
 * - `locked`: read, and neither program is logged in;
 * - `open`: at least one program is logged in.
 */
export type GateStatus = 'reading' | 'unreachable' | 'locked' | 'open';

export interface UseLoginGate {
  states: ComputedRef<ProgramState[]>;
  status: ComputedRef<GateStatus>;
  /** True while a read is in flight, the first one included. */
  isChecking: Ref<boolean>;
  /** Reads the states again; the only way they are read after the page opens. */
  checkAgain(): void;
}

/** Whether the page may open, from the login states the service reports. */
export function useLoginGate(): UseLoginGate {
  const query = useProgramsQuery();
  const states = computed<ProgramState[]>(() => query.data.value ?? []);

  const status = computed<GateStatus>(() => {
    if (query.isPending.value) return 'reading';
    // A failed read after a good one keeps the old data; the page still says it cannot read.
    if (query.isError.value) return 'unreachable';
    // Unknown is never taken for a login.
    return states.value.some(program => program.state === 'logged in') ? 'open' : 'locked';
  });

  function checkAgain(): void {
    void query.refetch();
  }

  return { states, status, isChecking: query.isFetching, checkAgain };
}
