import { computed, watch, type ComputedRef } from 'vue';
import { useRoute, useRouter, type LocationQuery } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { usePreferredLanguages } from '@vueuse/core';
import { LOCALES, localeForBrowser, type Locale } from '@/i18n';
import type { Program, ProgramState } from '@/service/api/programs';
import { PROGRAM_ORDER } from '../constants';

/** The address query keys; the page keeps no other state in the address. */
const LANGUAGE_KEY = 'lang';
const PROGRAM_KEY = 'program';

export interface UseAddressState {
  language: ComputedRef<Locale>;
  /** Programs logged in, in the service's order. */
  loggedIn: ComputedRef<Program[]>;
  /** The program that answers: the one the address names when it is logged in, else the first logged in. */
  program: ComputedRef<Program | null>;
  chooseLanguage(language: Locale): void;
  chooseProgram(program: Program): void;
}

function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && (LOCALES as readonly string[]).includes(value);
}

/**
 * The language and the answering program, kept in the address so a reload or a shared link opens
 * the same view. A user's choice is a `push`; correcting the address to a valid value is a
 * `replace`, made only once the login states are known, and never when it already matches.
 */
export function useAddressState(states: ComputedRef<ProgramState[]>): UseAddressState {
  const route = useRoute();
  const router = useRouter();
  const { locale } = useI18n({ useScope: 'global' });

  const browserLanguages = usePreferredLanguages();

  // The address decides: a language chosen on the page or in a shared link. A first visit, with
  // none in the address, takes the browser's preferred language; it is then written to the address.
  const language = computed<Locale>(() => {
    const raw = route.query[LANGUAGE_KEY];
    return isLocale(raw) ? raw : localeForBrowser(browserLanguages.value);
  });

  const loggedIn = computed<Program[]>(() =>
    PROGRAM_ORDER.filter(program =>
      states.value.some(state => state.program === program && state.state === 'logged in')
    )
  );

  const program = computed<Program | null>(() => {
    const raw = route.query[PROGRAM_KEY];
    return loggedIn.value.find(candidate => candidate === raw) ?? loggedIn.value[0] ?? null;
  });

  // The document's language follows the page's, so the browser and a screen reader read an
  // English page as English.
  watch(
    language,
    value => {
      locale.value = value;
      document.documentElement.lang = value;
    },
    { immediate: true }
  );

  watch(
    [language, program],
    () => {
      const wanted: LocationQuery = { ...route.query, [LANGUAGE_KEY]: language.value };
      if (program.value !== null) wanted[PROGRAM_KEY] = program.value;
      const same = [LANGUAGE_KEY, PROGRAM_KEY].every(key => route.query[key] === wanted[key]);
      if (same) return;
      void router.replace({ query: wanted });
    },
    { immediate: true }
  );

  function choose(key: string, value: string): void {
    if (route.query[key] === value) return;
    void router.push({ query: { ...route.query, [key]: value } });
  }

  return {
    language,
    loggedIn,
    program,
    chooseLanguage: value => choose(LANGUAGE_KEY, value),
    chooseProgram: value => choose(PROGRAM_KEY, value)
  };
}
