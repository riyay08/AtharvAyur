/**
 * i18n bootstrap. Keeps everything client-side: ships both `en` and `hi`
 * resources in the bundle, persists the chosen language in localStorage
 * under `holistica_lang`, and falls back to English if a key is missing.
 */

import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import hi from "./locales/hi.json";

export const SUPPORTED_LANGS = /** @type {const} */ (["en", "hi"]);
export const LANG_STORAGE_KEY = "holistica_lang";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { en: { translation: en }, hi: { translation: hi } },
    fallbackLng: "en",
    supportedLngs: [...SUPPORTED_LANGS],
    nonExplicitSupportedLngs: true,
    detection: {
      order: ["localStorage", "navigator", "htmlTag"],
      lookupLocalStorage: LANG_STORAGE_KEY,
      caches: ["localStorage"],
    },
    interpolation: { escapeValue: false },
    returnNull: false,
  });

// Mirror the active language onto <html lang> so screen readers / browser
// translation features behave correctly. Runs only in the browser.
if (typeof document !== "undefined") {
  const apply = (lng) => {
    const code = (lng || "en").slice(0, 2);
    document.documentElement.setAttribute("lang", code);
  };
  apply(i18n.resolvedLanguage || i18n.language);
  i18n.on("languageChanged", apply);
}

export default i18n;
