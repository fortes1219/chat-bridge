import { useI18n } from 'vue-i18n';
import type { Locale, MessageSchema } from '@/i18n';
import type { PriceTime } from '@/service/api/strategy';
import { MISSING } from '../constants';

export interface StrategyFormat {
  /** Taiwan dollars, whole. */
  money(value: string | null): string;
  /** A price as the service rounded it, with its decimals kept. */
  price(value: string | null): string;
  /** A percent; with `signed`, a rise carries its plus sign. */
  percent(value: string | null, signed?: boolean): string;
  /**
   * When a price is from: a live price's time, or the trading day of a daily value, which is the
   * day's close once the day has ended and its latest price while it trades.
   */
  priceTime(at: PriceTime | null): string;
  /** The same, short enough for a table cell: month, day and time, or month and day. */
  priceTimeShort(at: PriceTime): string;
}

function decimals(value: string): number {
  return value.split('.')[1]?.length ?? 0;
}

/**
 * The strategy screen's numbers in the page's language. They are drawn as the service computed
 * them; nothing here computes a value. A missing value is drawn as missing, never as zero.
 */
export function useStrategyFormat(): StrategyFormat {
  const { t, locale } = useI18n<{ message: MessageSchema }, Locale>();

  function money(value: string | null): string {
    if (value === null) return MISSING;
    return new Intl.NumberFormat(locale.value, {
      style: 'currency',
      currency: 'TWD',
      maximumFractionDigits: 0
    }).format(Number(value));
  }

  function price(value: string | null): string {
    if (value === null) return MISSING;
    const digits = decimals(value);
    return new Intl.NumberFormat(locale.value, {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits
    }).format(Number(value));
  }

  function percent(value: string | null, signed = false): string {
    if (value === null) return MISSING;
    const sign = signed && Number(value) > 0 ? '+' : '';
    return `${sign}${value}%`;
  }

  function priceTime(at: PriceTime | null): string {
    if (at === null) return MISSING;
    if (at.basis === 'daily' || at.time === null) return t('strategy.quotes.closeOn', { day: at.day ?? MISSING });
    const time = new Intl.DateTimeFormat(locale.value, { dateStyle: 'short', timeStyle: 'medium' }).format(
      new Date(at.time)
    );
    return t('strategy.quotes.liveAt', { time });
  }

  function priceTimeShort(at: PriceTime): string {
    if (at.basis === 'daily' || at.time === null) {
      // 2026-11-21 becomes 11-21: the year is this year's in a list of latest prices.
      return t('strategy.quotes.closeOn', { day: (at.day ?? MISSING).slice(5) });
    }
    // A 24-hour clock: shorter than a 12-hour one with its 下午 or PM.
    return new Intl.DateTimeFormat(locale.value, {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hourCycle: 'h23'
    }).format(new Date(at.time));
  }

  return { money, price, percent, priceTime, priceTimeShort };
}
