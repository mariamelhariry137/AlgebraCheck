import React, { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import { prettifyText } from '../utils/math.js'

const DIFF = {
  Easy:   { bg: 'var(--green-light)', color: 'var(--green)', border: 'var(--green-mid)', dot: '#10b981' },
  Medium: { bg: 'var(--gold-light)',  color: 'var(--gold)',  border: 'var(--gold-mid)',  dot: '#f59e0b' },
  Hard:   { bg: 'var(--red-light)',   color: 'var(--red)',   border: 'var(--red-mid)',   dot: '#ef4444' },
}

function SectionLabel({ children }) {
  return (
    <div style={{
      fontFamily: "'DM Mono', monospace", fontSize: '.62rem', fontWeight: 500,
      letterSpacing: '2.5px', textTransform: 'uppercase',
      color: 'var(--muted2)', marginBottom: '.7rem',
      display: 'flex', alignItems: 'center', gap: '.6rem',
    }}>
      {children}
      <span style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, var(--bdr), transparent)' }} />
    </div>
  )
}

const DIFF_CONFIG = {
  Easy:   { color: '#047857', bg: '#f0fdf4', border: '#bbf7d0', activeBg: '#dcfce7', dot: '#10b981', tabBg: '#ecfdf5' },
  Medium: { color: '#b45309', bg: '#fffbeb', border: '#fde68a', activeBg: '#fef3c7', dot: '#f59e0b', tabBg: '#fffbeb' },
  Hard:   { color: '#b91c1c', bg: '#fef2f2', border: '#fecaca', activeBg: '#fee2e2', dot: '#ef4444', tabBg: '#fef2f2' },
}

