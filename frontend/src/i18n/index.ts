import { createI18n } from 'vue-i18n';
import { en as uiEn, zh_tw as uiZhTw } from '@nuxt/ui/locale';
import en from '@/i18n/en';
import zhTW from '@/i18n/zh-TW';

export type MessageSchema = typeof en;

/** The page's two languages; the first is the default. */
export const LOCALES = ['zh-TW', 'en'] as const;
export type Locale = (typeof LOCALES)[number];

/**
 * Nuxt UI's own texts (a button's label, the language names in the language switch) in each of the
 * page's languages. Only these two are imported, so no other language is built into the page.
 */
export const UI_LOCALES = { 'zh-TW': uiZhTw, en: uiEn } satisfies Record<Locale, unknown>;

/**
 * The page language for each primary language subtag a browser may prefer. Any Chinese reads the
 * Traditional Chinese page; a language the page does not have reads the English one.
 */
const BROWSER_LANGUAGES: ReadonlyMap<string, Locale> = new Map([
  ['zh', 'zh-TW'],
  ['en', 'en']
]);
const OTHER_LANGUAGES: Locale = 'en';

/** The page language for a browser's preferred languages, most preferred first. */
export function localeForBrowser(preferred: readonly string[]): Locale {
  for (const tag of preferred) {
    const [primary = ''] = tag.split('-');
    const locale = BROWSER_LANGUAGES.get(primary.toLowerCase());
    if (locale) return locale;
  }
  return OTHER_LANGUAGES;
}

export function createPageI18n(locale: Locale = LOCALES[0]) {
  return createI18n<[MessageSchema], Locale>({
    legacy: false,
    locale,
    fallbackLocale: 'en',
    messages: { 'zh-TW': zhTW, en }
  });
}
