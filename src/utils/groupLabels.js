/**
 * Localize default seed group/option names from the API.
 * Custom user-created names fall back to the raw DB string.
 */

export function localizeGroupName(name, t) {
  if (!name) return name;
  const key = `groups.names.${name}`;
  const translated = t(key);
  // t() returns the key path when missing — treat that as "no translation"
  if (!translated || translated === key) return name;
  return translated;
}

export function localizeOptionName(name, t) {
  if (!name) return name;
  const key = `groups.options.${name}`;
  const translated = t(key);
  if (!translated || translated === key) return name;
  return translated;
}
