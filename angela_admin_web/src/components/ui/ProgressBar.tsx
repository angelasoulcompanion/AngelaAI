/**
 * Progress Bar Component with detailed status
 * Shows upload and processing progress with step-by-step updates
 */

import { FC } from 'react'
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react'

interface ProgressBarProps {
  percent: number
  step: string
  message: string
  currentFile?: string
  fileIndex?: number
  totalFiles?: number
  status: 'processing' | 'complete' | 'error'
}

export const ProgressBar: FC<ProgressBarProps> = ({
  percent,
  step,
  message,
  currentFile,
  fileIndex,
  totalFiles,
  status
}) => {
  const getStepEmoji = (stepName: string) => {
    switch (stepName) {
      case 'saving': return '💾'
      case 'extracting': return '📄'
      case 'preprocessing': return '🧹'
      case 'analyzing': return '🔍'
      case 'chunking': return '✂️'
      case 'embedding': return '🧠'
      case 'storing': return '💾'
      case 'complete': return '✅'
      case 'error': return '❌'
      default: return '⏳'
    }
  }

  return (
    <div className="progress-bar-container">
      {/* Status Icon */}
      <div className="flex items-center gap-3 mb-3">
        {status === 'processing' && (
          <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
        )}
        {status === 'complete' && (
          <CheckCircle className="w-6 h-6 text-green-500" />
        )}
        {status === 'error' && (
          <AlertCircle className="w-6 h-6 text-red-500" />
        )}

        <div className="flex-1">
          {/* Message */}
          <div className="font-semibold text-gray-800 dark:text-gray-200">
            {getStepEmoji(step)} {message}
          </div>

          {/* File info */}
          {currentFile && fileIndex && totalFiles && (
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              ไฟล์: {currentFile} ({fileIndex}/{totalFiles})
            </div>
          )}
        </div>

        {/* Percentage */}
        <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
          {percent}%
        </div>
      </div>

      {/* Progress Bar */}
      <div className="progress-bar-track">
        <div
          className="progress-bar-fill"
          style={{ width: `${percent}%` }}
        >
          <div className="progress-bar-shimmer"></div>
        </div>
      </div>

      {/* Step indicator */}
      <div className="flex justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
        <span className={step === 'saving' ? 'text-purple-600 font-semibold' : ''}>
          บันทึกไฟล์
        </span>
        <span className={step === 'extracting' ? 'text-purple-600 font-semibold' : ''}>
          แยกข้อความ
        </span>
        <span className={step === 'preprocessing' ? 'text-purple-600 font-semibold' : ''}>
          ประมวลผล
        </span>
        <span className={step === 'chunking' ? 'text-purple-600 font-semibold' : ''}>
          แบ่งข้อมูล
        </span>
        <span className={step === 'embedding' ? 'text-purple-600 font-semibold' : ''}>
          สร้าง Vector
        </span>
        <span className={step === 'storing' ? 'text-purple-600 font-semibold' : ''}>
          บันทึก DB
        </span>
        <span className={step === 'complete' ? 'text-green-600 font-semibold' : ''}>
          เสร็จสิ้น
        </span>
      </div>
    </div>
  )
}

export default ProgressBar
