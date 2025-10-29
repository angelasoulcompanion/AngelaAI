import { useState, useEffect } from 'react'
import { X, Download, Loader2, CheckCircle, AlertCircle, Database } from 'lucide-react'
import axios from 'axios'

interface ExportTrainingDataDialogProps {
  isOpen: boolean
  onClose: () => void
}

interface PrepareRequest {
  min_importance: number
  max_per_topic: number
  test_split: number
  min_length: number
  time_window: number
}

interface PrepareResponse {
  success: boolean
  message: string
  stats: {
    total_examples: number
    train_examples: number
    test_examples: number
    avg_importance: number
    topics_covered: number
    file_sizes_mb: {
      training?: number
      test?: number
      statistics?: number
      quality_report?: number
    }
  }
  files: {
    training: string | null
    test: string | null
    statistics: string
    quality_report: string | null
  }
}

interface FileStatus {
  exists: boolean
  size_mb: number
  modified: string | null
  path: string
}

interface StatusResponse {
  files: {
    training: FileStatus
    test: FileStatus
    statistics: FileStatus
    quality_report: FileStatus
  }
  statistics: any
  has_data: boolean
}

export default function ExportTrainingDataDialog({ isOpen, onClose }: ExportTrainingDataDialogProps) {
  const [preparing, setPreparing] = useState(false)
  const [prepared, setPrepared] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [prepareResponse, setPrepareResponse] = useState<PrepareResponse | null>(null)
  const [status, setStatus] = useState<StatusResponse | null>(null)

  // Form state
  const [formData, setFormData] = useState<PrepareRequest>({
    min_importance: 7,
    max_per_topic: 150,
    test_split: 0.1,
    min_length: 10,
    time_window: 5
  })

  // Load status when dialog opens
  useEffect(() => {
    if (isOpen) {
      loadStatus()
    }
  }, [isOpen])

  const loadStatus = async () => {
    try {
      const response = await axios.get<StatusResponse>('http://localhost:8000/api/training-data/status')
      setStatus(response.data)
      if (response.data.has_data) {
        setPrepared(true)
      }
    } catch (err) {
      console.error('Failed to load status:', err)
    }
  }

  const handlePrepare = async () => {
    setPreparing(true)
    setError(null)
    setPrepared(false)
    setPrepareResponse(null)

    try {
      const response = await axios.post<PrepareResponse>(
        'http://localhost:8000/api/training-data/prepare',
        formData
      )
      setPrepareResponse(response.data)
      setPrepared(true)
      await loadStatus()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to prepare training data')
    } finally {
      setPreparing(false)
    }
  }

  const handleDownload = async (fileType: string) => {
    try {
      const response = await axios.get(
        `http://localhost:8000/api/training-data/download/${fileType}`,
        { responseType: 'blob' }
      )

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url

      // Set filename from response headers or default
      const contentDisposition = response.headers['content-disposition']
      const defaultFilenames: Record<string, string> = {
        'training': 'angela_training_data.jsonl',
        'test': 'angela_test_data.jsonl',
        'statistics': 'data_statistics.json',
        'quality_report': 'data_quality_report.txt'
      }
      let filename = defaultFilenames[fileType] || `angela_${fileType}.jsonl`
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
        if (filenameMatch) filename = filenameMatch[1]
      }

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
      await axios.delete('http://localhost:8000/api/training-data/clear')
      setPrepared(false)
      setPrepareResponse(null)
      setStatus(null)
      await loadStatus()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to clear training data')
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Database className="w-6 h-6 text-purple-600" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Export Training Data
            </h2>
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
          {status && status.has_data && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-green-800 dark:text-green-200 font-medium">
                    Training data is ready!
                  </p>
                  {status.statistics && (
                    <p className="text-green-700 dark:text-green-300 text-sm mt-1">
                      {status.statistics.total_examples} examples ({status.statistics.train_examples} train, {status.statistics.test_examples} test)
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Configuration Form */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Preparation Parameters
            </h3>

            <div className="grid grid-cols-2 gap-4">
              {/* Min Importance */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Min Importance (1-10)
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={formData.min_importance}
                  onChange={(e) => setFormData({ ...formData, min_importance: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  disabled={preparing}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Only include conversations with importance ≥ this value
                </p>
              </div>

              {/* Max Per Topic */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Max Per Topic
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.max_per_topic}
                  onChange={(e) => setFormData({ ...formData, max_per_topic: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  disabled={preparing}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Maximum examples per topic to prevent bias
                </p>
              </div>

              {/* Test Split */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Test Split (0.0-1.0)
                </label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={formData.test_split}
                  onChange={(e) => setFormData({ ...formData, test_split: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  disabled={preparing}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Fraction of data to use for testing (0.1 = 10%)
                </p>
              </div>

              {/* Min Length */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Min Message Length
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.min_length}
                  onChange={(e) => setFormData({ ...formData, min_length: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  disabled={preparing}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Minimum characters per message
                </p>
              </div>

              {/* Time Window */}
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Time Window (minutes)
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.time_window}
                  onChange={(e) => setFormData({ ...formData, time_window: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  disabled={preparing}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Group messages within this time window into conversations
                </p>
              </div>
            </div>
          </div>

          {/* Prepare Button */}
          <div className="flex gap-3">
            <button
              onClick={handlePrepare}
              disabled={preparing}
              className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400
                       text-white font-medium py-3 rounded-lg transition-colors
                       flex items-center justify-center gap-2"
            >
              {preparing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Preparing Data...
                </>
              ) : (
                <>
                  <Database className="w-5 h-5" />
                  Prepare Training Data
                </>
              )}
            </button>

            {status && status.has_data && (
              <button
                onClick={handleClear}
                className="px-6 py-3 border-2 border-red-500 text-red-600 dark:text-red-400
                         hover:bg-red-50 dark:hover:bg-red-900/20 font-medium rounded-lg transition-colors"
              >
                Clear Files
              </button>
            )}
          </div>

          {/* Statistics */}
          {prepareResponse && (
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-3">
              <h4 className="font-semibold text-gray-900 dark:text-white">
                Preparation Results
              </h4>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Total Examples</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    {prepareResponse.stats.total_examples}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Avg Importance</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    {(prepareResponse.stats.avg_importance ?? 0).toFixed(2)}/10
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Topics</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    {prepareResponse.stats.topics_covered}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Training Set</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {prepareResponse.stats.train_examples} examples
                    {prepareResponse.stats.file_sizes_mb.training &&
                      ` (${prepareResponse.stats.file_sizes_mb.training} MB)`}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Test Set</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {prepareResponse.stats.test_examples} examples
                    {prepareResponse.stats.file_sizes_mb.test &&
                      ` (${prepareResponse.stats.file_sizes_mb.test} MB)`}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Download Buttons */}
          {prepared && (
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

                <button
                  onClick={() => handleDownload('statistics')}
                  className="flex items-center justify-center gap-2 px-4 py-3
                           bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Statistics (.json)
                </button>

                <button
                  onClick={() => handleDownload('quality_report')}
                  className="flex items-center justify-center gap-2 px-4 py-3
                           bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Quality Report (.txt)
                </button>
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
