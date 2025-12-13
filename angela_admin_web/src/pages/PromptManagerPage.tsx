import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { api } from '@/lib/api'
import { Sparkles, FileText, Download, Check, RefreshCw, Eye, Settings, Copy } from 'lucide-react'
import { formatRelativeTime } from '@/lib/utils'

interface PromptVersion {
  version_id: string
  version: string
  preview: string
  components: string[]
  metadata: Record<string, any>
  notes: string | null
  created_at: string
}

interface PromptData {
  prompt: string
  version: string
  generated_at: string
  components: string[]
  metadata: Record<string, any>
  length: number
  model_target: string
}

interface CurrentPrompt {
  version_id?: string
  version: string
  prompt_text: string
  components: string[]
  metadata: Record<string, any>
  notes: string | null
  model_target: string
  created_at: string
  is_active: boolean
}

export default function PromptManagerPage() {
  const queryClient = useQueryClient()
  const [showFullPrompt, setShowFullPrompt] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null)
  const [copySuccess, setCopySuccess] = useState(false)

  // Query current active prompt
  const { data: currentPrompt, isLoading: isLoadingCurrent } = useQuery<CurrentPrompt>({
    queryKey: ['prompts', 'current'],
    queryFn: () => api.getCurrentPrompt(),
  })

  // Query prompt versions
  const { data: versions, isLoading: isLoadingVersions } = useQuery<PromptVersion[]>({
    queryKey: ['prompts', 'versions'],
    queryFn: () => api.getPromptVersions(),
  })

  // Query prompt stats
  const { data: stats } = useQuery({
    queryKey: ['prompts', 'stats'],
    queryFn: () => api.getPromptStats(),
  })

  // Generate new prompt mutation
  const generateMutation = useMutation({
    mutationFn: (params: {
      include_goals: boolean
      include_preferences: boolean
      include_emotions: boolean
    }) => api.generatePrompt(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })

  // Save prompt mutation
  const saveMutation = useMutation({
    mutationFn: (promptData: PromptData) => api.savePrompt(promptData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })

  // Activate prompt mutation
  const activateMutation = useMutation({
    mutationFn: (versionId: string) => api.activatePrompt(versionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
      setSelectedVersion(null)
    },
  })

  const [generatedPrompt, setGeneratedPrompt] = useState<PromptData | null>(null)

  const handleGeneratePrompt = async () => {
    const result = await generateMutation.mutateAsync({
      include_goals: true,
      include_preferences: true,
      include_emotions: true,
      max_length: 3000  // Allow longer prompts (2539 chars needed)
    })
    setGeneratedPrompt(result)
    setShowFullPrompt(true)
  }

  const handleSavePrompt = async () => {
    if (!generatedPrompt) return
    await saveMutation.mutateAsync(generatedPrompt)
    setGeneratedPrompt(null)
  }

  const handleActivateVersion = async (versionId: string) => {
    if (confirm('Activate this prompt version for production use?')) {
      await activateMutation.mutateAsync(versionId)
    }
  }

  const handleCopyPrompt = async (promptText: string) => {
    try {
      await navigator.clipboard.writeText(promptText)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000) // Reset after 2 seconds
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  if (isLoadingCurrent) {
    return (
      <div className="flex items-center justify-center min-h-screen dark:bg-gray-950">
        <div className="text-center">
          <Sparkles className="w-16 h-16 text-accent-500 dark:text-accent-400 animate-pulse mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading prompt manager...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <Sparkles className="w-8 h-8 text-accent-500" />
              Prompt Manager
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Optimize Angela's system prompts for mobile app
            </p>
          </div>
          <Button
            onClick={handleGeneratePrompt}
            disabled={generateMutation.isPending}
            className="bg-accent-500 hover:bg-accent-600 text-white"
          >
            {generateMutation.isPending ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Generate New Prompt
              </>
            )}
          </Button>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Total Versions</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stats.total_versions}
                    </p>
                  </div>
                  <FileText className="w-8 h-8 text-accent-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Active Version</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stats.active_version || 'None'}
                    </p>
                  </div>
                  <Check className="w-8 h-8 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Avg Length</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stats.avg_length} chars
                    </p>
                  </div>
                  <Settings className="w-8 h-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Model Target</p>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      Foundation Models
                    </p>
                  </div>
                  <Sparkles className="w-8 h-8 text-purple-500" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Current Active Prompt */}
        {currentPrompt && currentPrompt.prompt_text && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-500" />
                Current Active Prompt
                <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
                  (v{currentPrompt.version})
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Length</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {currentPrompt.prompt_text?.length || 0} chars
                  </p>
                </div>
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Components</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {currentPrompt.components.length}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Model</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {currentPrompt.model_target}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Created</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {formatRelativeTime(currentPrompt.created_at)}
                  </p>
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Components:
                </p>
                <div className="flex flex-wrap gap-2">
                  {currentPrompt.components.map((component) => (
                    <span
                      key={component}
                      className="px-3 py-1 bg-accent-100 dark:bg-accent-900 text-accent-700 dark:text-accent-300 rounded-full text-sm"
                    >
                      {component}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <div className="flex gap-2 mb-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowFullPrompt(!showFullPrompt)}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    {showFullPrompt ? 'Hide' : 'Show'} Full Prompt
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleCopyPrompt(currentPrompt.prompt_text)}
                    className={copySuccess ? 'bg-green-50 dark:bg-green-900 border-green-500' : ''}
                  >
                    <Copy className="w-4 h-4 mr-2" />
                    {copySuccess ? 'Copied!' : 'Copy Prompt'}
                  </Button>
                </div>

                {showFullPrompt && (
                  <pre className="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg overflow-auto max-h-96 text-sm text-gray-800 dark:text-gray-200">
                    {currentPrompt.prompt_text}
                  </pre>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Generated Prompt Preview */}
        {generatedPrompt && (
          <Card className="border-2 border-accent-500">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-accent-500" />
                Newly Generated Prompt (Not Saved)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Length</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {generatedPrompt.length} chars
                  </p>
                </div>
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Components</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {generatedPrompt.components.length}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Model Target</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {generatedPrompt.model_target}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Generated</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {formatRelativeTime(generatedPrompt.generated_at)}
                  </p>
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Components:
                </p>
                <div className="flex flex-wrap gap-2">
                  {generatedPrompt.components.map((component) => (
                    <span
                      key={component}
                      className="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full text-sm"
                    >
                      {component}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <pre className="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg overflow-auto max-h-96 text-sm text-gray-800 dark:text-gray-200">
                  {generatedPrompt.prompt}
                </pre>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleSavePrompt}
                  disabled={saveMutation.isPending}
                  className="bg-green-500 hover:bg-green-600 text-white"
                >
                  {saveMutation.isPending ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4 mr-2" />
                      Save to Database
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setGeneratedPrompt(null)}
                >
                  Discard
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Prompt Versions History */}
        <Card>
          <CardHeader>
            <CardTitle>Prompt Versions History</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoadingVersions ? (
              <p className="text-gray-600 dark:text-gray-400">Loading versions...</p>
            ) : versions && versions.length > 0 ? (
              <div className="space-y-3">
                {versions.map((version) => (
                  <div
                    key={version.version_id}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:border-accent-500 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold text-gray-900 dark:text-white">
                            Version {version.version}
                          </h3>
                          <span className="text-sm text-gray-500 dark:text-gray-400">
                            {formatRelativeTime(version.created_at)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                          {version.preview}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {version.components.map((component) => (
                            <span
                              key={component}
                              className="px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded text-xs"
                            >
                              {component}
                            </span>
                          ))}
                        </div>
                        {version.notes && (
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 italic">
                            Note: {version.notes}
                          </p>
                        )}
                      </div>
                      <Button
                        onClick={() => handleActivateVersion(version.version_id)}
                        disabled={activateMutation.isPending}
                        className="ml-4 bg-green-600 hover:bg-green-700 text-white font-semibold px-6 py-2 shadow-lg"
                      >
                        <Check className="w-5 h-5 mr-2" />
                        Activate
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600 dark:text-gray-400">No versions found</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
