---
title: 美國期中選舉後AI股重挫，標普500跌4.4%、那斯達克進入修正
event_date: 2026-11-05
targets: [1, 3, 4]
markets: [US]
tickers: [NVDA, AMD, CRWV, GEV]
exposure: [us_equity_broad, semiconductors, ai_infrastructure, us_politics, ai_debt_credit]
significance: key
keyword_groups:
  - [美股, Wall Street, US stocks]
  - [標普500, S&P 500, 道瓊, Dow Jones Industrial Average, 那斯達克, Nasdaq composite, Nasdaq 100]
  - [費城半導體指數, 費半, Philadelphia Semiconductor Index, semiconductor shares]
  - [美國期中選舉, midterm elections, 民主黨, Democrats]
  - [AI資料中心, AI data centers, data center construction]
  - [舉債, 借貸, borrowing, debt obligations, 融資成本]
  - [輝達, NVIDIA, NVDA]
  - [超微, Advanced Micro Devices, AMD]
  - [修正, correction territory, 股災, brutal sell-off]
sources:
  - id: s1
    url: https://www.boston.com/news/national-news/2026/11/05/a-brutal-sell-off-for-ai-stocks-sends-wall-street-reeling-and-the-sp-500-tumbles-4-4/
    publisher: Boston.com（Associated Press，Stan Choe）
    published: 2026-11-05
    accessed: 2026-11-18
    lang: en
    format: html
  - id: s2
    url: https://www.staradvertiser.com/2026/11/05/breaking-news/nasdaq-heads-for-correction-as-ai-stocks-plunge-after-midterms/
    publisher: Honolulu Star-Advertiser（Bloomberg News，Jessica Menton、Geoffrey Morgan）
    published: 2026-11-05
    accessed: 2026-11-18
    lang: en
    format: html
  - id: s3
    url: https://www.foxbusiness.com/markets/whats-fueling-wall-streets-growing-concerns-about-ai
    publisher: Fox Business（Sophia Compton）
    published: 2026-11-05
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

- AP: "The nationwide victories for Democrats raised the possibility that governments could force pauses in construction of more data centers". [s1]
- Bloomberg on the reason: the prospect that "Democrats' sweeping victory in the Congressional elections may herald a political shift" … [s2]

## 影響股市證據

- "All told, the S&P 500 fell 334.89 points to 7,353.73". [s1]
- "The Dow Jones Industrial Average dropped 1,833.06 to 51,523.06, and the Nasdaq composite sank 1,421.52 to 24,315.00". [s1]
- Fox Business: the Nasdaq Composite "closed in correction territory, at least 10% below its Oct. 6 record closing high". [s3]
- Bloomberg: "a closely watched index of semiconductor shares dropped 12%" …, and "All 30 companies in the Dow Jones Industrial Average fell". [s2]
- AP also cited worries that construction of further AI data centers may slow "because of how expensive it's become to borrow money". [s1]
- Fox Business: "Behind the rout are growing concerns about the massive spending and borrowing fueling the AI boom" … [s3]

## 相關標的

- AP: Nvidia fell 9.3%, Advanced Micro Devices tumbled 17.3%, CoreWeave fell 9.8% and GE Vernova sank 7.5%. [s1]
- AP: "The yield on the 10-year Treasury fell to 4.84% from 4.90% late Wednesday". [s1]

## 當日與之後的行情

> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。盤後才公布的事件，當日欄反應不到，請看次一交易日欄。

| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | 次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |
|---|---|---|---|---|---|---|---|---|---|---|
| 加權指數 | 2026-11-06 | 2026-11-05 | 41574.72 | -3.20% | 2026-11-06 | 39701.64 | -4.51% | +4.94% | +5.05% |  |
| 台積電 2330 | 2026-11-06 | 2026-11-05 | 2240.00 | -0.88% | 2026-11-06 | 2135.00 | -4.69% | +4.68% | +4.91% |  |
| 台達電 2308 | 2026-11-06 | 2026-11-05 | 1130.00 | -7.38% | 2026-11-06 | 1055.00 | -6.64% | +9.95% | +9.73% |  |
| 元大台灣50 0050 | 2026-11-06 | 2026-11-05 | 97.15 | -2.70% | 2026-11-06 | 92.50 | -4.79% | +5.35% | +5.51% |  |
| 富邦台50 006208 | 2026-11-06 | 2026-11-05 | 222.55 | -2.63% | 2026-11-06 | 210.10 | -5.59% | +6.43% | +5.62% |  |
| S&P 500 | 2026-11-05 | 2026-11-04 | 7688.62 | +1.58% | 2026-11-05 | 7353.73 | -4.36% | +0.31% | -1.25% |  |
| Nasdaq Composite | 2026-11-05 | 2026-11-04 | 25736.51 | +1.44% | 2026-11-05 | 24315.00 | -5.52% | +1.09% | -1.44% |  |
| Dow Jones Industrial Average | 2026-11-05 | 2026-11-04 | 53356.12 | +3.03% | 2026-11-05 | 51523.06 | -3.44% | -0.46% | -1.98% |  |
| 費城半導體指數 | 2026-11-05 | 2026-11-04 | 10268.65 | -3.13% | 2026-11-05 | 9011.14 | -12.25% | +4.21% | +2.32% |  |

## 後續與不同說法

- Greg Taylor, CIO of PenderFund Capital Management (via Bloomberg): "I'm getting flashbacks to 2008 or 2001". [s2]
- Michael O'Rourke, chief market strategist at JonesTrading (via Bloomberg): "The forecasts are no longer valid". [s2]
- Paul Mueller, economist at the American Institute for Economic Research (via Fox Business): "Wall Street is worried about the enormous amounts of debt obligations being issued by tech companies" … [s3]
- Adam Patti, CEO of VistaShares (via Fox Business), said investors are asking "how long hyperscalers can keep spending at this pace while free cash flow goes negative". [s3]
- Adam Patti also said: "This is a valuation and sentiment reset, not a change in fundamentals". [s3]
- Jakub Rochlitz, eToro market analyst (via Fox Business): "We are likely seeing a large number of crowded and leveraged trades unwind". [s3]

> significance 依據（key）：AP 稱標普500自2025年4月以來最差的一天，那斯達克進入修正。
