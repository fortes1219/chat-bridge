---
title: 美股創6月以來最差單日，Intel重挫，AI燒錢、自由現金流轉負與舉債受關注
event_date: 2026-10-30
targets: [1, 4]
markets: [US]
tickers: [INTC, AMZN, NVDA, GOOGL, QCOM, META, MSFT]
exposure: [us_equity_broad, big_tech_cloud, ai_debt_credit, semiconductors]
significance: key
keyword_groups:
  - [美股, Wall Street, US stocks]
  - [標普500, S&P 500, 道瓊, Dow, 那斯達克, Nasdaq]
  - [自由現金流, free cash flow, 燒錢, cash burn]
  - [舉債, debt, 發債]
  - [資本支出, capex]
  - [英特爾, Intel, INTC]
  - [Alphabet, Google, GOOGL]
  - [亞馬遜, Amazon, AMZN]
sources:
  - id: s1
    url: https://www.wlox.com/2026/10/30/wall-street-tumbles-its-worst-day-since-june-after-sell-off-tech-stocks-deepens/
    publisher: WLOX（Associated Press）
    published: 2026-10-30
    accessed: 2026-11-18
    lang: en
    format: html
  - id: s2
    url: https://techcrunch.com/2026/10/30/cracks-are-emerging-in-the-ai-spending-boom/
    publisher: TechCrunch（Rebecca Bellan）
    published: 2026-10-30
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

- AP: the S&P 500 "dropped 1.8% Friday for its worst day since June"; the Nasdaq fell 2.9% and the Dow 1.1%. [s1]
- TechCrunch wrote about negative free cash flow, mounting debt, and whether the investments "will ever generate enough returns". [s2]
- TechCrunch, citing S&P Global, said five companies raised a combined $326 billion in debt in 2026. [s2]
- TechCrunch: Alphabet, Amazon, Meta and Microsoft plan over $740 billion in 2026 capex. [s2]

## 影響股市證據

- TechCrunch: "The Nasdaq fell 2.9%, and chip stocks took a drubbing, too". [s2]

## 相關標的

- AP (closing update): Intel sank almost 29%. [s1]
- AP: Alphabet had dropped more than 12% the day before. [s1]
- AP, in the earlier intraday update "as of 3:05 p.m. Eastern time": Nvidia dropped 4.9% and Amazon 1.9%; the 10-year Treasury yield fell to 4.93% from 4.98%; Brent rose 2.4% to $113.43. These are intraday figures. [s1]
- TechCrunch gave Q3 free cash flow of negative $9.1 billion for Alphabet and negative $2.1 billion for Meta, negative $42.4 billion over 12 months for Amazon, and positive $18.6 billion for Microsoft in its latest quarter. [s2]

## 當日與之後的行情

> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。盤後才公布的事件，當日欄反應不到，請看次一交易日欄。

| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | 次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |
|---|---|---|---|---|---|---|---|---|---|---|
| 加權指數 | 2026-10-31 | 2026-10-30 | 45211.83 | -2.49% | 2026-11-02 | 44920.14 | -0.65% | -3.59% | -7.85% |  |
| 台積電 2330 | 2026-10-31 | 2026-10-30 | 2370.00 | -1.86% | 2026-11-02 | 2330.00 | -1.69% | -1.50% | -5.70% |  |
| 台達電 2308 | 2026-10-31 | 2026-10-30 | 1335.00 | -9.80% | 2026-11-02 | 1355.00 | +1.50% | -6.27% | -13.11% |  |
| 元大台灣50 0050 | 2026-10-31 | 2026-10-30 | 104.95 | -2.14% | 2026-11-02 | 104.10 | -0.81% | -3.36% | -7.15% |  |
| 富邦台50 006208 | 2026-10-31 | 2026-10-30 | 240.75 | -2.03% | 2026-11-02 | 238.65 | -0.87% | -3.39% | -7.12% |  |
| S&P 500 | 2026-10-30 | 2026-10-29 | 7720.39 | -0.30% | 2026-10-30 | 7580.07 | -1.82% | -0.51% | -4.45% |  |
| Nasdaq Composite | 2026-10-30 | 2026-10-29 | 26184.72 | -1.38% | 2026-10-30 | 25437.00 | -2.86% | -1.07% | -6.13% |  |
| Dow Jones Industrial Average | 2026-10-30 | 2026-10-29 | 52342.56 | -0.25% | 2026-10-30 | 51770.31 | -1.09% | +0.41% | -2.02% |  |
| 費城半導體指數 | 2026-10-30 | 2026-10-29 | 11518.20 | -1.42% | 2026-10-30 | 10688.80 | -7.20% | -3.37% | -18.47% |  |

## 後續與不同說法

- Joe Tigay, portfolio manager at Equity Armor Investments (via AP): "We're moving out of the hopes and dreams phase of the AI trade and into the 'show me' phase". [s1]
- TechCrunch also noted that demand for AI compute remains strong. [s2]

> significance 依據（key）：來源稱美股6月以來最差單日，記者與分析把它連到AI燒錢與舉債，是目標4的核心證據。
