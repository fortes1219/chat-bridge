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
    latestDate: 'The sources reach {date}.',
    noLatestDate: 'None of the sources has a date.',
    stopped: 'Stopped.',
    searching: 'Searching the news…',
    waiting: 'Waiting for {program} to answer…',
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
    }
  },
  samples: {
    fed: 'Which of the Fed’s moves over the past half year shook the stock market?',
    aiSpending: 'Why are investors worried about Microsoft’s and other tech giants’ AI spending?',
    tsmc: 'Which recent events have affected TSMC and its supply chain?',
    recovery: 'Do any authoritative sources say the market will return to normal?'
  }
};
