import type en from '@/i18n/en';

/** Traditional Chinese texts, with the same keys as the English ones. */
const zhTW: typeof en = {
  login: {
    reading: '正在確認 Claude Code 與 Codex 是否已登入……',
    title: '請先登入 Claude Code 或 Codex',
    description: '回答由這台電腦上登入的 Claude Code 或 Codex 產生。請在終端機登入其中一個，再按「重新偵測」。',
    unreachableTitle: '連不到聊天服務',
    unreachable: '請確認 uv run chat-bridge 還在執行，再按「重新偵測」。',
    checkAgain: '重新偵測',
    copy: '複製',
    copied: '已複製'
  },
  loginState: {
    loggedIn: '已登入',
    notLoggedIn: '未登入',
    notInstalled: '未安裝',
    unknown: '讀不到狀態'
  },
  loginNext: {
    loggedIn: '可以回答。',
    notLoggedIn: '在終端機執行這個指令登入：',
    notInstalled: '用下面的指令安裝 {program}，再用最後一行登入，然後按「重新偵測」。',
    unknown: '讀不到它的狀態，請再偵測一次。'
  },
  page: {
    language: '頁面語言'
  },
  chat: {
    placeholder: '問問今年六月以來的市場消息……',
    answerWith: '回答的程式',
    samplesTitle: '可以從這幾題開始',
    sources: '出處',
    noDate: '無日期',
    latestDate: '資料最新到 {date}。',
    noLatestDate: '資料都沒有日期。',
    splitFailed: '這個問題沒能拆成幾個部分，所以整句一起查。',
    allSources: '找到 {count} 個出處',
    citedSources: '答案引用的出處',
    noneCited: '答案沒有引用任何出處。',
    stopped: '已停止。',
    searching: '正在查新聞資料……',
    waiting: '正在等 {program} 回答……',
    emptyQuestion: '請先輸入問題。',
    longQuestion: '問題最多 {limit} 個字。'
  },
  errors: {
    knowledge_base_empty: {
      title: '還沒有匯入任何新聞。',
      description: '在終端機按 Ctrl+C 停掉服務，再啟動一次；它會先匯入範例新聞。'
    },
    knowledge_base_outdated: {
      title: '知識庫是別的版本建的。',
      description: '停掉服務，刪掉 local_data/pgdata 資料夾，再啟動一次；它會重新匯入範例新聞。'
    },
    setup_failed: {
      title: '服務載入不到需要的檔案。',
      description: '執行 chat-bridge 的終端機會寫是哪個檔、要怎麼做。'
    },
    not_logged_in: {
      title: '回答的程式已經登出了。',
      description: '請在終端機重新登入；頁面已經重新確認過登入狀態。'
    },
    answer_failed: {
      title: '回答中途出錯。',
      description: '請再問一次。一直發生的話，執行 chat-bridge 的終端機會寫原因。'
    },
    rejected: {
      title: '這一題沒辦法回答。',
      description: '請再問一次。一直發生的話，執行 chat-bridge 的終端機會寫原因。'
    },
    stream_error: {
      title: '回答中途出錯。',
      description: '請再問一次。一直發生的話，執行 chat-bridge 的終端機會寫原因。'
    },
    network_error: {
      title: '連不到聊天服務。',
      description: '請確認 uv run chat-bridge 還在執行，再問一次。'
    },
    contract_error: {
      title: '頁面和服務對不上。',
      description: '請重新整理頁面；一直發生的話，重新啟動服務。'
    },
    invalid_input: {
      title: '這一題送不出去。',
      description: '請檢查問題，再問一次。'
    },
    unknown_error: {
      title: '發生了未預期的錯誤。',
      description: '請再問一次；一直發生的話，重新整理頁面。'
    }
  },
  samples: {
    fed: '聯準會在這近半年的動向哪些行為導致股市動盪？',
    aiSpending: '微軟與其他科技巨頭的 AI 投資，為什麼讓投資人擔心？',
    tsmc: '台積電與供應鏈最近受到哪些事件影響？',
    recovery: '有沒有權威說法認為股市會恢復正常？'
  }
};

export default zhTW;
