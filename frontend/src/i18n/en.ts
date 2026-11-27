/** English texts. Keys are at most three levels deep; zh-TW has the same keys. */
export default {
  login: {
    reading: 'Checking whether Claude Code and Codex are logged in…',
    title: 'Log in to Claude Code or Codex first',
    description:
      'Answers come from the Claude Code or Codex logged in on this computer. Log in to one of them in a terminal, then check again.',
    unreachableTitle: 'The chat service cannot be reached',
    unreachable: 'Make sure uv run chat-bridge is still running, then check again.',
    checkAgain: 'Check again',
    copy: 'Copy',
    copied: 'Copied'
  },
  loginState: {
    loggedIn: 'Logged in',
    notLoggedIn: 'Not logged in',
    notInstalled: 'Not installed',
    unknown: 'Could not be read'
  },
  loginNext: {
    loggedIn: 'Ready to answer.',
    notLoggedIn: 'Run this in a terminal to log in:',
    notInstalled: 'Install {program} with a command below, log in with the last one, then check again.',
    unknown: 'Its state could not be read. Check again.'
  },
  page: {
    language: 'Page language'
  },
  chat: {
    placeholder: 'Ask about the documents in the knowledge base…',
    answerWith: 'Answer with',
    effortLabel: 'How hard the program thinks',
    effort: {
      fast: 'Fast',
      default: 'Default',
      precise: 'Precise'
    },
    samplesTitle: 'Try one of these',
    sources: 'Sources',
    noDate: 'No date',
    latestDate: 'The data reaches {date}.',
    noLatestDate: 'None of the data has a date.',
    splitFailed: 'This question could not be split into parts, so it was searched as a whole.',
    allSources: 'Found one source | Found {count} sources',
    citedSources: 'Sources the answer cites',
    noneCited: 'The answer cites none of the sources.',
    stopped: 'Stopped.',
    searching: 'Searching the news…',
    waiting: 'Waiting for {program} to answer…',
    waitingProposal: '{program} is writing the answer and a revised strategy; the answer arrives all at once…',
    proposalReady: 'A revised strategy is ready beside the chat.',
    viewProposal: 'See the difference',
    proposalRefused: 'The revised strategy was not shown: {reason}.',
    noProposal: 'No change to the strategy was proposed.',
    proposalClosed: 'This revision was accepted, rejected or replaced; it is no longer waiting for you.',
    emptyQuestion: 'Type a question first.',
    longQuestion: 'A question can be at most {limit} characters.'
  },
  errors: {
    knowledge_base_empty: {
      title: 'No news has been imported yet.',
      description: 'Stop the service with Ctrl+C and start it again; it imports the sample news first.'
    },
    knowledge_base_outdated: {
      title: 'The knowledge base was built by another version.',
      description:
        'Stop the service, delete the local_data/pgdata folder, and start it again; it imports the sample news again.'
    },
    setup_failed: {
      title: 'The service could not load a file it needs.',
      description: 'The terminal running chat-bridge says which file and what to do.'
    },
    not_logged_in: {
      title: 'The answering program is no longer logged in.',
      description: 'Log in again in a terminal; the page has checked the login states again.'
    },
    answer_failed: {
      title: 'The answer stopped with an error.',
      description: 'Ask again. If it keeps happening, the terminal running chat-bridge shows why.'
    },
    rejected: {
      title: 'This question could not be answered.',
      description: 'Ask again. If it keeps happening, the terminal running chat-bridge shows why.'
    },
    stream_error: {
      title: 'The answer stopped with an error.',
      description: 'Ask again. If it keeps happening, the terminal running chat-bridge shows why.'
    },
    network_error: {
      title: 'The chat service cannot be reached.',
      description: 'Check that uv run chat-bridge is still running, then ask again.'
    },
    contract_error: {
      title: 'The page and the service do not match.',
      description: 'Reload the page. If it keeps happening, start the service again.'
    },
    invalid_input: {
      title: 'This question could not be sent.',
      description: 'Check the question, then ask again.'
    },
    unknown_error: {
      title: 'Something went wrong.',
      description: 'Ask again. If it keeps happening, reload the page.'
    },
    profile_missing: {
      title: 'The sample profile has not been loaded.',
      description: 'Stop the service with Ctrl+C and start it again; it loads the sample profile.'
    },
    proposal_not_found: {
      title: 'This proposal no longer exists.',
      description: 'Reload the page to see the current strategy.'
    },
    proposal_not_open: {
      title: 'This proposal has already been decided or replaced.',
      description: 'The strategy shown is the current one.'
    },
    rule_unknown_kind: {
      title: 'The service does not know one of these kinds of rule.',
      description: 'Reload the page and edit the rules again.'
    },
    rule_limit_out_of_range: {
      title: 'A rule’s limit must be from 0 to 100%.',
      description: 'Change it, then save again.'
    },
    rule_market: {
      title: 'A market rule needs Taiwan or US; the other kinds name no market.',
      description: 'Change it, then save again.'
    },
    holding_symbol: {
      title: 'Only Taiwan symbols (ending in .TW or .TWO) and US tickers are kept.',
      description: 'Write it as Yahoo Finance does, such as 2330.TW or AAPL, then save again.'
    },
    holding_repeated: {
      title: 'A symbol can be listed only once.',
      description: 'Remove or change the repeated one, then save again.'
    },
    holding_name: {
      title: 'Every holding needs a name of at most 40 characters.',
      description: 'Change it, then save again.'
    },
    holding_amount: {
      title: 'A quantity must be above 0; a cost and the cash cannot be below 0; none above 1e15.',
      description: 'Write numbers only, with a point for decimals, then save again.'
    },
    holdings_too_many: {
      title: 'At most 30 holdings, cash aside.',
      description: 'Remove some, then save again.'
    }
  },
  refusals: {
    not_the_shape: 'it is not in the asked-for shape',
    unknown_holding: 'it names a holding that is not in the profile',
    repeated_holding: 'it lists a holding twice',
    missing_holding: 'it leaves a holding without a target',
    percent_out_of_range: 'a target is outside 0 to 100%',
    not_100: 'its targets do not add up to 100%',
    unknown_source: 'a reason cites a source the answer does not have'
  },
  strategy: {
    title: 'Strategy',
    open: 'Strategy',
    loading: 'Loading the strategy…',
    holding: 'Holding',
    target: 'Target',
    current: 'Current',
    proposed: 'Proposed',
    change: 'Change',
    proposalTitle: 'Revised strategy',
    proposedBy: 'Proposed by {program} for: {question}',
    reasons: 'Why',
    sources: 'Sources',
    accept: 'Accept',
    reject: 'Reject',
    noTrade: 'Accepting changes the target weights only; nothing is bought or sold.',
    cards: {
      total: 'Total value',
      change: 'Since each one’s previous close',
      profit: 'Profit or loss',
      pricesAt: 'Prices as of',
      leftOut: 'Left out of the totals for lack of a price or exchange rate: {names}.',
      changeLeftOut: 'Left out of the change, previous close not known: {names}.',
      changeNote:
        'Each holding against the previous close of its own market, summed: Taiwan and the US trade on different days, and a US price from before or after the session, or overnight, is against the last regular close.'
    },
    donut: {
      title: 'Allocation',
      share: 'Share'
    },
    holdingsTable: {
      title: 'Holdings',
      detail: '{symbol} · {quantity} at {cost}',
      targetOf: 'target {target}',
      price: 'Price',
      value: 'Value',
      weight: 'Weight',
      profit: 'Profit or loss',
      note: 'Values are in Taiwan dollars. US holdings, their cost included, are valued at the latest US dollar rate.'
    },
    quotes: {
      title: 'Quotes',
      realTime: 'real time',
      delayed: '{minutes} min delayed',
      delayUnstated: 'delay not stated',
      liveAt: '{time}',
      closeOn: 'daily, {day}',
      source: 'Prices from {name}, not the exchanges’ own feed.',
      terms: 'Terms of use',
      closeSources:
        'Previous closes of Taiwan holdings also come from FinMind and the open data of the Taiwan Stock Exchange and the Taipei Exchange.',
      openDataLicense: 'Open Government Data License',
      updating: 'Updating',
      sourceDown: 'Not connected to the price source; prices stay as of their times',
      connecting: 'Connecting…',
      disconnected: 'Not updating',
      invalid:
        '{count} updates did not match the expected format and were not drawn; the numbers on the screen may be out of date. Reload the page to read them again.'
    }
  },
  markets: {
    TW: 'Taiwan',
    US: 'US',
    cash: 'Cash'
  },
  holdings: {
    title: 'Edit holdings',
    edit: 'Edit holdings',
    add: 'Add a holding',
    remove: 'Remove this holding',
    save: 'Save',
    cancel: 'Cancel',
    symbol: 'Symbol',
    name: 'Name',
    quantity: 'Quantity',
    cost: 'Average cost',
    cash: 'Cash (TWD)',
    note: 'Write symbols as Yahoo Finance does: Taiwan with .TW or .TWO, US as the ticker. A new holding’s target is 0%; a removed holding’s target goes with it. Saving closes a proposal you have not decided on.',
    targetsTotal:
      'The targets add up to {total}%, not 100%. Ask in the chat for a revised strategy; accepting it sets them again.',
    which: 'Holding {item}: {title}'
  },
  rules: {
    title: 'Your rules',
    summary: '{met} of {enabled} rules met',
    noneOn: 'No rule is on.',
    note: 'The rules are checked against the strategy’s target weights, not today’s values, so prices do not change the results. Cash is not counted as a holding.',
    met: 'Met',
    broken: 'Not met',
    off: 'Off',
    breaking: 'Breaking it: {names}',
    edit: 'Edit rules',
    add: 'Add a rule',
    remove: 'Remove this rule',
    save: 'Save',
    cancel: 'Cancel',
    kind: 'Kind',
    limit: 'Limit (%)',
    market: 'Market',
    enabled: 'On',
    proposalTitle: 'Your rules, before and after',
    before: 'Current',
    after: 'Proposed',
    max_holding_weight: {
      name: 'Most per holding',
      rule: 'Any one holding at most {limit}%',
      measured: 'Largest: {value}%'
    },
    min_holding_weight: {
      name: 'Least per held holding',
      rule: 'Any held holding at least {limit}%',
      measured: 'Smallest held: {value}%'
    },
    max_market_weight: {
      name: 'Most per market',
      rule: '{market} holdings at most {limit}% in all',
      measured: 'In all: {value}%'
    }
  }
};
