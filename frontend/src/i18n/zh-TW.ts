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
    notInstalled: '請先安裝 {program}，再按「重新偵測」。',
    unknown: '讀不到它的狀態，請再偵測一次。'
  },
  chat: {
    placeholder: '問問今年六月以來的市場消息……',
    answerWith: '回答的程式',
    samplesTitle: '可以從這幾題開始',
    sources: '出處',
    noDate: '無日期',
    latestDate: '出處最新到 {date}。',
    noLatestDate: '出處都沒有日期。',
    stopped: '已停止。',
    failed: '回答中途出錯。',
    emptyQuestion: '請先輸入問題。',
    longQuestion: '問題最多 {limit} 個字。'
  },
  samples: {
    fed: '聯準會在這近半年的動向哪些行為導致股市動盪',
    aiSpending: '微軟與其他科技巨頭的 AI 投資，為什麼讓投資人擔心？',
    tsmc: '台積電與供應鏈最近受到哪些事件影響？',
    recovery: '有沒有權威說法認為股市會恢復正常？'
  }
};

export default zhTW;
