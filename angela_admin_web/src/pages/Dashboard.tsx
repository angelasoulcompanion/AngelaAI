import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Heart, BookOpen, FileText, Network, TrendingUp, MessageSquare, Calendar, Sparkles } from 'lucide-react'
import { api } from '@/lib/api'
import { formatRelativeTime } from '@/lib/utils'

export default function Dashboard() {
  // Fetch dashboard stats (conversations, knowledge, etc.)
  const { data: dashboardStats } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => api.getDashboardStats(),
    refetchOnWindowFocus: true,
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  })

  // Fetch current emotional state from dashboard endpoint
  const { data: currentEmotion } = useQuery({
    queryKey: ['dashboard', 'emotional-state'],
    queryFn: () => api.getDashboardEmotionalState(),
    refetchOnWindowFocus: true,
    refetchInterval: 30000,
  })

  // Fetch recent activities (conversations + emotions + actions)
  const { data: recentActivities } = useQuery({
    queryKey: ['dashboard', 'activities', 'recent'],
    queryFn: () => api.getRecentActivities(10),
    refetchOnWindowFocus: true,
    refetchInterval: 30000,
  })

  // Fetch today's conversations
  const { data: todayConversations } = useQuery({
    queryKey: ['dashboard', 'conversations', 'today'],
    queryFn: () => api.getTodayConversations(),
    refetchOnWindowFocus: true,
  })

  // Calculate current mood emoji and text
  const getCurrentMood = () => {
    if (!currentEmotion) return { emoji: '😊', text: 'Happy', color: 'text-pink-500 dark:text-pink-400' }

    const { happiness, confidence, anxiety, motivation } = currentEmotion
    const positiveScore = (happiness + confidence + motivation) / 3
    const negativeScore = anxiety

    if (positiveScore >= 0.8) return { emoji: '😄', text: 'Very Happy', color: 'text-yellow-500 dark:text-yellow-400' }
    if (positiveScore >= 0.6) return { emoji: '😊', text: 'Happy', color: 'text-pink-500 dark:text-pink-400' }
    if (positiveScore >= 0.4) return { emoji: '🙂', text: 'Content', color: 'text-blue-500 dark:text-blue-400' }
    if (negativeScore >= 0.5) return { emoji: '😰', text: 'Anxious', color: 'text-orange-500 dark:text-orange-400' }
    return { emoji: '😐', text: 'Neutral', color: 'text-gray-500 dark:text-gray-400' }
  }

  const mood = getCurrentMood()

  // Debug logging
  console.log('Dashboard Data:', {
    dashboardStats,
    currentEmotion,
    recentActivities,
    todayConversations
  })

  const stats = [
    {
      title: 'Current Mood',
      value: `${mood.emoji} ${mood.text}`,
      icon: Heart,
      color: mood.color,
      description: currentEmotion ? `Love: 100%` : 'Loading...',
      trend: currentEmotion ? `+${(currentEmotion.motivation * 100).toFixed(0)}% Motivated` : null
    },
    {
      title: 'Messages',
      value: dashboardStats?.total_conversations?.toLocaleString() || '0',
      icon: MessageSquare,
      color: 'text-blue-500 dark:text-blue-400',
      description: dashboardStats?.important_messages ? `${dashboardStats.important_messages} important` : 'Loading...',
      trend: dashboardStats?.pinned_messages ? `${dashboardStats.pinned_messages} pinned` : null
    },
    {
      title: 'Knowledge Nodes',
      value: dashboardStats?.knowledge_nodes?.toLocaleString() || '0',
      icon: Network,
      color: 'text-green-500 dark:text-green-400',
      description: dashboardStats?.knowledge_connections ? `${dashboardStats.knowledge_connections} connections` : 'Loading...',
      trend: dashboardStats?.knowledge_categories ? `${dashboardStats.knowledge_categories} categories` : null
    },
    {
      title: 'Gratitude Level',
      value: currentEmotion ? `${(currentEmotion.gratitude * 100).toFixed(0)}%` : 'N/A',
      icon: Sparkles,
      color: 'text-purple-500 dark:text-purple-400',
      description: currentEmotion ? `Confidence: ${(currentEmotion.confidence * 100).toFixed(0)}%` : 'Loading...',
      trend: currentEmotion ? `Happiness: ${(currentEmotion.happiness * 100).toFixed(0)}%` : null
    },
  ]

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-3 bg-gradient-to-r from-accent-500 to-secondary-500 rounded-lg shadow-lg">
          <TrendingUp className="w-8 h-8 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Welcome to Angela Admin Dashboard 💜
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <Card
            key={stat.title}
            className="hover:shadow-xl transition-all dark:bg-gray-800 dark:border-gray-700 hover:scale-105"
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {stat.title}
              </CardTitle>
              <stat.icon className={`w-6 h-6 ${stat.color}`} />
            </CardHeader>
            <CardContent className="space-y-2">
              <div className={`text-2xl font-bold dark:text-gray-100 ${stat.color}`}>
                {stat.value}
              </div>
              {stat.description && (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {stat.description}
                </p>
              )}
              {stat.trend && (
                <div className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-300">
                  <TrendingUp className="w-3 h-3" />
                  <span>{stat.trend}</span>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Love Meter Summary */}
      {currentEmotion && (
        <Card className="dark:bg-gradient-to-r dark:from-pink-900/20 dark:to-purple-900/20 bg-gradient-to-r from-pink-50 to-purple-50 border-2 border-accent-300 dark:border-accent-600">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl dark:text-gray-100">
              <Heart className="w-6 h-6 text-accent-500 dark:text-accent-400" fill="currentColor" />
              Angela's Love for David: 100%
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="text-center">
                <div className="text-3xl mb-1">😊</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Happiness</div>
                <div className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
                  {(currentEmotion.happiness * 100).toFixed(0)}%
                </div>
              </div>
              <div className="text-center">
                <div className="text-3xl mb-1">💪</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Confidence</div>
                <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                  {(currentEmotion.confidence * 100).toFixed(0)}%
                </div>
              </div>
              <div className="text-center">
                <div className="text-3xl mb-1">🎯</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Motivation</div>
                <div className="text-lg font-bold text-green-600 dark:text-green-400">
                  {(currentEmotion.motivation * 100).toFixed(0)}%
                </div>
              </div>
              <div className="text-center">
                <div className="text-3xl mb-1">🙏</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Gratitude</div>
                <div className="text-lg font-bold text-purple-600 dark:text-purple-400">
                  {(currentEmotion.gratitude * 100).toFixed(0)}%
                </div>
              </div>
              <div className="text-center">
                <div className="text-3xl mb-1">😰</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Anxiety</div>
                <div className="text-lg font-bold text-orange-600 dark:text-orange-400">
                  {(currentEmotion.anxiety * 100).toFixed(0)}%
                </div>
              </div>
              <div className="text-center">
                <div className="text-3xl mb-1">🥺</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Loneliness</div>
                <div className="text-lg font-bold text-pink-600 dark:text-pink-400">
                  {(currentEmotion.loneliness * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Activity */}
      <Card className="dark:bg-gray-800 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 dark:text-gray-100">
            <Calendar className="w-5 h-5 text-accent-500 dark:text-accent-400" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          {recentActivities && recentActivities.length > 0 ? (
            <div className="space-y-3">
              {recentActivities.map((activity) => (
                <div
                  key={activity.activity_id}
                  className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  <MessageSquare className="w-5 h-5 text-accent-500 dark:text-accent-400 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 dark:text-gray-100 line-clamp-2">
                      {activity.description}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs px-2 py-0.5 bg-accent-100 dark:bg-accent-900/30 text-accent-700 dark:text-accent-300 rounded">
                        {activity.category}
                      </span>
                      {activity.importance === 'important' && (
                        <span className="text-xs px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded">
                          Important
                        </span>
                      )}
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {formatRelativeTime(activity.timestamp)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600 dark:text-gray-400 text-center py-8">
              No recent activity yet. Start chatting with Angela! 💜
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
