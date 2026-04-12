/**
 * prettifyHTML — converts raw math input into coloured HTML for the overlay.
 *
 * Root cause of the old bug: we were HTML-escaping the whole string first,
 * then injecting <span> tags. Any > or < in the already-escaped string would
 * mix with the injected tags and produce visible HTML text like "op-sqrt">√(.
 *
 * Fix: never escape the full string up front. Instead, build a list of tokens
 * (each either a styled span or plain escaped text) and join them.
 */

const SUP_MAP = {
  '\u00b2':'2','\u00b3':'3','\u00b9':'1','\u2070':'0',
  '\u2074':'4','\u2075':'5','\u2076':'6','\u2077':'7','\u2078':'8','\u2079':'9'
}

const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
const sp  = (cls, t) => `<span class="${cls}">${t}</span>`

export function prettifyHTML(raw) {
  if (!raw) return ''

  // Tokenise the string left-to-right into [{ html, len }] pieces
  const tokens = []
  let i = 0
  const s = raw

  while (i < s.length) {
    // ── superscripts: x**2  x^2  x²
    let m

    m = s.slice(i).match(/^([a-zA-Z0-9)])(\*\*|\^)(\d+)/)
    if (m) {
      tokens.push(esc(m[1]) + `<sup>${m[3]}</sup>`)
      i += m[0].length; continue
    }

    m = s.slice(i).match(/^([a-zA-Z0-9)])([\u00b2\u00b3\u00b9\u2070\u2074-\u2079]+)/)
    if (m) {
      const digits = m[2].split('').map(c => SUP_MAP[c]||c).join('')
      tokens.push(esc(m[1]) + `<sup>${digits}</sup>`)
      i += m[0].length; continue
    }

    // ── sqrt(  or  √(
    m = s.slice(i).match(/^(sqrt\s*\(|√\s*\()/)
    if (m) {
      tokens.push(sp('op-sqrt','√') + sp('op-paren','('))
      i += m[0].length; continue
    }

    // ── bare √
    if (s[i] === '√') {
      tokens.push(sp('op-sqrt','√'))
      i++; continue
    }

    // ── multiplication  )*(
    m = s.slice(i).match(/^\)\s*\*\s*\(/)
    if (m) {
      tokens.push(sp('op-paren',')') + sp('op-mul','·') + sp('op-paren','('))
      i += m[0].length; continue
    }

    // ── digit * letter
    m = s.slice(i).match(/^(\d)\s*\*\s*([a-zA-Z(])/)
    if (m) {
      tokens.push(esc(m[1]) + sp('op-mul','·') + esc(m[2]))
      i += m[0].length; continue
    }

    // ── bare * or ·
    if (s[i] === '*' || s[i] === '·') {
      tokens.push(sp('op-mul','·'))
      i++; continue
    }

    // ── OR keyword
    m = s.slice(i).match(/^OR\b/)
    if (m) {
      tokens.push(sp('op-or','OR'))
      i += 2; continue
    }

    // ── equals
    if (s[i] === '=') {
      tokens.push(sp('op-eq','='))
      i++; continue
    }

    // ── minus operator (between spaces, or leading)
    if ((s[i] === '-' || s[i] === '\u2212') &&
        (i === 0 || s[i-1] === ' ') &&
        (i + 1 < s.length && s[i+1] === ' ')) {
      tokens.push(sp('op-neg','−'))
      i++; continue
    }
    // standalone unicode minus
    if (s[i] === '\u2212') {
      tokens.push(sp('op-neg','−'))
      i++; continue
    }

    // ── parens
    if (s[i] === '(') { tokens.push(sp('op-paren','(')); i++; continue }
    if (s[i] === ')') { tokens.push(sp('op-paren',')')); i++; continue }

    // ── default: plain escaped character
    tokens.push(esc(s[i]))
    i++
  }

  return tokens.join('')
}

/** Plain text prettify — no HTML, just unicode symbols for result panels */
export function prettifyText(raw) {
  if (!raw) return ''
  let s = raw
  const supMap = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}
  s = s.replace(/([a-zA-Z0-9])\*\*(\d+)/g, (_, b, e) => b + e.split('').map(c=>supMap[c]||c).join(''))
  s = s.replace(/([a-zA-Z0-9])\^(\d+)/g,   (_, b, e) => b + e.split('').map(c=>supMap[c]||c).join(''))
  s = s.replace(/\)\s*\*\s*\(/g, ')·(')
  s = s.replace(/\*/g, '·')
  s = s.replace(/sqrt\s*\(/g, '√(')
  s = s.replace(/ - /g, ' − ')
  return s
}