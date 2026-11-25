import { computed, toValue, type ComputedRef, type MaybeRefOrGetter } from 'vue';
import type { Source } from '@/service/api/chat';

/** Anything in square brackets; only brackets that hold source numbers alone are citations. */
const BRACKETS = /\[([^\]\n]+)\]/g;
/**
 * A citation as the answer rules ask for it: `[3]`, or several numbers in one, `[3, 5]`. A date
 * in brackets, `[2026-11-05]`, or a Markdown link's text holds more than numbers and is not one.
 */
const CITATION = /^\s*\d+(?:\s*[,，、]\s*\d+)*\s*$/;
const NUMBER = /\d+/g;

/**
 * The sources the answer cites, in number order, read from the answer's own marks: what the
 * answer rests on, so the list under it stays short however many sources the model was given.
 * A number that names no source is ignored.
 */
export function useCitedSources(
  answer: MaybeRefOrGetter<string>,
  sources: MaybeRefOrGetter<Source[]>
): ComputedRef<Source[]> {
  return computed(() => {
    const cited = new Set<number>();
    for (const [, inside = ''] of toValue(answer).matchAll(BRACKETS)) {
      if (!CITATION.test(inside)) continue;
      for (const [number] of inside.matchAll(NUMBER)) cited.add(Number(number));
    }
    return toValue(sources).filter(source => cited.has(source.number));
  });
}
