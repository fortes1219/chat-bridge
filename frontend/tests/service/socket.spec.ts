import { describe, expect, it } from 'vitest';
import { createSocketHub } from '@/service/socket/manager';
import { parseStrategyEvent } from '@/service/socket/strategy';
import { STRATEGY } from '../helpers/strategy';
import { standInManager, standInSockets } from '../helpers/socket';

describe('the socket hub', () => {
  it('opens one connection for every view that needs it and closes it after the last one', () => {
    const made = standInSockets.length;
    const hub = createSocketHub({ createManager: standInManager, origin: 'http://127.0.0.1:8000' });

    const first = hub.acquire();
    const second = hub.acquire();
    hub.release();
    const socket = standInSockets.at(-1);

    expect(second).toBe(first);
    expect(standInSockets.length).toBe(made + 1);
    expect(socket?.connects).toBe(1);
    expect(socket?.disconnects).toBe(0);
    hub.release();
    expect(socket?.disconnects).toBe(1);
    expect(hub.socket).toBeNull();
    hub.release();
    expect(socket?.disconnects).toBe(1);
  });
});

describe('the strategy event', () => {
  it('is the strategy when it matches the schema', () => {
    expect(parseStrategyEvent(STRATEGY)).toEqual(STRATEGY);
  });

  it.each([
    ['a missing valuation', { ...STRATEGY, valuation: undefined }],
    ['a field the strategy does not have', { ...STRATEGY, extra: 1 }],
    ['a price that is not a number', { ...STRATEGY, valuation: { ...STRATEGY.valuation, total_value: '1e6' } }],
    ['nothing', null]
  ])('is null for %s', (_, raw) => {
    expect(parseStrategyEvent(raw)).toBeNull();
  });
});