function PresetPicker({ presets, selected, onSelect }) {
  const [activeTab, setActiveTab] = useState('Easy')

  const tabPresets = presets
    .map((p, i) => ({ ...p, i }))
    .filter(p => p.difficulty === activeTab)

  return (
    <div>
      {/* Difficulty tabs — pill toggle matching Preset/Custom style */}
<div style={{
  display: 'inline-flex',
  background: 'var(--surf2)',
  border: '1px solid var(--bdr)',
  borderRadius: 10, padding: 3, gap: 3,
  marginBottom: '.75rem',
  width: '100%',
}}>
  {['Easy', 'Medium', 'Hard'].map(diff => {
    const dc = DIFF_CONFIG[diff]
    const active = activeTab === diff
    return (
      <button key={diff}
        onClick={() => setActiveTab(diff)}
        style={{
          flex: 1,
          background: active ? 'var(--surf)' : 'transparent',
          border: active ? '1px solid var(--bdr)' : '1px solid transparent',
          borderRadius: 7,
          color: active ? dc.color : 'var(--muted)',
          fontFamily: "'Plus Jakarta Sans', sans-serif",
          fontSize: '.82rem', fontWeight: active ? 600 : 400,
          padding: '.3rem .6rem',
          cursor: 'pointer', transition: 'all .15s',
          boxShadow: active ? 'var(--shadow-sm)' : 'none',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '.35rem',
        }}
      >
        <span style={{
          width: 7, height: 7, borderRadius: '50%',
          background: active ? dc.dot : 'var(--muted3)',
          transition: 'background .15s',
        }} />
        {diff}
      </button>
    )
  })}
</div>

      {/* Equation cards grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.4rem' }}>
        {tabPresets.map(p => {
          const dc = DIFF_CONFIG[p.difficulty]
          const isSelected = selected === p.i
          return (
            <button key={p.i}
              onClick={() => onSelect(p.i)}
              style={{
                background: isSelected ? dc.activeBg : dc.bg,
                border: `1.5px solid ${isSelected ? dc.dot : dc.border}`,
                borderRadius: 'var(--radius-sm)',
                padding: '.65rem .85rem',
                cursor: 'pointer', transition: 'all .15s',
                textAlign: 'left',
                boxShadow: isSelected ? `0 0 0 3px ${dc.dot}22` : 'none',
                position: 'relative', overflow: 'hidden',
              }}
              onMouseEnter={e => { if (!isSelected) e.currentTarget.style.borderColor = dc.dot }}
              onMouseLeave={e => { if (!isSelected) e.currentTarget.style.borderColor = dc.border }}
            >
              {/* Selected check */}
              {isSelected && (
                <div style={{
                  position: 'absolute', top: 5, right: 5,
                  width: 16, height: 16, borderRadius: '50%',
                  background: dc.dot,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontSize: '.55rem', fontWeight: 700,
                }}>✓</div>
              )}
              <div style={{
                fontFamily: "'DM Mono', monospace",
                fontSize: '.95rem', fontWeight: 500,
                color: isSelected ? dc.color : 'var(--text)',
                letterSpacing: '-.2px', lineHeight: 1.3,
              }}>
                {prettifyText(p.label)}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default function ProblemPanel({ problem, setProblem, loadPreset, onFocus }) {
  const [mode, setMode]         = useState('preset')
  const [presets, setPresets]   = useState([])
  const [selected, setSelected] = useState(0)
  const [focused, setFocused]   = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    api.presets().then(setPresets).catch(() => {})
  }, [])

  useEffect(() => {
    if (focused && inputRef.current) {
      const el = inputRef.current
      el.setSelectionRange(el.value.length, el.value.length)
    }
  }, [problem, focused])

  const preset = presets[selected]
  const ds = preset ? (DIFF[preset.difficulty] || DIFF.Easy) : null

  return (
    <section style={{ marginBottom: '1.2rem' }}>
      <SectionLabel>01 · Problem</SectionLabel>

      {/* Mode toggle */}
      <div style={{
        display: 'inline-flex',
        background: 'var(--surf2)',
        border: '1px solid var(--bdr)',
        borderRadius: 10, padding: 3, gap: 3,
        marginBottom: '1rem',
      }}>
        {['preset', 'custom'].map(m => (
          <button key={m}
            onClick={() => { setMode(m); if (m === 'custom') setProblem('') }}
            style={{
              background: mode === m ? 'var(--surf)' : 'transparent',
              border: mode === m ? '1px solid var(--bdr)' : '1px solid transparent',
              color: mode === m ? 'var(--accent)' : 'var(--muted)',
              fontFamily: "'Plus Jakarta Sans', sans-serif",
              fontSize: '.82rem', fontWeight: mode === m ? 600 : 400,
              padding: '.3rem 1rem', borderRadius: 7,
              cursor: 'pointer', transition: 'all .15s',
              boxShadow: mode === m ? 'var(--shadow-sm)' : 'none',
            }}
          >{m === 'preset' ? 'Preset' : 'Custom'}</button>
        ))}
      </div>

      {mode === 'preset' ? (
        <>
          <PresetPicker
            presets={presets}
            selected={selected}
            onSelect={i => { setSelected(i); if (presets[i]) setProblem(presets[i].problem) }}
          />

          {/* Load buttons */}
          {preset && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.5rem', marginTop: '.85rem' }}>
              {[
                { label: '✓ Load correct steps', mode: 'correct', bg: '#f0fdf4', border: '#bbf7d0', color: '#047857' },
                { label: '✗ Load error example', mode: 'error',   bg: '#fef2f2', border: '#fecaca', color: '#b91c1c' },
              ].map(btn => (
                <button key={btn.mode}
                  onClick={() => loadPreset(preset, btn.mode)}
                  style={{
                    background: btn.bg, border: `1px solid ${btn.border}`,
                    borderRadius: 'var(--radius-sm)', color: btn.color,
                    fontFamily: "'Plus Jakarta Sans', sans-serif",
                    fontSize: '.82rem', fontWeight: 600, padding: '.45rem .7rem',
                    cursor: 'pointer', transition: 'all .15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.filter = 'brightness(.97)'}
                  onMouseLeave={e => e.currentTarget.style.filter = 'none'}
                >{btn.label}</button>
              ))}
            </div>
          )}
        </>
      ) : (
        <>
          <input
            ref={inputRef}
            value={problem}
            onChange={e => setProblem(e.target.value)}
            placeholder="e.g. x² − 5x + 6 = 0"
            onFocus={() => { setFocused(true); onFocus('problem') }}
            onBlur={() => setFocused(false)}
            style={{
              width: '100%', background: 'var(--surf)',
              border: `1px solid ${focused ? 'var(--accent)' : 'var(--bdr)'}`,
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text)', fontFamily: "'DM Mono', monospace",
              fontSize: '.92rem', padding: '.5rem .85rem',
              outline: 'none', marginBottom: '.9rem',
              boxShadow: focused ? '0 0 0 3px rgba(37,99,235,.1)' : 'var(--shadow-sm)',
              transition: 'border-color .15s, box-shadow .15s',
            }}
          />
          {problem && (
            <div style={{
              background: 'linear-gradient(135deg, var(--gold-light) 0%, #fff 100%)',
              border: '1px solid var(--gold-mid)',
              borderRadius: 'var(--radius)', padding: '1rem 1.3rem',
            }}>
              <div style={{
                fontFamily: "'DM Mono', monospace", fontSize: '.58rem',
                letterSpacing: '2px', textTransform: 'uppercase',
                color: 'var(--muted)', marginBottom: '.3rem',
              }}>Equation</div>
              <div style={{
                fontFamily: "'DM Mono', monospace",
                fontSize: '1.5rem', fontWeight: 500, color: 'var(--text)',
              }}>{prettifyText(problem)} = 0</div>
            </div>
          )}
        </>
      )}
    </section>
  )
}