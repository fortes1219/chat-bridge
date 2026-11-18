---
title: 沃勒稱若數據確認通膨壓力降溫，傾向主張下次會議按兵不動；升息機率下降、美股上漲
event_date: 2026-09-03
targets: [2, 1]
markets: [US]
tickers: []
exposure: [fed_policy, us_equity_broad, rates_treasuries]
significance: supporting
keyword_groups:
  - [聯準會, Fed, Federal Reserve]
  - [沃勒, Waller, Christopher Waller]
  - [升息機率, rate hike odds, CME FedWatch]
  - [標普500, S&P 500, 道瓊, Dow, 那斯達克, Nasdaq]
sources:
  - id: s1
    url: https://wealthinsights.metrobank.com.ph/news/global-markets-bond-yields-fall-stocks-rally-as-feds-waller-comments-curb-rate-hike-bets
    publisher: Metrobank Wealth Insights（Reuters，Caroline Valetkevitch、Amanda Cooper）
    published: 2026-09-04
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

- "Waller, in remarks for a Reuters NEXT Newsmaker event, said that, if upcoming data confirmed inflation pressures were cooling off, he was inclined to argue in favor of keeping interest rates steady at the US central bank's next policy meeting". [s1]

## 影響股市證據

- "Stock markets rallied while bond yields fell on Thursday as comments from Federal Reserve Governor Christopher Waller signaled a willingness to remain patient on raising interest rates". [s1]
- "The Dow Jones Industrial Average rose 624.16 points, or 1.18%, to 53,686.11". [s1]
- "the S&P 500 rose 81.11 points, or 1.06%, to 7,747.71"; "the Nasdaq Composite rose 366.23 points, or 1.40%, to 26,584.06". [s1]
- Traders priced "a roughly 50% chance for a hike, versus about 63% in the prior session, according to CME FedWatch". [s1]

## 相關標的

> 本檔讀過的來源沒有點名個別標的。

## 當日與之後的行情

> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。盤後才公布的事件，當日欄反應不到，請看次一交易日欄。

| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | 次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |
|---|---|---|---|---|---|---|---|---|---|---|
| 加權指數 | 2026-09-04 | 2026-09-03 | 45857.66 | -0.67% | 2026-09-04 | 46551.13 | +1.51% | +1.67% | +0.71% |  |
| 台積電 2330 | 2026-09-04 | 2026-09-03 | 2390.00 | +0.21% | 2026-09-04 | 2410.00 | +0.84% | +2.07% | +0.84% |  |
| 台達電 2308 | 2026-09-04 | 2026-09-03 | 1760.00 | +1.73% | 2026-09-04 | 1825.00 | +3.69% | +1.37% | -7.95% |  |
| 元大台灣50 0050 | 2026-09-04 | 2026-09-03 | 106.20 | -0.56% | 2026-09-04 | 107.90 | +1.60% | +1.85% | +1.41% |  |
| 富邦台50 006208 | 2026-09-04 | 2026-09-03 | 243.80 | -0.57% | 2026-09-04 | 247.25 | +1.42% | +1.78% | +0.94% |  |
| S&P 500 | 2026-09-03 | 2026-09-02 | 7666.60 | +0.46% | 2026-09-03 | 7747.71 | +1.06% | -0.38% | -0.13% |  |
| Nasdaq Composite | 2026-09-03 | 2026-09-02 | 26217.83 | +0.45% | 2026-09-03 | 26584.06 | +1.40% | -0.29% | +0.44% |  |
| Dow Jones Industrial Average | 2026-09-03 | 2026-09-02 | 53061.95 | +0.56% | 2026-09-03 | 53686.11 | +1.18% | -0.51% | -0.92% |  |
| 費城半導體指數 | 2026-09-03 | 2026-09-02 | 11339.25 | +0.45% | 2026-09-03 | 11352.13 | +0.11% | +3.37% | +4.27% |  |

> significance 依據（supporting）：官員談話使升息預期下降、美股上漲，是聯準會影響行情的例子，但不是這段期間最大的變動之一。
