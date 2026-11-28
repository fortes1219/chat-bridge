"""The chat service: one FastAPI app that only this machine can reach.

It listens on 127.0.0.1 and not on 0.0.0.0, which would let other machines on the network
reach it.

It also refuses a request whose Host header names any other host. A web page the user has open
can send requests to 127.0.0.1. With a host name it controls that points at 127.0.0.1, it could
also read the replies; its own host name in the Host header gives it away.

JSON request bodies keep FastAPI's strict Content-Type check, which stops a page from posting a
question without the browser first asking the service for permission. No CORS rule is added, so
that permission is never given.
"""

import asyncio
import json
import logging
import socket
import threading
import time
import urllib.request
import webbrowser
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, closing
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from chat_bridge import web
from chat_bridge.chat import service as chat_service
from chat_bridge.chat.router import router
from chat_bridge.chat.samples import SAMPLE_NEWS
from chat_bridge.cli import EXIT_OK, print_error
from chat_bridge.config import PROJECT_ROOT
from chat_bridge.database import stop_server
from chat_bridge.embedding import load_model
from chat_bridge.errors import LocalSetupError
from chat_bridge.ingest import service as ingest_service
from chat_bridge.strategy import realtime
from chat_bridge.strategy.prices import PriceSource, YahooPrices
from chat_bridge.strategy.router import router as strategy_router
from chat_bridge.strategy.sample import SAMPLE_PROFILE, load_sample_if_empty
from chat_bridge.strategy.state import STATE

logger = logging.getLogger(__name__)

TITLE = "chat-bridge"
HOST = "127.0.0.1"
# The port FastAPI's own commands use, so the address in its docs and examples is this one.
PORT = 8000
ADDRESS = f"http://{HOST}:{PORT}"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
# How long to wait for the service to accept connections before giving up on opening the page.
BROWSER_WAIT_SECONDS = 30
# How long Ctrl+C waits for open connections before the service stops anyway. On Windows, a
# connection the browser dropped without closing (a tab or browser that crashed) can stay counted
# as open: asyncio's proactor raises ConnectionResetError in `_call_connection_lost` at
# `sock.shutdown()` before it detaches the connection from the server, so `Server.wait_closed()`
# never returns and the service, its price stream and its database would not stop. uvicorn's
# graceful shutdown timeout bounds that wait. It also cuts an answer still coming in: Ctrl+C
# means stop, and the cut answer is still recorded (service.finish_answers). Five seconds, not a
# production server's 30, so Ctrl+C does not look frozen.
SHUTDOWN_WAIT_SECONDS = 5


def create_app(page: Path | None = None, prices: PriceSource | None = None) -> FastAPI:
    """The service, and the built chat page at `/` when `page` names its folder.

    `prices` is where the strategy screen's prices come from; without one, prices are missing.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await STATE.start(prices, [realtime.publish])
        try:
            yield
        finally:
            # An answer that the shutdown limit cut off writes its record as it ends; the
            # database it writes to stops below.
            await chat_service.finish_answers(SHUTDOWN_WAIT_SECONDS)
            await STATE.stop()
            # After Ctrl+C or Ctrl+Break, uvicorn shuts down and then raises the same signal
            # again to end the process. A process ended that way never runs its exit hooks, and
            # the embedded database stops in one of them, so it is stopped here, while shutting
            # down.
            stop_server()

    app = FastAPI(title=TITLE, lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
    app.include_router(router)
    app.include_router(strategy_router)
    # Inside the app, so the Host check above covers the real-time connection too.
    app.mount(realtime.PATH, realtime.asgi_app())
    if page is not None:
        # After the service's routes, so the page's fallback never answers for them.
        web.mount_page(app, page)
    return app


def port_is_free(host: str, port: int) -> bool:
    """Whether the port can be bound, checked before the service starts so a taken port is
    explained in words instead of as the operating system's error."""
    try:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.bind((host, port))
    except OSError:
        return False
    return True


def runs_chat_bridge(address: str) -> bool:
    """Whether the program answering at the address is this service: its API document names it."""
    try:
        with urllib.request.urlopen(f"{address}/openapi.json", timeout=2) as response:
            return bool(json.load(response).get("info", {}).get("title") == TITLE)
    except (OSError, ValueError):
        return False


def open_when_ready(host: str, port: int, address: str) -> None:
    """Open the page in the default browser once the service accepts connections."""
    deadline = time.monotonic() + BROWSER_WAIT_SECONDS
    while time.monotonic() < deadline:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                webbrowser.open(address)
                return
        time.sleep(0.2)


def prepare_knowledge_base() -> None:
    """Make the knowledge base usable before any question, so one command is enough to ask: a
    knowledge base an earlier version made is cleared, an index built another way is rebuilt,
    and the sample news is ingested when nothing has been. The profile and the question records
    are kept."""
    refreshed = asyncio.run(ingest_service.refresh_index())
    if refreshed.outdated:
        logger.info(
            "The knowledge base was made by an earlier version of chat-bridge (%s), so it was "
            "cleared and is made again. Ingest any folder of your own documents again.",
            "; ".join(refreshed.outdated),
        )
    elif refreshed.index_update is not ingest_service.IndexUpdate.NONE:
        logger.info(
            "The search index was built another way, so it was rebuilt (%s).",
            refreshed.index_update,
        )
    if not asyncio.run(ingest_service.knowledge_base_is_empty()):
        return
    logger.info(
        "The knowledge base is empty, so the sample news in %s is ingested first. The first "
        "time, this downloads a word list and a 2.3 GB embedding model and can take several "
        "minutes.",
        SAMPLE_NEWS.relative_to(PROJECT_ROOT).as_posix(),
    )
    report = asyncio.run(ingest_service.ingest_folder(SAMPLE_NEWS))
    logger.info(
        "Ingested %d files, %d sections.", len(report.written), report.sections_written
    )


def prepare_profile() -> None:
    """Load the simulated sample profile when there is none, so the strategy screen has one."""
    if asyncio.run(load_sample_if_empty()):
        logger.info(
            "Loaded the simulated sample profile from %s.",
            SAMPLE_PROFILE.relative_to(PROJECT_ROOT).as_posix(),
        )


def serve(open_browser: bool = True) -> int:
    """Build the chat page and fill an empty knowledge base if needed, run the service until
    Ctrl+C, and open the page.

    The port is checked first: when chat-bridge is already running, a second start neither
    rebuilds the page that service is serving nor opens the database it is using.
    """
    if not port_is_free(HOST, PORT):
        if not runs_chat_bridge(ADDRESS):
            return print_error(
                f"port {PORT} on {HOST} is used by another program. Stop that program, then "
                "run the command again."
            )
        logger.info("Already running. The chat page is at %s", ADDRESS)
        if open_browser:
            webbrowser.open(ADDRESS)
        return EXIT_OK
    try:
        page = web.prepare_page()
        prepare_knowledge_base()
        prepare_profile()
        # Loaded before requests are taken, so the first question does not wait for it.
        logger.info("Loading the embedding model.")
        load_model()
    except LocalSetupError as error:
        return print_error(str(error))
    logger.info("The chat page is at %s. Stop the service with Ctrl+C.", ADDRESS)
    if open_browser:
        threading.Thread(
            target=open_when_ready, args=(HOST, PORT, ADDRESS), daemon=True
        ).start()
    uvicorn.run(
        create_app(page, YahooPrices()),
        host=HOST,
        port=PORT,
        timeout_graceful_shutdown=SHUTDOWN_WAIT_SECONDS,
    )
    return EXIT_OK
