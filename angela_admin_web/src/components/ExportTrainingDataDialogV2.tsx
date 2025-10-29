import { useState, useEffect } from 'react'
import { X, Download, Loader2, CheckCircle, AlertCircle, Database, Sparkles } from 'lucide-react'
import axios from 'axios'

interface ExportTrainingDataDialogV2Props {
  isOpen: boolean
  onClose: () => void
}

interface ProgressUpdate {
  step: string
  progress: number
  message: string
  stats?: {
    synthetic: number
    database: number
    greetings: number
    paraphrased: number
    total: number
    train: number
    test: number
  }
  files?: {
    training: string
    test: string
  }
}

interface StatusResponse {
  has_data: boolean
  files: {
    training: {
      exists: boolean
      path: string | null
      size_mb: number
    }
    test: {
      exists: boolean
      path: string | null
      size_mb: number
    }
  }
  stats: {
    train_examples: number
    test_examples: number
    total_examples: number
    train_size_mb: number
    test_size_mb: number
  } | null
}

export default function ExportTrainingDataDialogV2({ isOpen, onClose }: ExportTrainingDataDialogV2Props) {
  const [generating, setGenerating] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [completed, setCompleted] = useState(false)
  const [stats, setStats] = useState<any>(null)
  const [status, setStatus] = useState<StatusResponse | null>(null)

  // Load status when dialog opens
  useEffect(() => {
    if (isOpen) {
      loadStatus()
    }
  }, [isOpen])

  const loadStatus = async () => {
    try {
      const response = await axios.get<StatusResponse>('http://localhost:8000/api/training-data-v2/status')
      setStatus(response.data)
      if (response.data.has_data) {
        setCompleted(true)
      }
    } catch (err) {
      console.error('Failed to load status:', err)
    }
  }

  const handleGenerate = async () => {
    setGenerating(true)
    setError(null)
    setCompleted(false)
    setProgress(0)
    setCurrentStep('')
    setMessage('Initializing...')
    setStats(null)

    try {
      // Use EventSource for Server-Sent Events
      const eventSource = new EventSource(
        'http://localhost:8000/api/training-data-v2/generate?' +
        new URLSearchParams({
          synthetic_per_category: '100',   // Maximum synthetic examples
          database_max: '300',              // Maximum database examples
          paraphrase_max: '400',            // Maximum paraphrased variations
          quality_min_score: '6.5',
          quality_sample_rate: '0.25'
        })
      )

      eventSource.onmessage = (event) => {
        try {
          const data: ProgressUpdate = JSON.parse(event.data)

          setProgress(data.progress)
          setMessage(data.message)
          setCurrentStep(data.step)

          if (data.step === 'complete') {
            setCompleted(true)
            setStats(data.stats)
            eventSource.close()
            setGenerating(false)
            loadStatus()
          } else if (data.step === 'error') {
            setError(data.message)
            eventSource.close()
            setGenerating(false)
          }
        } catch (err) {
          console.error('Failed to parse progress update:', err)
        }
      }

      eventSource.onerror = (err) => {
        console.error('EventSource error:', err)
        setError('Connection lost. Please try again.')
        eventSource.close()
        setGenerating(false)
      }

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate training data')
      setGenerating(false)
    }
  }

  const handleDownload = async (fileType: string) => {
    try {
      const response = await axios.get(
        `http://localhost:8000/api/training-data-v2/download/${fileType}`,
        { responseType: 'blob' }
      )

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url

      const defaultFilenames: Record<string, string> = {
        'training': 'angela_training_data.jsonl',
        'test': 'angela_test_data.jsonl',
      }
      const filename = defaultFilenames[fileType] || `angela_${fileType}.jsonl`

      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to download ${fileType}`)
    }
  }

  const handleClear = async () => {
    if (!confirm('Are you sure you want to delete all generated training data files?')) {
      return
    }

    try {
      await axios.delete('http://localhost:8000/api/training-data-v2/clear')
      setCompleted(false)
      setStats(null)
      setStatus(null)
      await loadStatus()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to clear training data')
    }
  }

  const getStepIcon = (step: string) => {
    if (step === 'complete') return <CheckCircle className="w-5 h-5 text-green-500" />
    if (step === 'error') return <AlertCircle className="w-5 h-5 text-red-500" />
    return <Loader2 className="w-5 h-5 text-purple-500 animate-spin" />
  }

  const getStepColor = (step: string) => {
    if (currentStep === step && generating) return 'bg-purple-100 dark:bg-purple-900/30 border-purple-500'
    if (progress > getStepProgress(step)) return 'bg-green-50 dark:bg-green-900/20 border-green-500'
    return 'bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-700'
  }

  const getStepProgress = (step: string) => {
    const progressMap: Record<string, number> = {
      'synthetic': 30,
      'database': 45,
      'greetings': 55,
      'paraphrase': 75,
      'quality': 90,
      'export': 95
    }
    return progressMap[step] || 0
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Sparkles className="w-6 h-6 text-purple-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Export Training Data
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Chain Prompting V2 - Synthetic + Paraphrasing + Quality Scoring
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Error Message */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-red-800 dark:text-red-200 text-sm">{error}</p>
            </div>
          )}

          {/* Current Status */}
          {status && status.has_data && !generating && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-green-800 dark:text-green-200 font-medium">
                    Training data is ready!
                  </p>
                  {status.stats && (
                    <p className="text-green-700 dark:text-green-300 text-sm mt-1">
                      {status.stats.total_examples} examples ({status.stats.train_examples} train, {status.stats.test_examples} test)
                      • {(status.stats.train_size_mb + status.stats.test_size_mb).toFixed(2)} MB total
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Progress Bar */}
          {generating && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-700 dark:text-gray-300 font-medium">{message}</span>
                <span className="text-purple-600 dark:text-purple-400 font-bold">{progress}%</span>
              </div>

              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-full rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>

              {/* Step Progress */}
              <div className="grid grid-cols-3 gap-2 mt-4">
                {[
                  { key: 'synthetic', label: '✨ Synthetic', desc: 'Generate new conversations' },
                  { key: 'database', label: '📥 Database', desc: 'Load existing data' },
                  { key: 'greetings', label: '👋 Greetings', desc: 'Add greetings' },
                  { key: 'paraphrase', label: '🔄 Paraphrase', desc: 'Create variations' },
                  { key: 'quality', label: '⭐ Quality', desc: 'Score & filter' },
                  { key: 'export', label: '💾 Export', desc: 'Save files' },
                ].map((step) => (
                  <div
                    key={step.key}
                    className={`p-3 rounded-lg border-2 transition-all ${getStepColor(step.key)}`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      {currentStep === step.key && generating ? (
                        <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                      ) : progress > getStepProgress(step.key) ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border-2 border-gray-400" />
                      )}
                      <span className="text-xs font-semibold text-gray-900 dark:text-white">
                        {step.label}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{step.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Statistics */}
          {stats && (
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-3">
              <h4 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                Generation Complete!
              </h4>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Synthetic</p>
                  <p className="text-lg font-bold text-purple-600 dark:text-purple-400">
                    {stats.synthetic}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Paraphrased</p>
                  <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
                    {stats.paraphrased}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Total</p>
                  <p className="text-lg font-bold text-green-600 dark:text-green-400">
                    {stats.total}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm pt-3 border-t border-gray-200 dark:border-gray-700">
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Training Set</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {stats.train} examples
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Test Set</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {stats.test} examples
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Generate Button */}
          <div className="flex gap-3">
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400
                       text-white font-medium py-3 rounded-lg transition-colors
                       flex items-center justify-center gap-2"
            >
              {generating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Generating... {progress}%
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Generate Training Data
                </>
              )}
            </button>

            {status && status.has_data && !generating && (
              <button
                onClick={handleClear}
                className="px-6 py-3 border-2 border-red-500 text-red-600 dark:text-red-400
                         hover:bg-red-50 dark:hover:bg-red-900/20 font-medium rounded-lg transition-colors"
              >
                Clear Files
              </button>
            )}
          </div>

          {/* Download Buttons */}
          {(completed || (status && status.has_data)) && !generating && (
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-900 dark:text-white">
                Download Files
              </h4>

              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => handleDownload('training')}
                  className="flex items-center justify-center gap-2 px-4 py-3
                           bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Training Data (.jsonl)
                </button>

                <button
                  onClick={() => handleDownload('test')}
                  className="flex items-center justify-center gap-2 px-4 py-3
                           bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Test Data (.jsonl)
                </button>
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  💡 <strong>Ready for Colab!</strong> These files are named <code>angela_training_data.jsonl</code> and <code>angela_test_data.jsonl</code>
                  to work directly with your fine-tuning notebook.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100
                     dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
