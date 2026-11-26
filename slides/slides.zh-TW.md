---
layout: research
slideId: cover
locale: zh-TW
theme: default
routerMode: hash
colorSchema: light
aspectRatio: 16/9
fonts:
  provider: none
title: chat-bridge · 台美股投資研究
appearance: ink
composition: cover
---

# 哪些市場消息<br>跟我的持股有關？

<p class="lead">用自然語言查台美股事件。沿著引用核對資料，再看調整配置會差多少。</p>

---
layout: research
slideId: workflow
locale: zh-TW
---

# 從一句問題，走到配置差異

> 聯準會最近的利率決策和大廠 AI 支出，跟我手上的台積電與 0050 有什麼關係？

<div class="summary-grid">
<section><h2>問自己的持股</h2><p>輸入一個自然語言問題，系統會帶上目前的持股與規則。</p></section>
<section><h2>回到證據</h2><p>回答標出引用與資料日期。點開可看到實際找到的文件與段落。</p></section>
<section><h2>比較配置</h2><p>需要時才請模型提出目標權重。使用者看到差異後，再決定是否套用。</p></section>
</div>

---
layout: research
slideId: corpus
locale: zh-TW
---

# 一個事件一檔，先把來源寫清楚

<div class="case-grid">

<div>

<div class="display-stat"><span>71 份</span><p>原始評估用的市場事件</p></div>

<p class="caption">範例匯入後有 316 個段落。</p>
</div>

<div>

**檔頭**保留事件日、標的、分類、關鍵字組和來源。

**內文**分成事件事實、報導中的行情與歸因、相關標的。

**行情表**另附收盤價和漲跌。來源明說的歸因保留出處。

</div>
</div>

---
layout: research
slideId: normalization
locale: zh-TW
---

# 台股用語要讓搜尋認得

| 原始寫法 | 進資料或搜尋時的做法 |
| --- | --- |
| 1774.18 億元 | 保留幣別與精度，寫成 NT$177.418 billion。 |
| 升息 1 碼 | 寫成 0.25 個百分點，保留原文的時間與條件。 |
| 費半 | 查詢時一併找「費城半導體指數」與 SOX。 |
| 央行 | 保留原詞。要查台灣央行或聯準會，由問題和證據區分。 |

<p class="caption">同一概念的中英名稱與代號成組管理。含歧義的詞避免自動展開。</p>

---
layout: research
slideId: ingest
locale: zh-TW
composition: diagram
---

# 切段後，還能找到原本那一頁

Markdown 和 Word 保留標題，PDF 保留頁碼。內容相同的檔案用 SHA-256 跳過。

---
layout: research
slideId: hybrid
locale: zh-TW
composition: diagram
---

# 向量找語意，全文索引抓關鍵字

bge-m3 與 pgvector 找語意相近的段落。jieba 與 PostgreSQL 全文索引找公司名、代號和別名。兩路一般各取 20 個候選，再用 RRF 合併。

---
layout: research
slideId: failure
locale: zh-TW
appearance: ink
composition: scene
---

# 問了六件事，第一輪卻漏了利率

同一題問到**利率、AI 資本支出、台積電、0050、美股科技指數和機構看法**。

六個面向一起競爭前 8 段的位置。這一輪沒有任何利率證據進入回答的上下文。

---
layout: research
slideId: retrieval
locale: zh-TW
appearance: ink
composition: scene
---

# 讓每個子題各自找證據

保留原題前 8 段，另取 30 段。最多拆成 8 個子題，每題各取 8 段。

**合併時去重。** 每個子題原本找到的證據會留在結果裡。

<p class="caption">右側切換「拆題後」，看利率這一組補回哪些資料。</p>

---
layout: research
slideId: evaluation
locale: zh-TW
composition: diagram
---

# 保留題也找回了更多證據

初版保留題含 25 筆新聞目標和 3 張行情表。這一頁量的是模型收到的證據。

---
layout: research
slideId: tradeoffs
locale: zh-TW
composition: diagram
---

# 試過多取與重排，最後留下拆題

原型比較三個做法。除了總命中，也看利率案例能不能救回，以及每題多花多少時間。

---
layout: research
slideId: grounding
locale: zh-TW
---

# 把檢索和回答分開評估

<div class="case-grid">

<div>

<div class="display-stat"><span>14 份</span><p>7 題 × 兩個回答程式</p></div>

</div>

<div>

**先看有沒有漏答。** 10 份涵蓋所有應答項，另 4 份各漏一件，能追到檢索未送出的文件。

**再核對答案的數字。** 約 200 個數值對回來源，未發現數值轉錄錯誤。其中一份把兩個時間口徑的先後說反。

</div>
</div>

---
layout: research
slideId: proposal
locale: zh-TW
---

# 配置要改多少，先算給使用者看

1. 模型提出既有標的的目標權重與引用。
2. 後端檢查比例合計 100%，計算差了幾個百分點及規則結果。
3. 使用者確認後，才更新目標權重。

---
layout: research
slideId: controls
locale: zh-TW
---

# 模型可以提案，寫入由程式和人把關

<div class="summary-grid">
<section><h2>收到哪些資料</h2><p>CLI 收到問題、檢索段落和持股資料。聊天執行器依各 CLI 的方式限制工具。</p></section>
<section><h2>誰負責驗證</h2><p>後端提供來源清單、固定聲明和數值。提案格式錯誤時，仍可保留文字回答。</p></section>
<section><h2>誰負責套用</h2><p>後端驗證提案仍待處理。使用者確認後，才在交易內更新目標權重。</p></section>
</div>

---
layout: research
slideId: operations
locale: zh-TW
composition: diagram
---

# 行情和模型回覆各走自己的路

聊天用使用者登入的 Claude Code 或 Codex。台股昨收可由 FinMind 與交易所公開資料補足。

<p class="caption">前端用 oRPC 和 Zod 檢查資料合約，由 TanStack Query 管理伺服器狀態。</p>

---
layout: research
slideId: delivery
locale: zh-TW
---

# 我怎麼讓 AI 協作留下可查的結果

<div class="summary-grid">
<section><h2>實作前</h2><p>用 Spec Kit 記錄需求、計畫、套件來源與驗收條件。</p></section>
<section><h2>實作時</h2><p>把可判斷的規則放進 Claude Code hook，例如攔下欠缺規格的程式變更。</p></section>
<section><h2>交付前</h2><p>用固定題與保留題各驗一次，人工核對樣本，最後由維護者決定提交。</p></section>
</div>

<p class="caption">同一案例留了輸入、命中證據和答案，面試可回到原始紀錄說明。</p>

---
layout: research
slideId: limits
locale: zh-TW
---

# Demo 最值得看的是哪一段

1. 問一題同時涉及利率、AI 支出和持股的問題。
2. 打開引用，核對模型手上的證據與資料日期。
3. 預覽配置調整，確認或拒絕提案。

<p class="caption">這是本機單人展示。保留題樣本有限，中文利率查詢仍有漏檢案例。歷史查詢依事件日過濾，事件檔仍可能含後續行情。</p>

<code class="shortcut">uv run chat-bridge</code>
