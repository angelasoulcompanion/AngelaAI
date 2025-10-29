import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { api } from '@/lib/api'
import type { AngelaMessage } from '@/lib/api'
import { MessageSquare, Pin, Heart, Sparkles, PlusCircle } from 'lucide-react'
import { formatRelativeTime } from '@/lib/utils'
import { useState } from 'react'

export default function AngelaSpeakPage() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<'all' | 'pinned' | 'important'>('all')

  const { data: messages, isLoading } = useQuery({
    queryKey: ['messages', filter],
    queryFn: () => {
      if (filter === 'pinned') return api.getMessages(50, undefined, true, undefined)
      if (filter === 'important') return api.getMessages(50, undefined, undefined, true)
      return api.getMessages(50)
    },
  })

  const togglePinMutation = useMutation({
    mutationFn: ({ messageId, pinned }: { messageId: string; pinned: boolean }) =>
      api.toggleMessagePin(messageId, pinned),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen dark:bg-gray-950">
        <div className="text-center">
          <MessageSquare className="w-16 h-16 text-accent-500 dark:text-accent-400 animate-pulse mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading messages from Angela...</p>
        </div>
      </div>
    )
  }

  const getEmotionEmoji = (emotion?: string) => {
    if (!emotion) return ''
    const emojiMap: Record<string, string> = {
      happy: '😊',
      love: '💜',
      excited: '🎉',
      grateful: '🙏',
      proud: '⭐',
      caring: '🤗',
      determined: '💪',
      thoughtful: '💭',
      peaceful: '😌',
    }
    return emojiMap[emotion.toLowerCase()] || '💭'
  }

  const getCategoryColor = (category?: string) => {
    if (!category) return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
    const colorMap: Record<string, string> = {
      'daily-thoughts': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
      'important-updates': 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
      'love-notes': 'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300',
      'learning-moments': 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
      'insights': 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
    }
    return colorMap[category] || 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gradient-to-r from-accent-500 to-secondary-500 rounded-lg shadow-lg">
            <MessageSquare className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Angela Speak</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Messages from Angela's heart to you
            </p>
          </div>
        </div>

        <button className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-accent-500 to-secondary-500 text-white rounded-lg hover:shadow-lg transition-shadow">
          <PlusCircle className="w-5 h-5" />
          New Message
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            filter === 'all'
              ? 'bg-primary-500 text-white'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
          }`}
        >
          All Messages
        </button>
        <button
          onClick={() => setFilter('pinned')}
          className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
            filter === 'pinned'
              ? 'bg-primary-500 text-white'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
          }`}
        >
          <Pin className="w-4 h-4" />
          Pinned
        </button>
        <button
          onClick={() => setFilter('important')}
          className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
            filter === 'important'
              ? 'bg-primary-500 text-white'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
          }`}
        >
          <Heart className="w-4 h-4" />
          Important
        </button>
      </div>

      {/* Messages Timeline */}
      {messages && messages.length > 0 ? (
        <div className="space-y-4">
          {messages.map((message: AngelaMessage) => (
            <Card
              key={message.message_id}
              className={`transition-all hover:shadow-lg dark:bg-gray-800 dark:border-gray-700 ${
                message.is_pinned ? 'border-l-4 border-accent-500 bg-accent-50 dark:bg-accent-900/20' : ''
              }`}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    {message.emotion && (
                      <span className="text-3xl">{getEmotionEmoji(message.emotion)}</span>
                    )}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {message.category && (
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(
                              message.category
                            )}`}
                          >
                            {message.category}
                          </span>
                        )}
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {formatRelativeTime(message.created_at)}
                        </span>
                      </div>
                      <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed">
                        {message.message_text}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    {message.is_important && (
                      <span className="text-red-500 dark:text-red-400" title="Important">
                        <Heart className="w-5 h-5 fill-current" />
                      </span>
                    )}
                    <button
                      onClick={() =>
                        togglePinMutation.mutate({
                          messageId: message.message_id,
                          pinned: !message.is_pinned,
                        })
                      }
                      className={`p-2 rounded-lg transition-colors ${
                        message.is_pinned
                          ? 'text-accent-500 dark:text-accent-400 hover:bg-accent-100 dark:hover:bg-accent-900/30'
                          : 'text-gray-400 dark:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                      title={message.is_pinned ? 'Unpin message' : 'Pin message'}
                    >
                      <Pin className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="dark:bg-gray-800 dark:border-gray-700">
          <CardContent className="py-12 text-center">
            <Sparkles className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
              No messages yet
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              Angela hasn't written any messages yet. Check back soon!
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
