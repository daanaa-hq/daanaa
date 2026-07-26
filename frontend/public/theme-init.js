/* Theme initialisation — must run before first paint.
 *
 * Dark is the default. Light is opt-in and applied by setting
 * `data-theme="light"` on <html>, which activates the [data-theme="light"]
 * blocks in index.css and suppresses Tailwind's dark: variants (see the
 * darkMode selector in tailwind.config.js).
 *
 * This lives in an external file rather than inline in index.html for one
 * reason: production sends `script-src 'self'` with no 'unsafe-inline' and no
 * hash, so the previous inline version was silently blocked by CSP on
 * daanaa.org. Light mode therefore never survived a page load in production
 * (it worked locally only because vite preview sends no CSP).
 *
 * An external same-origin file is already permitted by `'self'`, so this needs
 * no CSP change and no hash to keep in sync. A hashed inline script would work
 * too, but the hash goes stale the moment anyone edits the script, and the
 * failure mode is silent: exactly the bug this replaces.
 *
 * Loaded synchronously from <head> so the attribute is set before the body
 * renders. No flash of the wrong theme.
 */
(function () {
  try {
    if (localStorage.getItem('daanaa-theme') === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    }
  } catch (e) {
    /* private mode or storage blocked: fall through to the dark default */
  }
})();
