import React, { useState } from 'react'

const ROW1 = [
  { label: 'x²', value: 'x²' },
  { label: 'x³', value: 'x³' },
  { label: '√()', value: '√()' },
  { label: '()', value: '()' },
  { label: 'OR', value: ' OR ' },
]
const ROW2 = [
  { label: '=0', value: ' = 0' },
  { label: '±',  value: '±' },
  { label: '+',  value: '+' },
  { label: '−',  value: ' − ' },
  { label: '·',  value: '·' },
]

function SymBtn({ label, value, onInsert }) {
  const [hov, setHov] = useState(false)
  return (
    <button
      onClick={() => onInsert(value)}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        flex: 1,
        background: hov ? 'var(--accent)' : 'var(--surf)',
        border: `1px solid ${hov ? 'var(--accent)' : 'var(--bdr)'}`,
        color: hov ? '#fff' : 'var(--text2)',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '.82rem', fontWeight: 500,
        padding: '.35rem .5rem', borderRadius: 7,
        cursor: 'pointer', transition: 'all .12s',
        transform: hov ? 'translateY(-1px)' : 'none',
        boxShadow: hov ? '0 2px 8px rgba(37,99,235,.25)' : 'var(--shadow)',
        whiteSpace: 'nowrap',
      }}
    >{label}</button>
  )
}

const code = {
  background: 'var(--surf2)', border: '1px solid var(--bdr)',
  color: 'var(--accent)', padding: '.02rem .3rem', borderRadius: 4,
  fontFamily: "'JetBrains Mono', monospace", fontSize: '.67rem',
}

export default function SymbolToolbar({ onInsert, activeTarget }) {
  const targetLabel = activeTarget === 'problem'
    ? 'Problem input'
    : `Step ${(activeTarget ?? 0) + 1}`

  return (
    <section style={{ marginBottom: '1.4rem' }}>
      <div style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '.6rem', fontWeight: 600,
        letterSpacing: '2.5px', textTransform: 'uppercase',
        color: 'var(--muted)', marginBottom: '.65rem',
        display: 'flex', alignItems: 'center', gap: '.6rem',
      }}>
        02 · Symbol Toolbar
        <span style={{ flex: 1, height: 1, background: 'var(--bdr)' }} />
      </div>

      <div style={{
        background: 'var(--surf)', border: '1px solid var(--bdr)',
        borderRadius: 12, padding: '.85rem 1rem .75rem',
        boxShadow: 'var(--shadow)',
      }}>
        <div style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '.58rem', letterSpacing: '2px',
          textTransform: 'uppercase', color: 'var(--muted2)',
          marginBottom: '.6rem',
        }}>
          Inserts into →{' '}
          <span style={{ color: 'var(--accent)', fontWeight: 700 }}>{targetLabel}</span>
        </div>

        <div style={{ display: 'flex', gap: '.3rem', marginBottom: '.3rem' }}>
          {ROW1.map(s => <SymBtn key={s.label} {...s} onInsert={onInsert} />)}
        </div>
        <div style={{ display: 'flex', gap: '.3rem', marginBottom: '.65rem' }}>
          {ROW2.map(s => <SymBtn key={s.label} {...s} onInsert={onInsert} />)}
        </div>

        <p style={{ fontSize: '.69rem', color: 'var(--muted2)', lineHeight: 1.6 }}>
          Type <code style={code}>x^2</code> or click <code style={code}>x²</code>
          &nbsp;·&nbsp; <code style={code}>sqrt(</code> or click <code style={code}>√()</code>
          &nbsp;·&nbsp; <code style={code}>(x-2)*(x-3)</code> → (x−2)·(x−3)
        </p>
      </div>
    </section>
  )
}