"""Pages and feeds collected from saved answers, with no network."""

from collections.abc import Callable
from configparser import ConfigParser
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
import yaml

from chat_bridge.collect import pages
from chat_bridge.collect.pages import Pacing, collect_addresses, file_name
from chat_bridge.ingest.sections import parse_markdown

SITE = "https://news.example.com"
ARTICLE = f"{SITE}/fed"
COLLECTED = datetime(2026, 11, 26, 6, 0, tzinfo=UTC)
HTML = """<!doctype html><html><head><title>Fed holds rates | Example News</title>
<meta property="og:site_name" content="Example News">
{date}</head><body><nav><a href="/">Home</a> | <a href="/markets">Markets menu</a></nav>
<article><h1>Fed holds rates steady</h1>
<p>The Federal Reserve kept its benchmark rate unchanged on Wednesday, the minutes released at 2 p.m. showed.</p>
<p>Officials said further increases may be needed if inflation stays high, and several members favored a larger move.</p>
<p>Analysts expect the next meeting in December to be decisive for the path of policy and markets.</p>
</article><footer>Copyright Example News. Privacy policy.</footer></body></html>"""
DATED = '<meta property="article:published_time" content="2026-11-19T14:05:00-05:00">\n'
FEED = f"""<?xml version="1.0"?><rss version="2.0"><channel><title>Example</title>
<item><title>Fed holds rates</title><link>{ARTICLE}</link><description>Short summary.</description>
<pubDate>Thu, 19 Nov 2026 19:10:00 GMT</pubDate></item>
<item><title>Gone story</title><link>{SITE}/gone</link><description>The gone story in brief.</description>
<pubDate>Wed, 18 Nov 2026 10:00:00 GMT</pubDate></item>
</channel></rss>"""


def _answer(
    body: str | bytes, kind: str, status: int = 200, url: str = ""
) -> pages.Response:
    data = body.encode("utf-8") if isinstance(body, str) else body
    response = pages.Response(data, status, url)
    response.store_headers({"Content-Type": kind})
    response.decode_data(True)
    return response


Answers = dict[str, pages.Response | None]


def _fetch(
    answers: Answers, asked: list[str]
) -> Callable[[str, ConfigParser], pages.Response | None]:
    def fetch(url: str, config: ConfigParser) -> pages.Response | None:
        asked.append(url)
        return answers.get(url)

    return fetch


def _collect(
    urls: list[str], folder: Path, answers: Answers, asked: list[str] | None = None
) -> list[pages.Outcome]:
    calls = asked if asked is not None else []
    robots = {f"{SITE}/robots.txt": _answer("User-agent: *\nAllow: /\n", "text/plain")}
    return collect_addresses(
        urls,
        folder,
        now=lambda: COLLECTED,
        fetch=_fetch({**robots, **answers}, calls),
        pacing=Pacing(wait=0.0, sleep=lambda seconds: None),
    )


def _front(path: Path) -> dict[str, object]:
    loaded: dict[str, object] = yaml.safe_load(
        path.read_text(encoding="utf-8").split("---\n")[1]
    )
    return loaded


def test_a_page_is_written_with_its_main_text_and_ingest_reads_it(
    tmp_path: Path,
) -> None:
    answers: Answers = {
        ARTICLE: _answer(
            HTML.format(date=DATED), "text/html; charset=utf-8", url=ARTICLE
        )
    }

    outcomes = _collect([ARTICLE], tmp_path, answers)

    assert [outcome.kind for outcome in outcomes] == ["written"]
    path = tmp_path / file_name(ARTICLE)
    text = path.read_text(encoding="utf-8")
    assert "kept its benchmark rate unchanged" in text
    assert "Markets menu" not in text and "Privacy policy" not in text
    assert _front(path) == {
        "title": "Fed holds rates steady",
        "url": ARTICLE,
        "site": "Example News",
        "collected": "2026-11-26T06:00:00+00:00",
        "event_date": date(2026, 11, 19),
    }
    assert parse_markdown(text, "fallback").event_date == date(2026, 11, 19)


def test_a_page_without_its_own_date_has_no_event_date(tmp_path: Path) -> None:
    answers: Answers = {
        ARTICLE: _answer(HTML.format(date=""), "text/html", url=ARTICLE)
    }

    _collect([ARTICLE], tmp_path, answers)

    assert "event_date" not in _front(tmp_path / file_name(ARTICLE))


def test_a_page_collected_again_unchanged_is_left_as_it_was(tmp_path: Path) -> None:
    answers: Answers = {
        ARTICLE: _answer(HTML.format(date=DATED), "text/html", url=ARTICLE)
    }
    _collect([ARTICLE], tmp_path, answers)
    path = tmp_path / file_name(ARTICLE)
    first = path.read_bytes()

    outcomes = _collect([ARTICLE], tmp_path, answers)

    assert [outcome.kind for outcome in outcomes] == ["unchanged"]
    assert path.read_bytes() == first


