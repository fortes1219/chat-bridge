[English](README.md) | 繁體中文

# chat-bridge

把市場新聞整理成可檢索的知識庫，讓使用者用自然語言詢問、並依自己的指標調整投資設定的 RAG 展示專案。建置中。

## 一個指令跑起來

前提：

- [uv](https://docs.astral.sh/uv/)（Python 的專案管理工具；沒有的話見下一節）
- Node.js
- 已登入你自己的 Claude Code

在 repo 根目錄執行：

```
uv run chat-bridge
```

第一次執行時，uv 會在 repo 裡建立 `.venv`，照 `uv.lock` 安裝依賴；機器上沒有 `.python-version` 指定的 Python 時，uv 會自己下載。依賴約 1.2 GB，大部分是只用 CPU 的 PyTorch。之後依賴沒變就直接啟動。

目前狀態：可以用命令列導入文件並查詢（見下一節）。不帶參數執行 `uv run chat-bridge` 會列出所有指令。聊天頁面還沒做。

## 導入文件並查詢

```
uv run chat-bridge ingest data/truth
uv run chat-bridge search "台積電 法說會"
uv run chat-bridge search "Did the Fed raise rates?"
```

- `ingest <資料夾>` 讀取資料夾與子資料夾裡所有 `.docx`、`.pdf`、`.txt`、`.md` 檔，轉成 Markdown，依標題切段，存進內嵌的 PostgreSQL 資料庫。和上次比內容沒變的檔會跳過。
- 讀不到的檔會列出檔名與原因，其他檔照樣存進去。包括不支援的檔案類型、不是 UTF-8 的文字檔、沒有文字層的 PDF。不做 OCR。
- `search <問題>` 列出最符合的段落，每段附檔名、事件日期、標題路徑與一段內文。用 `--limit` 改列出幾段（預設 5 段）。沒有任何段落符合時，會明講資料裡沒有。
- `search <問題> --as-of 2026-07-31` 只查事件發生在那一天（含）以前的檔，用來看「當時知道什麼」。日期取自 Markdown 檔 front matter 的 `event_date`。沒有這個欄位的檔不列入這種查詢，輸出會講有幾個檔因此沒列入。Word 和 PDF 沒有 front matter，要列入就先轉成 Markdown、加上 `event_date`。
- 日期過濾以整個檔為單位，同一個檔裡較晚的段落不會被濾掉：範例資料裡，事件之後幾天的行情與後續發展都寫在那個事件的檔裡。所以 `--as-of` 擋得住之後才發生的事件，擋不住寫進較早事件檔裡的後來的事。
- 搜尋是混合檢索，繁體中文或英文都可以問。關鍵字那一邊用 jieba 斷詞；向量那一邊用在你的 CPU 上跑的 [bge-m3](https://huggingface.co/BAAI/bge-m3) 模型，所以用英文問也找得到中文的段落，反過來也一樣。兩邊的排名用 Reciprocal Rank Fusion 合併。每筆結果會標出合併後的分數，以及兩種方法各排第幾（沒找到的那一邊標 `-`）。
- Markdown 表格（包括從 Word、PDF 轉出來的）和它周圍的文字分開查。表格在關鍵字排名裡排在文字後面，也不參加向量搜尋，所以每張表都列到的名稱，不會把真正談它的文字擠下去。只有表格裡才有的詞，仍然查得到。
- 問題裡的名稱會連同它的別名一起查，別名在 `data/synonyms.txt`（例如問「費半」也會查「費城半導體指數」與 SOX）。改了這個檔之後再跑一次 `ingest`，它會重建關鍵字索引，向量不重算。
- 每次 `search` 大約要 15 秒，大部分花在啟動 Python 與載入模型。
- 第一次執行時會下載 jieba 的繁體中文詞典（8.6 MB）與 bge-m3 模型（約 2.3 GB）。資料庫、詞典與模型都放在 `local_data/`，git 不追蹤。要從頭來就刪掉這個資料夾；要換位置就設環境變數 `CHAT_BRIDGE_LOCAL_DATA`。
- 結束代碼：全部成功是 `0`；`ingest` 有檔被拒、或 `search` 查不到是 `1`；發生錯誤是 `2`。

### 還沒有 uv

照 [uv 官方安裝說明](https://docs.astral.sh/uv/getting-started/installation/)：

- Windows（PowerShell）：

  ```
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

- macOS／Linux：

  ```
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### 不用 uv（備用）

需要 Python 3.11 以上。這條路不使用 `uv.lock`，依賴版本可能和上面不同。pip 也會裝預設版本的 PyTorch，在 Linux 上它包含 CUDA，會大上好幾 GB。

- Windows：

  ```
  py -m venv .venv
  .venv\Scripts\activate
  py -m pip install -e .
  chat-bridge
  ```

- macOS／Linux：

  ```
  python3 -m venv .venv
  source .venv/bin/activate
  python3 -m pip install -e .
  chat-bridge
  ```

## 範例資料

- `data/truth/`：2026 年 6 月到 11 月的台股、美股、聯準會與 AI 產業事件，一個事件一檔，每一條附來源連結，並附事件前後的行情。格式見 `docs/truth_format.md`。
- `data/synonyms.txt`：意思相同的名稱，一行一組，用 Solr 的同義詞格式。檔案開頭的註解列出哪些刻意不放、為什麼。

## 開發

```
uv run pytest
uv run pytest -m slow
uv run ruff check chat_bridge tests
uv run ruff format --check chat_bridge tests
uv run mypy chat_bridge tests
```

- `uv run pytest` 跑不需要模型、也不需要資料庫的測試，幾秒就跑完。
- `uv run pytest -m slow` 跑標成 slow 的測試：會載入模型、起內嵌的資料庫、導入 `data/truth`，要好幾分鐘。其中一個測試會問 41 題，結果比 `tests/data/search_yield.yaml` 裡量好的基準差就失敗。
- 測試不碰專案的 `local_data/`，每次執行都用自己的資料夾。只有模型例外：`local_data/models` 已經有模型時，測試透過 huggingface_hub 的 `HF_HUB_CACHE` 設定從那裡讀，不再下載 2.3 GB。要把模型放在別的地方，自己設 `HF_HUB_CACHE` 即可，程式本身也讀同一個設定。

### 在容器裡跑慢的測試

```
docker compose -f compose.test.yml run --rm slow-tests
```

- 用 Docker 在 Linux 容器裡跑慢的測試，模型與資料庫不會在你的機器上載入。`slow-tests` 後面的參數會交給 pytest，例如 `-k yield`。
- 容器最多用 6 核與 8 GB 記憶體，不開任何埠，測試結束就移除。它留下的網路用 `docker compose -f compose.test.yml down` 移除。
- 只以唯讀方式掛上測試需要的東西：`chat_bridge/`、`tests/`、`data/`、`scripts/`、`pyproject.toml`、`uv.lock`、`README.md`、`.python-version`。repo 裡其他的東西（例如 `.git/`、`local_data/`）在容器裡都看不到。
- 第一次會下載 Python 映像檔與依賴（約 1.6 GB）以及模型（約 2.3 GB），分別存在 Docker volume `chat-bridge-venv` 與 `chat-bridge-models`，之後不再下載。繁體中文詞典（8.6 MB）每次都會下載一次，因為 `local_data/` 沒有掛進去。
- 容器裡的 pgvector 會從原始碼重新編譯。內嵌資料庫附的 Linux x86_64 版是用 pgvector 預設的 `-march=native` 編的。在驗過的那顆沒有 AVX-512 的 x86_64 CPU 上，它會出現「Illegal instruction」而當掉；這裡用的是 pgvector README 寫的可攜編法。同一顆 CPU 上 Windows 版可以正常用；其他平台沒有驗過。

lint、格式與型別檢查的設定照 FastAPI 的 repo。新增依賴用 `uv add <套件>`，會同時更新 `pyproject.toml` 與 `uv.lock`。
