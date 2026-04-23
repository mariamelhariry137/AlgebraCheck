import React, { useEffect, useState } from 'react'
import { api } from './api.js'
import { usePipeline } from './hooks/usePipeline.js'
import Header          from './components/Header.jsx'
import ProblemPanel    from './components/ProblemPanel.jsx'
import SymbolToolbar   from './components/SymbolToolbar.jsx'
import StepsPanel      from './components/StepsPanel.jsx'
import ResultPanel     from './components/ResultPanel.jsx'
import OnboardingDemo  from './components/OnboardingDemo.jsx'

const divider = { height: 1, background: 'var(--bdr)', margin: '1rem 0' }

const sectionCard = {
  background: 'var(--surf)', border: '1px solid var(--bdr)',
  borderRadius: 14, padding: '1.4rem 1.5rem',
  boxShadow: 'var(--shadow-md)',
}

const DEMO_KEY = 'algebracheck_demo_seen'

export default function App() {
  const [apiMode, setApiMode] = useState(null)
  const [showDemo, setShowDemo] = useState(false)

  const {
    problem, setProblem,
    steps, updateStep, addStep, removeStep, insertSymbol,
    activeStep, activeTarget, setActiveTarget,
    result, loading, error,
    loadPreset, clear, analyze,
  } = usePipeline()

  useEffect(() => {
    api.health().then(h => setApiMode(h.mode)).catch(() => {})
    // Show demo only on first visit
    if (!sessionStorage.getItem(DEMO_KEY)) {
      setShowDemo(true)
    }
  }, [])

  function handleDemoDone() {
    sessionStorage.setItem(DEMO_KEY, '1')
    setShowDemo(false)
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {showDemo && <OnboardingDemo onDone={handleDemoDone} />}

      <Header apiMode={apiMode} />

      <main style={{
        flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr',
        gap: '1.5rem', maxWidth: 1280, width: '100%',
        margin: '0 auto', padding: '1.8rem 1.8rem 1rem',
        alignItems: 'start',
      }}>
        {/* LEFT */}
        <div style={sectionCard}>
          <ProblemPanel
            problem={problem}
            setProblem={setProblem}
            loadPreset={loadPreset}
            onFocus={setActiveTarget}
          />
          <div style={divider} />
          <SymbolToolbar
            onInsert={insertSymbol}
            activeTarget={activeTarget}
          />
          <div style={divider} />
          <StepsPanel
            steps={steps}
            updateStep={updateStep}
            addStep={addStep}
            removeStep={removeStep}
            setActiveStep={setActiveTarget}
            activeStep={activeStep}
            clear={clear}
            onAnalyze={analyze}
            loading={loading}
          />
        </div>

        {/* RIGHT */}
        <div style={{ ...sectionCard, minHeight: 400 }}>
          <div style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '.6rem', fontWeight: 600,
            letterSpacing: '2.5px', textTransform: 'uppercase',
            color: 'var(--muted)', marginBottom: '.9rem',
            display: 'flex', alignItems: 'center', gap: '.6rem',
          }}>
            04 · Analysis
            <span style={{ flex: 1, height: 1, background: 'var(--bdr)' }} />
          </div>
          <ResultPanel result={result} error={error} loading={loading} />
        </div>
      </main>

      <footer style={{
        textAlign: 'center', padding: '1.1rem 0',
        borderTop: '1px solid var(--bdr)',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '.63rem', color: 'var(--muted2)', letterSpacing: '0.5px',
        background: 'var(--surf)',
      }}>
        AlgebraCheck &nbsp;·&nbsp; SymPy Symbolic Engine &nbsp;·&nbsp;
        <span style={{ color: 'var(--accent)' }}>AI Error Detection &amp; Misconception Classification</span>
        &nbsp;·&nbsp;
        <button
          onClick={() => setShowDemo(true)}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '.63rem', color: 'var(--muted2)',
            padding: 0, textDecoration: 'underline',
            letterSpacing: '0.5px',
          }}
        >
          replay demo
        </button>
      </footer>
    </div>
  )
}