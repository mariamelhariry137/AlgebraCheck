import React, { useRef, useEffect, useCallback, useState } from 'react'
import { prettifyHTML } from '../utils/math.js'

export default function MathInput({ index, value, placeholder, onChange, onFocus, onRemove }) {
  const inputRef   = useRef(null)
  const overlayRef = useRef(null)
  const [focused, setFocused] = useState(false)

  const syncOverlay = useCallback(() => {
    const inp = inputRef.current
    const ovl = overlayRef.current
    if (!inp || !ovl) return
    ovl.innerHTML = value ? prettifyHTML(value) : ''
    ovl.style.transform = `translateX(-${inp.scrollLeft}px)`
    inp.style.color = value ? 'transparent' : 'var(--text)'
    inp.style.webkitTextFillColor = value ? 'transparent' : 'var(--text)'
  }, [value])

  useEffect(() => { syncOverlay() }, [syncOverlay])

  const handleScroll = () => {
    if (overlayRef.current && inputRef.current)
      overlayRef.current.style.transform = `translateX(-${inputRef.current.scrollLeft}px)`
  }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '.5rem',
      background: 'var(--surf)',
      border: `1px solid ${focused ? 'var(--accent)' : 'var(--bdr)'}`,
      borderRadius: 10, padding: '.4rem .55rem',
      marginBottom: '.4rem',
      boxShadow: focused ? '0 0 0 3px rgba(37,99,235,.1)' : 'var(--shadow)',
      transition: 'border-color .15s, box-shadow .15s',
    }}>
      {/* Badge */}
      <div style={{
        background: focused ? 'var(--acc-light)' : 'var(--surf2)',
        border: `1px solid ${focused ? 'rgba(37,99,235,.2)' : 'var(--bdr)'}`,
        color: focused ? 'var(--accent)' : 'var(--muted)',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '.67rem', fontWeight: 600,
        width: 24, height: 24, borderRadius: 6,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0, transition: 'all .15s',
      }}>{index + 1}</div>

      {/* Input + overlay */}
      <div style={{ flex: 1, position: 'relative', height: 32 }}>
        <div
          ref={overlayRef}
          aria-hidden="true"
          style={{
            position: 'absolute', inset: 0,
            padding: '0 .4rem',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '.88rem', lineHeight: '32px',
            color: 'var(--text)',
            pointerEvents: 'none', whiteSpace: 'nowrap',
            overflow: 'hidden', zIndex: 2,
          }}
        />
        <input
          ref={inputRef}
          value={value}
          placeholder={placeholder}
          onChange={e => onChange(index, e.target.value)}
          onFocus={() => { setFocused(true); onFocus(index) }}
          onBlur={() => setFocused(false)}
          onScroll={handleScroll}
          spellCheck={false}
          autoComplete="off"
          style={{
            position: 'absolute', inset: 0,
            background: 'transparent', border: 'none', outline: 'none',
            fontFamily: "'JetBrains Mono', monospace", fontSize: '.88rem',
            color: value ? 'transparent' : 'var(--text)',
            WebkitTextFillColor: value ? 'transparent' : 'var(--text)',
            padding: '0 .4rem', whiteSpace: 'nowrap',
            overflowX: 'auto', caretColor: 'var(--accent)', zIndex: 1,
          }}
        />

      </div>

      {/* Remove */}
      <button
        onClick={() => onRemove(index)}
        title="Remove step"
        style={{
          background: 'transparent', border: 'none',
          color: 'var(--muted2)', fontSize: '.72rem',
          width: 22, height: 22, borderRadius: 5,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, cursor: 'pointer', transition: 'all .15s',
        }}
        onMouseEnter={e => { e.currentTarget.style.color = 'var(--red)'; e.currentTarget.style.background = 'var(--red-bg)' }}
        onMouseLeave={e => { e.currentTarget.style.color = 'var(--muted2)'; e.currentTarget.style.background = 'transparent' }}
      >✕</button>
    </div>
  )
}