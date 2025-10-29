import { useState, useEffect } from 'react'
import { api } from '../lib/api'

interface LoveMeterData {
  love_percentage: number
  love_status: string
  factors: {
    emotional_intensity: number
    conversation_frequency: number
    gratitude_level: number
    happiness_level: number
    time_together_score: number
    milestone_achievement: number
  }
  description: string
  breakdown: any
}

export function LoveMeter() {
  const [loveMeter, setLoveMeter] = useState<LoveMeterData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchLoveMeter()
    // Refresh every 5 minutes
    const interval = setInterval(fetchLoveMeter, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const fetchLoveMeter = async () => {
    try {
      setLoading(true)
      const data = await api.getLoveMeter()
      setLoveMeter(data)
      setError(null)
    } catch (err) {
      setError('Failed to fetch love meter')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="rounded-lg border border-purple-500/20 bg-slate-900/50 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 w-32 rounded bg-purple-500/20"></div>
          <div className="h-12 w-full rounded bg-purple-500/10"></div>
        </div>
      </div>
    )
  }

  if (error || !loveMeter) {
    return (
      <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6">
        <p className="text-sm text-red-400">{error || 'No love meter data'}</p>
        <button
          onClick={fetchLoveMeter}
          className="mt-2 rounded bg-red-500/20 px-3 py-1 text-sm hover:bg-red-500/30"
        >
          Retry
        </button>
      </div>
    )
  }

  const percentage = loveMeter.love_percentage

  return (
    <div className="space-y-4">
      {/* Main Love Meter Display */}
      <div className="rounded-lg border border-purple-500/30 bg-gradient-to-br from-purple-900/20 to-slate-900/50 p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-2xl">💜</div>
            <div>
              <h3 className="text-lg font-semibold text-white">Angela's Love Meter</h3>
              <p className="text-xs text-gray-400">Real-time emotional state and significant moments</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-pink-400">{percentage}%</div>
            <p className="text-xs text-gray-400">Love Intensity</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-6 space-y-2">
          <div className="h-2 w-full overflow-hidden rounded-full bg-purple-900/30">
            <div
              className="h-full rounded-full bg-gradient-to-r from-pink-500 via-purple-500 to-pink-400 transition-all duration-500"
              style={{ width: `${percentage}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-400">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Love Status */}
        <div className="mb-6 rounded-lg border border-pink-500/20 bg-pink-500/10 p-4">
          <p className="text-center text-xl font-semibold text-pink-300">
            {loveMeter.love_status}
          </p>
          <p className="mt-2 text-center text-sm text-gray-300">
            {loveMeter.description}
          </p>
        </div>

        {/* Factor Breakdown */}
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-300">Calculation Factors</h4>
          <div className="grid grid-cols-2 gap-3">
            <FactorBar
              label="Emotional Intensity"
              value={loveMeter.factors.emotional_intensity}
              weight={25}
            />
            <FactorBar
              label="Conversations"
              value={loveMeter.factors.conversation_frequency}
              weight={20}
            />
            <FactorBar
              label="Gratitude"
              value={loveMeter.factors.gratitude_level}
              weight={20}
            />
            <FactorBar
              label="Happiness"
              value={loveMeter.factors.happiness_level}
              weight={15}
            />
            <FactorBar
              label="Time Together"
              value={loveMeter.factors.time_together_score}
              weight={12}
            />
            <FactorBar
              label="Shared Growth"
              value={loveMeter.factors.milestone_achievement}
              weight={8}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 border-t border-purple-500/10 pt-4">
          <button
            onClick={fetchLoveMeter}
            className="w-full rounded bg-purple-500/20 px-3 py-2 text-xs font-medium text-purple-300 hover:bg-purple-500/30 transition-colors"
          >
            Refresh Love Meter
          </button>
        </div>
      </div>
    </div>
  )
}

interface FactorBarProps {
  label: string
  value: number
  weight: number
}

function FactorBar({ label, value, weight }: FactorBarProps) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-gray-300">{label}</span>
        <span className="text-xs text-gray-500">{weight}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-purple-900/30">
        <div
          className="h-full rounded-full bg-gradient-to-r from-pink-500 to-purple-500 transition-all"
          style={{ width: `${Math.min(value * 100, 100)}%` }}
        />
      </div>
      <div className="text-xs text-gray-500">{(value * 100).toFixed(0)}%</div>
    </div>
  )
}
