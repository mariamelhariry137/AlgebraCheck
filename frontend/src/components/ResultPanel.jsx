import React from 'react'
import { prettifyText } from '../utils/math.js'
import VideoExplainer from './VideoExplainer'

const CAT_ICON = {
  'Procedural Error':               '⚙️',
  'Computational Error':            '🔢',
  'Conceptual Error':               '💡',
  'Radical & Simplification Error': '✂️',
  'Common Factor Error':            '🔗',
}

const STATUS = {
  correct:            { bg: 'var(--green-bg)', border: 'rgba(5,150,105,.2)',  tagBg: '#dcfce7', tagColor: '#15803d', text: '✓' },
  incorrect:          { bg: 'var(--red-bg)',   border: 'rgba(220,38,38,.2)',  tagBg: '#fee2e2', tagColor: '#b91c1c', text: '✗' },
  derived_from_error: { bg: 'var(--red-bg)',   border: 'rgba(220,38,38,.2)',  tagBg: '#fee2e2', tagColor: '#b91c1c', text: '✗' },
}

function Card({ accentColor, children, style = {} }) {
  return (
    <div style={{
      background: 'var(--surf)', border: '1px solid var(--bdr)',
      borderLeft: `4px solid ${accentColor}`,
      borderRadius: 10, padding: '.9rem 1.15rem',
      boxShadow: 'var(--shadow)', ...style,
    }}>{children}</div>
  )
}

function SectionLabel({ children }) {
  return (
    <div style={{
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: '.6rem', fontWeight: 600,
      letterSpacing: '2.5px', textTransform: 'uppercase',
      color: 'var(--muted)', marginBottom: '.5rem',
      display: 'flex', alignItems: 'center', gap: '.6rem',
    }}>
      {children}
      <span style={{ flex: 1, height: 1, background: 'var(--bdr)' }} />
    </div>
  )
}

function PanelTitle({ color, children }) {
  return (
    <div style={{
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: '.58rem', letterSpacing: '2px',
      textTransform: 'uppercase', color,
      marginBottom: '.6rem', fontWeight: 600,
    }}>{children}</div>
  )
}