def test_a_feeds_items_are_collected_and_an_unreadable_one_from_its_summary(
    tmp_path: Path,
) -> None:
    feed = f"{SITE}/rss.xml"
    answers: Answers = {
        feed: _answer(FEED, "application/rss+xml"),
        ARTICLE: _answer(HTML.format(date=""), "text/html", url=ARTICLE),
        f"{SITE}/gone": _answer("missing", "text/html", status=404),
    }

    outcomes = _collect([feed], tmp_path, answers)

    assert [outcome.kind for outcome in outcomes] == ["written", "written"]
    article = _front(tmp_path / file_name(ARTICLE))
    assert article["feed"] == feed and article["event_date"] == date(2026, 11, 19)
    gone = (tmp_path / file_name(f"{SITE}/gone")).read_text(encoding="utf-8")
    assert "This file holds the feed's summary of the item" in gone
    assert "status 404" in gone and "The gone story in brief." in gone


@pytest.mark.parametrize(
    ("robots", "allowed"),
    [
        (_answer("User-agent: *\nDisallow: /fed\n", "text/plain"), False),
        (_answer("not here", "text/html", status=404), True),
        (None, False),
        (_answer("down", "text/html", status=503), False),
    ],
    ids=["disallowed", "no robots.txt", "unreachable", "server error"],
)
def test_robots_txt_is_followed_as_rfc_9309_reads_it(
    tmp_path: Path, robots: pages.Response | None, allowed: bool
) -> None:
    asked: list[str] = []
    answers: Answers = {
        ARTICLE: _answer(HTML.format(date=DATED), "text/html", url=ARTICLE)
    }

    outcomes = collect_addresses(
        [ARTICLE],
        tmp_path,
        now=lambda: COLLECTED,
        fetch=_fetch({f"{SITE}/robots.txt": robots, **answers}, asked),
        pacing=Pacing(wait=0.0, sleep=lambda seconds: None),
    )

    assert (ARTICLE in asked) is allowed
    assert outcomes[0].kind == ("written" if allowed else "refused")


def test_a_document_that_is_not_a_page_is_refused_with_what_to_do(
    tmp_path: Path,
) -> None:
    report = f"{SITE}/report.pdf"
    answers: Answers = {report: _answer(b"%PDF-1.7 ...", "application/pdf")}

    outcomes = _collect([report], tmp_path, answers)

    assert outcomes[0].kind == "refused"
    assert (
        "application/pdf" in outcomes[0].detail
        and "ingest the file" in outcomes[0].detail
    )
    assert not list(tmp_path.iterdir())


def test_an_address_that_could_not_be_read_is_named(tmp_path: Path) -> None:
    outcomes = _collect([f"{SITE}/slow"], tmp_path, {f"{SITE}/slow": None})

    assert (outcomes[0].kind, outcomes[0].detail) == ("refused", "it could not be read")


def test_an_address_with_a_user_name_or_password_is_refused(tmp_path: Path) -> None:
    asked: list[str] = []
    secret = "https://user:secret@news.example.com/fed"

    outcomes = _collect([secret], tmp_path, {}, asked)

    assert (
        outcomes[0].kind == "refused" and "user name or password" in outcomes[0].detail
    )
    assert asked == [] and not list(tmp_path.iterdir())


def test_a_file_is_named_from_the_host_alone() -> None:
    assert file_name("https://News.Example.com:8443/a").startswith(
        "news.example.com_8443-"
    )


def test_each_outcome_is_told_as_it_happens(tmp_path: Path) -> None:
    feed = f"{SITE}/rss.xml"
    told: list[str] = []
    robots = {f"{SITE}/robots.txt": _answer("User-agent: *\nAllow: /\n", "text/plain")}
    answers: Answers = {
        **robots,
        feed: _answer(FEED, "application/rss+xml"),
        ARTICLE: _answer(HTML.format(date=""), "text/html", url=ARTICLE),
        f"{SITE}/gone": None,
    }

    collect_addresses(
        [feed],
        tmp_path,
        now=lambda: COLLECTED,
        fetch=_fetch(answers, []),
        pacing=Pacing(wait=0.0, sleep=lambda seconds: None),
        progress=told.append,
    )

    assert told[0] == f"  feed           {feed}: 2 items"
    assert told[1].startswith(f"  written        {ARTICLE}  ->  ")
    assert told[2].startswith(f"  written        {SITE}/gone  ->  ")
    assert len(told) == 3


def test_a_site_is_asked_again_only_after_the_wait() -> None:
    clock = [100.0]
    slept: list[float] = []

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        clock[0] += seconds

    pacing = Pacing(wait=5.0, now=lambda: clock[0], sleep=sleep)
    pacing.before(f"{SITE}/robots.txt")
    clock[0] += 1.5
    pacing.before(ARTICLE)
    pacing.before("https://other.example.org/a")

    assert slept == [3.5]


def test_downloads_refuse_unverified_connections_and_name_the_command() -> None:
    config = pages.download_config()

    assert config["DEFAULT"]["INSECURE_SSL_FALLBACK"] == "off"
    assert config["DEFAULT"]["USER_AGENTS"].startswith("chat-bridge/")
    assert config["DEFAULT"]["SSRF_PROTECTION"] == "on"
    assert config["DEFAULT"]["MAX_FILE_SIZE"] == "20000000"
