"""What `chat-bridge ingest` prints and returns, with the ingest itself stubbed: no database is
read and no model is loaded."""

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from chat_bridge.cli import EXIT_ERROR, EXIT_OK, main
from chat_bridge.ingest import service as ingest_service
from chat_bridge.ingest.service import IngestReport


@dataclass
class StandIn:
    """The report the stubbed ingest returns, and each folder it was given with the option."""

    report: IngestReport = field(default_factory=IngestReport)
    runs: list[tuple[Path, bool]] = field(default_factory=list)


@pytest.fixture
def stand_in(monkeypatch: pytest.MonkeyPatch) -> StandIn:
    made = StandIn()

    async def ingest(root: Path, *, replace: bool = False) -> IngestReport:
        made.runs.append((root, replace))
        return made.report

    monkeypatch.setattr(ingest_service, "ingest_folder", ingest)
    return made


@pytest.mark.parametrize(("option", "replace"), [([], False), (["--replace"], True)])
def test_the_option_asks_to_replace(
    stand_in: StandIn, tmp_path: Path, option: list[str], replace: bool
) -> None:
    assert main(["ingest", str(tmp_path), *option]) == EXIT_OK

    assert stand_in.runs == [(tmp_path.resolve(), replace)]


def test_removed_documents_are_listed(
    stand_in: StandIn, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stand_in.report.not_in_folder.extend(["a.md", "b.md"])

    main(["ingest", str(tmp_path), "--replace"])

    out = capsys.readouterr().out
    assert "Removed 2 documents that are not in" in out
    assert "  a.md\n  b.md\n" in out


def test_without_replace_the_other_documents_are_counted_and_the_option_named(
    stand_in: StandIn, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stand_in.report.others_kept = 71

    assert main(["ingest", str(tmp_path)]) == EXIT_OK

    out = capsys.readouterr().out
    assert "also holds 71 documents that are not in" in out
    assert "Run with --replace to keep only this folder's documents." in out


def test_nothing_is_said_about_other_documents_when_there_are_none(
    stand_in: StandIn, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["ingest", str(tmp_path)])

    out = capsys.readouterr().out
    assert "--replace" not in out
    assert "Removed" not in out


def test_a_refused_replacement_fails_and_says_nothing_changed(
    stand_in: StandIn, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stand_in.report.replace_refused = True

    assert main(["ingest", str(tmp_path), "--replace"]) == EXIT_ERROR

    captured = capsys.readouterr()
    assert "nothing was replaced" in captured.err
    assert "Written:" not in captured.out
