---
title: 聯準會7月維持利率不變、三位委員主張升息；同日油價跳升、道瓊跌逾1100點
event_date: 2026-07-29
targets: [2, 1]
markets: [US]
tickers: [NVDA, KLAC]
exposure: [fed_policy, us_equity_broad, oil_energy, middle_east_conflict, rates_treasuries]
significance: supporting
keyword_groups:
  - [聯準會, Fed, Federal Reserve]
  - [FOMC, 聯邦公開市場委員會]
  - [聯邦基金利率, federal funds rate]
  - [利率決策]
  - [按兵不動]
  - [反對票, dissent]
  - [升息派]
  - [Hammack]
  - [Kashkari]
  - [Logan]
  - [華許, Warsh, Kevin Warsh]
  - [聯準會主席]
  - [通膨, inflation]
  - [伊朗, Iran]
  - [油價]
  - [Brent, 布蘭特原油]
  - [標普500, S&P 500]
  - [道瓊, Dow]
  - [那斯達克, Nasdaq]
sources:
  - id: s1
    url: https://www.federalreserve.gov/newsevents/pressreleases/monetary20260729a.htm
    publisher: Board of Governors of the Federal Reserve System
    published: 2026-07-29
    accessed: 2026-11-18
    lang: en
    format: html
  - id: s2
    url: https://fortune.com/2026/07/29/dow-drops-over-1100-points-as-sinking-tech-stocks-combine-with-jumping-oil-prices-to-drag-markets-down
    publisher: Fortune（Associated Press，Stan Choe）
    published: 2026-07-29
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

- The Committee decided "to maintain the target range for the federal funds rate at 3-1/2 to 3-3/4 percent". [s1]
- The statement was approved "by a 9 – 3 vote". [s1]
- "Voting against the monetary policy action were Beth M. Hammack, Neel Kashkari, and Lorie K. Logan, who preferred to raise the target range for the federal funds rate by 1/4 percentage point at this meeting". [s1]
- The statement said inflation "remains elevated relative to the Committee's 2 percent goal". [s1]
- The statement said economic activity "is expanding at a solid pace despite elevated uncertainty that owes, in part, to the conflict in the Middle East". [s1]

## 影響股市證據

- AP: the S&P 500 fell 112.63 to 7,316.15 (1.5%); the Dow dropped 1,153.18 to 51,594.14 (2.2%); the Nasdaq sank 433.97 to 24,442.94 (1.7%). [s2]
- AP's headline attributes the drop to "sinking tech stocks" combined with "jumping oil prices". [s2]
- AP reported the Fed kept rates steady while three members wanted a hike; traders had priced about a 34% chance of a hike. [s2]

## 相關標的

- AP: Brent leaped 7.3% to settle at $88.09 after fighting resumed in the war with Iran. [s2]
- AP: Nvidia fell 3.6% and KLA 10.8%; Seoul's Kospi fell 6% and SK Hynix 9.6%. [s2]
- AP: the 10-year Treasury yield rose to 4.68% from 4.61%; the 2-year yield fell to 4.24% from 4.26%. [s2]

## 當日與之後的行情

> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。盤後才公布的事件，當日欄反應不到，請看次一交易日欄。

| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | 次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |
|---|---|---|---|---|---|---|---|---|---|---|
| 加權指數 | 2026-07-30 | 2026-07-29 | 40039.18 | -3.76% | 2026-07-30 | 39933.30 | -0.26% | +7.98% | +10.88% |  |
| 台積電 2330 | 2026-07-30 | 2026-07-29 | 2200.00 | -3.51% | 2026-07-30 | 2205.00 | +0.23% | +9.98% | +7.50% |  |
| 台達電 2308 | 2026-07-30 | 2026-07-29 | 1495.00 | -5.38% | 2026-07-30 | 1530.00 | +2.34% | +7.19% | +12.37% |  |
| 元大台灣50 0050 | 2026-07-30 | 2026-07-29 | 93.70 | -3.55% | 2026-07-30 | 93.50 | -0.21% | +10.00% | +10.25% |  |
| 富邦台50 006208 | 2026-07-30 | 2026-07-29 | 214.05 | -3.62% | 2026-07-30 | 214.40 | +0.16% | +9.77% | +10.51% |  |
| S&P 500 | 2026-07-29 | 2026-07-28 | 7428.78 | +0.21% | 2026-07-29 | 7316.15 | -1.52% | +1.66% | +3.97% |  |
| Nasdaq Composite | 2026-07-29 | 2026-07-28 | 24876.91 | -0.22% | 2026-07-29 | 24442.94 | -1.74% | +2.78% | +5.98% |  |
| Dow Jones Industrial Average | 2026-07-29 | 2026-07-28 | 52747.32 | +1.03% | 2026-07-29 | 51594.14 | -2.19% | +1.19% | +3.04% |  |
| 費城半導體指數 | 2026-07-29 | 2026-07-28 | 11035.68 | -4.49% | 2026-07-29 | 10447.49 | -5.33% | +8.19% | +8.82% |  |

## 後續與不同說法

- Warsh, as quoted by AP, asked "Did the Fed take an explicit change in its policy rate today?" and answered "No, but I think that's the beginning of the story". [s2]

> significance 依據（supporting）：聯準會開會日，但來源把當天大跌的主因寫成科技股與油價，聯準會不是主因。
