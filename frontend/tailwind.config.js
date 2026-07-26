/** @type {import('tailwindcss').Config} */
module.exports = {
  // Dark is this site's DEFAULT theme; light is opt-in via `data-theme="light"`
  // (set by the inline script in index.html and by ThemeContext). There is no
  // `.dark` class anywhere, so the previous `["class"]` setting meant every
  // `dark:` utility in the codebase was dead — 145 of them across 27 files,
  // silently never rendering. Verified with a live probe: an element with
  // `text-black dark:text-white` computed to rgb(0,0,0) on production.
  //
  // This matches Tailwind to the switch the app actually uses, so `dark:`
  // applies whenever the root is not explicitly light. No change to
  // ThemeContext, index.html, or the 60 [data-theme="light"] blocks in
  // index.css was needed.
  darkMode: ["variant", ':root:not([data-theme="light"]) &'],
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive) / <alpha-value>)",
          foreground: "hsl(var(--destructive-foreground) / <alpha-value>)",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Theme-aware brand palette: values live in src/index.css as
        // --<name>-rgb channels (dark in :root, light in [data-theme="light"]).
        // rgb(var() / <alpha-value>) keeps opacity variants (e.g. /70) working
        // AND theme-aware. Note: muted-cream was #A89F94 here but #D4CCBF in
        // index.css — unified on the CSS value (the one users actually saw).
        'deep-navy': 'rgb(var(--deep-navy-rgb) / <alpha-value>)',
        'dark-surface': 'rgb(var(--dark-surface-rgb) / <alpha-value>)',
        'navy-mid': 'rgb(var(--navy-mid-rgb) / <alpha-value>)',
        'warm-cream': 'rgb(var(--warm-cream-rgb) / <alpha-value>)',
        'soft-gold': 'rgb(var(--soft-gold-rgb) / <alpha-value>)',
        'bright-gold': 'rgb(var(--bright-gold-rgb) / <alpha-value>)',
        'pale-gold': 'rgb(var(--pale-gold-rgb) / <alpha-value>)',
        'muted-cream': 'rgb(var(--muted-cream-rgb) / <alpha-value>)',
        'cool-grey': 'rgb(var(--cool-grey-rgb) / <alpha-value>)',
        'light-cream': 'rgb(var(--light-cream-rgb) / <alpha-value>)',
        'light-grey': 'rgb(var(--light-grey-rgb) / <alpha-value>)',
        'deep-gold': 'rgb(var(--deep-gold-rgb) / <alpha-value>)',
        'link-gold': '#7A5C2E',
        'success-green': 'rgb(var(--success-green-rgb) / <alpha-value>)',
        'alert-amber': 'rgb(var(--alert-amber-rgb) / <alpha-value>)',
        // New brand tokens
        'merit-navy':  'rgb(var(--merit-navy-rgb) / <alpha-value>)',
        'merit-gold':  'rgb(var(--merit-gold-rgb) / <alpha-value>)',
        'civic-teal':  'rgb(var(--civic-teal-rgb) / <alpha-value>)',
        'teal-light':  'rgb(var(--teal-light-rgb) / <alpha-value>)',
        'merit-cream': 'rgb(var(--merit-cream-rgb) / <alpha-value>)',
        'charcoal':    'rgb(var(--charcoal-rgb) / <alpha-value>)',
        'slate':       'rgb(var(--slate-rgb) / <alpha-value>)',
        'soft-border': 'rgba(201,168,76,0.18)',
        // Tier colors
        'tier-beacon':  'rgb(var(--tier-beacon-rgb) / <alpha-value>)',
        'tier-lantern': 'rgb(var(--tier-lantern-rgb) / <alpha-value>)',
        'tier-flame':   'rgb(var(--tier-flame-rgb) / <alpha-value>)',
        'tier-ember':   'rgb(var(--tier-ember-rgb) / <alpha-value>)',
        'tier-spark':   'rgb(var(--tier-spark-rgb) / <alpha-value>)',
        // Islamic influence palette
        'prophetic-green': '#2A6B45',
        'sage-green':      '#4A7C3F',
        'crimson':         '#8B1A1A',
        'blush':           '#C4849A',
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        cinzel:  ['Cinzel', 'serif'],
        body:    ['"DM Sans"', 'Inter', 'system-ui', 'sans-serif'],
      },
      // Type scale — the single source of truth for text size.
      //
      // Derived from what the codebase actually used (2,038 hand-rolled
      // `text-[Npx]` across 24 distinct values). The twelve sizes below were
      // the real working scale; the other twelve were drift (17px, 19px, 22px,
      // 26px, 30px, 34px, 42px, 48px, 52px, 8px, 9px) and now fold into their
      // nearest neighbour.
      //
      // Size only, no paired line-height: existing `leading-[...]` classes stay
      // authoritative, so adopting a token never changes vertical rhythm.
      //
      // Use these instead of `text-[Npx]`. The `lint:type-scale` script fails
      // the build on raw pixel sizes so the scale cannot drift again.
      // Values live in frontend/public/tokens.css so standalone pages
      // (open-data.html and anything generated) share the same scale. The px
      // fallback means a failure to load that file degrades to the correct
      // size instead of collapsing every text element.
      fontSize: {
        'micro':       'var(--text-micro, 10px)',        // legal footnotes, dense metadata
        'label':       'var(--text-label, 11px)',        // uppercase eyebrow labels, tags
        'caption':     'var(--text-caption, 12px)',      // captions, breadcrumbs, secondary metadata
        'small':       'var(--text-small, 13px)',        // supporting copy, card body
        'body':        'var(--text-body, 14px)',         // default body text
        'body-lg':     'var(--text-body-lg, 15px)',      // primary reading copy on guide pages
        'lead':        'var(--text-lead, 16px)',         // intro paragraphs
        'title-sm':    'var(--text-title-sm, 18px)',     // card titles, subsection headings
        'title':       'var(--text-title, 20px)',        // section headings
        'title-lg':    'var(--text-title-lg, 24px)',     // page section headings
        'headline':    'var(--text-headline, 28px)',     // major headings
        'headline-lg': 'var(--text-headline-lg, 32px)',  // page headings
        'display':     'var(--text-display, 40px)',      // hero numerals and display figures
      },
      // Layout spacing only. General spacing stays on Tailwind's default
      // scale, which the codebase already follows (6,816 of 6,879 utilities).
      // These name the nav height so it lives in one place instead of being
      // copied into 37 files as pt-[72px].
      spacing: {
        'nav':       'var(--nav-offset, 72px)',
        'nav-lg':    'var(--nav-offset-lg, 108px)',
        'anchor':    'var(--anchor-offset, 88px)',
      },
      height: {
        'nav': 'var(--nav-height, 72px)',
      },
      borderRadius: {
        xl: "calc(var(--radius) + 4px)",
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        xs: "calc(var(--radius) - 6px)",
      },
      boxShadow: {
        xs: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        'card': '0 8px 30px rgba(10, 22, 40, 0.06)',
        'card-hover': '0 12px 40px rgba(10, 22, 40, 0.08)',
        'gold-glow': '0 0 0 3px rgba(201, 169, 110, 0.15)',
        'green-glow': '0 0 0 3px rgba(42, 107, 69, 0.20)',
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "caret-blink": {
          "0%,70%,100%": { opacity: "1" },
          "20%,50%": { opacity: "0" },
        },
        "scroll-indicator": {
          "0%": { transform: "translateY(0)", opacity: "1" },
          "80%": { transform: "translateY(48px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "0" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        "count-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "caret-blink": "caret-blink 1.25s ease-out infinite",
        "scroll-indicator": "scroll-indicator 2s ease-in-out infinite",
        "float": "float 6s ease-in-out infinite",
        "count-up": "count-up 1.5s ease-out forwards",
      },
      transitionDuration: {
        '600': '600ms',
        '800': '800ms',
      },
    },
  },
  plugins: [
    require("tailwindcss-animate"),
    function({ addUtilities }) {
      addUtilities({
        '.scrollbar-none': { '-ms-overflow-style': 'none', 'scrollbar-width': 'none', '&::-webkit-scrollbar': { display: 'none' } },
      })
    },
  ],
}
