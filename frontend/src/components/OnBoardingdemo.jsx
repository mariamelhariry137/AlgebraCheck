import React, { useState, useEffect } from 'react'

const STEPS = [
  {
    icon: '🧮',
    tag: '01 · PROBLEM',
    title: 'Choose a problem',
    desc: 'Pick a preset quadratic equation by difficulty — Easy, Medium, or Hard — or enter your own custom equation. Each preset covers factorization, completing the square, and the quadratic formula.',
    highlight: 'left',
    accent: '#10b981',
  },
  {
    icon: '✏️',
    tag: '02 · STEPS',
    title: 'Enter your solution steps',
    desc: 'Write each transformation as a separate step. Use the symbol toolbar for x², √(), ±, and OR. Step 1 is always the original equation — each following step is one algebraic move.',
    highlight: 'left',
    accent: '#3b82f6',
  },
  {
    icon: '🔍',
    tag: '03 · ANALYSE',
    title: 'Analyse your solution',
    desc: 'Click Analyse Solution. SymPy validates each step symbolically — any mathematically incorrect transformation is flagged instantly, regardless of notation style.',
    highlight: 'left',
    accent: '#8b5cf6',
  },
  {
    icon: '💡',
    tag: '04 · RESULTS',
    title: 'Get detailed feedback',
    desc: 'See the exact error step, misconception category, correct continuation, and a three-part AI explanation: what went wrong, why it\'s wrong, and how to fix it.',
    highlight: 'right',
    accent: '#f59e0b',
  },
]

