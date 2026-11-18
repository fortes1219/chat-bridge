"""`chat-bridge` 指令的進入點。

之後這裡會依序起內嵌資料庫、導入範例資料、起 API、印出網址；目前只有版本與說明。
"""

import argparse

from chat_bridge import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chat-bridge", description="A RAG demo over market news.")
    parser.add_argument("--version", action="version", version=f"chat-bridge {__version__}")
    parser.parse_args(argv)
    print("chat-bridge: only the development environment is set up so far; there is no service to start yet.")
    return 0
