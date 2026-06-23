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
    Solve any step for x, handling all student notation formats.
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

    # ── Space-separated x-clauses ────────────────────────────────────────────
    fragments = re.findall(r'x\s*[\-=+][^\s,]+(?:\s*=\s*[^\s,]+)?', step_norm, re.IGNORECASE)
    if len(fragments) >= 2:
        sols = set()
        for f in fragments:
            sols |= _solve_clause(f.strip())
        if sols:
            return sols

    # ── ± step: expand into two equations and solve both ─────────────────────
    if '±' in step_norm:
        plus_ver  = step_norm.replace('±', '+')
        minus_ver = step_norm.replace('±', '-')
        sols = set()
        for ver in [plus_ver, minus_ver]:
            sols |= _solve_clause(ver)
        return sols

    # ── Regular single equation ───────────────────────────────────────────────
    return _solve_clause(step_norm)


# ── Completing-the-square intermediate step solver ────────────────────────────

def _solve_full_equation(step: str) -> set:
    """
    Solve a full 'LHS = RHS' equation where RHS may be non-zero.
    e.g. 'x^2 + 6x = -5'  →  {-1, -5}
         'x^2 + 6x + 9 = 4'  →  {-1, -5}
         '(x+3)^2 = 4'  →  {-1, -5}
    Unlike _solve_clause this does NOT strip the RHS.
    """
    step = step.strip()
    norm = normalize_expression(step)
    if '=' not in norm:
        return set()
    parts = norm.split('=', 1)
    lhs = sympy_digitize(parts[0].strip())
    rhs = sympy_digitize(parts[1].strip())
    if lhs is None or rhs is None:
        return set()
    try:
        sols = sp.solve(lhs - rhs, x)
        result = set()
        for s in sols:
            try:
                result.add(float(s.evalf()))
            except Exception:
                result.add(s)
        return result
    except Exception:
        return set()


def _is_solution_step(step: str) -> bool:
    s = step.strip()
    if re.search(r'\bor\b', s, re.IGNORECASE):
        return True
    if '±' in s or re.search(r'\+\s*[-/]\s*-?', s):
        return True
    return bool(re.match(r'^\s*x\s*=', s, re.IGNORECASE))


def _is_standard_quadratic(step: str) -> bool:
    norm = normalize_expression(step)
    if not re.search(r'x\s*\*\*\s*2|x\^2', norm, re.IGNORECASE):
        return False
    if '=' not in norm:
        return False
    rhs_sym = sympy_digitize(norm.split('=', 1)[1].strip())
    return rhs_sym is not None and rhs_sym == 0


def _is_intermediate_step(step: str) -> bool:
    if _is_solution_step(step) or _is_standard_quadratic(step):
        return False
    if '=' not in step:
        return False
    rhs_sym = sympy_digitize(normalize_expression(step.split('=', 1)[1].strip()))
    if rhs_sym is None or rhs_sym == 0:
        return False
    return x not in rhs_sym.free_symbols


# ── Structural equivalence (fallback) ────────────────────────────────────────

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
    if s1 == s2:
        return True
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
    1. For completing-the-square intermediate steps, solve both full equations
       (preserving RHS) and compare solution sets.
    2. For standard steps, solve both for x and compare solution sets.
    3. Fall back to structural equivalence for non-equation steps.
    """
    # ── Strategy 1: intermediate steps (e.g. x^2+6x=-5, (x+3)^2=4) ──────────
    if _is_intermediate_step(step_curr) or _is_intermediate_step(step_prev):
        sols_prev = _solve_full_equation(step_prev)
        sols_curr = _solve_full_equation(step_curr)
        if sols_prev and sols_curr:
            if _solutions_close(sols_prev, sols_curr):
                return {"valid": True, "reason": "solution_sets_match"}
            if sols_curr.issubset(sols_prev) and len(sols_curr) < len(sols_prev):
                return {"valid": False, "reason": "missing_roots"}
            return {"valid": False, "reason": "solution_sets_differ"}
        # If either side can't be solved (e.g. irrational), fall through

    # ── Strategy 2: standard step solving ────────────────────────────────────
    sols_prev = solve_step(step_prev)
    sols_curr = solve_step(step_curr)

    if sols_prev and sols_curr:
        if _solutions_close(sols_prev, sols_curr):
            return {"valid": True, "reason": "solution_sets_match"}
        # Missing root: student has fewer correct solutions
        if sols_curr.issubset(sols_prev) and len(sols_curr) < len(sols_prev):
            return {"valid": False, "reason": "missing_roots"}
        return {"valid": False, "reason": "solution_sets_differ"}

    # ── Strategy 3: structural fallback ──────────────────────────────────────
    if sols_prev and not sols_curr:
        from .digitizer import digitize_step
        sym_prev = digitize_step(step_prev)
        sym_curr = digitize_step(step_curr)
        if sym_prev is not None and sym_curr is not None:
            is_eq = _expressions_equivalent(sym_prev, sym_curr)
            return {"valid": is_eq, "reason": "equivalent" if is_eq else "not_equivalent"}
        return {"valid": False, "reason": "parse_error_curr"}

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


# ── Legacy aliases ────────────────────────────────────────────────────────────

def is_or_step(step: str) -> bool:
    return bool(re.search(r'\bor\b', step, re.IGNORECASE))

def is_multi_solution_step(step: str) -> bool:
    return len(solve_step(step)) > 0

def extract_solutions(step: str):
    sols = solve_step(step)
    return sols if sols else None