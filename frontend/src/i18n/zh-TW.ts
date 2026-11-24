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
    waitingProposal: '{program} 正在寫答案與修正後的策略，答案會一次出現……',
    proposalReady: '修正後的策略已列在聊天旁邊。',
    viewProposal: '看前後差異',
    proposalRefused: '修正後的策略沒有顯示：{reason}。',
    noProposal: '這次沒有提出策略修正。',
    proposalClosed: '這份修正已經接受、否決，或被新的取代，不再等你決定。',
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
    },
    profile_missing: {
      title: '範例投資組合還沒載入。',
      description: '在終端機按 Ctrl+C 停掉服務，再啟動一次；它會載入範例投資組合。'
    },
    proposal_not_found: {
      title: '這份修正已經不在了。',
      description: '重新整理頁面，看目前的策略。'
    },
    proposal_not_open: {
      title: '這份修正已經接受、否決，或被新的取代了。',
      description: '畫面上的是目前的策略。'
    },
    rule_unknown_kind: {
      title: '其中一條規則的種類，服務不認得。',
      description: '重新整理頁面，再編輯一次規則。'
    },
    rule_limit_out_of_range: {
      title: '規則的上下限要在 0 到 100% 之間。',
      description: '改好之後再儲存一次。'
    },
    rule_market: {
      title: '市場上限的規則要選台股或美股；其他種類不選市場。',
      description: '改好之後再儲存一次。'
    }
  },
  refusals: {
    not_the_shape: '格式不符',
    unknown_holding: '列了投資組合裡沒有的標的',
    repeated_holding: '同一個標的列了兩次',
    missing_holding: '有標的沒有給目標比例',
    percent_out_of_range: '有目標比例超出 0 到 100%',
    not_100: '目標比例加總不是 100%',
    unknown_source: '理由引用了答案沒有的出處'
  },
  strategy: {
    title: '投資策略',
    open: '投資策略',
    loading: '正在讀取投資策略……',
    holding: '標的',
    target: '目標',
    current: '目前',
    proposed: '修正後',
    change: '變化',
    proposalTitle: '修正後的策略',
    proposedBy: '由 {program} 依這個問題提出：{question}',
    reasons: '理由',
    sources: '出處',
    accept: '接受',
    reject: '否決',
    noTrade: '接受只會改目標比例，不會買賣任何標的。',
    cards: {
      total: '總值',
      change: '比各自前一個收盤',
      profit: '損益',
      pricesAt: '價格時間（最新）',
      leftOut: '沒有價格或匯率、未計入總值與損益：{names}。',
      changeLeftOut: '不知道前一個收盤、未計入漲跌：{names}。',
      changeNote:
        '每一檔比它自己市場的前一個收盤加總：台股與美股的交易日不同；美股盤前、盤後與夜盤的價格比的是前一個正式收盤。'
    },
    donut: {
      title: '配置',
      share: '比例'
    },
    holdingsTable: {
      title: '持有標的',
      detail: '{symbol}・{quantity} 股，均價 {cost}',
      targetOf: '目標 {target}',
      price: '價格',
      value: '市值',
      weight: '比例',
      profit: '損益',
      note: '金額以新台幣計。美股（含成本）以最新的美元匯率換算。'
    },
    quotes: {
      title: '行情',
      realTime: '即時',
      delayed: '延遲 {minutes} 分鐘',
      delayUnstated: '未標明延遲',
      liveAt: '{time}',
      closeOn: '{day} 日線',
      source: '價格來自 {name}，不是交易所官方的資料。',
      terms: '使用條款',
      updating: '更新中',
      sourceDown: '沒有連上行情來源，價格停在顯示的時間',
      connecting: '連線中…',
      disconnected: '未更新',
      invalid: '有 {count} 次更新的資料不符格式、沒有畫上去，畫面上的數字可能不是最新的。重新整理頁面可以再讀一次。'
    }
  },
  markets: {
    TW: '台股',
    US: '美股',
    cash: '現金'
  },
  rules: {
    title: '你的規則',
    summary: '符合 {met} / {enabled} 條規則',
    noneOn: '沒有開啟的規則。',
    note: '規則檢查的是策略的目標比例，不是今天的市值，所以價格變動不會改變結果。現金不算一個標的。',
    met: '符合',
    broken: '不符合',
    off: '關閉',
    breaking: '不符合的：{names}',
    edit: '編輯規則',
    add: '新增規則',
    remove: '刪除這條規則',
    save: '儲存',
    cancel: '取消',
    kind: '種類',
    limit: '上下限（%）',
    market: '市場',
    enabled: '開啟',
    proposalTitle: '你的規則：修正前後',
    before: '目前',
    after: '修正後',
    max_holding_weight: {
      name: '單一標的上限',
      rule: '任一標的最多 {limit}%',
      measured: '最高 {value}%'
    },
    min_holding_weight: {
      name: '持有標的下限',
      rule: '有持有的標的最少 {limit}%',
      measured: '最低 {value}%'
    },
    max_market_weight: {
      name: '單一市場上限',
      rule: '{market}合計最多 {limit}%',
      measured: '合計 {value}%'
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
