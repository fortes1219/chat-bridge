import { defineStore } from 'pinia';
import { ref } from 'vue';

export type SocketConnectionState = 'disconnected' | 'connecting' | 'connected';

/**
 * The real-time connection's own state, for the page to say whether prices are updating. The
 * strategy it brings is server data and goes into the query cache, not here.
 */
export const useStrategySocketStore = defineStore('strategy-socket', () => {
  const connectionState = ref<SocketConnectionState>('disconnected');
  /** Events that did not match the strategy's schema and were not drawn. */
  const invalidPayloadCount = ref(0);

  function setConnectionState(state: SocketConnectionState): void {
    connectionState.value = state;
  }

  function countInvalid(): void {
    invalidPayloadCount.value += 1;
  }

  return { connectionState, invalidPayloadCount, setConnectionState, countInvalid };
});
