import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import en from './locales/en';
import zh from './locales/zh';

const STORAGE_KEY = 'nightlio_locale';

const dictionaries = { en, zh };

const I18nContext = createContext(null);

function detectLocale() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && dictionaries[saved]) return saved;
  } catch {
    /* ignore */
  }
  if (typeof navigator !== 'undefined') {
    const lang = (navigator.language || navigator.userLanguage || '').toLowerCase();
    if (lang.startsWith('zh')) return 'zh';
  }
  return 'en';
}

function getByPath(obj, path) {
  if (!obj || !path) return undefined;
  const parts = path.split('.');
  let cur = obj;
  for (const p of parts) {
    if (cur == null || typeof cur !== 'object') return undefined;
    cur = cur[p];
  }
  return cur;
}

function interpolate(template, vars = {}) {
  if (typeof template !== 'string') return template;
  return template.replace(/\{(\w+)\}/g, (_, key) => {
    if (vars[key] === undefined || vars[key] === null) return `{${key}}`;
    return String(vars[key]);
  });
}

export function I18nProvider({ children }) {
  const [locale, setLocaleState] = useState(detectLocale);

  const setLocale = useCallback((next) => {
    if (!dictionaries[next]) return;
    setLocaleState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = locale === 'zh' ? 'zh-CN' : 'en';
    }
  }, [locale]);

  const t = useCallback(
    (key, vars) => {
      const primary = getByPath(dictionaries[locale], key);
      const fallback = getByPath(dictionaries.en, key);
      const value = primary !== undefined ? primary : fallback;
      if (value === undefined) return key;
      return interpolate(value, vars);
    },
    [locale]
  );

  const value = useMemo(
    () => ({
      locale,
      setLocale,
      t,
      locales: [
        { code: 'zh', labelKey: 'common.chinese' },
        { code: 'en', labelKey: 'common.english' },
      ],
    }),
    [locale, setLocale, t]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return ctx;
}

export function useT() {
  return useI18n().t;
}

/** Mood value 1–5 → i18n key under mood.* */
export const MOOD_LABEL_KEYS = {
  1: 'mood.terrible',
  2: 'mood.bad',
  3: 'mood.okay',
  4: 'mood.good',
  5: 'mood.amazing',
};

export default I18nContext;
