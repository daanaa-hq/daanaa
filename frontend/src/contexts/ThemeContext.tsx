import { createContext, useContext, useState } from 'react'

// Light/dark theme toggle. The saved theme is applied to <html data-theme>
// by an inline script in index.html BEFORE React mounts (no flash of wrong
// theme); this context just keeps React state in sync and handles toggling.
// Light mode works by overriding the CSS custom properties in index.css
// ([data-theme="light"]) that the .bg-*/.text-* utility classes read.

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

function readInitialTheme(): Theme {
  if (typeof document !== 'undefined' &&
      document.documentElement.getAttribute('data-theme') === 'light') {
    return 'light'
  }
  return 'dark'
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(readInitialTheme)

  const toggleTheme = () => {
    const next: Theme = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    try {
      localStorage.setItem('daanaa-theme', next)
    } catch { /* private mode: toggle still works for this visit */ }
    if (next === 'light') {
      document.documentElement.setAttribute('data-theme', 'light')
    } else {
      document.documentElement.removeAttribute('data-theme')
    }
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
