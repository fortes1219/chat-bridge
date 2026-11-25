import { Manager } from 'socket.io-client';

/** The part of a Socket.IO socket the page uses, so tests can hand in a stand-in without a network. */
export interface SocketLike {
  connected: boolean;
  connect(): void;
  disconnect(): void;
  on(event: string, handler: (...args: unknown[]) => void): void;
  off(event: string, handler?: (...args: unknown[]) => void): void;
}

export interface ManagerLike {
  socket(namespace: string): SocketLike;
}

export interface SocketHubDeps {
  createManager?: (uri: string) => ManagerLike;
  origin?: string;
}

export interface SocketHub {
  /** A view starts needing the connection; the first one opens it. Returns the socket. */
  acquire(): SocketLike;
  /** A view stops needing it; the last one closes it. */
  release(): void;
  readonly socket: SocketLike | null;
}

/** Where the service serves Socket.IO, on the page's own origin. */
const SOCKET_PATH = '/socket.io';

function defaultOrigin(): string {
  return typeof window !== 'undefined' ? window.location.origin : '';
}

/**
 * One connection to the service for the whole page. It is opened when the first view needs it and
 * closed when the last one goes, so a page that shows no strategy holds no connection. WebSocket
 * only: the service is on this machine, so a failure shows at once instead of falling back to
 * polling.
 */
export function createSocketHub(deps: SocketHubDeps = {}): SocketHub {
  const origin = deps.origin ?? defaultOrigin();
  const createManager =
    deps.createManager ??
    ((uri: string) =>
      new Manager(uri, {
        path: SOCKET_PATH,
        autoConnect: false,
        reconnection: true,
        transports: ['websocket']
      }) as unknown as ManagerLike);

  let socket: SocketLike | null = null;
  let users = 0;

  function acquire(): SocketLike {
    users += 1;
    if (socket === null) {
      socket = createManager(origin).socket('/');
      socket.connect();
    }
    return socket;
  }

  function release(): void {
    if (users === 0) return;
    users -= 1;
    if (users > 0 || socket === null) return;
    socket.disconnect();
    socket = null;
  }

  return {
    acquire,
    release,
    get socket() {
      return socket;
    }
  };
}

let singleton: SocketHub | null = null;

/** The page's one hub, made on first use. */
export function getSocketHub(): SocketHub {
  if (singleton === null) singleton = createSocketHub();
  return singleton;
}
