"""The section's rows, notes and first line, from fixed closes worked out by hand."""

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from chat_bridge.collect.closes import SeriesCloses
from chat_bridge.collect.markets import Backup, Market, MarketSeries, Series
from chat_bridge.collect.moves import NO_DATA, NOT_YET, Event, section

TAIPEI = ZoneInfo("Asia/Taipei")
NEW_YORK = ZoneInfo("America/New_York")
US = Market("US", "美股", NEW_YORK, time(9, 30), time(16))
TW = Market("TW", "台股", TAIPEI, time(9), time(13, 30))
TAIEX = Series("^TWII", "加權指數", TW, Backup("finmind", "TAIEX"))
SP500 = Series("^GSPC", "S&P 500", US, None)
LISTED = MarketSeries((US, TW), (TAIEX, SP500))


def _closes(values: dict[int, float], **kwargs: object) -> SeriesCloses:
    found = SeriesCloses(
        closes={date(2026, 11, day): close for day, close in values.items()}
    )
    for name, days in kwargs.items():
        getattr(found, name).update(date(2026, 11, day) for day in days)  # type: ignore[attr-defined]
    return found


# The TAIEX closes of 2026-11-18 to 2026-11-25, and the S&P 500's of the same days.
TAIEX_CLOSES = {
    18: 40194.91,
    19: 38426.89,
    20: 36033.29,
    23: 36811.89,
    24: 40122.35,
    25: 38195.43,
}
SP500_CLOSES = {18: 7330.0, 19: 7183.0, 20: 6910.39, 23: 7237.9, 24: 7200.0, 25: 7180.0}


def _cells(lines: tuple[str, ...], name: str) -> list[str]:
    row = next(line for line in lines if line.startswith(f"| {name} |"))
    return [cell.strip() for cell in row.strip("|").split("|")]


def test_a_market_day_event_gives_the_changes_worked_out_by_hand() -> None:
    event = Event(date(2026, 11, 24), TW, datetime(2026, 11, 24, 13, 30, tzinfo=TAIPEI))
    closes = {"^TWII": _closes(TAIEX_CLOSES), "^GSPC": _closes(SP500_CLOSES)}

    cells = _cells(section(event, LISTED, closes).lines, "加權指數")

    # 36811.89 / 36033.29, 40122.35 / 36811.89, 38195.43 / 40122.35; day +5 is not in the data.
    assert cells == [
        "加權指數",
        "2026-11-24",
        "2026-11-23",
        "36811.89",
        "+2.16%",
        "2026-11-24",
        "40122.35",
        "+8.99%",
        "-4.80%",
        NO_DATA,
        "",
    ]


def test_an_event_during_the_us_session_is_noted_and_reaches_taiwan_the_next_day() -> (
    None
):
    event = Event(
        date(2026, 11, 18), US, datetime(2026, 11, 18, 14, 0, tzinfo=NEW_YORK)
    )
    closes = {"^TWII": _closes(TAIEX_CLOSES), "^GSPC": _closes(SP500_CLOSES)}

    lines = section(event, LISTED, closes).lines

    us, tw = _cells(lines, "S&P 500"), _cells(lines, "加權指數")
    assert (us[5], tw[5]) == ("2026-11-18", "2026-11-19")
    assert us[10].startswith("事件發生在 D0 這一盤的交易時間內")
    assert tw[10] == ""
    assert "事件時刻：2026-11-18T14:00:00-05:00（event_time）" in lines[2]


def test_a_day_0_the_data_does_not_have_yet_is_a_row_without_data() -> None:
    event = Event(
        date(2026, 11, 25), US, datetime(2026, 11, 25, 16, 30, tzinfo=NEW_YORK)
    )
    closes = {"^TWII": _closes(TAIEX_CLOSES), "^GSPC": _closes(SP500_CLOSES)}

    cells = _cells(section(event, LISTED, closes).lines, "S&P 500")

    assert cells[2:10] == [NO_DATA] * 8 and cells[10] == NOT_YET


def test_a_day_from_the_backup_is_named_and_the_backup_is_a_data_source() -> None:
    event = Event(date(2026, 11, 24), TW, datetime(2026, 11, 24, 13, 30, tzinfo=TAIPEI))
    closes = {
        "^TWII": _closes(TAIEX_CLOSES, filled=[24]),
        "^GSPC": _closes(SP500_CLOSES),
    }

    result = section(event, LISTED, closes)

    assert result.uses_backup
    assert "資料來源 d1、d2" in result.lines[2]
    assert _cells(result.lines, "加權指數")[10] == "2026-11-24 的收盤取自 FinMind"


def test_a_session_a_series_lacks_is_named_and_its_cells_have_no_data() -> None:
    lacking = {day: close for day, close in TAIEX_CLOSES.items() if day != 23}
    # The day is a Taiwan session: another Taiwan series closed on it.
    other = Series("2330.TW", "台積電 2330", TW, None)
    listed = MarketSeries((US, TW), (TAIEX, other, SP500))
    event = Event(date(2026, 11, 24), TW, datetime(2026, 11, 24, 13, 30, tzinfo=TAIPEI))
    closes = {
        "^TWII": _closes(lacking),
        "2330.TW": _closes(dict.fromkeys(TAIEX_CLOSES, 2000.0)),
        "^GSPC": _closes(SP500_CLOSES),
    }

    cells = _cells(section(event, listed, closes).lines, "加權指數")

    assert cells[3:5] == [NO_DATA, NO_DATA] and cells[7] == NO_DATA
    assert cells[10] == "Yahoo 回應缺 2026-11-23 這一根"


def test_an_ex_dividend_day_in_the_window_is_noted() -> None:
    event = Event(date(2026, 11, 24), TW, datetime(2026, 11, 24, 13, 30, tzinfo=TAIPEI))
    closes = {
        "^TWII": _closes(TAIEX_CLOSES, dividends=[25]),
        "^GSPC": _closes(SP500_CLOSES),
    }

    cells = _cells(section(event, LISTED, closes).lines, "加權指數")

    assert cells[10] == "視窗內有除息日 2026-11-25（收盤未調整）"


def test_a_change_on_a_half_rounds_as_the_earlier_files_do() -> None:
    event = Event(date(2026, 11, 24), TW, datetime(2026, 11, 24, 13, 30, tzinfo=TAIPEI))
    closes = {
        "^TWII": _closes({20: 2400.0, 23: 2415.0, 24: 2410.0, 25: 2420.0}),
        "^GSPC": _closes(SP500_CLOSES),
    }

    assert _cells(section(event, LISTED, closes).lines, "加權指數")[4] == "+0.63%"


def test_by_date_the_first_line_is_the_earlier_files_one() -> None:
    event = Event(date(2026, 11, 19), US, None)
    closes = {"^TWII": _closes(TAIEX_CLOSES), "^GSPC": _closes(SP500_CLOSES)}

    lines = section(event, LISTED, closes).lines

    assert lines[2] == (
        "> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；"
        "美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。"
        "盤後才公布的事件，當日欄反應不到，請看次一交易日欄。"
    )
    assert _cells(lines, "加權指數")[1] == "2026-11-20"


def test_by_date_an_event_on_a_day_without_a_session_says_so() -> None:
    event = Event(date(2026, 11, 21), US, None)
    closes = {"^TWII": _closes(TAIEX_CLOSES), "^GSPC": _closes(SP500_CLOSES)}

    lines = section(event, LISTED, closes).lines

    assert (
        lines[3]
        == "> 行情註：event_date 2026-11-21 不是交易日，D0 取之後第一個交易日。"
    )
