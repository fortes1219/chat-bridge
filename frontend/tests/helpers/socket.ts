import type { ManagerLike, SocketLike } from '@/service/socket/manager';

type Handler = (...args: unknown[]) => void;

/** A Socket.IO socket with no network: a test makes it receive events and drop its connection. */
export class StandInSocket implements SocketLike {
  connected = false;
  connects = 0;
  disconnects = 0;
  private readonly handlers = new Map<string, Set<Handler>>();

  /** As a real socket, it is connected only once the service answers: `receive('connect')`. */
  connect(): void {
    this.connects += 1;
  }

  disconnect(): void {
    this.connected = false;
    this.disconnects += 1;
  }

  on(event: string, handler: Handler): void {
    const set = this.handlers.get(event) ?? new Set<Handler>();
    set.add(handler);
    this.handlers.set(event, set);
  }

  off(event: string, handler?: Handler): void {
    if (handler === undefined) this.handlers.delete(event);
    else this.handlers.get(event)?.delete(handler);
  }

  /** The service sends an event, or the connection changes: `connect`, `disconnect`. */
  receive(event: string, ...args: unknown[]): void {
    if (event === 'connect') this.connected = true;
    if (event === 'disconnect') this.connected = false;
    for (const handler of this.handlers.get(event) ?? []) handler(...args);
  }

  listeners(event: string): number {
    return this.handlers.get(event)?.size ?? 0;
  }
}

/** Every socket the stand-in manager made, the latest last. */
export const standInSockets: StandInSocket[] = [];

export function latestSocket(): StandInSocket {
  const socket = standInSockets.at(-1);
  if (socket === undefined) throw new Error('no socket was opened');
  return socket;
}

export function standInManager(): ManagerLike {
  return {
    socket: () => {
      const socket = new StandInSocket();
      standInSockets.push(socket);
      return socket;
    }
  };
}
