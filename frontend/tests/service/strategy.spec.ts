import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PROPOSAL, STRATEGY } from '../helpers/strategy';

const requestMock = vi.fn();
vi.mock('@/service/request', () => ({
  request: (...args: unknown[]) => requestMock(...args)
}));

import { contract } from '@/service/contract';
import { decideProposal, getStrategy } from '@/service/api/strategy';
import { StrategySchema } from '@/service/schema/strategy';
import { ChatEventSchema } from '@/service/schema/chat';

beforeEach(() => {
  requestMock.mockReset();
});

describe('StrategySchema', () => {
  it('accepts the strategy with and without an open proposal', () => {
    expect(StrategySchema.parse(STRATEGY)).toEqual(STRATEGY);
    expect(StrategySchema.parse({ ...STRATEGY, proposal: PROPOSAL }).proposal?.id).toBe(5);
  });

  it('refuses an amount sent as a number, which a float could round', () => {
    const [first, ...rest] = STRATEGY.holdings;
    expect(() => StrategySchema.parse({ ...STRATEGY, holdings: [{ ...first, quantity: 2000 }, ...rest] })).toThrow();
  });

  it('refuses a target outside 0 to 100, a market or status it does not know, and any extra field', () => {
    expect(() => StrategySchema.parse({ ...STRATEGY, targets: [{ symbol: 'CASH', current: 101 }] })).toThrow();
    const [first, ...rest] = STRATEGY.holdings;
    expect(() => StrategySchema.parse({ ...STRATEGY, holdings: [{ ...first, market: 'JP' }, ...rest] })).toThrow();
    expect(() => StrategySchema.parse({ ...STRATEGY, proposal: { ...PROPOSAL, status: 'pending' } })).toThrow();
    expect(() => StrategySchema.parse({ ...STRATEGY, extra: 1 })).toThrow();
  });
});

describe('the proposal event of the chat stream', () => {
  it('accepts a kept proposal, a refusal, and neither', () => {
    const event = { type: 'response.proposal', delta: null, context: null };
    expect(ChatEventSchema.parse({ ...event, proposal: { proposal: PROPOSAL, refused: null } }).type).toBe(
      'response.proposal'
    );
    expect(() =>
      ChatEventSchema.parse({ ...event, proposal: { proposal: null, refused: { code: 'not_100', message: 'm' } } })
    ).not.toThrow();
    expect(() => ChatEventSchema.parse({ ...event, proposal: { proposal: null, refused: null } })).not.toThrow();
  });

  it('refuses a refusal reason it does not know', () => {
    expect(() =>
      ChatEventSchema.parse({
        type: 'response.proposal',
        delta: null,
        context: null,
        proposal: { proposal: null, refused: { code: 'too_risky', message: 'm' } }
      })
    ).toThrow();
  });
});

describe('getStrategy', () => {
  it('reads the contract’s path and returns the checked strategy', async () => {
    requestMock.mockResolvedValue(STRATEGY);

    expect(await getStrategy()).toEqual(STRATEGY);
    expect(contract.strategy.getStrategy['~orpc'].route.path).toBe('/strategy');
    expect(requestMock).toHaveBeenCalledWith(expect.objectContaining({ url: '/strategy', method: 'GET' }));
  });

  it('throws a contract error on a drifted response', async () => {
    requestMock.mockResolvedValue({ ...STRATEGY, targets: 'none' });

    await expect(getStrategy()).rejects.toMatchObject({ code: 'contract_error' });
  });
});

describe('decideProposal', () => {
  it('posts the decision as a JSON body to the proposal’s path', async () => {
    requestMock.mockResolvedValue(STRATEGY);

    await decideProposal({ params: { id: 5 }, body: { decision: 'accept' } });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        url: '/strategy/proposals/5/decision',
        method: 'POST',
        data: { decision: 'accept' }
      })
    );
  });

  it('checks the decision before anything is sent', async () => {
    await expect(
      decideProposal({ params: { id: 5 }, body: { decision: 'approve' as 'accept' } })
    ).rejects.toMatchObject({ code: 'invalid_input' });
    expect(requestMock).not.toHaveBeenCalled();
  });
});
