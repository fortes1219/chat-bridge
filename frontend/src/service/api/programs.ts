import type { InferContractRouterOutputs } from '@orpc/contract';
import { request } from '@/service/request';
import { parseContract } from '@/service/error';
import { ProgramStateSchema } from '@/service/schema/program';
import type { contract } from '@/service/contract';

/**
 * One program's login state, inferred from the contract; `ProgramStateSchema` still checks it at
 * run time. Other layers import the type from here.
 */
export type ProgramState = InferContractRouterOutputs<typeof contract>['programs']['getPrograms'][number];
export type Program = ProgramState['program'];

/** Whether Claude Code and Codex are each installed and logged in, read without starting a model. */
export async function getPrograms(signal?: AbortSignal): Promise<ProgramState[]> {
  const data = await request<unknown>({
    url: '/chat/programs',
    method: 'GET',
    signal
  });
  return parseContract(ProgramStateSchema.array(), data);
}
