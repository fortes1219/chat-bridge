import { z } from 'zod';
import { LocalizedSchema } from '@/service/schema/common';

/**
 * `GET /chat/samples`: questions the page offers before the first one, each in both languages.
 * None when the knowledge base does not hold the documents they are about.
 */
export const SampleQuestionsSchema = z
  .object({
    questions: LocalizedSchema.array()
  })
  .strict();
