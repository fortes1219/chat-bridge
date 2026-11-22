import { z } from 'zod';

/** The two programs that can answer, named as the service names them. */
export const ProgramSchema = z.enum(['claude-code', 'codex']);

/** A program's login state. `unknown` means the state could not be read; it is never a login. */
export const LoginSchema = z.enum(['logged in', 'not logged in', 'not installed', 'unknown']);

/**
 * `GET /chat/programs`: one program's login state. Only the state: the program's own status text
 * can name the account, so the service never sends it.
 */
export const ProgramStateSchema = z
  .object({
    program: ProgramSchema,
    state: LoginSchema
  })
  .strict();
