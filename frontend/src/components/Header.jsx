import React from 'react'

export default function Header({ apiMode }) {
  return (
    <header style={{
      background: 'var(--surf)',
      borderBottom: '1px solid var(--bdr)',
      padding: '1.6rem 2.5rem 1.4rem',
      position: 'relative',
      overflow: 'hidden',
      boxShadow: 'var(--shadow)',
    }}>
      {/* Subtle blue glow top-left */}
      <div style={{
        position: 'absolute', top: -80, left: -60,
        width: 320, height: 320,
        background: 'radial-gradient(circle, rgba(37,99,235,.06) 0%, transparent 70%)',
        borderRadius: '50%', pointerEvents: 'none',
      }} />
      {/* Decorative sigma */}
      <div style={{
        position: 'absolute', right: '2.5rem', top: '50%',
        transform: 'translateY(-50%)',
        fontFamily: "'Syne', sans-serif", fontSize: '7rem', fontWeight: 800,
        color: 'rgba(37,99,235,.05)', lineHeight: 1,
        pointerEvents: 'none', userSelect: 'none',
      }}>∑</div>

      <div style={{ position: 'relative' }}>
        <p style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '.62rem', letterSpacing: '3px', textTransform: 'uppercase',
          color: 'var(--accent)', marginBottom: '.35rem', fontWeight: 500,
        }}>AI-Powered · Math Error Analysis</p>

        <h1 style={{
          fontFamily: "'Syne', sans-serif",
          fontSize: '2.2rem', fontWeight: 800,
          color: 'var(--text)', letterSpacing: '-1px',
          lineHeight: 1, marginBottom: '.35rem',
        }}>
          Algebra<em style={{ fontStyle: 'normal', color: 'var(--accent)' }}>Check</em>
        </h1>

        <p style={{ fontSize: '.87rem', color: 'var(--muted)', fontWeight: 400 }}>
          Detect algebraic errors · Classify misconceptions · Generate corrections
        </p>

        <div style={{ display: 'flex', gap: '.4rem', marginTop: '.8rem', flexWrap: 'wrap' }}>
          {['SymPy Engine', 'Step Validation', 'Misconception Taxonomy', 'Auto Correction'].map(t => (
            <span key={t} style={{
              background: 'var(--acc-light)',
              border: '1px solid rgba(37,99,235,.15)',
              color: 'var(--accent)', fontSize: '.63rem', fontWeight: 500,
              padding: '.2rem .7rem', borderRadius: 20,
              fontFamily: "'JetBrains Mono', monospace",
            }}>{t}</span>
          ))}
          {apiMode && (
            <span style={{
              background: 'var(--green-bg)',
              border: '1px solid rgba(5,150,105,.2)',
              color: 'var(--green)', fontSize: '.63rem', fontWeight: 500,
              padding: '.2rem .7rem', borderRadius: 20,
              fontFamily: "'JetBrains Mono', monospace",
            }}>
              {apiMode && apiMode.startsWith('full') ? '✦ Groq Active' : '⚡ Rule-Based Mode'}
            </span>
          )}
        </div>
      </div>
    </header>
  )
}
