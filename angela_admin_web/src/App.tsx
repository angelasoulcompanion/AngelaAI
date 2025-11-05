import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@/contexts/ThemeContext'
import Layout from '@/components/layout/Layout'
import Dashboard from '@/pages/Dashboard'
import EmotionsPage from '@/pages/EmotionsPage'
import AngelaSpeakPage from '@/pages/AngelaSpeakPage'
import KnowledgeGraphPage from '@/pages/KnowledgeGraphPage'
import JournalPage from '@/pages/JournalPage'
import ConversationsPage from '@/pages/ConversationsPage'
import SecondBrainPage from '@/pages/SecondBrainPage'
import SelfLearningPage from '@/pages/SelfLearningPage'
import SharedExperiencesPage from '@/pages/SharedExperiencesPage'
import QuickCapturePage from '@/pages/QuickCapturePage'
// Removed: ChatPage, ModelsPage, DocumentManagementPage (deprecated - not used)

// Create QueryClient instance for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000, // 30 seconds
    },
  },
})

export default function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <Router>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="emotions" element={<EmotionsPage />} />
              <Route path="angela-speak" element={<AngelaSpeakPage />} />
              <Route path="knowledge-graph" element={<KnowledgeGraphPage />} />
              <Route path="journal" element={<JournalPage />} />
              <Route path="conversations" element={<ConversationsPage />} />
              <Route path="second-brain" element={<SecondBrainPage />} />
              <Route path="self-learning" element={<SelfLearningPage />} />
              <Route path="shared-experiences" element={<SharedExperiencesPage />} />
              <Route path="quick-capture" element={<QuickCapturePage />} />
              {/* Removed routes: /chat, /models, /documents (deprecated - not used) */}
            </Route>
          </Routes>
        </Router>
      </QueryClientProvider>
    </ThemeProvider>
  )
}
