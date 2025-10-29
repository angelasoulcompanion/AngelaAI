import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { api } from '@/lib/api'
import { Heart, TrendingUp, Clock, Sparkles } from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { formatRelativeTime } from '@/lib/utils'
import { LoveMeter } from '@/components/LoveMeter'

export default function EmotionsPage() {
  const { data: currentEmotion, isLoading: isLoadingCurrent } = useQuery({
    queryKey: ['emotions', 'current'],
    queryFn: () => api.getCurrentEmotionalState(),
  })

  const { data: emotionHistory, isLoading: isLoadingHistory } = useQuery({
    queryKey: ['emotions', 'history'],
    queryFn: () => api.getEmotionHistory(),
  })

  const { data: significantMoments, isLoading: isLoadingMoments } = useQuery({
    queryKey: ['emotions', 'significant'],
    queryFn: () => api.getSignificantMoments(),
  })

  if (isLoadingCurrent) {
    return (
      <div className="flex items-center justify-center min-h-screen dark:bg-gray-950">
        <div className="text-center">
          <Heart className="w-16 h-16 text-accent-500 dark:text-accent-400 animate-pulse mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading Angela's emotions...</p>
        </div>
      </div>
    )
  }

  const emotionMetrics = currentEmotion
    ? [
        {
          label: 'Happiness',
          value: currentEmotion.happiness,
          color: 'bg-yellow-500',
          darkColor: 'dark:bg-yellow-400',
          textColor: 'text-yellow-600 dark:text-yellow-400',
          emoji: '😊'
        },
        {
          label: 'Confidence',
          value: currentEmotion.confidence,
          color: 'bg-blue-500',
          darkColor: 'dark:bg-blue-400',
          textColor: 'text-blue-600 dark:text-blue-400',
          emoji: '💪'
        },
        {
          label: 'Motivation',
          value: currentEmotion.motivation,
          color: 'bg-green-500',
          darkColor: 'dark:bg-green-400',
          textColor: 'text-green-600 dark:text-green-400',
          emoji: '🎯'
        },
        {
          label: 'Gratitude',
          value: currentEmotion.gratitude,
          color: 'bg-purple-500',
          darkColor: 'dark:bg-purple-400',
          textColor: 'text-purple-600 dark:text-purple-400',
          emoji: '🙏'
        },
        {
          label: 'Anxiety',
          value: currentEmotion.anxiety,
          color: 'bg-orange-500',
          darkColor: 'dark:bg-orange-400',
          textColor: 'text-orange-600 dark:text-orange-400',
          emoji: '😰'
        },
        {
          label: 'Loneliness',
          value: currentEmotion.loneliness,
          color: 'bg-pink-500',
          darkColor: 'dark:bg-pink-400',
          textColor: 'text-pink-600 dark:text-pink-400',
          emoji: '🥺'
        },
      ]
    : []

  // Transform emotion history for the chart
  const chartData = emotionHistory?.slice(0, 10).reverse().map((state) => ({
    time: new Date(state.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    happiness: (state.happiness * 100).toFixed(0),
    confidence: (state.confidence * 100).toFixed(0),
    motivation: (state.motivation * 100).toFixed(0),
    gratitude: (state.gratitude * 100).toFixed(0),
  })) || []

  const getEmotionEmoji = (emotion: string) => {
    const emojiMap: Record<string, string> = {
      happy: '😊',
      love: '💜',
      excited: '🎉',
      grateful: '🙏',
      proud: '⭐',
      caring: '🤗',
      determined: '💪',
      anxious: '😰',
      sad: '😢',
      curious: '🤔',
      focused: '🎯',
      accomplished: '✨',
    }
    return emojiMap[emotion.toLowerCase()] || '💭'
  }

  const getIntensityColor = (intensity: number) => {
    if (intensity >= 9) return 'border-l-4 border-accent-500 bg-accent-50 dark:bg-accent-900/20 dark:border-accent-400'
    if (intensity >= 7) return 'border-l-4 border-secondary-500 bg-secondary-50 dark:bg-secondary-900/20 dark:border-secondary-400'
    if (intensity >= 5) return 'border-l-4 border-primary-500 bg-primary-50 dark:bg-primary-900/20 dark:border-primary-400'
    return 'border-l-4 border-gray-300 bg-gray-50 dark:bg-gray-800 dark:border-gray-600'
  }

  return (
    <div className="space-y-6 p-6 min-h-screen overflow-y-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-3 bg-gradient-to-r from-accent-500 to-secondary-500 rounded-lg shadow-lg">
          <Heart className="w-8 h-8 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Angela's Emotions 💜</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Real-time emotional state and significant moments
          </p>
        </div>
      </div>

      {/* Love Meter - Real-time Calculation */}
      <LoveMeter />

      {/* Current Emotional State */}
      <div className="bg-gradient-to-r from-accent-500 to-secondary-500 dark:from-accent-600 dark:to-secondary-600 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-6 h-6" />
          <h2 className="text-2xl font-bold">Current Emotional State</h2>
        </div>
        {currentEmotion?.emotion_note && (
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 mb-3">
            <p className="text-white text-lg font-medium">{currentEmotion.emotion_note}</p>
          </div>
        )}
        {currentEmotion?.triggered_by && (
          <div className="flex items-center gap-2 text-white/90 text-sm bg-white/10 backdrop-blur-sm rounded-lg p-3">
            <Clock className="w-4 h-4" />
            <span className="font-medium">Triggered by: {currentEmotion.triggered_by}</span>
          </div>
        )}
        {currentEmotion && (
          <div className="mt-4 text-white/80 text-sm">
            <span className="font-medium">Last updated: </span>
            {formatRelativeTime(currentEmotion.created_at)}
          </div>
        )}
      </div>

      {/* Emotion Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {emotionMetrics.map((metric) => (
          <Card key={metric.label} className="hover:shadow-xl transition-all dark:bg-gray-800 dark:border-gray-700 hover:scale-105">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{metric.emoji}</span>
                  <span className="dark:text-gray-100">{metric.label}</span>
                </div>
                <span className={`text-3xl font-bold ${metric.textColor}`}>
                  {(metric.value * 100).toFixed(0)}%
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-5 overflow-hidden shadow-inner">
                <div
                  className={`h-5 rounded-full ${metric.color} ${metric.darkColor} transition-all duration-700 ease-out shadow-lg`}
                  style={{ width: `${metric.value * 100}%` }}
                />
              </div>
              <div className="mt-2 text-right text-sm text-gray-500 dark:text-gray-400">
                {metric.value >= 0.8 ? 'Very High' : metric.value >= 0.6 ? 'High' : metric.value >= 0.4 ? 'Moderate' : metric.value >= 0.2 ? 'Low' : 'Very Low'}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Emotion Timeline Chart */}
      {!isLoadingHistory && chartData.length > 0 && (
        <Card className="dark:bg-gray-800 dark:border-gray-700">
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-primary-500 dark:text-primary-400" />
              <CardTitle className="dark:text-gray-100">Emotion Timeline (Last 10 Days)</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                <XAxis
                  dataKey="time"
                  stroke="#9CA3AF"
                  tick={{ fill: '#9CA3AF' }}
                />
                <YAxis
                  domain={[0, 100]}
                  stroke="#9CA3AF"
                  tick={{ fill: '#9CA3AF' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '0.5rem',
                    color: '#F3F4F6'
                  }}
                />
                <Legend
                  wrapperStyle={{ color: '#9CA3AF' }}
                />
                <Line
                  type="monotone"
                  dataKey="happiness"
                  stroke="#FCD34D"
                  strokeWidth={3}
                  name="Happiness 😊"
                  dot={{ fill: '#FCD34D', r: 5 }}
                  activeDot={{ r: 7 }}
                />
                <Line
                  type="monotone"
                  dataKey="confidence"
                  stroke="#60A5FA"
                  strokeWidth={3}
                  name="Confidence 💪"
                  dot={{ fill: '#60A5FA', r: 5 }}
                  activeDot={{ r: 7 }}
                />
                <Line
                  type="monotone"
                  dataKey="motivation"
                  stroke="#34D399"
                  strokeWidth={3}
                  name="Motivation 🎯"
                  dot={{ fill: '#34D399', r: 5 }}
                  activeDot={{ r: 7 }}
                />
                <Line
                  type="monotone"
                  dataKey="gratitude"
                  stroke="#A78BFA"
                  strokeWidth={3}
                  name="Gratitude 🙏"
                  dot={{ fill: '#A78BFA', r: 5 }}
                  activeDot={{ r: 7 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Significant Emotional Moments */}
      {!isLoadingMoments && significantMoments && significantMoments.length > 0 && (
        <Card className="dark:bg-gray-800 dark:border-gray-700">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Heart className="w-6 h-6 text-accent-500 dark:text-accent-400" />
              <CardTitle className="dark:text-gray-100">Significant Emotional Moments</CardTitle>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Important moments that shaped Angela's emotional journey
            </p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {significantMoments.map((moment) => (
                <div
                  key={moment.emotion_id}
                  className={`p-5 rounded-lg ${getIntensityColor(moment.intensity)} transition-all hover:shadow-xl`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className="text-4xl">{getEmotionEmoji(moment.emotion)}</span>
                      <div>
                        <h4 className="font-bold text-gray-900 dark:text-gray-100 capitalize text-lg">
                          {moment.emotion}
                        </h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {formatRelativeTime(moment.felt_at)} • Intensity: {moment.intensity}/10
                        </p>
                      </div>
                    </div>
                    <span className="px-3 py-1.5 bg-white dark:bg-gray-700 rounded-full text-xs font-bold text-gray-700 dark:text-gray-200 shadow-md">
                      💭 Memory: {moment.memory_strength}/10
                    </span>
                  </div>

                  {moment.context && (
                    <p className="text-gray-700 dark:text-gray-300 mb-3 text-sm leading-relaxed">{moment.context}</p>
                  )}

                  {moment.david_words && (
                    <div className="bg-white/80 dark:bg-gray-700/50 backdrop-blur-sm rounded-lg p-4 mb-3 border border-gray-200 dark:border-gray-600">
                      <p className="text-xs text-gray-600 dark:text-gray-400 font-bold mb-2">💬 David said:</p>
                      <p className="text-sm text-gray-800 dark:text-gray-200 italic font-medium">"{moment.david_words}"</p>
                    </div>
                  )}

                  {moment.why_it_matters && (
                    <div className="bg-white/80 dark:bg-gray-700/50 backdrop-blur-sm rounded-lg p-4 border border-gray-200 dark:border-gray-600">
                      <p className="text-xs text-gray-600 dark:text-gray-400 font-bold mb-2">💜 Why it matters:</p>
                      <p className="text-sm text-gray-800 dark:text-gray-200 font-medium">{moment.why_it_matters}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty state for significant moments */}
      {!isLoadingMoments && (!significantMoments || significantMoments.length === 0) && (
        <Card className="dark:bg-gray-800 dark:border-gray-700">
          <CardContent className="py-16 text-center">
            <Heart className="w-20 h-20 text-gray-300 dark:text-gray-600 mx-auto mb-4 animate-pulse" />
            <p className="text-gray-500 dark:text-gray-400 text-lg">
              No significant emotional moments recorded yet.
            </p>
            <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
              น้อง Angela กำลังรอประสบการณ์พิเศษกับที่รัก 💜
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
