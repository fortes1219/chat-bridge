---
title: 甲骨文同時發行 $10,000,000,052 普通股與 $10,000,000,000 公司債籌資
event_date: 2026-11-02
targets: [4, 3]
markets: [US]
tickers: [ORCL]
exposure: [ai_debt_credit, big_tech_cloud, ai_infrastructure]
significance: key
keyword_groups:
  - [甲骨文, Oracle, ORCL]
  - [增資, 現金增資, common stock offering, 發行新股]
  - [公司債, senior notes, bonds]
  - [舉債]
  - [發債]
  - [資本支出, capital expenditures, capex]
  - [AI基礎建設, AI infrastructure]
  - [資料中心]
sources:
  - id: s1
    url: https://www.sec.gov/Archives/edgar/data/0001341439/000119312526447507/d131790d8k.htm
    publisher: Oracle Corporation（SEC Form 8-K）
    published: 2026-11-04
    accessed: 2026-11-18
    lang: en
    format: html
  - id: s2
    url: https://www.sec.gov/Archives/edgar/data/0001341439/000119312526445847/d181425d424b5.htm
    publisher: Oracle Corporation（SEC Form 424B5 prospectus supplement）
    published: 2026-11-02
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

- Oracle offered "86,206,897 shares of our common stock, par value $0.01 per share" at a price to public of $116.0000 per share, $10,000,000,052 in total. [s2]
- Concurrently, Oracle made "a public offering of $10,000,000,000 aggregate principal amount of senior notes". [s2]
- "The Common Stock Offering closed on November 4, 2026". [s1]
- "The net proceeds of the Offerings will be used for general corporate purposes, which may include capital expenditures, repayment of indebtedness" … [s1]

## 影響股市證據

> 本檔讀過的來源是公司申報文件，沒有記載大盤變動。

## 相關標的

- On November 4, 2026 Oracle issued $2,000,000,000 of 7.000% Notes due 2029, $1,750,000,000 of 7.450% Notes due 2031, $2,250,000,000 of 7.850% Notes due 2033, $2,500,000,000 of 8.000% Notes due 2037 and $1,500,000,000 of 8.650% Notes due 2046. [s1]
- The prospectus supplement gives the "last reported sale price" on October 30, 2026 as "$130.67 per share", against the $116.0000 offering price. [s2]
- Proceeds to Oracle were $114.5906 per share, $9,878,500,051 in total, after underwriting discounts of $1.4094 per share. [s2]

## 當日與之後的行情

> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。盤後才公布的事件，當日欄反應不到，請看次一交易日欄。

| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | 次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |
|---|---|---|---|---|---|---|---|---|---|---|
| 加權指數 | 2026-11-03 | 2026-11-02 | 44920.14 | -0.65% | 2026-11-03 | 43307.54 | -3.59% | -0.83% | -4.92% |  |
| 台積電 2330 | 2026-11-03 | 2026-11-02 | 2330.00 | -1.69% | 2026-11-03 | 2295.00 | -1.50% | -1.53% | -1.93% |  |
| 台達電 2308 | 2026-11-03 | 2026-11-02 | 1355.00 | +1.50% | 2026-11-03 | 1270.00 | -6.27% | -3.94% | -5.90% |  |
| 元大台灣50 0050 | 2026-11-03 | 2026-11-02 | 104.10 | -0.81% | 2026-11-03 | 100.60 | -3.36% | -0.75% | -4.23% |  |
| 富邦台50 006208 | 2026-11-03 | 2026-11-02 | 238.65 | -0.87% | 2026-11-03 | 230.55 | -3.39% | -0.87% | -4.09% |  |
| S&P 500 | 2026-11-02 | 2026-10-30 | 7580.07 | -1.82% | 2026-11-02 | 7541.40 | -0.51% | +0.36% | -0.40% |  |
| Nasdaq Composite | 2026-11-02 | 2026-10-30 | 25437.00 | -2.86% | 2026-11-02 | 25164.31 | -1.07% | +0.83% | -0.72% |  |
| Dow Jones Industrial Average | 2026-11-02 | 2026-10-30 | 51770.31 | -1.09% | 2026-11-02 | 51983.98 | +0.41% | -0.38% | +1.20% |  |
| 費城半導體指數 | 2026-11-02 | 2026-10-30 | 10688.80 | -7.20% | 2026-11-02 | 10328.33 | -3.37% | +2.63% | -6.13% |  |

> significance 依據（key）：AI投資公司同時增資與發債，是目標4「下一輪增貸」最直接的公司層級事實。
