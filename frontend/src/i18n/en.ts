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
  chat: {
    placeholder: 'Ask about the market news since June…',
    answerWith: 'Answer with',
    samplesTitle: 'Try one of these',
    sources: 'Sources',
    noDate: 'No date',
    latestDate: 'The sources reach {date}.',
    noLatestDate: 'None of the sources has a date.',
    stopped: 'Stopped.',
    failed: 'The answer stopped with an error.',
    notAnswered: 'This question could not be answered.',
    unreachable: 'The chat service cannot be reached.',
    emptyQuestion: 'Type a question first.',
    longQuestion: 'A question can be at most {limit} characters.'
  },
  samples: {
    fed: 'Which of the Fed’s moves over the past half year shook the stock market?',
    aiSpending: 'Why are investors worried about Microsoft’s and other tech giants’ AI spending?',
    tsmc: 'Which recent events have affected TSMC and its supply chain?',
    recovery: 'Do any authoritative sources say the market will return to normal?'
  }
};
