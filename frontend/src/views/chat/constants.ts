import type { Program, ProgramState } from '@/service/api/programs';
import type { MessageSchema } from '@/i18n';

/** Product names, the same in every language. */
export const PROGRAM_NAMES: Record<Program, string> = {
  'claude-code': 'Claude Code',
  codex: 'Codex'
};

/** The service's order when no program is named: the first one logged in answers. */
export const PROGRAM_ORDER: readonly Program[] = ['claude-code', 'codex'];

/** The message key of each login state, for its label and for its next step. */
export const STATE_KEYS: Record<ProgramState['state'], keyof MessageSchema['loginState']> = {
  'logged in': 'loggedIn',
  'not logged in': 'notLoggedIn',
  'not installed': 'notInstalled',
  unknown: 'unknown'
};

/** The keys of the sample questions in the page's messages, in the order they are shown. */
export const SAMPLE_QUESTION_KEYS = ['fed', 'aiSpending', 'tsmc', 'recovery'] as const;
