import os
import subprocess
import sys
from pathlib import Path

import chat_bridge


def test_package_imports_with_version() -> None:
    assert chat_bridge.__version__


def test_cli_version_exits_zero() -> None:
    exe = Path(sys.executable).parent / (
        "chat-bridge.exe" if os.name == "nt" else "chat-bridge"
    )
    result = subprocess.run(
        [str(exe), "--version"], capture_output=True, text=True, encoding="utf-8"
    )
    assert result.returncode == 0
    assert result.stdout.strip() == f"chat-bridge {chat_bridge.__version__}"
