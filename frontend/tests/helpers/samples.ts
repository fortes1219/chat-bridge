import { vi } from 'vitest';
import type { SampleQuestion } from '@/service/api/samples';

/** The sample questions the service offers while the sample news is stored. */
export const SAMPLE_QUESTIONS: SampleQuestion[] = [
  {
    'zh-TW': '聯準會在這近半年的動向哪些行為導致股市動盪？',
    en: 'Which of the Fed’s moves over the past half year shook the stock market?'
  },
  {
    'zh-TW': '台積電與供應鏈最近受到哪些事件影響？',
    en: 'Which recent events have affected TSMC and its supply chain?'
  }
];

/**
 * The stand-in for `getSampleQuestions` in every test (tests/setup.ts): the sample questions,
 * unless a test makes it answer otherwise.
 */
export const getSampleQuestionsMock = vi.fn<() => Promise<SampleQuestion[]>>();
