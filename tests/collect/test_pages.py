"""Pages and feeds read from saved answers, with no network."""

from collections.abc import Callable
from configparser import ConfigParser
from datetime import date

import pytest

from chat_bridge.collect import pages
from chat_bridge.collect.pages import Pacing, Reader

SITE = "https://news.example.com"
ARTICLE = f"{SITE}/fed"
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
ALLOW_ALL = "User-agent: *\nAllow: /\n"


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


def _reader(
    answers: Answers,
    asked: list[str] | None = None,
    told: list[str] | None = None,
    robots: pages.Response | None = None,
) -> Reader:
    calls = asked if asked is not None else []
    rules = {f"{SITE}/robots.txt": robots or _answer(ALLOW_ALL, "text/plain")}
    return Reader(
        fetch=_fetch({**rules, **answers}, calls),
        pacing=Pacing(wait=0.0, sleep=lambda seconds: None),
        progress=(told.append if told is not None else lambda line: None),
    )


def test_a_page_is_read_as_its_main_text_with_title_site_and_date() -> None:
    answers: Answers = {
        ARTICLE: _answer(
            HTML.format(date=DATED), "text/html; charset=utf-8", url=ARTICLE
        )
    }

    read = _reader(answers).read_addresses([ARTICLE])

    assert read.refused == ()
    page = read.pages[0]
    assert "kept its benchmark rate unchanged" in page.text
    assert "Markets menu" not in page.text and "Privacy policy" not in page.text
    assert (page.asked, page.url, page.title, page.site, page.published) == (
        ARTICLE,
        ARTICLE,
        "Fed holds rates steady",
        "Example News",
        date(2026, 11, 19),
    )


def test_a_page_without_its_own_date_has_none() -> None:
    answers: Answers = {
        ARTICLE: _answer(HTML.format(date=""), "text/html", url=ARTICLE)
    }

    assert _reader(answers).read_addresses([ARTICLE]).pages[0].published is None


def test_a_feeds_items_are_read_and_an_unreadable_one_is_refused_not_summarised() -> (
    None
):
    feed = f"{SITE}/rss.xml"
    told: list[str] = []
    answers: Answers = {
        feed: _answer(FEED, "application/rss+xml"),
        ARTICLE: _answer(HTML.format(date=""), "text/html", url=ARTICLE),
        f"{SITE}/gone": _answer("missing", "text/html", status=404),
    }

    read = _reader(answers, told=told).read_addresses([feed])

    assert [page.url for page in read.pages] == [ARTICLE]
    assert read.refused == (
        pages.Refusal(f"{SITE}/gone", "the site answered with status 404"),
    )
    assert told == [
        f"    feed      {feed}: 2 items",
        f"    read      {ARTICLE}",
        f"    not read  {SITE}/gone: the site answered with status 404",
    ]


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
    robots: pages.Response | None, allowed: bool
) -> None:
    asked: list[str] = []
    answers: Answers = {
        f"{SITE}/robots.txt": robots,
        ARTICLE: _answer(HTML.format(date=DATED), "text/html", url=ARTICLE),
    }
    reader = Reader(
        fetch=_fetch(answers, asked),
        pacing=Pacing(wait=0.0, sleep=lambda seconds: None),
    )

    read = reader.read_addresses([ARTICLE])

    assert (ARTICLE in asked) is allowed
    assert bool(read.pages) is allowed


def test_a_redirect_to_another_site_is_read_only_when_its_robots_txt_allows_it() -> (
    None
):
    elsewhere = "https://mirror.example.org/fed"
    asked: list[str] = []
    answers: Answers = {
        ARTICLE: _answer(HTML.format(date=DATED), "text/html", url=elsewhere),
        "https://mirror.example.org/robots.txt": _answer(
            "User-agent: *\nDisallow: /\n", "text/plain"
        ),
    }

    read = _reader(answers, asked).read_addresses([ARTICLE])

    assert read.pages == ()
    assert read.refused == (
        pages.Refusal(
            ARTICLE, f"it moved to {elsewhere}, whose robots.txt does not allow it"
        ),
    )
    assert "https://mirror.example.org/robots.txt" in asked


def test_robots_txt_is_read_once_for_the_events_of_a_run() -> None:
    asked: list[str] = []
    answers: Answers = {
        ARTICLE: _answer(HTML.format(date=DATED), "text/html", url=ARTICLE)
    }
    reader = _reader(answers, asked)

    reader.read_addresses([ARTICLE])
    reader.read_addresses([ARTICLE])

    assert asked.count(f"{SITE}/robots.txt") == 1


def test_a_document_that_is_not_a_page_is_refused_with_what_to_do() -> None:
    report = f"{SITE}/report.pdf"
    answers: Answers = {report: _answer(b"%PDF-1.7 ...", "application/pdf")}

    read = _reader(answers).read_addresses([report])

    assert read.pages == ()
    assert "application/pdf" in read.refused[0].reason
    assert "ingest the file" in read.refused[0].reason


def test_an_address_that_could_not_be_read_is_named() -> None:
    read = _reader({f"{SITE}/slow": None}).read_addresses([f"{SITE}/slow"])

    assert read.refused == (pages.Refusal(f"{SITE}/slow", "it could not be read"),)


def test_an_address_with_a_user_name_or_password_is_refused() -> None:
    asked: list[str] = []
    secret = "https://user:secret@news.example.com/fed"

    read = _reader({}, asked).read_addresses([secret])

    assert "user name or password" in read.refused[0].reason
    assert asked == []


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
