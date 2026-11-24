import { computed, onBeforeUnmount, onMounted, type ComputedRef } from 'vue';
import { useQueryClient } from '@tanstack/vue-query';
import { strategyKeys } from '@/queries/keys';
import { getSocketHub, type SocketHub, type SocketLike } from '@/service/socket/manager';
import { parseStrategyEvent, STRATEGY_EVENT } from '@/service/socket/strategy';
import { useStrategySocketStore, type SocketConnectionState } from '@/stores/strategy-socket';

/**
 * Keeps the strategy current while the view is shown: each `strategy` event the service sends is
 * checked and written into the strategy query's cache, so the strategy has one copy in the page.
 * The connection is taken when the view mounts and given back when it goes.
 */
export function useStrategySocket(hub: SocketHub = getSocketHub()): {
  connectionState: ComputedRef<SocketConnectionState>;
  invalidUpdates: ComputedRef<number>;
} {
  const queryClient = useQueryClient();
  const store = useStrategySocketStore();
  let socket: SocketLike | null = null;

  function onStrategy(raw: unknown): void {
    const strategy = parseStrategyEvent(raw);
    if (strategy === null) {
      store.countInvalid();
      return;
    }
    queryClient.setQueryData(strategyKeys.current(), strategy);
  }
  const onConnect = (): void => store.setConnectionState('connected');
  // The connection tries again on its own after a drop.
  const onDisconnect = (): void => store.setConnectionState('connecting');

  onMounted(() => {
    socket = hub.acquire();
    socket.on(STRATEGY_EVENT, onStrategy);
    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    store.setConnectionState(socket.connected ? 'connected' : 'connecting');
  });

  onBeforeUnmount(() => {
    if (socket === null) return;
    socket.off(STRATEGY_EVENT, onStrategy);
    socket.off('connect', onConnect);
    socket.off('disconnect', onDisconnect);
    socket = null;
    hub.release();
    if (hub.socket === null) store.setConnectionState('disconnected');
  });

  return {
    connectionState: computed(() => store.connectionState),
    invalidUpdates: computed(() => store.invalidPayloadCount)
  };
}
