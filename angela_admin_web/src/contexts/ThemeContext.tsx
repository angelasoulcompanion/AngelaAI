import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  // Initialize from localStorage or default to 'light'
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('theme')
    return (saved as Theme) || 'light'
  })

  useEffect(() => {
    // Update document class and localStorage when theme changes
    const root = document.documentElement

    console.log('🎨 Theme changed to:', theme)

    if (theme === 'dark') {
      root.classList.add('dark')
      console.log('✅ Added dark class to document')
    } else {
      root.classList.remove('dark')
      console.log('✅ Removed dark class from document')
    }

    localStorage.setItem('theme', theme)
    console.log('💾 Saved theme to localStorage:', theme)
  }, [theme])

  const toggleTheme = () => {
    console.log('🔄 Toggle theme clicked! Current theme:', theme)
    setTheme(prev => {
      const newTheme = prev === 'light' ? 'dark' : 'light'
      console.log('🔄 Switching from', prev, 'to', newTheme)
      return newTheme
    })
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
