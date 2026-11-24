import type { Program } from '@/service/api/programs';

/** Product names, the same in every language, for the program that made a proposal. */
export const PROGRAM_NAMES: Record<Program, string> = {
  'claude-code': 'Claude Code',
  codex: 'Codex'
};

/** What the screen shows for a value it does not have, such as a missing price: never zero. */
export const MISSING = '--';

/** The holding that stands for the profile's cash, as the service names it. */
export const CASH = 'CASH';
