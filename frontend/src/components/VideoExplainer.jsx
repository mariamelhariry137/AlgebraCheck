import { useState } from 'react'

const VIDEO_MAP = {
  'Wrong factors':                     { id: 'J7MjMM_mi4k', title: 'Solving quadratics by factoring' },
  'Incorrect factorization':           { id: 'J7MjMM_mi4k', title: 'Solving quadratics by factoring' },
  'Missing root':                      { id: 'J7MjMM_mi4k', title: 'Zero product property' },
  'Incorrect zero product application':{ id: 'J7MjMM_mi4k', title: 'Zero product property' },
  'Quadratic formula misuse':          { id: 'Z3JpGMkpuxo', title: 'Using the quadratic formula' },
  'Incorrect coefficient':             { id: 'Z3JpGMkpuxo', title: 'Using the quadratic formula' },
  'Discriminant error':                { id: 'XuM6SwtjPgM', title: 'The discriminant explained' },
  'Radical simplification error':      { id: '8G4L2Zq6sJQ', title: 'Simplifying square roots' },
  'Sign error':                        { id: 'Z3JpGMkpuxo', title: 'Using the quadratic formula' },
  'Arithmetic mistake':                { id: 'Z3JpGMkpuxo', title: 'Using the quadratic formula' },
  'Wrong sequence of steps':           { id: 'J7MjMM_mi4k', title: 'Solving quadratics by factoring' },
  'Incomplete procedure':              { id: 'J7MjMM_mi4k', title: 'Solving quadratics by factoring' },
  'Other':                             { id: 'J7MjMM_mi4k', title: 'Solving quadratics by factoring' },
}

export default function VideoExplainer({ errorType }) {
  const [open, setOpen] = useState(false)
  const video = VIDEO_MAP[errorType] || VIDEO_MAP['Other']

  return (
    <div style={{ marginTop: '1rem' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '.45rem',
          background: open ? 'var(--acc-light, #eff6ff)' : 'var(--surf2)',
          border: `1px solid ${open ? 'rgba(37,99,235,.3)' : 'var(--bdr)'}`,
          borderRadius: 8,
          color: open ? 'var(--accent, #2563eb)' : 'var(--muted)',
          fontFamily: "'Plus Jakarta Sans', sans-serif",
          fontSize: '.82rem',
          fontWeight: 500,
          padding: '.35rem .9rem',
          cursor: 'pointer',
          transition: 'all .15s',
        }}
      >
        <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
          <circle cx="6.5" cy="6.5" r="6" stroke="currentColor" strokeWidth="1"/>
          <polygon points="5,4 10,6.5 5,9" fill="currentColor"/>
        </svg>
        {open ? 'Hide video' : 'Watch explanation'}
      </button>

      {open && (
        <div style={{
          marginTop: '.75rem',
          borderRadius: 10,
          overflow: 'hidden',
          border: '1px solid var(--bdr)',
          background: '#000',
        }}>
          <div style={{
            background: 'var(--surf2)',
            borderBottom: '1px solid var(--bdr)',
            padding: '.4rem .75rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: '.65rem',
              color: 'var(--muted)',
              letterSpacing: '.5px',
            }}>
              {video.title}
            </span>
            <button
              onClick={() => setOpen(false)}
              style={{
                background: 'none', border: 'none',
                color: 'var(--muted)', cursor: 'pointer',
                fontSize: '.85rem', lineHeight: 1, padding: '0 .2rem',
              }}
            >✕</button>
          </div>

          <div style={{ position: 'relative', paddingTop: '56.25%' }}>
            <iframe
              src={`https://www.youtube.com/embed/${video.id}?rel=0`}
              title={video.title}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              style={{
                position: 'absolute', top: 0, left: 0,
                width: '100%', height: '100%', border: 'none',
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}