export default function ResultPanel({ result, error, loading }) {

  if (loading) return (
    <div style={{
      background: 'var(--surf)', border: '1px solid var(--bdr)',
      borderRadius: 12, padding: '3.5rem 2rem', textAlign: 'center',
      boxShadow: 'var(--shadow-md)',
    }}>
      <div style={{
        width: 36, height: 36, border: '3px solid var(--bdr)',
        borderTopColor: 'var(--accent)', borderRadius: '50%',
        animation: 'spin .8s linear infinite', margin: '0 auto 1rem',
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <p style={{ fontSize: '.88rem', color: 'var(--muted)' }}>Running symbolic validation…</p>
    </div>
  )

  if (error) return (
    <Card accentColor="var(--red)">
      <div style={{ fontFamily: "'Syne',sans-serif", fontSize: '1rem', fontWeight: 800, color: 'var(--red)', marginBottom: '.2rem' }}>⚠ Error</div>
      <div style={{ fontSize: '.82rem', color: 'var(--muted)' }}>{error}</div>
    </Card>
  )

  if (!result) return (
    <div style={{
      background: 'var(--surf)', border: '2px dashed var(--bdr)',
      borderRadius: 14, padding: '4rem 2rem', textAlign: 'center',
    }}>
      <div style={{
        fontFamily: "'Syne',sans-serif", fontSize: '4rem', fontWeight: 800,
        background: 'linear-gradient(135deg, var(--accent), var(--purple))',
        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        backgroundClip: 'text', lineHeight: 1, marginBottom: '1rem',
      }}>∑</div>
      <p style={{ fontSize: '.9rem', color: 'var(--muted)', lineHeight: 1.7 }}>
        Enter your steps on the left,<br />
        then click <strong style={{ color: 'var(--accent)' }}>Analyze Solution</strong>
      </p>
    </div>
  )

  const { all_correct, steps, error_step_num, error_step_text,
          operation, misconception, correction, feedback, error_analysis } = result

  return (
    <div>
      {/* Result header */}
      {all_correct ? (
        <Card accentColor="var(--green)" style={{ marginBottom: '.9rem' }}>
          <div style={{ fontFamily: "'Syne',sans-serif", fontSize: '1rem', fontWeight: 800, color: 'var(--green)', marginBottom: '.15rem' }}>
            ✓ All Steps Correct
          </div>
          <div style={{ fontSize: '.82rem', color: 'var(--muted)' }}>
            Every transformation is mathematically valid. Well done!
          </div>
        </Card>
      ) : (
        <Card accentColor="var(--red)" style={{ marginBottom: '.9rem' }}>
          <div style={{ fontFamily: "'Syne',sans-serif", fontSize: '1rem', fontWeight: 800, color: 'var(--red)', marginBottom: '.2rem' }}>
            ⚠ Error at Step {error_step_num}
          </div>
          <div style={{ fontSize: '.82rem', color: 'var(--muted)' }}>
            <code style={{
              background: 'var(--red-bg)', padding: '1px 7px', borderRadius: 4,
              fontFamily: "'JetBrains Mono',monospace", fontSize: '.78rem',
              color: 'var(--red)', border: '1px solid rgba(220,38,38,.15)',
            }}>{prettifyText(error_step_text)}</code>
            &nbsp;·&nbsp;{operation}
          </div>
        </Card>
      )}

      {/* Step breakdown */}
      <SectionLabel>Step Breakdown</SectionLabel>
      {steps?.map(s => {
        const st = STATUS[s.status] || STATUS.correct
        return (
          <div key={s.step_index} style={{
            display: 'flex', alignItems: 'center', gap: '.6rem',
            padding: '.45rem .75rem', borderRadius: 8, marginBottom: '.3rem',
            background: st.bg, border: `1px solid ${st.border}`,
          }}>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '.62rem', color: 'var(--muted2)', minWidth: 18 }}>
              #{s.step_index + 1}
            </span>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '.82rem', color: 'var(--text)', flex: 1 }}>
              {prettifyText(s.step)}
            </span>
            <span style={{
              fontFamily: "'JetBrains Mono',monospace", fontSize: '.6rem', fontWeight: 600,
              padding: '.1rem .45rem', borderRadius: 5,
              background: st.tagBg, color: st.tagColor, whiteSpace: 'nowrap',
            }}>{st.text}</span>
            <span style={{ fontSize: '.67rem', color: 'var(--muted2)', fontStyle: 'italic', whiteSpace: 'nowrap' }}>
              {s.operation}
            </span>
          </div>
        )
      })}

      {/* Error-only panels */}
      {!all_correct && (
        <>
          {/* Misconception */}
          <div style={{
            background: 'var(--surf)', border: '1px solid var(--bdr)',
            borderRadius: 10, margin: '.75rem 0',
            boxShadow: 'var(--shadow)', overflow: 'hidden',
          }}>
            {/* Header row */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: '.85rem',
              padding: '.85rem 1.1rem',
              borderBottom: (error_analysis?.specific_error || misconception?.subcategory) ? '1px solid var(--bdr)' : 'none',
            }}>
              <span style={{ fontSize: '1.3rem', flexShrink: 0 }}>
                {CAT_ICON[misconception?.category] || '⚠️'}
              </span>
              <div style={{ flex: 1 }}>
                <div style={{
                  fontFamily: "'JetBrains Mono',monospace", fontSize: '.6rem', fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '1.5px',
                  color: 'var(--gold)', marginBottom: '.12rem',
                }}>
                  Misconception Category
                </div>
                <div style={{ fontSize: '.92rem', color: 'var(--text)', fontWeight: 700 }}>
                  {misconception?.category}
                </div>
              </div>
            </div>

            {/* Detail rows */}
            <div style={{ padding: '.7rem 1.1rem', display: 'flex', flexDirection: 'column', gap: '.55rem' }}>

              {/* Subcategory */}
              {misconception?.subcategory && (
                <div style={{ display: 'flex', gap: '.75rem', alignItems: 'flex-start' }}>
                  <div style={{
                    fontFamily: "'JetBrains Mono',monospace", fontSize: '.6rem', fontWeight: 600,
                    textTransform: 'uppercase', letterSpacing: '1px',
                    color: 'var(--muted)', minWidth: 110, paddingTop: '.05rem',
                  }}>Type</div>
                  <div style={{ fontSize: '.87rem', color: 'var(--text2)', fontWeight: 500 }}>
                    {misconception.subcategory}
                  </div>
                </div>
              )}

             
              
            </div>
          </div>

          {/* Correct continuation */}
          {correction?.full_solution?.length > 0 && (
            <div style={{
              background: 'var(--surf)', border: '1px solid var(--bdr)',
              borderTop: '3px solid var(--accent)', borderRadius: 10,
              padding: '.85rem 1.1rem', margin: '.75rem 0',
              boxShadow: 'var(--shadow)',
            }}>
              <PanelTitle color="var(--accent)">Correct Continuation</PanelTitle>
              {correction.retained?.map((s, i) => (
                <div key={`r${i}`} style={{
                  fontFamily: "'JetBrains Mono',monospace", fontSize: '.83rem',
                  color: 'var(--green)', padding: '.18rem .55rem',
                  borderLeft: '3px solid var(--green)', marginBottom: '.22rem',
                  background: 'var(--green-bg)', borderRadius: '0 5px 5px 0',
                }}>✓ &nbsp;{prettifyText(s)}</div>
              ))}
              {correction.retained?.length > 0 && (
                <hr style={{ border: 'none', borderTop: '1px dashed var(--bdr2)', margin: '.5rem 0' }} />
              )}
              {correction.continuation?.map((s, i) => (
                <div key={`c${i}`} style={{
                  fontFamily: "'JetBrains Mono',monospace", fontSize: '.83rem',
                  color: 'var(--accent)', padding: '.18rem .55rem',
                  borderLeft: '3px solid var(--accent)', marginBottom: '.22rem',
                  background: 'var(--acc-light)', borderRadius: '0 5px 5px 0',
                }}>▸ &nbsp;{prettifyText(s)}</div>
              ))}
            </div>
          )}

          {/* Feedback */}
          {feedback && (
            <div style={{
              background: 'var(--surf)', border: '1px solid var(--bdr)',
              borderTop: '3px solid var(--purple)', borderRadius: 10,
              padding: '.85rem 1.1rem', margin: '.75rem 0',
              boxShadow: 'var(--shadow)',
            }}>
              <PanelTitle color="var(--purple)">Explanation</PanelTitle>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '.6rem' }}>
                {feedback.split('\n').filter(Boolean).map((line, i) => {
                  const [label, ...rest] = line.split(':')
                  const text = rest.join(':').trim()
                  return (
                    <div key={i} style={{ display: 'flex', gap: '.75rem', alignItems: 'flex-start' }}>
                      <span style={{
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: '.65rem', fontWeight: 700,
                        color: 'var(--purple)',
                        background: 'var(--purple-bg, #f5f3ff)',
                        border: '1px solid rgba(124,58,237,.15)',
                        padding: '.15rem .5rem', borderRadius: 5,
                        whiteSpace: 'nowrap', marginTop: '.1rem',
                        flexShrink: 0,
                      }}>{label}</span>
                      <span style={{
                        fontSize: '.87rem', color: 'var(--text2)', lineHeight: 1.75,
                      }}>{text}</span>
                    </div>
                  )
                })}
              </div>
              <VideoExplainer errorType={error_analysis?.error_type} />
            </div>
          )}
        </>
      )}
    </div>
  )
}