"""The real-time connection that brings the strategy, recomputed from each new price, to the page.

A Socket.IO server mounted inside the service, so the service's Host check covers it too. Its
allowed origins are left at the default, which accepts only the origin of the request's own Host,
so another web page in the browser cannot open it. The page sends nothing on it: every change to
the strategy goes through the endpoints.
"""

import socketio

from chat_bridge.strategy import store
from chat_bridge.strategy.schemas import StrategyView
from chat_bridge.strategy.state import STATE

# The address the page connects to, and the one event it gets.
PATH = "/socket.io"
EVENT = "strategy"

server = socketio.AsyncServer(async_mode="asgi")


def asgi_app() -> socketio.ASGIApp:
    """The server as an app to mount at PATH. The path is given whole, since the mount keeps the
    full path in what it passes on."""
    return socketio.ASGIApp(server, socketio_path=PATH)


async def connect(sid: str, environ: dict[str, object]) -> None:
    """Send the strategy at once, so the page does not wait for the next price."""
    try:
        view = await STATE.view()
    except store.ProfileMissingError:
        return
    await server.emit(EVENT, view.model_dump(mode="json"), to=sid)


server.on("connect", connect)


async def publish(view: StrategyView) -> None:
    """Send the strategy to every open page."""
    await server.emit(EVENT, view.model_dump(mode="json"))
