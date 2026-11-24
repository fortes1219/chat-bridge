import { oc } from '@orpc/contract';
import { z } from 'zod';
import { DecisionRequestSchema, StrategySchema } from '@/service/schema/strategy';

/** The strategy screen's calls (oRPC, types only: nothing calls it at run time). */
export const strategyContract = {
  getStrategy: oc
    .route({
      method: 'GET',
      path: '/strategy',
      summary: 'The profile, its current targets, and the proposal waiting for the person'
    })
    .output(StrategySchema),
  decideProposal: oc
    .route({
      method: 'POST',
      path: '/strategy/proposals/{id}/decision',
      summary: 'Accept or reject the open proposal',
      inputStructure: 'detailed'
    })
    .input(
      z.object({
        params: z.object({ id: z.number().int().positive() }).strict(),
        body: DecisionRequestSchema
      })
    )
    .output(StrategySchema)
};
