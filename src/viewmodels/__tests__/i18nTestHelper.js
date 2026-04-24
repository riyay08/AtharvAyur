/**
 * A tiny fake `t` for ViewModel unit tests. Reads the canonical English
 * translations directly from `src/i18n/locales/en.json` and performs
 * minimal `{{var}}` interpolation, so we can assert against real copy
 * (e.g. /valid email/) without standing up the full i18next runtime.
 */
import en from "../../i18n/locales/en.json";

function lookup(key) {
  const parts = key.split(".");
  let node = en;
  for (const part of parts) {
    if (node && typeof node === "object" && part in node) node = node[part];
    else return key;
  }
  return typeof node === "string" ? node : key;
}

export function fakeT(key, vars = {}) {
  let out = lookup(key);
  for (const [k, v] of Object.entries(vars || {})) {
    out = out.replace(new RegExp(`\\{\\{\\s*${k}\\s*\\}\\}`, "g"), String(v));
  }
  return out;
}
