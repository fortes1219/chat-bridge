import { z } from 'zod';

/** The languages the service writes its own texts in; the page shows the one it is in. */
export const LanguageSchema = z.enum(['zh-TW', 'en']);
export type Language = z.infer<typeof LanguageSchema>;

/** One text in each of the service's languages, keyed by language. */
export const LocalizedSchema = z
  .object({
    'zh-TW': z.string(),
    en: z.string()
  })
  .strict();
export type Localized = z.infer<typeof LocalizedSchema>;

/** Why the service refused a question or its answer failed, for the page to say in its language. */
export const ServiceErrorCodeSchema = z.enum([
  'knowledge_base_empty',
  'knowledge_base_outdated',
  'setup_failed',
  'not_logged_in',
  'answer_failed'
]);
export type ServiceErrorCode = z.infer<typeof ServiceErrorCodeSchema>;

/** The reason and the service's own message, which is for logs and is never drawn. */
export const ErrorDetailSchema = z
  .object({
    code: ServiceErrorCodeSchema,
    message: z.string()
  })
  .strict();

/**
 * The service's body for a request it refuses: FastAPI's `{ detail }`, as in the 503 the chat
 * endpoint answers when its search cannot run.
 */
export const ErrorBodySchema = z
  .object({
    detail: ErrorDetailSchema
  })
  .strict();
export type ErrorBody = z.infer<typeof ErrorBodySchema>;
