---
title: 川普取消轟炸伊朗威脅，美股創兩個月最大單日漲幅
event_date: 2026-06-11
targets: [1, 3]
markets: [US]
tickers: [MRVL, ORCL, LRCX, KLAC]
exposure: [us_equity_broad, middle_east_conflict, oil_energy, rates_treasuries]
significance: supporting
keyword_groups:
  - [美股, Wall Street, US stocks]
  - [川普, Trump, Donald Trump]
  - [伊朗, Iran, 中東衝突]
  - [油價, Brent, 布蘭特原油, benchmark U.S. crude]
  - [標普500, S&P 500, 道瓊, Dow, 那斯達克, Nasdaq]
sources:
  - id: s1
    url: https://www.investmentexecutive.com/news/research-and-markets/u-s-stocks-jump-to-their-best-day-in-two-months/
    publisher: Investment Executive（Associated Press，Stan Choe、Alex Veiga）
    published: 2026-06-11
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

- AP: U.S. stocks rose "after President Donald Trump called off his threat to bomb Iran in the evening". [s1]
- Trump's statement, as quoted by AP: "discussions with the Islamic Republic of Iran have been brought to the highest level of Iranian leadership and approved" … [s1]

## 影響股市證據

- The S&P 500 jumped 1.8%, rising 127.31 points to 7,394.30; the Dow rose 929.97 to 50,848.75 (1.9%); the Nasdaq rallied 640.16 to 25,809.66 (2.5%). [s1]

## 相關標的

- The 10-year Treasury yield dropped to 4.45% from 4.55% late Wednesday. [s1]
- "The price for a barrel of benchmark U.S. crude sank 2.6% to US$87.71". [s1]
- "Brent crude, the international standard, fell 2.9% to $90.38, though it’s still above its roughly $70 price from before the war". [s1]
- Marvell climbed 11.1%, Lam Research 12.7% and KLA 12.9%; Oracle had an 8.5% drop. [s1]

## 當日與之後的行情

> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。盤後才公布的事件，當日欄反應不到，請看次一交易日欄。

| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | 次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |
|---|---|---|---|---|---|---|---|---|---|---|
| 加權指數 | 2026-06-12 | 2026-06-11 | 43149.46 | -0.18% | 2026-06-12 | 44169.04 | +2.36% | +2.78% | +10.64% |  |
| 台積電 2330 | 2026-06-12 | 2026-06-11 | 2250.00 | -0.22% | 2026-06-12 | 2310.00 | +2.67% | +2.81% | +11.56% | 視窗內有除息日 2026-06-11（收盤未調整） |
| 台達電 2308 | 2026-06-12 | 2026-06-11 | 2160.00 | -1.82% | 2026-06-12 | 2215.00 | +2.55% | -0.23% | -0.46% | 視窗內有除息日 2026-06-17（收盤未調整） |
| 元大台灣50 0050 | 2026-06-12 | 2026-06-11 | 99.85 | -0.40% | 2026-06-12 | 101.95 | +2.10% | +3.24% | +11.32% |  |
| 富邦台50 006208 | 2026-06-12 | 2026-06-11 | 231.00 | -0.45% | 2026-06-12 | 236.10 | +2.21% | +3.39% | +11.45% |  |
| S&P 500 | 2026-06-11 | 2026-06-10 | 7266.99 | -1.62% | 2026-06-11 | 7394.30 | +1.75% | +0.50% | +3.21% |  |
| Nasdaq Composite | 2026-06-11 | 2026-06-10 | 25169.50 | -1.98% | 2026-06-11 | 25809.66 | +2.54% | +0.31% | +5.36% |  |
| Dow Jones Industrial Average | 2026-06-11 | 2026-06-10 | 49918.78 | -1.87% | 2026-06-11 | 50848.75 | +1.86% | +0.70% | +3.30% |  |
| 費城半導體指數 | 2026-06-11 | 2026-06-10 | 12206.46 | -3.57% | 2026-06-11 | 13171.44 | +7.91% | +1.52% | +17.49% |  |

> significance 依據（supporting）：說明伊朗局勢與油價對美股的影響，屬於脈絡，不是這段期間最大的變動之一。
