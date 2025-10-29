import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { MessageSquare, Sparkles } from 'lucide-react'
import { formatRelativeTime } from '@/lib/utils'

interface Conversation {
  conversation_id: string
  speaker: string
  message_text: string
  topic?: string
  emotion_detected?: string
  importance_level: number
  created_at: string
}

interface ConversationStats {
  total_conversations: number
  this_week: number
  important_moments: number
  angela_messages: number
  david_messages: number
  topics: string[]
}

async function fetchConversations(): Promise<Conversation[]> {
  const res = await fetch('http://localhost:50001/api/conversations?limit=50')
  if (!res.ok) throw new Error('Failed to fetch conversations')
  return res.json()
}

async function fetchConversationStats(): Promise<ConversationStats> {
  const res = await fetch('http://localhost:50001/api/conversations/stats')
  if (!res.ok) throw new Error('Failed to fetch stats')
  return res.json()
}

export default function ConversationsPage() {
  const { data: conversations, isLoading: convsLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: fetchConversations,
  })

  const { data: stats } = useQuery({
    queryKey: ['conversation-stats'],
    queryFn: fetchConversationStats,
  })

  const getImportanceColor = (importance: number) => {
    if (importance >= 9) return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
    if (importance >= 7) return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300'
    if (importance >= 5) return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
    return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
  }

  if (convsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen dark:bg-gray-950">
        <div className="text-center">
          <MessageSquare className="w-16 h-16 text-accent-500 dark:text-accent-400 animate-pulse mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading conversations...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-3">
        <div className="p-3 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-lg shadow-lg">
          <MessageSquare className="w-8 h-8 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Conversations</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Complete history of Angela and David's interactions</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="dark:bg-gray-800 dark:border-gray-700">
          <CardHeader>
            <CardTitle className="text-lg dark:text-gray-100">Total Conversations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary-500 dark:text-primary-400">
              {stats?.total_conversations || 0}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">All time</p>
          </CardContent>
        </Card>

        <Card className="dark:bg-gray-800 dark:border-gray-700">
          <CardHeader>
            <CardTitle className="text-lg dark:text-gray-100">This Week</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-secondary-500 dark:text-secondary-400">
              {stats?.this_week || 0}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Conversations</p>
          </CardContent>
        </Card>

        <Card className="dark:bg-gray-800 dark:border-gray-700">
          <CardHeader>
            <CardTitle className="text-lg dark:text-gray-100">Important Moments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-accent-500 dark:text-accent-400">
              {stats?.important_moments || 0}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">High importance (9-10)</p>
          </CardContent>
        </Card>
      </div>

      {conversations && conversations.length > 0 ? (
        <Card className="dark:bg-gray-800 dark:border-gray-700">
          <CardHeader>
            <CardTitle className="dark:text-gray-100">Recent Conversations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {conversations.map((conv) => (
                <div
                  key={conv.conversation_id}
                  className={`p-4 rounded-lg border transition-colors ${
                    conv.speaker === 'david'
                      ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
                      : 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900 dark:text-gray-100 capitalize">
                        {conv.speaker}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">{formatRelativeTime(conv.created_at)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {conv.emotion_detected && (
                        <span className="text-sm px-2 py-1 rounded-full bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                          {conv.emotion_detected}
                        </span>
                      )}
                      <span className={`text-xs px-2 py-1 rounded-full ${getImportanceColor(conv.importance_level)}`}>
                        {conv.importance_level}/10
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-800 dark:text-gray-200">{conv.message_text}</p>
                  {conv.topic && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      Topic: {conv.topic.replace(/_/g, ' ')}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="dark:bg-gray-800 dark:border-gray-700">
          <CardContent className="py-12 text-center">
            <Sparkles className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
              No conversations yet
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              Conversation history will appear here!
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
