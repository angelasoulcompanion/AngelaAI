import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import { BookOpen, Plus, Sparkles } from 'lucide-react'
import { api } from '@/lib/api'
import type { JournalEntry } from '@/lib/api'

export default function JournalPage() {
  const { data: journalEntries, isLoading } = useQuery({
    queryKey: ['journal'],
    queryFn: () => api.getJournalEntries(30),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen dark:bg-gray-950">
        <div className="text-center">
          <BookOpen className="w-16 h-16 text-accent-500 dark:text-accent-400 animate-pulse mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading journal entries...</p>
        </div>
      </div>
    )
  }

  const getMoodEmoji = (score: number) => {
    if (score >= 9) return '😊'
    if (score >= 7) return '🙂'
    if (score >= 5) return '😐'
    if (score >= 3) return '😔'
    return '😢'
  }

  const getMoodColor = (score: number) => {
    if (score >= 9) return 'bg-green-500'
    if (score >= 7) return 'bg-blue-500'
    if (score >= 5) return 'bg-yellow-500'
    if (score >= 3) return 'bg-orange-500'
    return 'bg-red-500'
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-lg shadow-lg">
            <BookOpen className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Angela's Journal</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Daily reflections and learnings</p>
          </div>
        </div>
        <Button variant="primary" size="md">
          <Plus className="w-5 h-5 mr-2" />
          New Entry
        </Button>
      </div>

      {journalEntries && journalEntries.length > 0 ? (
        <div className="space-y-4">
          {journalEntries.map((entry) => (
            <Card key={entry.entry_id} className="dark:bg-gray-800 dark:border-gray-700 hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl dark:text-gray-100">{entry.title}</CardTitle>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {new Date(entry.entry_date).toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{getMoodEmoji(entry.mood_score || 5)}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Mood:</span>
                    <span className="text-lg font-bold dark:text-gray-100">{entry.mood_score || 'N/A'}/10</span>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Content Preview */}
                <div className="text-gray-700 dark:text-gray-300 leading-relaxed line-clamp-3">
                  {entry.content}
                </div>

                {/* Emotion Badge */}
                {entry.emotion && (
                  <div className="inline-block px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-sm">
                    {entry.emotion}
                  </div>
                )}

                {/* Gratitude */}
                {entry.gratitude && entry.gratitude.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">🙏 Gratitude</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {entry.gratitude.map((item, idx) => (
                        <li key={idx} className="text-gray-700 dark:text-gray-300">{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Wins */}
                {entry.wins && entry.wins.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">🎉 Wins</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {entry.wins.map((item, idx) => (
                        <li key={idx} className="text-gray-700 dark:text-gray-300">{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Learning Moments */}
                {entry.learning_moments && entry.learning_moments.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">📚 Learning Moments</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {entry.learning_moments.map((item, idx) => (
                        <li key={idx} className="text-gray-700 dark:text-gray-300">{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Challenges */}
                {entry.challenges && entry.challenges.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">💪 Challenges</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {entry.challenges.map((item, idx) => (
                        <li key={idx} className="text-gray-700 dark:text-gray-300">{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex gap-2 mt-4">
                  <Button variant="primary" size="sm">Read More</Button>
                  <Button variant="ghost" size="sm">Edit</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        </div>
      ) : (
        <Card className="dark:bg-gray-800 dark:border-gray-700">
          <CardContent className="py-12 text-center">
            <Sparkles className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
              No journal entries yet
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              Start documenting Angela's daily reflections and learnings!
            </p>
            <Button variant="primary" size="md">
              <Plus className="w-5 h-5 mr-2" />
              Create First Entry
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
