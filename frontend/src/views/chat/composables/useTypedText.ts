import { computed, ref, watch, type ComputedRef, type Ref } from 'vue';
import { usePreferredReducedMotion, useRafFn } from '@vueuse/core';

/**
 * The typing pace: a character waits at most MAX_CHAR_INTERVAL_MS, and less the more text is
 * waiting, so whatever has arrived is on screen within about DRAIN_MS. A whole answer that
 * arrives at once is typed, not dropped in, and the screen never falls far behind what has
 * arrived.
 */
const DRAIN_MS = 250;
const MAX_CHAR_INTERVAL_MS = 5;

export interface TypedTextSources {
  /** The text received so far. It only grows. */
  text(): string;
  /** Whether more text may still arrive. */
  arriving(): boolean;
  /** Whether the answer ended early, stopped or failed: what has arrived is then shown at once. */
  cutShort(): boolean;
}

export interface TypedText {
  /** The part of the text on screen. */
  shown: Ref<string>;
  /** Whether more is still to be typed or to arrive; the caret shows while it is. */
  typing: ComputedRef<boolean>;
}

/**
 * Types a streamed text onto the screen at a steady pace, whatever the size of the pieces it
 * arrives in. A text that had finished before it was drawn, a stopped or failed answer, and a
 * reader who asked the system for reduced motion all get the whole text at once.
 *
 * The pace is counted from the time since the last frame, so a tab that was in the background,
 * where the browser runs no frames, shows everything that arrived meanwhile when it comes back.
 */
export function useTypedText({ text, arriving, cutShort }: TypedTextSources): TypedText {
  const reducedMotion = usePreferredReducedMotion();
  const shown = ref(arriving() ? '' : text());
  // Frame time not yet spent on a character, carried to the next frame so the pace stays even.
  let banked = 0;

  const { pause, resume } = useRafFn(
    ({ delta }) => {
      const full = text();
      const remaining = full.length - shown.value.length;
      if (remaining <= 0) {
        banked = 0;
        pause();
        return;
      }
      const perCharacter = Math.min(MAX_CHAR_INTERVAL_MS, DRAIN_MS / remaining);
      banked += delta;
      const count = Math.min(remaining, Math.floor(banked / perCharacter));
      if (count === 0) return;
      banked -= count * perCharacter;
      shown.value = full.slice(0, shown.value.length + count);
    },
    { immediate: false }
  );

  watch(
    [text, cutShort, reducedMotion],
    ([full, isCutShort, motion]) => {
      if (isCutShort || motion === 'reduce') {
        shown.value = full;
        pause();
        return;
      }
      if (shown.value.length < full.length) resume();
    },
    { immediate: true }
  );

  const typing = computed(() => arriving() || shown.value.length < text().length);

  return { shown, typing };
}
