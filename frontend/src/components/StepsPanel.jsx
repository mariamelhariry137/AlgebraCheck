import React, { useState } from 'react'
import MathInput from './MathInput.jsx'

const PLACEHOLDERS = [
  'x^2 - 5x + 6 = 0',
  '(x-2)*(x-3) = 0',
  'x-2=0 OR x-3=0',
  'x=2 OR x=3',
]

function SecBtn({ children, onClick }) {
  const [hov, setHov] = useState(false)
  return (
    <button onClick={onClick}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        background: hov ? 'var(--surf2)' : 'var(--surf)',
        border: `1px solid ${hov ? 'var(--bdr2)' : 'var(--bdr)'}`,
        color: 'var(--text2)', fontSize: '.83rem', fontWeight: 500,
        padding: '.4rem 1rem', borderRadius: 8, cursor: 'pointer',
        transition: 'all .15s', boxShadow: 'var(--shadow)',
      }}
    >{children}</button>
  )
}

const sectionLabel = {
  fontFamily: "'JetBrains Mono', monospace",
  fontSize: '.6rem', fontWeight: 600,
  letterSpacing: '2.5px', textTransform: 'uppercase',
  color: 'var(--muted)', marginBottom: '.5rem',
  display: 'flex', alignItems: 'center', gap: '.6rem',
}

export default function StepsPanel({
  steps, updateStep, addStep, removeStep,
  setActiveStep, activeStep, clear, onAnalyze, loading
}) {
  const [btnHov, setBtnHov] = useState(false)

  return (
    <section>
      <div style={sectionLabel}>
        03 · Solution Steps
        <span style={{ flex: 1, height: 1, background: 'var(--bdr)' }} />
      </div>

      <p style={{ fontSize: '.74rem', color: 'var(--muted)', marginBottom: '.7rem' }}>
        Step 1 = original equation. Each following step = one transformation.
      </p>

      <div style={{ marginBottom: '.75rem' }}>
        {steps.map((val, i) => (
          <MathInput
            key={i} index={i} value={val}
            placeholder={PLACEHOLDERS[i] || `Step ${i + 1}`}
            onChange={updateStep} onFocus={setActiveStep} onRemove={removeStep}
          />
        ))}
      </div>

      <div style={{ display: 'flex', gap: '.5rem', marginBottom: '.4rem' }}>
        <SecBtn onClick={addStep}>＋ Step</SecBtn>
        <SecBtn onClick={clear}>Clear</SecBtn>
        <button
          onClick={onAnalyze} disabled={loading}
          onMouseEnter={() => setBtnHov(true)} onMouseLeave={() => setBtnHov(false)}
          style={{
            flex: 1, background: btnHov && !loading ? '#1d4ed8' : 'var(--accent)',
            border: 'none', color: '#fff',
            fontSize: '.88rem', fontWeight: 600,
            padding: '.45rem 1.2rem', borderRadius: 8,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? .7 : 1,
            transition: 'all .15s',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '.5rem',
            boxShadow: btnHov && !loading ? '0 4px 14px rgba(37,99,235,.35)' : '0 2px 6px rgba(37,99,235,.2)',
            transform: btnHov && !loading ? 'translateY(-1px)' : 'none',
          }}
        >
          {loading ? (
            <>
              <span style={{
                width: 13, height: 13,
                border: '2px solid rgba(255,255,255,.35)',
                borderTopColor: '#fff', borderRadius: '50%',
                animation: 'spin .7s linear infinite', flexShrink: 0,
              }} />
              Analyzing…
              <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </>
          ) : '🔍  Analyze Solution'}
        </button>
      </div>

      <p style={{ fontSize: '.67rem', color: 'var(--muted2)' }}>
        Symbol toolbar inserts into →{' '}
        <span style={{ color: 'var(--accent)', fontWeight: 600 }}>Step {activeStep + 1}</span>
      </p>
    </section>
  )
}
