import { useEffect, useMemo, useRef, useState } from 'react'
import './styles/App.css'

const initialMessages = [
  { role: 'assistant', content: '안녕하세요! 궁금한 내용을 입력하면 바로 답변해드릴게요.' },
]

function App() {
  const [messages, setMessages] = useState(initialMessages)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const endRef = useRef(null)

  const trimmedInput = useMemo(() => input.trim(), [input])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!trimmedInput || isLoading) return

    const nextMessages = [...messages, { role: 'user', content: trimmedInput }]
    setMessages(nextMessages)
    setInput('')
    setError('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: nextMessages }),
      })

      if (!response.ok) {
        throw new Error('응답을 가져오지 못했습니다.')
      }

      const data = await response.json()
      const reply = data?.reply ?? data?.message ?? '답변을 가져오지 못했습니다.'
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }])
    } catch (fetchError) {
      console.error(fetchError)
      setError('메시지를 보내지 못했어요. 서버 상태를 확인해주세요.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <p className="app__eyebrow">Local LLM Chat</p>
          <h1 className="app__title">나만의 챗봇</h1>
          <p className="app__subtitle">로컬에서 구동되는 LLM과 대화해보세요.</p>
        </div>
      </header>

      <main className="chat">
        <div className="chat__messages" role="log" aria-live="polite">
          {messages.map((message, index) => (
            <article
              key={`${message.role}-${index}`}
              className={`chat__message chat__message--${message.role}`}
            >
              <div className="chat__meta">{message.role === 'user' ? '나' : '봇'}</div>
              <p className="chat__bubble">{message.content}</p>
            </article>
          ))}
          <div ref={endRef} />
        </div>

        <form className="chat__form" onSubmit={handleSubmit}>
          <label className="chat__label" htmlFor="chat-input">
            메시지를 입력하세요
          </label>
          <div className="chat__input-row">
            <textarea
              id="chat-input"
              className="chat__input"
              placeholder="로컬 LLM에게 질문을 던져보세요"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              rows={3}
              disabled={isLoading}
            />
            <button className="chat__submit" type="submit" disabled={!trimmedInput || isLoading}>
              {isLoading ? '전송 중...' : '보내기'}
            </button>
          </div>
          {error && <p className="chat__error">{error}</p>}
          <p className="chat__hint">/api/chat 엔드포인트와 연결되어 있어요. 서버가 실행 중인지 확인해주세요.</p>
        </form>
      </main>
    </div>
  )
}

export default App
