#!/bin/sh
# Runs the slow tests inside the container that compose.test.yml starts. The files the
# tests need are mounted read-only at /src; this copies them into /work, installs the locked
# dependencies into the /venv volume, and runs the tests marked slow. Arguments go to
# pytest. Nothing is written back to /src.
set -eu

for item in chat_bridge tests data pyproject.toml uv.lock README.md .python-version; do
  cp -R "/src/$item" /work/
done

uv sync --locked

# The project's local_data/ is not mounted, so the Traditional Chinese dictionary is
# downloaded once here, into /work/local_data, by the app's own checked download. The tests
# copy it from there, so it is not downloaded again for every test database.
uv run --locked python -c "from chat_bridge.tokenizer import ensure_dictionary; ensure_dictionary()"

# Replace the shipped vector.so with the portable build (see Dockerfile.test). with_llvm=no
# skips the LLVM bitcode, which would need clang.
PG_CONFIG=/venv/lib/python3.13/site-packages/pixeltable_pgserver/pginstall/bin/pg_config
make -s -C /opt/pgvector OPTFLAGS="" with_llvm=no PG_CONFIG="$PG_CONFIG" clean all install

uv run --locked pytest -m slow -p no:cacheprovider "$@"
