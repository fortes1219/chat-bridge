import { oc } from '@orpc/contract';
import { z } from 'zod';
import {
  DecisionRequestSchema,
  HoldingsRequestSchema,
  RulesRequestSchema,
  StrategySchema
} from '@/service/schema/strategy';

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
    .output(StrategySchema),
  saveRules: oc
    .route({
      method: 'PUT',
      path: '/strategy/rules',
      summary: 'Replace the person’s rules; the checks come back recomputed'
    })
    .input(RulesRequestSchema)
    .output(StrategySchema),
  saveHoldings: oc
    .route({
      method: 'PUT',
      path: '/strategy/holdings',
      summary: 'Replace the person’s holdings and cash; the prices then follow the saved holdings'
    })
    .input(HoldingsRequestSchema)
    .output(StrategySchema)
};
