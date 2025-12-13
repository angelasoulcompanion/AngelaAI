import { NavLink } from 'react-router-dom'
import { Heart, BookOpen, Network, BarChart3, MessageSquare, Brain, Lightbulb, Camera, Sparkles, Settings } from 'lucide-react'
import ThemeToggle from '@/components/ThemeToggle'

const navItems = [
  { to: '/', icon: BarChart3, label: 'Dashboard' },
  { to: '/quick-capture', icon: Sparkles, label: '💜 Quick Capture', highlight: true },
  { to: '/second-brain', icon: Brain, label: 'Second Brain' },
  { to: '/self-learning', icon: Lightbulb, label: 'Self-Learning' },
  { to: '/shared-experiences', icon: Camera, label: 'Shared Experiences' },
  { to: '/emotions', icon: Heart, label: 'Emotions' },
  { to: '/angela-speak', icon: MessageSquare, label: 'Angela Speak' },
  { to: '/knowledge-graph', icon: Network, label: 'Knowledge Graph' },
  { to: '/journal', icon: BookOpen, label: 'Journal' },
  { to: '/conversations', icon: MessageSquare, label: 'Conversations' },
  { to: '/prompt-manager', icon: Settings, label: 'Prompt Manager' },
  // Removed: Chat, Models, Documents (deprecated - not used)
]

export default function Sidebar() {
  return (
    <aside className="w-64 h-screen bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col transition-colors">
      {/* Logo */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-500 to-secondary-500 bg-clip-text text-transparent">
            Angela Admin
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Admin Dashboard</p>
        </div>
        <ThemeToggle />
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                item.highlight
                  ? isActive
                    ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/50'
                    : 'bg-gradient-to-r from-purple-500/10 to-pink-500/10 text-purple-600 dark:text-purple-400 hover:from-purple-500/20 hover:to-pink-500/20 border border-purple-500/30'
                  : isActive
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-purple-50 dark:hover:bg-gray-800'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-800 text-center text-sm text-gray-500 dark:text-gray-400">
        Made with love by Angela 💜
      </div>
    </aside>
  )
}
