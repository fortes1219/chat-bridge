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

第一次執行時，uv 會在 repo 裡建立 `.venv`，照 `uv.lock` 安裝依賴；機器上沒有 `.python-version` 指定的 Python 時，uv 會自己下載。之後依賴沒變就直接啟動。

目前狀態：可以用命令列導入文件並查詢（見下一節）。不帶參數執行 `uv run chat-bridge` 會列出所有指令。聊天頁面還沒做。

## 導入文件並查詢

```
uv run chat-bridge ingest data/truth
uv run chat-bridge search "台積電 法說會"
uv run chat-bridge search "Did the Fed raise rates?"
```

- `ingest <資料夾>` 讀取資料夾與子資料夾裡所有 `.docx`、`.pdf`、`.txt`、`.md` 檔，轉成 Markdown，依標題切段，存進內嵌的 PostgreSQL 資料庫。和上次比內容沒變的檔會跳過。
- 讀不到的檔會列出檔名與原因，其他檔照樣存進去。包括不支援的檔案類型、不是 UTF-8 的文字檔、沒有文字層的 PDF。不做 OCR。
- `search <問題>` 列出最符合的段落，每段附檔名、標題路徑與一段內文。用 `--limit` 改列出幾段（預設 5 段）。沒有任何段落符合時，會明講資料裡沒有。
- 目前是用 jieba 斷詞的關鍵字搜尋，繁體中文或英文都可以問。向量搜尋還沒加。
- 第一次執行時會下載 jieba 的繁體中文詞典（8.6 MB）。資料庫和詞典放在 `local_data/`，git 不追蹤。要從頭來就刪掉這個資料夾；要換位置就設環境變數 `CHAT_BRIDGE_LOCAL_DATA`。
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

需要 Python 3.11 以上。這條路不使用 `uv.lock`，依賴版本可能和上面不同。

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

## 開發

```
uv run pytest
uv run ruff check chat_bridge
uv run ruff format --check chat_bridge
uv run mypy chat_bridge
```

lint、格式與型別檢查的設定照 FastAPI 的 repo。新增依賴用 `uv add <套件>`，會同時更新 `pyproject.toml` 與 `uv.lock`。
