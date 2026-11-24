import { vi } from 'vitest';

// Every view that shows the strategy opens the page's one real-time connection. In the tests it is
// made by a stand-in manager, so nothing reaches the network and a test can send it events.
vi.mock('@/service/socket/manager', async importOriginal => {
  const actual = await importOriginal<typeof import('@/service/socket/manager')>();
  const { standInManager } = await import('./helpers/socket');
  const hub = actual.createSocketHub({ createManager: standInManager, origin: 'http://127.0.0.1:8000' });
  return { ...actual, getSocketHub: () => hub };
});
