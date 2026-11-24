import type { Program } from '@/service/api/programs';

/** Product names, the same in every language, for the program that made a proposal. */
export const PROGRAM_NAMES: Record<Program, string> = {
  'claude-code': 'Claude Code',
  codex: 'Codex'
};
