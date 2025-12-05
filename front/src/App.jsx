import { useEffect, useMemo, useRef, useState } from 'react'
import './styles/App.css'

const initialMessages = [
  { role: 'assistant', content: '안녕하세요! 내용을 입력하시면 적절한 문장인지 판단해드릴게요.' },
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
      // 🔹 여기서 백엔드(8000 포트)로 직접 요청
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: nextMessages }),
      })

      if (!response.ok) {
        throw new Error('응답을 가져오지 못했습니다.')
      }

      const data = await response.json()

      // 🔹 백엔드 ChatResponse: { role, content, is_safe, raw_decision }
      const reply = data?.content ?? '답변을 가져오지 못했습니다.'

      // 필터 결과에 따라 부가 메시지 붙이고 싶으면 이렇게
      const extra =
        data?.is_safe === false
          ? ' (필터에 의해 부적절한 표현으로 판단되었습니다.)'
          : ''

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: reply + extra },
      ])
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
          <p className="app__eyebrow">Local LLM FILTER</p>
          <h1 className="app__title">필터링 LLM</h1>
          <p className="app__subtitle">로컬에서 구동되는 필터링 LLM을 이용해보세요.</p>
        </div>
      </header>

      <main className="chat">
        <div className="chat__messages" role="log" aria-live="polite">
          {messages.map((message, index) => (
            <article
              key={`${message.role}-${index}`}
              className={`chat__message chat__message--${message.role}`}
            >
              <div className="chat__meta">
                {message.role === 'user' ? '나' : '봇'}
              </div>
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
              placeholder="봇이 검열할 문장을 입력하세요"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              rows={3}
              disabled={isLoading}
            />
            <button
              className="chat__submit"
              type="submit"
              disabled={!trimmedInput || isLoading}
            >
              {isLoading ? '전송 중...' : '보내기'}
            </button>
          </div>
          {error && <p className="chat__error">{error}</p>}
          <p className="chat__hint">
            백엔드: http://localhost:8000/api/chat 에 연결되어 있어요.
          </p>
        </form>
      </main>
    </div>
  )
}

export default App
