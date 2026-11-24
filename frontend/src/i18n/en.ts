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
    placeholder: 'Ask about the market news since June…',
    answerWith: 'Answer with',
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
  samples: {
    fed: 'Which of the Fed’s moves over the past half year shook the stock market?',
    aiSpending: 'Why are investors worried about Microsoft’s and other tech giants’ AI spending?',
    tsmc: 'Which recent events have affected TSMC and its supply chain?',
    recovery: 'Do any authoritative sources say the market will return to normal?'
  }
};
