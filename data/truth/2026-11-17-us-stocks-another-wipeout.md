---
title: 美股下跌，標普500收7,340.53點；UBS看未來6至12個月有漲幅，聖路易聯準銀行總裁看還要升息
event_date: 2026-11-17
targets: [1, 5, 2]
markets: [US]
tickers: [NVDA, JPM]
exposure: [us_equity_broad, rates_treasuries, fed_policy, ai_infrastructure]
significance: supporting
keyword_groups:
  - [美股, Wall Street, US stocks]
  - [標普500, S&P 500, 道瓊, Dow, 那斯達克, Nasdaq]
  - [公債殖利率, Treasury yield, 10-year Treasury]
  - [聯準會, Fed, 穆薩萊姆, Musalem]
  - [瑞銀, UBS]
  - [回穩, 反彈, recovery, gains]
sources:
  - id: s1
    url: https://www.wistv.com/2026/11/17/another-wipeout-hits-wall-street-nvidia-other-jittery-ai-stocks-swing-lower/
    publisher: WIS（Associated Press，Stan Choe）
    published: 2026-11-17
    accessed: 2026-11-18
    lang: en
    format: html
  - id: s2
    url: https://www.cnbc.com/2026/11/16/stock-market-today-live-updates.html
    publisher: CNBC（live blog）
    published: 2026-11-17
    accessed: 2026-11-18
    lang: en
    format: html
  - id: d1
    url: https://query1.finance.yahoo.com/v8/finance/chart/
    publisher: Yahoo Finance chart API（程式下載的日線收盤；^TWII、2330.TW、2308.TW、0050.TW、006208.TW、^GSPC、^IXIC、^DJI、^SOX）
    published: unknown
    accessed: 2026-11-18T03:23:58+00:00
    lang: en
    format: json
---

## 事件發生

- AP: the S&P 500 fell 76.06 points to 7,340.53 (1%); the Dow dropped 848.75 to 50,759.42 (1.6%); the Nasdaq sank 181.37 to 24,328.38 (0.7%). [s1]

## 影響股市證據

- AP: "AI-related stocks have been shaky for months because of a rolling chain of worries". [s1]

## 相關標的

- AP: the 10-year Treasury yield "climbed toward 5.15% Tuesday morning from 5.12% late Monday before later pulling back to 5.10%"; Brent rose 0.8% to $93.14. [s1]
- AP: Nvidia dropped as much as 3.7% before trimming its loss to 0.4%; JPMorgan fell 2.4%. [s1]

## 當日與之後的行情

> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。盤後才公布的事件，當日欄反應不到，請看次一交易日欄。

| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | 次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |
|---|---|---|---|---|---|---|---|---|---|---|
| 加權指數 | 2026-11-18 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 資料還沒有到這一天 |
| 台積電 2330 | 2026-11-18 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 資料還沒有到這一天 |
| 台達電 2308 | 2026-11-18 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 資料還沒有到這一天 |
| 元大台灣50 0050 | 2026-11-18 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 資料還沒有到這一天 |
| 富邦台50 006208 | 2026-11-18 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 沒有資料 | 資料還沒有到這一天 |
| S&P 500 | 2026-11-17 | 2026-11-16 | 7416.59 | -1.92% | 2026-11-17 | 7340.53 | -1.03% | 沒有資料 | 沒有資料 |  |
| Nasdaq Composite | 2026-11-17 | 2026-11-16 | 24509.76 | -2.49% | 2026-11-17 | 24328.38 | -0.74% | 沒有資料 | 沒有資料 |  |
| Dow Jones Industrial Average | 2026-11-17 | 2026-11-16 | 51608.17 | -1.41% | 2026-11-17 | 50759.42 | -1.64% | 沒有資料 | 沒有資料 |  |
| 費城半導體指數 | 2026-11-17 | 2026-11-16 | 9610.65 | -5.28% | 2026-11-17 | 9642.88 | +0.34% | 沒有資料 | 沒有資料 |  |

## 後續與不同說法

- St. Louis Fed President Alberto Musalem (via CNBC): the economy will likely require "several interest rate increases before the spring of 2027". [s2]
- Ulrike Hoffmann-Burchardi, CIO Americas at UBS (via CNBC): "We therefore continue to see potential for gains in broad equity markets over the next six to 12 months". [s2]
- Art Hogan of B. Riley Wealth (via CNBC) described "that aggregate of the compounding of bizarre stories that just have become too much of a headwind, at least in the near term". [s2]
- Megan Horneman of Verdence Capital Advisors (via CNBC) described a "panic type of stage right now". [s2]

> significance 依據（supporting）：最新一天的美股跌勢，以及策略師與聯準會官員的看法；跌幅不在這段期間最大之列。
