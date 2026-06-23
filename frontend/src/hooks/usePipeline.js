import { useState, useCallback, useRef } from 'react'
import { api } from '../api.js'

const EMPTY_STEPS = ['']

export function usePipeline() {
  const [problem, setProblem]   = useState('')
  const [steps, setSteps]       = useState(EMPTY_STEPS)
  const [result, setResult]     = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)

  // activeTarget: 'problem' | number (step index)
  const [activeTarget, setActiveTarget] = useState(0)

  // Tracks the actual focused DOM input element, so insertSymbol can read/restore
  // cursor position. Registered by MathInput/ProblemPanel via registerInput().
  const lastInputRef = useRef(null)

  const activeStep = typeof activeTarget === 'number' ? activeTarget : 0

  const updateStep = useCallback((idx, val) => {
    setSteps(prev => prev.map((s, i) => i === idx ? val : s))
    setActiveTarget(idx)
  }, [])

  const addStep = useCallback(() => {
    setSteps(prev => {
      setActiveTarget(prev.length)
      return [...prev, '']
    })
  }, [])

  const removeStep = useCallback((idx) => {
    setSteps(prev => prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev)
  }, [])

  // Insert symbol at the cursor position of the currently focused input.
  // Because toolbar buttons use onMouseDown+preventDefault, the input never
  // loses focus, so document.activeElement === el is reliably true here.
  const insertSymbol = useCallback((sym) => {
    const el = lastInputRef.current

    if (el) {
      const start = el.selectionStart ?? el.value.length
      const end   = el.selectionEnd   ?? el.value.length
      const before = el.value.slice(0, start)
      const after  = el.value.slice(end)
      const newVal = before + sym + after
      const newCursor = start + sym.length

      if (activeTarget === 'problem') {
        setProblem(newVal)
      } else {
        const idx = activeTarget
        setSteps(prev => prev.map((s, i) => i === idx ? newVal : s))
      }

      // Restore cursor position right after the symbol, so the user can
      // keep typing immediately without re-clicking anywhere
      requestAnimationFrame(() => {
        if (el) {
          el.focus()
          el.setSelectionRange(newCursor, newCursor)
        }
      })
    } else {
      // No input has ever been focused yet — fall back to appending
      if (activeTarget === 'problem') {
        setProblem(prev => prev + sym)
      } else {
        const idx = activeTarget
        setSteps(prev => prev.map((s, i) => i === idx ? s + sym : s))
      }
    }
  }, [activeTarget])

  // Called by MathInput/ProblemPanel on focus to register the live DOM node
  const registerInput = useCallback((el) => {
    lastInputRef.current = el
  }, [])

  const loadPreset = useCallback((preset, mode) => {
    setProblem(preset.problem)
    setSteps(mode === 'correct' ? [...preset.correct] : [...preset.error])
    setResult(null)
    setError(null)
    setActiveTarget(0)
  }, [])

  const clear = useCallback(() => {
    setSteps(EMPTY_STEPS)
    setResult(null)
    setError(null)
    setActiveTarget(0)
  }, [])

  const analyze = useCallback(async () => {
    const cleanSteps = steps.filter(s => s.trim())
    if (!problem.trim()) { setError('Please enter or select a problem.'); return }
    if (!cleanSteps.length) { setError('Add at least one step.'); return }
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await api.analyze(problem, cleanSteps)
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [problem, steps])

  return {
    problem, setProblem,
    steps, updateStep, addStep, removeStep, insertSymbol,
    activeStep, activeTarget, setActiveTarget,
    registerInput,
    result, loading, error,
    loadPreset, clear, analyze,
  }
}