/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
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
        'deep-navy': '#0A1628',
        'dark-surface': '#111D2E',
        'navy-mid': '#1A2744',
        'warm-cream': '#F5F0EB',
        'soft-gold': '#C9A96E',
        'bright-gold': '#D4B87A',
        'pale-gold': '#E8D5A3',
        'muted-cream': '#A89F94',
        'cool-grey': '#374151',
        'light-cream': '#EDE8E0',
        'light-grey': '#E5E0DB',
        'deep-gold': '#8B7340',
        'success-green': '#4ADE80',
        'alert-amber': '#F59E0B',
        // New brand tokens
        'merit-navy':  '#0D1C36',
        'merit-gold':  '#C9A84C',
        'civic-teal':  '#1A4A4A',
        'teal-light':  '#2D7070',
        'merit-cream': '#FAF8F3',
        'charcoal':    '#1E2530',
        'slate':       '#4B5563',
        'soft-border': 'rgba(201,168,76,0.18)',
        // Tier colors
        'tier-beacon':  '#B8902F',
        'tier-lantern': '#C9A84C',
        'tier-flame':   '#D4B968',
        'tier-ember':   '#D9A876',
        'tier-spark':   '#E8C896',
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
