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

import uvicorn
from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from chat_bridge.chat.router import router
from chat_bridge.cli import EXIT_OK

HOST = "127.0.0.1"
# The port FastAPI's own commands use, so the address in its docs and examples is this one.
PORT = 8000
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


def create_app() -> FastAPI:
    app = FastAPI(title="chat-bridge")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
    app.include_router(router)
    return app


def serve() -> int:
    """Run the chat service until it is stopped with Ctrl+C."""
    uvicorn.run(create_app(), host=HOST, port=PORT)
    return EXIT_OK
