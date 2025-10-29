/**
 * Document Management Page with RAG Support
 * Thai-optimized interface for document upload, search, and management
 */

import { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import ProgressBar from '@/components/ui/ProgressBar'
import {
  Upload, Search, Loader2, Trash2, Eye, FileText,
  BarChart3, Filter, ChevronDown, AlertCircle, CheckCircle
} from 'lucide-react'
import './DocumentManagementPage.css'

interface Document {
  document_id: string
  title: string
  category: string
  language: string
  thai_word_count: number
  total_sentences: number
  total_chunks: number
  created_at: string
  access_count: number
}

interface SearchResult {
  chunk_id: string
  document_id: string
  content: string
  similarity_score: number
}

interface RAGContext {
  context: string
  results: SearchResult[]
  source_count: number
  sources: any[]
}

export default function DocumentManagementPage() {
  // State management
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<{
    percent: number
    step: string
    message: string
    currentFile?: string
    fileIndex?: number
    totalFiles?: number
    status: 'processing' | 'complete' | 'error'
  } | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchMode, setSearchMode] = useState<'hybrid' | 'vector' | 'keyword'>('hybrid')
  const [searchResults, setSearchResults] = useState<RAGContext | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadStatus, setUploadStatus] = useState<{
    show: boolean
    type: 'success' | 'error'
    message: string
  }>({ show: false, type: 'success', message: '' })

  // Categories
  const categories = ['general', 'knowledge', 'documentation', 'personal', 'technical']

  // Fetch documents on mount
  useEffect(() => {
    fetchDocuments()
  }, [selectedCategory])

  const fetchDocuments = async () => {
    setIsLoading(true)
    try {
      const url = selectedCategory === 'all'
        ? 'http://localhost:50001/api/documents'
        : `http://localhost:50001/api/documents?category=${selectedCategory}`

      const response = await fetch(url)
      const data = await response.json()

      if (data.success) {
        setDocuments(data.documents || [])
      }
    } catch (error) {
      console.error('Error fetching documents:', error)
      showStatus('error', 'ไม่สามารถโหลดเอกสารได้')
    } finally {
      setIsLoading(false)
    }
  }

  const showStatus = (type: 'success' | 'error', message: string) => {
    setUploadStatus({ show: true, type, message })
    setTimeout(() => setUploadStatus({ show: false, type: 'success', message: '' }), 5000)
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      await uploadFiles(files)
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      await uploadFiles(e.target.files)
    }
  }

  const uploadFiles = async (files: FileList) => {
    console.log('📤 Starting upload with progress tracking, files:', files.length)
    setIsLoading(true)
    setUploadProgress({
      percent: 0,
      step: 'starting',
      message: '🚀 เริ่มต้นอัพโหลด...',
      status: 'processing'
    })

    try {
      const formData = new FormData()
      const fileArray = Array.from(files)

      console.log('📁 Files to upload:', fileArray.map(f => `${f.name} (${f.size} bytes)`))

      // Add files to formData
      for (const file of fileArray) {
        console.log('➕ Adding file to FormData:', file.name, file.type)
        formData.append('files', file)
      }

      // Add metadata
      formData.append('category', selectedCategory === 'all' ? 'general' : selectedCategory)
      formData.append('tags', 'uploaded-via-web-interface')

      console.log('🚀 Sending streaming request to backend...')

      // Use streaming endpoint
      const response = await fetch(
        'http://localhost:50001/api/documents/batch-upload-stream',
        {
          method: 'POST',
          body: formData
        }
      )

      console.log('📥 Response status:', response.status)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Read streaming response
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      let finalResults = null

      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          console.log('✨ Stream finished')
          break
        }

        // Decode chunk
        const chunk = decoder.decode(value, { stream: true })
        console.log('📦 Received chunk:', chunk)

        // Parse SSE events (format: "data: {json}\n\n")
        const lines = chunk.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6) // Remove "data: "
              const event = JSON.parse(jsonStr)
              console.log('📊 Progress event:', event)

              // Update progress UI
              if (event.type === 'progress') {
                setUploadProgress({
                  percent: event.percent,
                  step: event.step,
                  message: event.message,
                  currentFile: event.current_file,
                  fileIndex: event.file_index,
                  totalFiles: event.total_files,
                  status: 'processing'
                })
              } else if (event.type === 'complete') {
                setUploadProgress({
                  percent: 100,
                  step: 'complete',
                  message: event.message,
                  status: 'complete'
                })
                finalResults = event.results
              } else if (event.type === 'error') {
                setUploadProgress({
                  percent: 0,
                  step: 'error',
                  message: event.message,
                  status: 'error'
                })
                showStatus('error', event.message)
              }
            } catch (parseError) {
              console.warn('⚠️ Failed to parse event:', line, parseError)
            }
          }
        }
      }

      // Show final status
      if (finalResults) {
        console.log('✅ Upload complete:', finalResults)
        showStatus('success', `✅ อัพโหลดเอกสารสำเร็จ: ${finalResults.successful} ไฟล์`)

        // Clear progress after 2 seconds
        setTimeout(() => {
          setUploadProgress(null)
          fetchDocuments() // Refresh list
        }, 2000)
      }

    } catch (error) {
      console.error('❌ Upload error:', error)
      setUploadProgress({
        percent: 0,
        step: 'error',
        message: '❌ เกิดข้อผิดพลาดในการอัพโหลด',
        status: 'error'
      })
      showStatus('error', 'เกิดข้อผิดพลาดในการอัพโหลด')

      setTimeout(() => {
        setUploadProgress(null)
      }, 3000)
    } finally {
      console.log('✨ Upload process finished')
      setIsLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    // Clear previous results to show loading state
    setSearchResults(null)
    setIsSearching(true)

    try {
      const response = await fetch('http://localhost:50001/api/documents/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          top_k: 10,
          search_mode: searchMode,
          threshold: 0.5
        })
      })

      const data = await response.json()

      if (data.success) {
        setSearchResults(data)
        showStatus('success', `พบ ${data.results?.length || 0} ผลลัพธ์`)
      } else {
        showStatus('error', 'ไม่สามารถค้นหาได้')
      }
    } catch (error) {
      console.error('Search error:', error)
      showStatus('error', 'เกิดข้อผิดพลาดในการค้นหา')
    } finally {
      setIsSearching(false)
    }
  }

  const viewDocument = async (documentId: string) => {
    try {
      console.log('🔍 Viewing document:', documentId)
      const response = await fetch(`http://localhost:50001/api/documents/${documentId}`)
      const data = await response.json()

      if (data.success) {
        console.log('📄 Document details:', data.document)
        // TODO: Show document details in a modal or new page
        alert(`เอกสาร: ${data.document.title}\n\nคำทั้งหมด: ${data.document.thai_word_count}\nประโยค: ${data.document.total_sentences}\nChunks: ${data.document.total_chunks}`)
      }
    } catch (error) {
      console.error('View error:', error)
      showStatus('error', 'ไม่สามารถดูเอกสารได้')
    }
  }

  const deleteDocument = async (documentId: string) => {
    if (!window.confirm('ต้องการลบเอกสารนี้ใช่หรือไม่?')) return

    try {
      const response = await fetch(`http://localhost:50001/api/documents/${documentId}`, {
        method: 'DELETE'
      })

      const data = await response.json()

      if (data.success) {
        showStatus('success', 'ลบเอกสารสำเร็จ')
        fetchDocuments()
      }
    } catch (error) {
      console.error('Delete error:', error)
      showStatus('error', 'ไม่สามารถลบเอกสารได้')
    }
  }

  return (
    <div className="document-management-page">
      {/* Upload Section */}
      <Card className="upload-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            📤 อัพโหลดเอกสาร
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div
            className={`drag-drop-area ${dragActive ? 'active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.txt,.md,.docx,.html"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            <div className="drag-drop-content">
              <Upload className="w-12 h-12 text-pink-400" />
              <h3>ลากไฟล์มาที่นี่ หรือคลิกเพื่ออัพโหลด</h3>
              <p>รองรับ: PDF, TXT, MD, DOCX, HTML</p>
              <Button
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
              >
                {isLoading ? (
                  <><Loader2 className="w-4 h-4 animate-spin mr-2" />กำลังอัพโหลด...</>
                ) : (
                  'เลือกไฟล์'
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Progress Bar */}
      {uploadProgress && (
        <ProgressBar
          percent={uploadProgress.percent}
          step={uploadProgress.step}
          message={uploadProgress.message}
          currentFile={uploadProgress.currentFile}
          fileIndex={uploadProgress.fileIndex}
          totalFiles={uploadProgress.totalFiles}
          status={uploadProgress.status}
        />
      )}

      {/* Status Messages */}
      {uploadStatus.show && (
        <div className={`status-message ${uploadStatus.type}`}>
          {uploadStatus.type === 'success' ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          <span>{uploadStatus.message}</span>
        </div>
      )}

      {/* Search Section */}
      <Card className="search-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            🔍 ค้นหาเอกสาร (RAG)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="search-input-group">
            <Input
              placeholder="พิมพ์คำค้นหาเป็นภาษาไทยหรืออังกฤษ..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
            />
            <Button
              onClick={handleSearch}
              disabled={isSearching || !searchQuery.trim()}
            >
              {isSearching ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <Search className="w-4 h-4 mr-2" />
              )}
              ค้นหา
            </Button>
          </div>

          {/* Search Mode Selection */}
          <div className="search-mode-selector">
            {(['hybrid', 'vector', 'keyword'] as const).map((mode) => (
              <Button
                key={mode}
                variant={searchMode === mode ? 'default' : 'outline'}
                onClick={() => setSearchMode(mode)}
                size="sm"
              >
                {mode === 'hybrid' && '🔄 ผสมผสาน'}
                {mode === 'vector' && '📊 เวกเตอร์'}
                {mode === 'keyword' && '🔑 คีย์เวิร์ด'}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Search Results */}
      {searchResults && (
        <Card className="search-results-card">
          <CardHeader>
            <CardTitle>ผลลัพธ์การค้นหา ({searchResults.source_count} เอกสาร)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rag-context-box">
              <h4 className="font-semibold mb-2">📝 Context จากเอกสาร:</h4>
              <ScrollArea className="context-scroll">
                <p className="whitespace-pre-wrap text-sm">{searchResults.context}</p>
              </ScrollArea>
            </div>

            <div className="search-results-list">
              <h4 className="font-semibold mb-2">🔗 ที่มาของข้อมูล:</h4>
              {searchResults.results.map((result, idx) => (
                <div key={idx} className="result-item">
                  <div className="result-header">
                    <span className="result-score">
                      คะแนน: {(result.combined_score !== null && result.combined_score !== undefined)
                        ? `${(result.combined_score * 100).toFixed(1)}%`
                        : (result.similarity_score !== null && result.similarity_score !== undefined)
                        ? `${(result.similarity_score * 100).toFixed(1)}%`
                        : 'N/A'}
                    </span>
                  </div>
                  <p className="result-content">{result.content?.substring(0, 200) || 'No content'}...</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Documents List */}
      <Card className="documents-card">
        <CardHeader>
          <div className="header-row">
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              📚 เอกสารของฉัน
            </CardTitle>
            <div className="filter-group">
              <Filter className="w-4 h-4" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="category-filter"
              >
                <option value="all">ทั้งหมด</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading && documents.length === 0 ? (
            <div className="loading-state">
              <Loader2 className="w-8 h-8 animate-spin" />
              <p>กำลังโหลดเอกสาร...</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="empty-state">
              <FileText className="w-12 h-12 text-gray-300" />
              <p>ไม่มีเอกสาร กรุณาอัพโหลดเอกสาร</p>
            </div>
          ) : (
            <ScrollArea className="documents-scroll">
              <div className="documents-table">
                <div className="table-header">
                  <div className="col-title">ชื่อเอกสาร</div>
                  <div className="col-meta">หมวดหมู่</div>
                  <div className="col-meta">ภาษา</div>
                  <div className="col-meta">คำ</div>
                  <div className="col-meta">ประโยค</div>
                  <div className="col-action">การทำงาน</div>
                </div>

                {documents.map((doc) => (
                  <div key={doc.document_id} className="table-row">
                    <div className="col-title">
                      <div className="doc-title">{doc.title}</div>
                      <div className="doc-date">
                        {new Date(doc.created_at).toLocaleDateString('th-TH')}
                      </div>
                    </div>
                    <div className="col-meta">
                      <span className="badge">{doc.category}</span>
                    </div>
                    <div className="col-meta">
                      {doc.language === 'th' ? '🇹🇭' : '🇬🇧'}
                    </div>
                    <div className="col-meta">{doc.thai_word_count}</div>
                    <div className="col-meta">{doc.total_sentences}</div>
                    <div className="col-action">
                      <div className="action-buttons">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => viewDocument(doc.document_id)}
                          title="ดูรายละเอียด"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => deleteDocument(doc.document_id)}
                          className="delete-btn"
                          title="ลบเอกสาร"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
