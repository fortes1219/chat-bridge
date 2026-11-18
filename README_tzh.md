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

目前狀態：只完成工作環境。`uv run chat-bridge --version` 會印出版本；不帶參數時只印一句說明，還沒有可啟動的服務。

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
```

新增依賴用 `uv add <套件>`，會同時更新 `pyproject.toml` 與 `uv.lock`。
