import { useState, useCallback } from 'react'
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

  // Keep activeStep as a number for the toolbar label (steps only)
  const activeStep = typeof activeTarget === 'number' ? activeTarget : 0

  const updateStep = useCallback((idx, val) => {
    setSteps(prev => prev.map((s, i) => i === idx ? val : s))
    setActiveTarget(idx)
  }, [])

  const addStep = useCallback(() => {
    setSteps(prev => {
      setActiveTarget(prev.length) // new step index
      return [...prev, '']
    })
  }, [])

  const removeStep = useCallback((idx) => {
    setSteps(prev => prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev)
  }, [])

  // Insert symbol into whichever input was last focused
  const insertSymbol = useCallback((sym) => {
    if (activeTarget === 'problem') {
      setProblem(prev => prev + sym)
    } else {
      const idx = activeTarget
      setSteps(prev => prev.map((s, i) => i === idx ? s + sym : s))
    }
  }, [activeTarget])

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
    result, loading, error,
    loadPreset, clear, analyze,
  }
}