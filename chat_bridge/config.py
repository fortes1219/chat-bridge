"""Where the app keeps its run-time data.

The layout follows private-gpt: run-time data lives in a `local_data` folder at the
project root that git ignores. Set `CHAT_BRIDGE_LOCAL_DATA` to use another folder.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_DATA_ENV = "CHAT_BRIDGE_LOCAL_DATA"


def local_data_dir() -> Path:
    """Return the run-time data folder, creating it on first use."""
    configured = os.environ.get(LOCAL_DATA_ENV)
    path = (
        Path(configured).expanduser().resolve()
        if configured
        else PROJECT_ROOT / "local_data"
    )
    path.mkdir(parents=True, exist_ok=True)
    return path
