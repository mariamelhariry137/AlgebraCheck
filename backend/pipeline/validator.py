"""Stage 3 — Symbolic Validation Engine

Core principle: instead of comparing algebraic expressions structurally,
solve every step for x and compare solution sets. This handles all valid
student notations: quadratic formula with ±, completing the square,
factored forms, OR/comma/space-separated solutions, etc.
"""
import re
import sympy as sp
from .digitizer import normalize_expression, sympy_digitize

x = sp.symbols('x')


# ── Step solving ──────────────────────────────────────────────────────────────

def _solve_clause(clause: str) -> set:
    """
    Solve a single equation clause for x.
    e.g. 'x=2', 'x-2=0', 'x+2=2', '(x+2)^2=4', 'x=(3+1)/2'
    Returns a set of SymPy solutions.
    """
    clause = clause.strip()
    if not clause:
        return set()

    norm = normalize_expression(clause)

    if '=' in norm:
        parts = norm.split('=', 1)
        lhs = sympy_digitize(parts[0].strip())
        rhs = sympy_digitize(parts[1].strip())
        if lhs is None or rhs is None:
            return set()
        expr = lhs - rhs
    else:
        parsed = sympy_digitize(norm)
        if parsed is None:
            return set()
        expr = parsed

    try:
        sols = sp.solve(expr, x)
        # Convert to numeric floats for reliable comparison across simplifications
        result = set()
        for s in sols:
            try:
                result.add(float(s.evalf()))
            except Exception:
                result.add(s)
        return result
    except Exception:
        return set()


def solve_step(step: str) -> set:
    """
    Solve any step for x, handling all student notation formats:
      - Regular equation:         x^2 - 3x + 2 = 0
      - Quadratic formula (±):    x = (3 ± √(9-8)) / 2
      - Plus-minus variants:      x = +-sqrt(4), x = +/-2
      - OR-separated:             x=2 OR x=1, x+2=2 OR x+2=-2
      - Comma-separated:          x=2, x=1
      - Space-separated:          x=2 x=1, x-2=0 x-3=0
      - Completing the square:    (x+2)^2 = 4, x+2 = 2 OR x+2 = -2
    Returns a set of float solutions (empty set if unparseable).
    """
    step = step.strip()
    if not step:
        return set()

    # Normalize ± variants: +-, +/- → ±
    step_norm = re.sub(r'\+\s*[-/]\s*-?', '±', step)

    # ── OR-separated clauses ──────────────────────────────────────────────────
    if re.search(r'\bor\b', step_norm, re.IGNORECASE):
        clauses = re.split(r'\s+or\s+', step_norm, flags=re.IGNORECASE)
        sols = set()
        for c in clauses:
            sols |= _solve_clause(c.strip())
        return sols

    # ── Comma-separated clauses ───────────────────────────────────────────────
    if ',' in step_norm and re.search(r'x\s*[=\-+]', step_norm, re.IGNORECASE):
        clauses = step_norm.split(',')
        sols = set()
        for c in clauses:
            sols |= _solve_clause(c.strip())
        if sols:
            return sols

    # ── Space-separated x-clauses (e.g. x=2 x=1 or x-2=0 x-3=0) ────────────
    fragments = re.findall(r'x\s*[\-=+][^\s,]+(?:\s*=\s*[^\s,]+)?', step_norm, re.IGNORECASE)
    if len(fragments) >= 2:
        sols = set()
        for f in fragments:
            sols |= _solve_clause(f.strip())
        if sols:
            return sols

    # ── ± step: expand into two equations and solve both ─────────────────────
    if '±' in step_norm:
        plus_ver = step_norm.replace('±', '+')
        minus_ver = step_norm.replace('±', '-')
        sols = set()
        for ver in [plus_ver, minus_ver]:
            sols |= _solve_clause(ver)
        return sols

    # ── Regular single equation ───────────────────────────────────────────────
    return _solve_clause(step_norm)


# ── Structural equivalence (fallback for non-equation steps) ─────────────────

