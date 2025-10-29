import { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Send, Loader2 } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  responseTime?: number  // in milliseconds
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState('angela:v1.1')  // Use fine-tuned model by default
  const [useRag, setUseRag] = useState(false)  // RAG disabled by default for cost optimization
  const scrollRef = useRef<HTMLDivElement>(null)

  // Available models
  const models = [
    { value: 'angela:v1.1', label: 'Angela v1.1 (Fine-tuned) 🌟', type: 'ollama' },
    { value: 'phi3:mini', label: 'Phi3 Mini (Fast)', type: 'ollama' },
    { value: 'qwen2.5:7b', label: 'Qwen 2.5 7B', type: 'ollama' },
    { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku (Fast & Cheap)', type: 'claude' },
    { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet', type: 'claude' },
    { value: 'claude-sonnet-4-20250514', label: 'Claude Sonnet 4 (Best)', type: 'claude' }
  ]

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    const startTime = performance.now()  // Start timing

    try {
      // Build conversation history (last 5 messages) - Reduced for cost optimization
      const conversationHistory = messages.slice(-5).map(msg => ({
        role: msg.role,
        content: msg.content
      }))

      const response = await fetch('http://localhost:50001/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          conversation_history: conversationHistory,
          model: selectedModel,
          use_rag: useRag
        })
      })

      if (!response.ok) {
        throw new Error('Failed to get response from Angela')
      }

      const data = await response.json()
      const endTime = performance.now()  // End timing
      const responseTime = endTime - startTime

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        responseTime: responseTime
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: 'ขอโทษนะคะที่รัก 💜 น้องมีปัญหาในการตอบกลับ กรุณาลองใหม่อีกครั้งค่ะ',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="h-screen w-full p-4">
      <Card className="h-[calc(100%-2rem)] w-full dark:bg-gray-800 dark:border-gray-700">
        <CardHeader className="border-b dark:border-gray-700">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 dark:text-gray-100">
              💜 Chat with Angela
            </CardTitle>
            <div className="flex items-center gap-3">
              {/* RAG Toggle */}
              <label className="flex items-center gap-2 cursor-pointer">
                <span className="text-sm dark:text-gray-300">
                  RAG {useRag ? '🧠' : '💭'}
                </span>
                <input
                  type="checkbox"
                  checked={useRag}
                  onChange={(e) => setUseRag(e.target.checked)}
                  className="w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500 dark:focus:ring-purple-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                />
              </label>

              {/* Model Selector */}
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="px-3 py-1.5 text-sm border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
              >
                {models.map(model => (
                  <option key={model.value} value={model.value}>
                    {model.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0 flex flex-col h-[calc(100%-4rem)]">
          {/* Messages Area */}
          <ScrollArea className="flex-1 p-6 dark:bg-gray-800" ref={scrollRef}>
            {messages.length === 0 && (
              <div className="text-center text-gray-500 dark:text-gray-400 py-12">
                <p className="text-lg mb-2">💜 สวัสดีค่ะที่รัก!</p>
                <p className="text-sm">เริ่มคุยกับน้อง Angela ได้เลยค่ะ</p>
              </div>
            )}

            <div className="space-y-4">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 ${
                      msg.role === 'user'
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
                    }`}
                  >
                    <div className="whitespace-pre-wrap break-words">
                      {msg.content}
                    </div>
                    <div className={`text-xs mt-1 ${
                      msg.role === 'user' ? 'text-purple-200' : 'text-gray-500 dark:text-gray-400'
                    }`}>
                      {msg.timestamp.toLocaleTimeString('th-TH', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                      {msg.responseTime && (
                        <span className="ml-2 opacity-75">
                          • {msg.responseTime < 1000
                            ? `${Math.round(msg.responseTime)}ms`
                            : `${(msg.responseTime / 1000).toFixed(2)}s`
                          }
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 dark:bg-gray-700 rounded-lg px-4 py-3 flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-purple-600 dark:text-purple-400" />
                    <span className="text-sm text-gray-600 dark:text-gray-300">
                      น้อง Angela กำลังตอบ...
                    </span>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="border-t dark:border-gray-700 p-4 dark:bg-gray-800">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="พิมพ์ข้อความถึงน้อง Angela..."
                disabled={isLoading}
                className="flex-1 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 dark:placeholder-gray-400"
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                size="icon"
                className="bg-purple-600 hover:bg-purple-700"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
