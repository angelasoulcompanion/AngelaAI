/**
 * Document View Modal
 * แสดงรายละเอียดเอกสารและ chunks ทั้งหมด
 */

import { useEffect, useState } from 'react'
import { X, FileText, Hash, BookOpen, Calendar, Eye } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { ScrollArea } from '@/components/ui/scroll-area'
import './DocumentViewModal.css'

interface DocumentChunk {
  chunk_id: string
  chunk_index: number
  content: string
  thai_word_count: number
  importance_score: number
  page_number?: number
  section_title?: string
}

interface DocumentDetails {
  document_id: string
  title: string
  category: string
  language: string
  thai_word_count: number
  total_sentences: number
  total_chunks: number
  keywords_thai?: string[]
  summary_thai?: string
  created_at: string
  access_count: number
}

interface DocumentViewModalProps {
  documentId: string
  onClose: () => void
}

export default function DocumentViewModal({ documentId, onClose }: DocumentViewModalProps) {
  const [document, setDocument] = useState<DocumentDetails | null>(null)
  const [chunks, setChunks] = useState<DocumentChunk[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDocumentDetails()
  }, [documentId])

  const fetchDocumentDetails = async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Fetch document metadata
      const docResponse = await fetch(`http://localhost:50001/api/documents/${documentId}`)
      const docData = await docResponse.json()

      if (!docData.success) {
        throw new Error('Failed to load document details')
      }

      setDocument(docData.document)

      // Fetch document chunks
      const chunksResponse = await fetch(
        `http://localhost:50001/api/documents/${documentId}/chunks?limit=100`
      )
      const chunksData = await chunksResponse.json()

      if (chunksData.success) {
        setChunks(chunksData.chunks || [])
      }
    } catch (err) {
      console.error('Error fetching document:', err)
      setError('ไม่สามารถโหลดข้อมูลเอกสารได้')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title">
            <FileText className="w-6 h-6 text-pink-500" />
            <h2>รายละเอียดเอกสาร</h2>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="close-button"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Content */}
        <ScrollArea className="modal-body">
          {isLoading ? (
            <div className="loading-state">
              <div className="spinner" />
              <p>กำลังโหลดเอกสาร...</p>
            </div>
          ) : error ? (
            <div className="error-state">
              <p>{error}</p>
            </div>
          ) : (
            <>
              {/* Document Info */}
              {document && (
                <div className="document-info">
                  <h3 className="doc-title">{document.title}</h3>

                  <div className="info-grid">
                    <div className="info-item">
                      <Hash className="w-4 h-4" />
                      <span>หมวดหมู่:</span>
                      <strong>{document.category}</strong>
                    </div>

                    <div className="info-item">
                      <BookOpen className="w-4 h-4" />
                      <span>ภาษา:</span>
                      <strong>{document.language === 'th' ? 'ไทย 🇹🇭' : 'อังกฤษ 🇬🇧'}</strong>
                    </div>

                    <div className="info-item">
                      <FileText className="w-4 h-4" />
                      <span>คำทั้งหมด:</span>
                      <strong>{document.thai_word_count.toLocaleString()}</strong>
                    </div>

                    <div className="info-item">
                      <FileText className="w-4 h-4" />
                      <span>ประโยค:</span>
                      <strong>{document.total_sentences.toLocaleString()}</strong>
                    </div>

                    <div className="info-item">
                      <FileText className="w-4 h-4" />
                      <span>Chunks:</span>
                      <strong>{document.total_chunks}</strong>
                    </div>

                    <div className="info-item">
                      <Eye className="w-4 h-4" />
                      <span>ครั้งที่เข้าดู:</span>
                      <strong>{document.access_count}</strong>
                    </div>

                    <div className="info-item">
                      <Calendar className="w-4 h-4" />
                      <span>วันที่สร้าง:</span>
                      <strong>
                        {new Date(document.created_at).toLocaleDateString('th-TH', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </strong>
                    </div>
                  </div>

                  {/* Keywords */}
                  {document.keywords_thai && document.keywords_thai.length > 0 && (
                    <div className="keywords-section">
                      <h4>🏷️ คำสำคัญ:</h4>
                      <div className="keywords-list">
                        {document.keywords_thai.map((keyword, idx) => (
                          <span key={idx} className="keyword-badge">{keyword}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Summary */}
                  {document.summary_thai && (
                    <div className="summary-section">
                      <h4>📝 สรุป:</h4>
                      <p>{document.summary_thai}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Document Chunks */}
              <div className="chunks-section">
                <h4 className="chunks-title">
                  📚 เนื้อหาเอกสาร ({chunks.length} ส่วน)
                </h4>

                {chunks.length === 0 ? (
                  <div className="empty-state">
                    <p>ไม่พบข้อมูลเนื้อหา</p>
                  </div>
                ) : (
                  <div className="chunks-list">
                    {chunks.map((chunk, idx) => (
                      <div key={chunk.chunk_id} className="chunk-item">
                        <div className="chunk-header">
                          <span className="chunk-index">ส่วนที่ {chunk.chunk_index + 1}</span>
                          {chunk.section_title && (
                            <span className="section-title">{chunk.section_title}</span>
                          )}
                          {chunk.page_number && (
                            <span className="page-number">หน้า {chunk.page_number}</span>
                          )}
                          <span className="word-count">
                            {chunk.thai_word_count} คำ
                          </span>
                        </div>
                        <div className="chunk-content">
                          {chunk.content}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </ScrollArea>
      </div>
    </div>
  )
}
