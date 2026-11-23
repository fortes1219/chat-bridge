---
title: 美國10月CPI月增0.4%、核心月增0.3%，殖利率跳升、輝達跌5.5%
event_date: 2026-11-10
targets: [2, 1]
markets: [US]
tickers: [NVDA]
exposure: [us_macro_data, rates_treasuries, fed_policy, us_equity_broad, semiconductors]
significance: supporting
keyword_groups:
  - [消費者物價指數, CPI, Consumer Price Index]
  - [通膨, inflation]
  - [核心CPI, all items less food and energy]
  - [core]
  - [美國勞工統計局, BLS, Bureau of Labor Statistics]
  - [公債殖利率, Treasury yield]
  - [10-year Treasury]
  - [升息, rate hike]
  - [輝達, NVIDIA, NVDA]
sources:
  - id: s1
    url: https://www.bls.gov/news.release/archives/cpi_11102026.htm
    publisher: U.S. Bureau of Labor Statistics
    published: 2026-11-10
    accessed: 2026-11-18
    lang: en
    format: html
  - id: s2
    url: https://www.ajc.com/news/2026/11/us-stocks-slip-following-a-discouraging-update-on-inflation/
    publisher: The Atlanta Journal-Constitution（Associated Press，Stan Choe）
    published: 2026-11-10
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

- "The Consumer Price Index for All Urban Consumers (CPI-U) increased 0.4 percent on a seasonally adjusted basis in October after rising 0.6 percent in September" … [s1]
- "The index for all items less food and energy rose 0.3 percent in October, as it did in September and August". [s1]
- "The index for energy increased 0.7 percent over the month following a 5.2-percent increase in September". [s1]
- BLS did not publish 12-month changes for these indexes: "BLS did not collect survey data for October 2025 because of a lapse in appropriations". [s1]

## 影響股市證據

- AP: "Pressure from the bond market undercut stocks following the discouraging report on inflation". [s2]
- AP: "the S&P 500 fell 29.01 points to 7,520.93. The Dow Jones Industrial Average dipped 157.86 to 52,231.89, and the Nasdaq composite sank 187.26 to 25,065.87". [s2]

## 相關標的

- AP: "The yield on the 10-year Treasury leaped to 4.99% from 4.88% late Monday". [s2]
- AP: "The single heaviest weight on the S&P 500 was Nvidia, which fell 5.5%". [s2]

## 當日與之後的行情

> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。盤後才公布的事件，當日欄反應不到，請看次一交易日欄。

| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | 次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |
|---|---|---|---|---|---|---|---|---|---|---|
| 加權指數 | 2026-11-11 | 2026-11-10 | 42711.92 | +2.52% | 2026-11-11 | 44257.15 | +3.62% | -2.63% | 沒有資料 |  |
| 台積電 2330 | 2026-11-11 | 2026-11-10 | 2285.00 | +2.24% | 2026-11-11 | 2395.00 | +4.81% | -2.30% | 沒有資料 |  |
| 台達電 2308 | 2026-11-11 | 2026-11-10 | 1275.00 | +9.91% | 2026-11-11 | 1295.00 | +1.57% | -4.25% | 沒有資料 |  |
| 元大台灣50 0050 | 2026-11-11 | 2026-11-10 | 99.70 | +2.31% | 2026-11-11 | 103.20 | +3.51% | -2.18% | 沒有資料 |  |
| 富邦台50 006208 | 2026-11-11 | 2026-11-10 | 228.90 | +2.37% | 2026-11-11 | 236.60 | +3.36% | -1.97% | 沒有資料 | 視窗內有除息日 2026-11-17（收盤未調整） |
| S&P 500 | 2026-11-10 | 2026-11-09 | 7549.94 | +2.35% | 2026-11-10 | 7520.93 | -0.38% | +1.31% | -2.77% |  |
| Nasdaq Composite | 2026-11-10 | 2026-11-09 | 25253.14 | +2.74% | 2026-11-10 | 25065.87 | -0.74% | +1.60% | -3.66% |  |
| Dow Jones Industrial Average | 2026-11-10 | 2026-11-09 | 52389.75 | +2.15% | 2026-11-10 | 52231.89 | -0.30% | +0.49% | -3.11% |  |
| 費城半導體指數 | 2026-11-10 | 2026-11-09 | 10033.93 | +6.85% | 2026-11-10 | 9998.33 | -0.35% | +5.66% | -3.90% |  |

## 後續與不同說法

- AP reported Fed Gov. Christopher Waller had said "a stronger policy move may be needed" if the underlying inflation measure rose 0.3%, and that "Tuesday's inflation report showed that the underlying measure of inflation Waller was worried about was exactly 0.3%". [s2]

> 同一天沃勒與鮑曼的演講見 2026-11-10-waller-bowman-signal-more-tightening.md。BLS 網址用的是有日期的存檔頁，不是每月替換的最新一期頁。

> significance 依據（supporting）：通膨數據推升升息預期與殖利率，當天美股下跌幅度不大。
