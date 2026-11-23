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
from chat_bridge.chat.router import router
from chat_bridge.cli import EXIT_OK, print_error
from chat_bridge.config import PROJECT_ROOT
from chat_bridge.database import stop_server
from chat_bridge.errors import LocalSetupError
from chat_bridge.ingest import service as ingest_service

logger = logging.getLogger(__name__)

TITLE = "chat-bridge"
HOST = "127.0.0.1"
# The port FastAPI's own commands use, so the address in its docs and examples is this one.
PORT = 8000
ADDRESS = f"http://{HOST}:{PORT}"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
# How long to wait for the service to accept connections before giving up on opening the page.
BROWSER_WAIT_SECONDS = 30
# The sample news the README ingests first; a fresh clone answers from it with no other command.
SAMPLE_NEWS = PROJECT_ROOT / "data" / "truth"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    # After Ctrl+C or Ctrl+Break, uvicorn shuts down and then raises the same signal again to end
    # the process. A process ended that way never runs its exit hooks, and the embedded database
    # stops in one of them, so it is stopped here, while shutting down.
    stop_server()


def create_app(page: Path | None = None) -> FastAPI:
    """The service, and the built chat page at `/` when `page` names its folder."""
    app = FastAPI(title=TITLE, lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
    app.include_router(router)
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
    """Ingest the sample news when nothing has been ingested, so one command is enough to ask.

    A database made by another version is not deleted here: it also holds the question records,
    so the error says what to delete and the person decides.
    """
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
    except LocalSetupError as error:
        return print_error(str(error))
    logger.info("The chat page is at %s. Stop the service with Ctrl+C.", ADDRESS)
    if open_browser:
        threading.Thread(
            target=open_when_ready, args=(HOST, PORT, ADDRESS), daemon=True
        ).start()
    uvicorn.run(create_app(page), host=HOST, port=PORT)
    return EXIT_OK
