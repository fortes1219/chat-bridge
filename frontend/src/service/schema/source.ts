import { z } from 'zod';
import { LocalizedSchema } from '@/service/schema/common';

/**
 * A section an answer may use, numbered as the model sees it. A section may have no event date.
 * `heading_localizations` is set only for the section names the sample news is written with; any
 * other heading is the document's own words and is shown as written. The chat's context lists
 * them, and a proposal keeps the ones its reasons cite.
 */
export const SourceSchema = z
  .object({
    number: z.number().int().positive(),
    file: z.string(),
    title: z.string(),
    heading: z.string(),
    heading_localizations: LocalizedSchema.nullable(),
    event_date: z.iso.date().nullable()
  })
  .strict();
