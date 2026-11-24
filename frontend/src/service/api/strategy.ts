import type { InferContractRouterInputs, InferContractRouterOutputs } from '@orpc/contract';
import { request } from '@/service/request';
import { parseContract, parseInput } from '@/service/error';
import { DecisionRequestSchema, RulesRequestSchema, StrategySchema } from '@/service/schema/strategy';
import type { contract } from '@/service/contract';

type Outputs = InferContractRouterOutputs<typeof contract>['strategy'];
type Inputs = InferContractRouterInputs<typeof contract>['strategy'];

/** The strategy as the service computes it; `StrategySchema` still checks it at run time. */
export type Strategy = Outputs['getStrategy'];
export type Holding = Strategy['holdings'][number];
export type Proposal = NonNullable<Strategy['proposal']>;
export type DiffRow = Proposal['rows'][number];
export type Valuation = Strategy['valuation'];
export type HoldingValue = Valuation['holdings'][number];
export type Quote = Valuation['quotes'][number];
export type PriceTime = NonNullable<Quote['at']>;
export type DecideInput = Inputs['decideProposal'];
export type Decision = DecideInput['body']['decision'];
export type RuleChecks = Strategy['rule_checks'];
export type RuleCheck = RuleChecks['rules'][number];
export type RulesInput = Inputs['saveRules'];
export type Rule = RulesInput['rules'][number];
export type RuleKind = Rule['kind'];
export type Market = NonNullable<Rule['market']>;

/** The profile, its current targets, and the proposal waiting for the person. */
export async function getStrategy(signal?: AbortSignal): Promise<Strategy> {
  const data = await request<unknown>({ url: '/strategy', method: 'GET', signal });
  return parseContract(StrategySchema, data);
}

/** Accept or reject the open proposal; returns the strategy after it. */
export async function decideProposal({ params, body }: DecideInput, signal?: AbortSignal): Promise<Strategy> {
  const decision = parseInput(DecisionRequestSchema, body);
  const data = await request<unknown>({
    url: `/strategy/proposals/${params.id}/decision`,
    method: 'POST',
    data: decision,
    signal
  });
  return parseContract(StrategySchema, data);
}

/** Replace the person's rules; returns the strategy with the checks recomputed. */
export async function saveRules(input: RulesInput, signal?: AbortSignal): Promise<Strategy> {
  const body = parseInput(RulesRequestSchema, input);
  const data = await request<unknown>({ url: '/strategy/rules', method: 'PUT', data: body, signal });
  return parseContract(StrategySchema, data);
}
