import { oc } from '@orpc/contract';
import { ProgramStateSchema } from '@/service/schema/program';

/** Login states, read without starting a model (oRPC, types only: nothing calls it at run time). */
export const programsContract = {
  getPrograms: oc
    .route({
      method: 'GET',
      path: '/chat/programs',
      summary: 'Whether Claude Code and Codex are each installed and logged in'
    })
    .output(ProgramStateSchema.array())
};
