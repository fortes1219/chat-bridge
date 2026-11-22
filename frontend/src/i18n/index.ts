import { createI18n } from 'vue-i18n';
import en from '@/i18n/en';
import zhTW from '@/i18n/zh-TW';

export type MessageSchema = typeof en;

/** The page's two languages; the first is the default. */
export const LOCALES = ['zh-TW', 'en'] as const;
export type Locale = (typeof LOCALES)[number];

export function createPageI18n(locale: Locale = LOCALES[0]) {
  return createI18n<[MessageSchema], Locale>({
    legacy: false,
    locale,
    fallbackLocale: 'en',
    messages: { 'zh-TW': zhTW, en }
  });
}
