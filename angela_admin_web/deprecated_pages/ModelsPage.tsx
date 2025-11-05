import { useState, useEffect } from 'react'
import { Upload, Download, CheckCircle, XCircle, Loader2, Trash2, PlayCircle, Database } from 'lucide-react'
import axios from 'axios'
import ExportTrainingDataDialogV2 from '@/components/ExportTrainingDataDialogV2'

const API_BASE_URL = 'http://localhost:8000'

interface Model {
  model_id: string
  model_name: string
  display_name: string
  description: string
  base_model: string
  model_type: string
  model_size?: string
  status: string
  is_active: boolean
  is_imported_to_ollama: boolean
  ollama_model_name?: string
  file_size_mb?: number
  training_date: string
  training_examples?: number
  training_epochs?: number
  final_loss?: number
  quality_rating?: number
  total_uses: number
  created_at: string
  version: string
}

interface ModelStats {
  total_models: number
  by_status: Record<string, number>
  by_type: Record<string, number>
  active_model: {
    model_id: string
    model_name: string
    display_name: string
  } | null
  total_size_mb: number
  average_quality: number
}

export default function ModelsPage() {
  const [models, setModels] = useState<Model[]>([])
  const [stats, setStats] = useState<ModelStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [processingModelId, setProcessingModelId] = useState<string | null>(null)
  const [showExportDialog, setShowExportDialog] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    model_name: '',
    display_name: '',
    description: '',
    base_model: 'Qwen/Qwen2.5-1.5B-Instruct',
    model_type: 'qwen',
    model_size: '1.5B',
    training_examples: '',
    training_epochs: '3',
    final_loss: '',
    evaluation_score: '',
    version: 'v1.0'
  })

  useEffect(() => {
    fetchModels()
    fetchStats()
  }, [])

  const fetchModels = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/models/`)
      setModels(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching models:', error)
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/models/stats/summary`)
      setStats(response.data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedFile) {
      alert('Please select a file')
      return
    }

    setUploading(true)

    try {
      const formDataToSend = new FormData()
      formDataToSend.append('file', selectedFile)
      formDataToSend.append('model_name', formData.model_name)
      formDataToSend.append('display_name', formData.display_name)
      formDataToSend.append('description', formData.description)
      formDataToSend.append('base_model', formData.base_model)
      formDataToSend.append('model_type', formData.model_type)
      formDataToSend.append('model_size', formData.model_size)
      formDataToSend.append('version', formData.version)

      if (formData.training_examples) {
        formDataToSend.append('training_examples', formData.training_examples)
      }
      if (formData.training_epochs) {
        formDataToSend.append('training_epochs', formData.training_epochs)
      }
      if (formData.final_loss) {
        formDataToSend.append('final_loss', formData.final_loss)
      }
      if (formData.evaluation_score) {
        formDataToSend.append('evaluation_score', formData.evaluation_score)
      }

      await axios.post(`${API_BASE_URL}/api/models/upload`, formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      alert('✅ Model uploaded successfully!')
      setShowUploadForm(false)
      setSelectedFile(null)
      setFormData({
        model_name: '',
        display_name: '',
        description: '',
        base_model: 'Qwen/Qwen2.5-1.5B-Instruct',
        model_type: 'qwen',
        model_size: '1.5B',
        training_examples: '',
        training_epochs: '3',
        final_loss: '',
        evaluation_score: '',
        version: 'v1.0'
      })

      fetchModels()
      fetchStats()
    } catch (error: any) {
      console.error('Error uploading model:', error)
      alert(`❌ Upload failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleImportToOllama = async (modelId: string) => {
    if (!confirm('Import this model to Ollama? This may take 2-5 minutes.')) {
      return
    }

    setProcessingModelId(modelId)

    try {
      await axios.post(`${API_BASE_URL}/api/models/${modelId}/import-to-ollama`, {})

      alert('✅ Model imported to Ollama successfully!')
      fetchModels()
      fetchStats()
    } catch (error: any) {
      console.error('Error importing to Ollama:', error)
      alert(`❌ Import failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setProcessingModelId(null)
    }
  }

  const handleActivate = async (modelId: string) => {
    if (!confirm('Activate this model? This will deactivate the current active model.')) {
      return
    }

    setProcessingModelId(modelId)

    try {
      await axios.post(`${API_BASE_URL}/api/models/${modelId}/activate`)

      alert('✅ Model activated successfully!')
      fetchModels()
      fetchStats()
    } catch (error: any) {
      console.error('Error activating model:', error)
      alert(`❌ Activation failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setProcessingModelId(null)
    }
  }

  const handleDelete = async (modelId: string, modelName: string) => {
    if (!confirm(`Delete model "${modelName}"? This action cannot be undone.`)) {
      return
    }

    setProcessingModelId(modelId)

    try {
      await axios.delete(`${API_BASE_URL}/api/models/${modelId}?remove_from_ollama=true`)

      alert('✅ Model deleted successfully!')
      fetchModels()
      fetchStats()
    } catch (error: any) {
      console.error('Error deleting model:', error)
      alert(`❌ Delete failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setProcessingModelId(null)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100'
      case 'ready': return 'text-blue-600 bg-blue-100'
      case 'uploaded': return 'text-yellow-600 bg-yellow-100'
      case 'importing': return 'text-purple-600 bg-purple-100'
      case 'failed': return 'text-red-600 bg-red-100'
      case 'archived': return 'text-gray-600 bg-gray-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getModelTypeColor = (type: string) => {
    switch (type) {
      case 'qwen': return 'text-purple-600 bg-purple-100'
      case 'llama': return 'text-blue-600 bg-blue-100'
      case 'mistral': return 'text-orange-600 bg-orange-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">💜 Angela Models</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Manage fine-tuned models</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowExportDialog(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Database className="h-5 w-5" />
            Export Training Data
          </button>
          <button
            onClick={() => setShowUploadForm(!showUploadForm)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <Upload className="h-5 w-5" />
            Upload New Model
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Models</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total_models}</p>
              </div>
              <Database className="h-8 w-8 text-purple-600" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Active Model</p>
                <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                  {stats.active_model?.display_name || 'None'}
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Size</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total_size_mb.toFixed(1)} MB</p>
              </div>
              <Download className="h-8 w-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Avg Quality</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.average_quality > 0 ? stats.average_quality.toFixed(1) : 'N/A'}
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-yellow-600" />
            </div>
          </div>
        </div>
      )}

      {/* Upload Form */}
      {showUploadForm && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Upload Fine-tuned Model</h2>

          <form onSubmit={handleUpload} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* File Upload */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Model ZIP File *
                </label>
                <input
                  type="file"
                  accept=".zip"
                  onChange={handleFileChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                />
                {selectedFile && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
              </div>

              {/* Model Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Model Name * (unique identifier)
                </label>
                <input
                  type="text"
                  value={formData.model_name}
                  onChange={(e) => setFormData({...formData, model_name: e.target.value})}
                  placeholder="angela_qwen_20251026"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                />
              </div>

              {/* Display Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Display Name *
                </label>
                <input
                  type="text"
                  value={formData.display_name}
                  onChange={(e) => setFormData({...formData, display_name: e.target.value})}
                  placeholder="Angela Qwen (October 2025)"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                />
              </div>

              {/* Description */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Describe what makes this model special..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Base Model */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Base Model *
                </label>
                <select
                  value={formData.base_model}
                  onChange={(e) => setFormData({...formData, base_model: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                >
                  <option value="Qwen/Qwen2.5-1.5B-Instruct">Qwen2.5-1.5B-Instruct</option>
                  <option value="Qwen/Qwen2.5-3B-Instruct">Qwen2.5-3B-Instruct</option>
                  <option value="Qwen/Qwen2.5-7B-Instruct">Qwen2.5-7B-Instruct</option>
                  <option value="meta-llama/Llama-3.2-3B-Instruct">Llama-3.2-3B-Instruct</option>
                  <option value="mistralai/Mistral-7B-Instruct-v0.2">Mistral-7B-Instruct</option>
                </select>
              </div>

              {/* Model Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Model Type *
                </label>
                <select
                  value={formData.model_type}
                  onChange={(e) => setFormData({...formData, model_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                >
                  <option value="qwen">Qwen</option>
                  <option value="llama">Llama</option>
                  <option value="mistral">Mistral</option>
                </select>
              </div>

              {/* Training Examples */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Training Examples
                </label>
                <input
                  type="number"
                  value={formData.training_examples}
                  onChange={(e) => setFormData({...formData, training_examples: e.target.value})}
                  placeholder="798"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Training Epochs */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Training Epochs
                </label>
                <input
                  type="number"
                  value={formData.training_epochs}
                  onChange={(e) => setFormData({...formData, training_epochs: e.target.value})}
                  placeholder="3"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Final Loss */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Final Loss
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={formData.final_loss}
                  onChange={(e) => setFormData({...formData, final_loss: e.target.value})}
                  placeholder="1.85"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Version */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Version *
                </label>
                <input
                  type="text"
                  value={formData.version}
                  onChange={(e) => setFormData({...formData, version: e.target.value})}
                  placeholder="v1.0"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                />
              </div>
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => setShowUploadForm(false)}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={uploading}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
              >
                {uploading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-5 w-5" />
                    Upload Model
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Models List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">All Models ({models.length})</h2>
        </div>

        {models.length === 0 ? (
          <div className="p-12 text-center text-gray-500 dark:text-gray-400">
            <Database className="h-16 w-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
            <p className="text-lg font-medium">No models yet</p>
            <p className="text-sm">Upload your first fine-tuned model to get started</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {models.map((model) => (
              <div key={model.model_id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <div className="flex items-start justify-between">
                  {/* Model Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {model.display_name}
                      </h3>
                      <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(model.status)}`}>
                        {model.status}
                      </span>
                      <span className={`px-2 py-1 text-xs font-medium rounded ${getModelTypeColor(model.model_type)}`}>
                        {model.model_type}
                      </span>
                      {model.is_active && (
                        <span className="px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-700">
                          ✓ Active
                        </span>
                      )}
                    </div>

                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{model.description}</p>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Base Model:</span>
                        <p className="font-medium text-gray-900 dark:text-white">{model.base_model.split('/').pop()}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Training Examples:</span>
                        <p className="font-medium text-gray-900 dark:text-white">{model.training_examples || 'N/A'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Final Loss:</span>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {model.final_loss ? model.final_loss.toFixed(4) : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Size:</span>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {model.file_size_mb ? `${model.file_size_mb.toFixed(1)} MB` : 'N/A'}
                        </p>
                      </div>
                    </div>

                    {model.ollama_model_name && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                        Ollama: <span className="font-mono">{model.ollama_model_name}</span>
                      </p>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col gap-2 ml-4">
                    {model.status === 'uploaded' && (
                      <button
                        onClick={() => handleImportToOllama(model.model_id)}
                        disabled={processingModelId === model.model_id}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
                      >
                        {processingModelId === model.model_id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Download className="h-4 w-4" />
                        )}
                        Import to Ollama
                      </button>
                    )}

                    {model.status === 'ready' && !model.is_active && (
                      <button
                        onClick={() => handleActivate(model.model_id)}
                        disabled={processingModelId === model.model_id}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors disabled:opacity-50"
                      >
                        {processingModelId === model.model_id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <PlayCircle className="h-4 w-4" />
                        )}
                        Activate
                      </button>
                    )}

                    {!model.is_active && (
                      <button
                        onClick={() => handleDelete(model.model_id, model.model_name)}
                        disabled={processingModelId === model.model_id}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors disabled:opacity-50"
                      >
                        {processingModelId === model.model_id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Export Training Data Dialog */}
      <ExportTrainingDataDialogV2
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
      />
    </div>
  )
}