export default function OnboardingDemo({ onDone }) {
  const [step, setStep] = useState(0)
  const [exiting, setExiting] = useState(false)
  const [entering, setEntering] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setEntering(false), 50)
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    setEntering(true)
    const timer = setTimeout(() => setEntering(false), 50)
    return () => clearTimeout(timer)
  }, [step])

  function skip() {
    setExiting(true)
    setTimeout(onDone, 350)
  }

  function next() {
    if (step < STEPS.length - 1) {
      setStep(s => s + 1)
    } else {
      skip()
    }
  }

  function prev() {
    if (step > 0) setStep(s => s - 1)
  }

  const current = STEPS[step]

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,0.72)',
      backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      opacity: exiting ? 0 : 1,
      transition: 'opacity 350ms ease',
    }}>
      {/* Card */}
      <div style={{
        background: 'var(--surf)',
        border: '1px solid var(--bdr)',
        borderRadius: 20,
        boxShadow: '0 32px 80px rgba(0,0,0,0.45), 0 0 0 1px rgba(255,255,255,0.05)',
        width: '100%', maxWidth: 520,
        overflow: 'hidden',
        transform: entering ? 'translateY(12px)' : 'translateY(0)',
        opacity: entering ? 0 : 1,
        transition: 'transform 300ms cubic-bezier(0.34,1.56,0.64,1), opacity 250ms ease',
        position: 'relative',
      }}>

        {/* Accent bar top */}
        <div style={{
          height: 3,
          background: `linear-gradient(90deg, ${current.accent}, ${current.accent}88)`,
          transition: 'background 400ms ease',
        }} />

        {/* Header */}
        <div style={{
          padding: '1.6rem 1.8rem 0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
        }}>
          <div>
            <div style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '.58rem', fontWeight: 600,
              letterSpacing: '2.5px', textTransform: 'uppercase',
              color: current.accent,
              marginBottom: '.5rem',
              transition: 'color 400ms ease',
            }}>
              {current.tag}
            </div>
            <h2 style={{
              margin: 0,
              fontSize: '1.35rem', fontWeight: 700,
              color: 'var(--fg)',
              letterSpacing: '-0.3px',
              lineHeight: 1.2,
            }}>
              {current.title}
            </h2>
          </div>
          <div style={{
            fontSize: '2rem',
            lineHeight: 1,
            marginTop: '.1rem',
            filter: 'drop-shadow(0 2px 4px rgba(0,0,0,.15))',
          }}>
            {current.icon}
          </div>
        </div>

        {/* Body */}
        <div style={{ padding: '1.2rem 1.8rem 0' }}>
          <p style={{
            margin: 0,
            fontSize: '.9rem', lineHeight: 1.7,
            color: 'var(--muted)',
          }}>
            {current.desc}
          </p>
        </div>

        {/* Step indicators */}
        <div style={{
          display: 'flex', gap: '.4rem',
          padding: '1.4rem 1.8rem .2rem',
          alignItems: 'center',
        }}>
          {STEPS.map((s, i) => (
            <button
              key={i}
              onClick={() => setStep(i)}
              style={{
                height: 4, borderRadius: 2,
                width: i === step ? 24 : 8,
                background: i === step ? current.accent : 'var(--bdr)',
                border: 'none', padding: 0, cursor: 'pointer',
                transition: 'width 300ms ease, background 300ms ease',
              }}
            />
          ))}
          <span style={{
            marginLeft: 'auto',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '.6rem', color: 'var(--muted2)',
            letterSpacing: '1px',
          }}>
            {step + 1} / {STEPS.length}
          </span>
        </div>

        {/* Mini preview */}
        <div style={{
          margin: '1rem 1.8rem',
          background: 'var(--bg, #f8fafc)',
          border: '1px solid var(--bdr)',
          borderRadius: 10,
          padding: '.9rem 1rem',
          display: 'flex', gap: '.6rem', flexWrap: 'wrap',
          minHeight: 48, alignItems: 'center',
        }}>
          {step === 0 && (
            <>
              {['x² − 5x + 6 = 0', 'x² − 4 = 0', 'x² + 4x = 0', 'x² − 3x + 2 = 0'].map((eq, i) => (
                <span key={i} style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '.7rem',
                  background: i === 0 ? current.accent + '22' : 'transparent',
                  border: `1px solid ${i === 0 ? current.accent + '66' : 'var(--bdr)'}`,
                  borderRadius: 6, padding: '.25rem .55rem',
                  color: i === 0 ? current.accent : 'var(--muted)',
                  transition: 'all 300ms',
                }}>
                  {eq}
                </span>
              ))}
            </>
          )}
          {step === 1 && (
            <div style={{ width: '100%' }}>
              {['x² − 5x + 6 = 0', '(x−2)(x−3) = 0', 'x=2 OR x=3'].map((s, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: '.5rem',
                  padding: '.2rem 0',
                }}>
                  <span style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: '.6rem', color: 'var(--muted2)',
                    minWidth: 14,
                  }}>{i + 1}</span>
                  <span style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: '.72rem', color: 'var(--fg)',
                  }}>{s}</span>
                </div>
              ))}
            </div>
          )}
          {step === 2 && (
            <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '.35rem' }}>
              {[
                { s: 'x² − 5x + 6 = 0', ok: true, label: 'Initial' },
                { s: '(x−2)(x−3) = 0', ok: true, label: 'Factorization' },
                { s: 'x=2',             ok: false, label: 'Apply Zero Product Rule' },
              ].map((row, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: '.5rem',
                  background: row.ok ? 'rgba(16,185,129,.07)' : 'rgba(239,68,68,.07)',
                  border: `1px solid ${row.ok ? 'rgba(16,185,129,.2)' : 'rgba(239,68,68,.2)'}`,
                  borderRadius: 6, padding: '.25rem .55rem',
                }}>
                  <span style={{ fontSize: '.7rem' }}>{row.ok ? '✓' : '✗'}</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.68rem', color: 'var(--fg)', flex: 1 }}>{row.s}</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.55rem', color: 'var(--muted2)' }}>{row.label}</span>
                </div>
              ))}
            </div>
          )}
          {step === 3 && (
            <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '.4rem' }}>
              <div style={{ display: 'flex', gap: '.5rem', alignItems: 'center' }}>
                <span style={{ fontSize: '.75rem' }}>⚙️</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.65rem', color: current.accent, fontWeight: 600 }}>Procedural Error</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.6rem', color: 'var(--muted2)' }}>· Missing root</span>
              </div>
              {['Step 1: The student set only one factor to zero…', 'Step 2: Both factors must equal zero independently…', 'Step 3: Set x−2=0 → x=2 and x−3=0 → x=3…'].map((s, i) => (
                <div key={i} style={{
                  display: 'flex', gap: '.4rem', alignItems: 'flex-start',
                }}>
                  <span style={{
                    fontFamily: "'JetBrains Mono', monospace", fontSize: '.55rem',
                    background: current.accent + '22', color: current.accent,
                    border: `1px solid ${current.accent}44`,
                    borderRadius: 4, padding: '.1rem .3rem', whiteSpace: 'nowrap', marginTop: 1,
                  }}>Step {i+1}</span>
                  <span style={{ fontSize: '.7rem', color: 'var(--muted)', lineHeight: 1.4 }}>{s}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '0 1.8rem 1.6rem',
          display: 'flex', alignItems: 'center', gap: '.75rem',
        }}>
          {step > 0 && (
            <button onClick={prev} style={{
              padding: '.5rem 1rem',
              background: 'transparent',
              border: '1px solid var(--bdr)',
              borderRadius: 8, cursor: 'pointer',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '.7rem', color: 'var(--muted)',
              transition: 'border-color 200ms, color 200ms',
            }}
              onMouseEnter={e => { e.target.style.borderColor = 'var(--fg)'; e.target.style.color = 'var(--fg)' }}
              onMouseLeave={e => { e.target.style.borderColor = 'var(--bdr)'; e.target.style.color = 'var(--muted)' }}
            >
              ← Back
            </button>
          )}

          <button onClick={next} style={{
            padding: '.55rem 1.4rem',
            background: current.accent,
            border: 'none', borderRadius: 8, cursor: 'pointer',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '.72rem', fontWeight: 700,
            color: '#fff', letterSpacing: '.5px',
            boxShadow: `0 4px 14px ${current.accent}55`,
            transition: 'background 400ms ease, box-shadow 400ms ease, transform 150ms',
          }}
            onMouseEnter={e => { e.target.style.transform = 'translateY(-1px)' }}
            onMouseLeave={e => { e.target.style.transform = 'translateY(0)' }}
          >
            {step < STEPS.length - 1 ? 'Next →' : 'Start Checking →'}
          </button>

          <button onClick={skip} style={{
            marginLeft: 'auto',
            padding: '.5rem .8rem',
            background: 'transparent', border: 'none',
            cursor: 'pointer',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '.62rem', color: 'var(--muted2)',
            letterSpacing: '.5px',
            transition: 'color 200ms',
          }}
            onMouseEnter={e => e.target.style.color = 'var(--muted)'}
            onMouseLeave={e => e.target.style.color = 'var(--muted2)'}
          >
            Skip demo
          </button>
        </div>
      </div>
    </div>
  )
}