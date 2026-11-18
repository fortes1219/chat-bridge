---
title: 博通財測不如預期加上就業報告強勁，那斯達克重挫4%創2025年4月以來最差
event_date: 2026-06-05
targets: [1, 2, 3]
markets: [US]
tickers: [AVGO, MU, INTC, CSCO, NVDA]
exposure: [us_equity_broad, semiconductors, us_macro_data, rates_treasuries, fed_policy]
significance: key
keyword_groups:
  - [美股, Wall Street, US stocks]
  - [標普500, S&P 500, 道瓊, Dow, 那斯達克, Nasdaq]
  - [博通, Broadcom, AVGO]
  - [就業報告, jobs report, 非農]
  - [升息, tighter monetary policy, rate cuts]
  - [公債殖利率, Treasury yield]
  - [AI熱潮, AI boom]
sources:
  - id: s1
    url: https://www.fortune.com/2026/06/05/tech-stocks-market-bloodbath-fed-rate-hikes-jobs-report-ai-fueled-chip-boom/
    publisher: Fortune（Jason Ma）
    published: 2026-06-05
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

- "Trouble began when chip designer Broadcom gave disappointing guidance late Wednesday, when it reported quarterly earnings". [s1]
- "The Labor Department's monthly tally showed employers added a net 172,000 jobs last month, nearly double Wall Street forecasts". [s1]

## 影響股市證據

- "The Nasdaq sank 4%, suffering its worst selloff since April 2025—during the height of President Donald Trump's tariff shock. The S&P 500 lost 2.6%, and the Dow Jones Industrial Average fell 1.35%". [s1]
- "Investors priced in a greater probability of tighter monetary policy, giving up on the prospect of additional rate cuts anytime soon". [s1]

## 相關標的

- "Chipmakers Micron Technology, Intel, Cisco and Nvidia led the charge lower" … [s1]
- "The yield on the 10-year Treasury jumped 5.5 basis points on Friday to 4.532%". [s1]

## 當日與之後的行情

> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。盤後才公布的事件，當日欄反應不到，請看次一交易日欄。

| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | 次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |
|---|---|---|---|---|---|---|---|---|---|---|
| 加權指數 | 2026-06-06 | 2026-06-05 | 45070.94 | -1.33% | 2026-06-08 | 43502.78 | -3.48% | +2.76% | +0.72% |  |
| 台積電 2330 | 2026-06-06 | 2026-06-05 | 2365.00 | -0.84% | 2026-06-08 | 2295.00 | -2.96% | +0.44% | +0.42% | 視窗內有除息日 2026-06-11（收盤未調整） |
| 台達電 2308 | 2026-06-06 | 2026-06-05 | 2300.00 | -5.15% | 2026-06-08 | 2255.00 | -1.96% | +7.10% | -3.91% |  |
| 元大台灣50 0050 | 2026-06-06 | 2026-06-05 | 104.15 | -1.84% | 2026-06-08 | 100.95 | -3.07% | +2.53% | +1.06% |  |
| 富邦台50 006208 | 2026-06-06 | 2026-06-05 | 241.05 | -1.99% | 2026-06-08 | 233.85 | -2.99% | +2.44% | +1.27% |  |
| S&P 500 | 2026-06-05 | 2026-06-04 | 7584.31 | +0.41% | 2026-06-05 | 7383.74 | -2.64% | +0.30% | -2.02% |  |
| Nasdaq Composite | 2026-06-05 | 2026-06-04 | 26830.96 | -0.09% | 2026-06-05 | 25709.43 | -4.18% | +0.86% | -3.51% |  |
| Dow Jones Industrial Average | 2026-06-05 | 2026-06-04 | 51561.93 | +1.73% | 2026-06-05 | 50866.78 | -1.35% | -0.16% | -0.70% |  |
| 費城半導體指數 | 2026-06-05 | 2026-06-04 | 13617.50 | -2.15% | 2026-06-05 | 12220.76 | -10.26% | +5.61% | -1.81% |  |

## 後續與不同說法

- Christopher Hodge, chief U.S. economist at Natixis CIB Americas, wrote: "The lack of a re-acceleration of wage growth in recent months points to a labor market that is stable, but not hot". [s1]

> 下一個台股交易日（6月8日）台股重挫，見 2026-06-08-taiex-falls-1568-points.md。

> significance 依據（key）：來源稱是2025年4月以來那斯達克最差的一天，也是下一個交易日台股史上第3大收盤跌點的前一晚。
