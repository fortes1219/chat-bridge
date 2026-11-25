import type { InferContractRouterOutputs } from '@orpc/contract';
import { request } from '@/service/request';
import { parseContract } from '@/service/error';
import { SampleQuestionsSchema } from '@/service/schema/sample';
import type { contract } from '@/service/contract';

/** One sample question in both languages, inferred from the contract. */
export type SampleQuestion = InferContractRouterOutputs<
  typeof contract
>['samples']['getSampleQuestions']['questions'][number];

/** The sample questions the service offers now; none when the sample news is not stored. */
export async function getSampleQuestions(signal?: AbortSignal): Promise<SampleQuestion[]> {
  const data = await request<unknown>({ url: '/chat/samples', method: 'GET', signal });
  return parseContract(SampleQuestionsSchema, data).questions;
}
