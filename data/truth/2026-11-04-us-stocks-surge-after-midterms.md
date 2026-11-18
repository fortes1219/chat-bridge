---
title: 期中選舉後美股大漲，道瓊漲1,569.40點、油價重挫
event_date: 2026-11-04
targets: [1, 3]
markets: [US]
tickers: [NVDA, GOOGL, TSLA]
exposure: [us_equity_broad, us_politics, oil_energy]
significance: supporting
keyword_groups:
  - [美股, Wall Street, US stocks]
  - [美國期中選舉, midterm elections, 民主黨, Democrats]
  - [川普, Trump]
  - [油價, Brent, 布蘭特原油]
  - [標普500, S&P 500, 道瓊, Dow, 那斯達克, Nasdaq]
sources:
  - id: s1
    url: https://www.eastidahonews.com/2026/11/stocks-surge-and-the-dow-soars-1500-points-as-oil-prices-tumble-following-the-us-midterm-elections/
    publisher: East Idaho News（Associated Press，Stan Choe、David McHugh）
    published: 2026-11-04
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

- "U.S. stocks soared Wednesday after President Donald Trump's party lost its sole control of Washington in the midterm elections". [s1]

## 影響股市證據

- The S&P 500 rose 119.70 points to 7,688.62 (1.6%); the Dow rallied 1,569.40 to 53,356.12 (3%); the Nasdaq climbed 364.50 to 25,736.51 (1.4%). [s1]

## 相關標的

- Brent plunged 8.7% to $94.62; the 10-year Treasury yield dropped to 4.88% from 4.95%. [s1]
- Nvidia sank 3.2% while Alphabet rose 3.2%. [s1]
- Tesla fell 3.3%. [s1]

## 當日與之後的行情

> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。盤後才公布的事件，當日欄反應不到，請看次一交易日欄。

| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | 次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |
|---|---|---|---|---|---|---|---|---|---|---|
| 加權指數 | 2026-11-05 | 2026-11-04 | 42948.91 | -0.83% | 2026-11-05 | 41574.72 | -3.20% | -4.51% | +0.33% |  |
| 台積電 2330 | 2026-11-05 | 2026-11-04 | 2260.00 | -1.53% | 2026-11-05 | 2240.00 | -0.88% | -4.69% | +3.54% |  |
| 台達電 2308 | 2026-11-05 | 2026-11-04 | 1220.00 | -3.94% | 2026-11-05 | 1130.00 | -7.38% | -6.64% | +1.64% |  |
| 元大台灣50 0050 | 2026-11-05 | 2026-11-04 | 99.85 | -0.75% | 2026-11-05 | 97.15 | -2.70% | -4.79% | +1.10% |  |
| 富邦台50 006208 | 2026-11-05 | 2026-11-04 | 228.55 | -0.87% | 2026-11-05 | 222.55 | -2.63% | -5.59% | +1.49% |  |
| S&P 500 | 2026-11-04 | 2026-11-03 | 7568.92 | +0.36% | 2026-11-04 | 7688.62 | +1.58% | -4.36% | +0.67% |  |
| Nasdaq Composite | 2026-11-04 | 2026-11-03 | 25372.01 | +0.83% | 2026-11-04 | 25736.51 | +1.44% | -5.52% | +0.37% |  |
| Dow Jones Industrial Average | 2026-11-04 | 2026-11-03 | 51786.72 | -0.38% | 2026-11-04 | 53356.12 | +3.03% | -3.44% | +1.35% |  |
| 費城半導體指數 | 2026-11-04 | 2026-11-03 | 10600.40 | +2.63% | 2026-11-04 | 10268.65 | -3.13% | -12.25% | -0.34% |  |

## 後續與不同說法

- Brian Jacobsen, chief economic strategist at Annex Wealth Management: "Earnings trump elections". [s1]
- Carsten Brzeski, global chief of macro at ING Bank, offered as one downbeat scenario that "Trump is not now a lame duck, but an angry duck". [s1]

> 隔天（11月5日）的美股見 2026-11-05-us-ai-selloff-after-midterms.md。

> significance 依據（supporting）：選舉結果當天的上漲，用來對照隔天的重挫。