def _expressions_equivalent(a, b) -> bool:
    if a is None or b is None:
        return False
    try:
        if sp.simplify(sp.expand(a) - sp.expand(b)) == 0:
            return True
        if sp.simplify(sp.factor(a) - sp.factor(b)) == 0:
            return True
        return False
    except Exception:
        return False


def _solutions_close(s1: set, s2: set, tol: float = 1e-9) -> bool:
    """Compare two solution sets with floating-point tolerance."""
    if len(s1) != len(s2):
        return False
    # Try exact match first
    if s1 == s2:
        return True
    # Try approximate match
    try:
        list1 = sorted(float(v) for v in s1)
        list2 = sorted(float(v) for v in s2)
        return all(abs(a - b) < tol for a, b in zip(list1, list2))
    except Exception:
        return False


# ── Core validation ───────────────────────────────────────────────────────────

def validate_step_pair(step_prev: str, step_curr: str) -> dict:
    """
    Validate that step_curr is a mathematically correct transformation of step_prev.

    Strategy:
    1. Solve both steps for x and compare solution sets (primary method).
       This handles quadratic formula, completing the square, ± notation,
       OR/comma/space-separated solutions, factored forms — everything.
    2. Fall back to structural expression equivalence for non-equation steps
       (e.g. intermediate algebraic manipulations that aren't yet solved).
    """
    sols_prev = solve_step(step_prev)
    sols_curr = solve_step(step_curr)

    # Both steps yield solutions → compare them
    if sols_prev and sols_curr:
        if _solutions_close(sols_prev, sols_curr):
            return {"valid": True, "reason": "solution_sets_match"}
        # Allow subset: e.g. student shows one root from a two-root equation
        # (but only if curr has fewer solutions — more would be wrong)
        if sols_curr.issubset(sols_prev) and len(sols_curr) < len(sols_prev):
            # This is actually an error (missing root) — mark invalid
            return {"valid": False, "reason": "missing_roots"}
        return {"valid": False, "reason": "solution_sets_differ"}

    # Only prev has solutions (curr might be an intermediate algebraic step)
    # Fall back to structural comparison via LHS
    if sols_prev and not sols_curr:
        from .digitizer import digitize_step
        sym_prev = digitize_step(step_prev)
        sym_curr = digitize_step(step_curr)
        if sym_prev is not None and sym_curr is not None:
            is_eq = _expressions_equivalent(sym_prev, sym_curr)
            return {"valid": is_eq, "reason": "equivalent" if is_eq else "not_equivalent"}
        # If we can't parse curr at all, it's probably wrong
        return {"valid": False, "reason": "parse_error_curr"}

    # Neither step yields solutions (e.g. pure algebraic manipulation)
    # Fall back to structural LHS comparison
    from .digitizer import digitize_step
    sym_prev = digitize_step(step_prev)
    sym_curr = digitize_step(step_curr)

    if sym_prev is None:
        return {"valid": False, "reason": "parse_error_prev"}
    if sym_curr is None:
        return {"valid": False, "reason": "parse_error_curr"}

    is_eq = _expressions_equivalent(sym_prev, sym_curr)
    return {"valid": is_eq, "reason": "equivalent" if is_eq else "not_equivalent"}


# ── Full list validation ──────────────────────────────────────────────────────

def validate_all_steps(steps: list) -> list:
    if not steps:
        return []
    results = [{"step_index": 0, "step": steps[0], "valid": True, "reason": "reference"}]
    for i in range(1, len(steps)):
        r = validate_step_pair(steps[i - 1], steps[i])
        results.append({"step_index": i, "step": steps[i], **r})
    return results


# ── Legacy aliases (keep runner.py working unchanged) ─────────────────────────

def is_or_step(step: str) -> bool:
    return bool(re.search(r'\bor\b', step, re.IGNORECASE))

def is_multi_solution_step(step: str) -> bool:
    return len(solve_step(step)) > 0

def extract_solutions(step: str):
    sols = solve_step(step)
    return sols if sols else None