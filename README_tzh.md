[English](README.md) | 繁體中文

# chat-bridge

哪些市場消息跟我的持股有關？chat-bridge 是在本機執行的台美股研究工具，用 RAG 從文件檢索資料再作答。
用繁體中文或英文提問，就能從回答追查市場新聞與文件。想調整投資配置時，可以先比較目前與建議的目標權重，
看看各自符合哪些規則，再決定要不要接受提案。

[英文簡報入口與封面](README.md#chat-bridge)

## 快速開始

用 Git 複製儲存庫，或從 GitHub 下載 ZIP 解壓縮。接著安裝 [Node.js](https://nodejs.org/en/download)
與 [uv](https://docs.astral.sh/uv/getting-started/installation/)。Node.js 請用目前仍受支援的 LTS
版本。22、24、26 系列的最低版本分別為 22.23.5、24.22.3、26.13.1。uv 會在需要時下載
`.python-version` 指定的 Python 版本。

從下面選**一個**聊天後端，用自己的帳號登入。

| 聊天後端 | 登入指令 | 安裝說明 |
| --- | --- | --- |
| Claude Code | `claude auth login` | [Claude Code 安裝指南](https://code.claude.com/docs/en/setup) |
| Codex | `codex login` | [Codex CLI 安裝指南](https://github.com/openai/codex) |

安裝後重新開啟終端機，讓系統找到新指令。在專案根目錄執行：

```sh
uv run chat-bridge
```

程式會建置網頁，知識庫是空的時會先匯入範例新聞，最後打開[聊天頁面](http://127.0.0.1:8000)。
初次啟動請預留幾分鐘與數 GB 空間。Python 套件約 1.2 GB，主要是 CPU 版 PyTorch。
向量模型另需約 2.3 GB。之後啟動會沿用裝好的套件和索引。

按 Ctrl+C 停止服務。加上 `--no-browser` 可只啟動服務，`uv run chat-bridge --help` 會列出其他指令。
如果 chat-bridge 已在執行，重跑指令會開啟原本的頁面。若有其他程式占用 8000 連接埠，啟動時會顯示原因。

## 試一次研究流程

1. **問市場。** 選一題範例，或問「聯準會的利率政策對台股有什麼影響？」打開出處清單，
   看系統找到哪些資料，再點回答裡的引用編號看原文。
2. **設定投資組合。** 可以先用模擬持股，也可以在「編輯持股」調整數量、平均成本與現金。
   另外可設定單一持股或單一市場的權重上限等規則。
3. **比較配置提案。** 在聊天裡請系統調整策略。提案會並列目前與建議的目標權重、各項差異，
   以及調整前後的規則檢查結果。接受後才會更新目標權重，拒絕則關閉提案。程式不會下單。

介面與聊天都支援繁體中文和英文。介面會依瀏覽器語言開啟，也可以手動切換。
這是投資研究用的展示專案，內容不構成投資建議。

### 持股設定

- 股票代號採用 Yahoo Finance 格式，例如 `2330.TW`、`6488.TWO`、`AAPL`、`BRK-B`。
  可儲存最多 30 檔台股與美股，另加現金。問題只提「我的持股」而未指定標的時，
  系統最多會逐檔檢索八檔。
- 新增持股的目標權重從 0% 開始。移除持股時，也會移除它的目標權重。
  權重合計偏離 100% 時，面板會提示。可以請聊天調整配置，再由你接受提案。
- 面板依最新可得的價格估算持股市值。儲存持股會覆寫原先的數量與成本。

## 檢索怎麼做

1. **建立文件索引。** 段落存進內嵌的 PostgreSQL，向量由 pgvector 管理。
   檢索結果保留標題路徑，方便回查原文。PDF 逐頁讀取文字層，並保留頁碼標籤。
   掃描版 PDF 要先做 OCR 才能匯入。長段落會依向量模型的 512 token 上限在自然斷點切分，
   Markdown 表格則保留完整。
2. **找相關段落。** 混合檢索結合 jieba 關鍵字搜尋與本機 bge-m3 向量搜尋，再用
   Reciprocal Rank Fusion（RRF）合併排名。中英文問題都可以找到另一種語言的資料。
   同義詞表會把「費半」擴展為「費城半導體指數」與 SOX。Markdown 表格另建關鍵字索引，
   權重低於正文。
3. **逐一查詢子題。** 先保留原問題排名前八的結果，再擴大搜尋正文。
   系統會檢查拆出的子題，最多逐一查八題。去除重複段落後，再附上命中事件的行情表。
   拆題失敗或超過 120 秒時，沿用原問題的檢索結果。
4. **依來源作答。** 回答後端收到檢索段落與出處資訊。同一份輸入裡和前面段落完全相同的表格或
   引用說明只送一次，後面的換成一行指回第一個段落；頁面上的來源與紀錄不受影響。
   應用程式會加上來源清單、知識庫最新事件日期與投資免責聲明。如果沒有查到資料，程式會說明
   缺口，且不呼叫回答後端。

用 20 道範例題、人工指定子題做檢索測試時，應找到的 63 份文件中命中 **59 份**，
原本只取前八段的做法命中 **45 份**。原本命中的文件都保留了。交給模型的內容變多，
回答也要等更久。實際用兩個後端回答時，部分主題在其中一種語言仍有漏查。
[檢索評估與耗時紀錄](specs/007-search-each-part/research.md)

### 聊天 API

可以在[本機 API 文件](http://127.0.0.1:8000/docs)試用端點。

| 端點 | 回傳內容 |
| --- | --- |
| `GET /chat/programs` | 各後端的安裝與登入狀態，查詢時不會啟動模型 |
| `POST /chat/stream` | 以 Server-Sent Events 回傳回答與配置提案 |
| `GET /chat/records` | 最近的提問及檢索結果。加上 `?unanswered=true` 可篩出未找到資料的提問 |

送出的 JSON 可以是 `{"question": "聯準會有升息嗎？"}`。也可傳入 `program`，指定
`claude-code` 或 `codex`。未指定時，應用程式優先使用已登入的 Claude Code，其次是 Codex。
手動指定的後端必須已登入。

`effort` 設定回答後端思考的強度：`low`、`medium`（預設）或 `high`，聊天頁面在輸入框下方
顯示為快速、預設、精準。同一題裡每次叫模型都套用。Claude Code 以 `--effort` 啟動，
Codex 以 `model_reasoning_effort` 啟動，更高的強度不開放。啟動 Claude Code 時會移除
`CLAUDE_CODE_EFFORT_LEVEL`，所以它蓋不掉頁面的選擇。模型沒有選到的強度時，Claude Code
會改用該模型有的、低於它的最高一級；沒有強度設定的模型不支援這個選項。
2026-11-27 每個後端在每種強度各問一次配置調整題，量到的秒數（到答案出現為止）：

| 後端 | 快速 | 預設 |
| --- | --- | --- |
| Claude Code 2.1.328 | 85.6 | 107.6 |
| Codex 0.171.0 | 40.4 | 42.6 |

拆題在兩種強度都是 7 到 8 秒。每個數字都只量了一次。[量測紀錄](specs/018-answer-effort/research.md)

答案結束時，最後一個事件 `response.completed` 帶著 `usage`：這一題每次叫模型的輸入、
快取輸入、輸出與總 token 數的加總，以及 `unreported_runs`，也就是沒有回報用量、沒算進去的次數。
Claude Code 的數字取自結果裡的 `modelUsage`，輸入是 `inputTokens` 加上快取讀取與寫入；
Codex 的數字取自 `turn.completed` 事件，它的輸入已經含快取。聊天頁面在答案下方顯示總數。
中途停止或出錯的答案沒有總數，但紀錄會保留每一次的用量。[用量怎麼讀](specs/019-token-usage/research.md)

第一筆 `response.context` 包含來源、索引中最新的事件日期、回答後端、拆題失敗標記
`split_failed` 與中英文免責聲明。回答文字由 `response.output_text.delta` 傳送。
Claude Code 的一般回答會分段送出，Codex 或包含提案的回答會一次送出。
配置提案可由 `response.proposal` 傳送。串流開始後的錯誤會送出 `error` 事件，
檢索無法啟動時則會先回傳 HTTP 503。行情更新走獨立的 Socket.IO 連線。
[前端聊天 API 合約](frontend/src/service/contract/chat.ts)

### 本機使用與模型權限

服務只綁定本機迴路位址，且只接受本機主機名稱。請在自己信任的電腦上單人使用。
內嵌的 PostgreSQL 未設密碼。Windows 上，服務執行期間，同一台電腦的其他程序可以連到資料庫。

問題與檢索段落會以資料的形式，經標準輸入交給回答後端。Claude Code 會停用工具。
Codex 會在空的工作目錄及唯讀沙箱中執行，停用指令、檔案和網路工具。
修補檔案的工具仍存在，但唯讀沙箱會阻止寫入。chat-bridge 使用 CLI 儲存的登入狀態，
啟動時會移除 API 金鑰環境變數。來源與免責聲明由應用程式附上。

Codex 0.166.0 的實測涵蓋三種情境：惡意聊天訊息、文件夾帶要求改寫答案的指令，
以及文件要求讀取本機檔案。三次回答都保留出處和免責聲明，沒有帶出本機檔案內容。
每種情境只測了一次，提示注入仍可能影響模型生成的文字。
[啟動參數與實測紀錄](specs/004-answer-with-codex/research.md)

## 匯入文件與搜尋

```sh
uv run chat-bridge ingest data/documents
uv run chat-bridge search "台積電 法說會"
uv run chat-bridge search "Did the Fed raise rates?" --limit 5
```

- `ingest` 會掃描資料夾與子資料夾中的 `.docx`、`.doc`、`.pdf`、`.txt` 和 `.md`。
  內容未改的檔案會跳過。讀不到的檔案會列出原因，其餘檔案仍會匯入。
  PDF 由 pypdf 讀取，`.doc` 用 office-oxide，`.docx` 用 MarkItDown。
  `.odt` 請先轉存為 DOCX 或 PDF，文字檔請用 UTF-8。
  [範例文件與授權](docs/sample_documents.md) · [PDF 擷取說明](specs/005-long-documents/research.md)
- `search` 預設列出五筆結果，包含檔名、事件日、標題路徑、內容節錄，以及關鍵字與向量排名。
  `--as-of 2026-07-31` 以 Markdown 檔頭的 `event_date` 篩選整份文件，沒有事件日的文件會排除。
  若較早的事件檔寫入了後續發展，那些段落仍可能出現在結果中。
- 改過 `data/synonyms.txt` 後，再跑一次 `ingest` 就會重建關鍵字索引並沿用向量。
  資料庫、詞典與模型放在 Git 忽略的 `local_data/`，可用 `CHAT_BRIDGE_LOCAL_DATA` 指定其他位置。
- 在腳本裡可用結束代碼判斷結果。`0` 表示成功，`1` 表示有檔案無法匯入或查無結果，`2` 表示發生錯誤。

### 只使用自己的文件

```sh
uv run chat-bridge ingest path/to/your-folder --replace
```

一般的 `ingest` 會把資料夾加進現有知識庫。加上 `--replace` 會移除知識庫中不屬於指定資料夾
的文件，包含範例新聞，並列出移除項目。若一份文件都讀不到，既有索引會保留。
新增、修改或刪除檔案後，可以重跑指令同步索引。移除範例新聞後，頁面也會隱藏相關問題。
若要加回範例，執行 `uv run chat-bridge ingest data/truth`。

## 收錄新的市場事件

```sh
uv run chat-bridge collect
uv run chat-bridge truth
uv run chat-bridge ingest data/truth
```

1. **收集來源。** `collect` 用已登入的 CLI，從最新一筆範例事件的日期開始，
   搜尋 `data/channels.json` 裡的網站。可以用 `--until 2026-11-25` 指定截止日，
   也可以直接傳入文章或訂閱來源的網址。程式會擷取符合範圍的網頁，按事件存進
   `local_data/collected/`。擷取會遵守 robots.txt、驗證 TLS、拒絕本機與內網位址，
   並限制每次下載最多 20 MB。PDF 請另行下載，再用 `ingest` 匯入。
2. **整理事件。** `truth` 依來源頁面整理成含引用的 Markdown，預設寫入 `data/truth`。
   程式會檢查引用原文、語言、詞彙和數字格式。初稿未通過會重試一次，再失敗就留到
   下次執行。可用 `--limit 3` 先處理三筆，也可用 `--workers 2` 把同時處理的工作從
   預設五個降為兩個。`--into` 可更換輸出資料夾。寫入自訂資料夾後，事件也會從待處理清單移除。
   若要再寫入預設資料夾，需重新收集這些事件。
3. **建立索引。** 執行 `ingest` 後，聊天才會查到新事件。收集與整理會使用你的 CLI
   帳號額度。重用來源內容前，請先確認對方的使用條款。

[事件格式與採集範圍](docs/truth_format.md) · [曝險詞彙表](docs/exposure_vocabulary.md)

若只想更新既有事件的「當日與之後的行情」，把檔案或資料夾交給 `collect`：

```sh
uv run chat-bridge collect data/truth/2026-11-17-taiex-falls-947-points.md
```

各市場會把收盤時間等於或晚於 `event_time` 的第一個交易日當成 D0。
沒有 `event_time` 時，改用事件日期對齊。日線收盤價取自 Yahoo Finance，
台股缺值有 FinMind 資料時會補上。兩邊都查不到就標記為「沒有資料」。
更新後可重新匯入，讓聊天查到新內容。

## 行情與資料來源

策略面板透過 yfinance 取得 Yahoo Finance 的行情，並附上 Yahoo 的使用條款。
台股昨收及除權息參考價，也會用到 [FinMind 公開 API](https://finmind.github.io/PrivacyPolicy/)
與交易所開放資料。

> 臺灣證券交易所 2026 臺灣證券交易所 OpenAPI 1.0：上市個股日成交資訊、上市股票除權除息預告表
>
> 證券櫃檯買賣中心 2026 證券櫃檯買賣中心 OpenAPI 1.0.0：上櫃股票行情、上櫃股票除權除息預告表
>
> 此開放資料依政府資料開放授權條款 (Open Government Data License) 進行公眾釋出，使用者於遵守本條款各項規定之前提下，得利用之。
>
> 政府資料開放授權條款：https://data.gov.tw/license

範例新聞涵蓋 2026 年 6 月至 11 月的台股、美股、聯準會與 AI 產業事件。
每份事件檔都附上來源與事件前後的行情。專案也附有雙語範例問題、同義詞與行情序列設定。
[事件檔格式](docs/truth_format.md)

## 開發

```sh
uv run pytest
uv run ruff check chat_bridge tests
uv run ruff format --check chat_bridge tests
uv run mypy chat_bridge tests
```

預設測試不需要向量模型或資料庫。整合測試可用 `uv run pytest -m slow` 執行，
也可以在 Linux 容器裡跑：

```sh
docker compose -f compose.test.yml run --rm slow-tests
```

整合測試會載入向量模型、啟動 PostgreSQL 並匯入範例新聞，其中包含 41 道查詢的回歸檢查。
測試各自使用獨立資料夾，並可透過 `HF_HUB_CACHE` 沿用模型快取。
容器會建置可在不同 x86-64 CPU 上使用的 pgvector，以唯讀方式掛載測試資料，
並把套件和模型快取在 Docker volumes。[檢索回歸測試基準](tests/data/search_yield.yaml)

### 不使用 uv

備用安裝方式需要 Python 3.11.5 以上。pip 會自行解析套件版本，Linux 上也可能下載較大的 PyTorch 版本。

- Windows（PowerShell）

  ```powershell
  py -m venv .venv
  .venv\Scripts\Activate.ps1
  py -m pip install -e .
  chat-bridge
  ```

- macOS 或 Linux

  ```sh
  python3 -m venv .venv
  source .venv/bin/activate
  python3 -m pip install -e .
  chat-bridge
  ```
