"""Stage 3 — Symbolic Validation Engine"""
import re
import sympy as sp
from .digitizer import digitize_step, normalize_expression, sympy_digitize

x = sp.symbols('x')


# ── helpers ───────────────────────────────────────────────────────────────────

def normalize_step(step: str) -> str:
    """Normalize common student notations before parsing."""
    step = step.replace('−', '-').replace('·', '*').replace('^', '**')
    step = re.sub(r'\)\s*\.\s*\(', ')*(', step)
    step = re.sub(r'(\d)\s*\.\s*\(', r'\1*(', step)
    step = re.sub(r'([a-zA-Z\)])\s*\.\s*([a-zA-Z\(])', r'\1*\2', step)
    return step


def expressions_equivalent(a, b) -> bool:
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


# ── plus-minus (±) step detection ────────────────────────────────────────────

def is_plus_minus_step(step: str) -> bool:
    """Detect steps like: x = ±√(4), x = ±2, x = +-sqrt(4), x = +/-2"""
    return bool(re.search(r'[±]|[+]\s*[-/]\s*[-]?', step) and re.search(r'x\s*=', step, re.IGNORECASE))


def extract_plus_minus_solutions(step: str) -> set:
    """
    Extract solution set from ± steps.
    Handles:
      x = ±√(4)     → {2, -2}
      x = ±√4       → {2, -2}
      x = ±2        → {2, -2}
      x = +-sqrt(4) → {2, -2}
      x = +/-2      → {2, -2}
    Returns empty set on failure.
    """
    # Normalize ± variants
    s = step.replace('±', '±')  # keep ±
    s = re.sub(r'\+\s*[-/]\s*-?', '±', s)   # +- or +/- → ±

    # Match: x = ± sqrt(val) or x = ± √(val) or x = ± √val
    m = re.search(
        r'x\s*=\s*±\s*(?:√|sqrt)\s*\(?\s*([^)\s]+?)\s*\)?',
        s, re.IGNORECASE
    )
    if m:
        val_str = m.group(1).strip().replace('^', '**')
        val = sympy_digitize(val_str)
        if val is not None:
            sq = sp.sqrt(val)
            return {sq, -sq}

    # Match: x = ± number (no sqrt)
    m2 = re.search(r'x\s*=\s*±\s*([\d\.]+)', s, re.IGNORECASE)
    if m2:
        val_str = m2.group(1)
        val = sp.sympify(val_str)
        return {val, -val}

    return set()


# ── multi-solution step detection ─────────────────────────────────────────────

def is_multi_solution_step(step: str) -> bool:
    """
    Detect any format where a student writes multiple solutions.
    Covers: OR, comma, space-separated x-clauses, ± steps.
    """
    if is_plus_minus_step(step):
        return True
    s = step.lower().strip()
    if re.search(r'\bor\b', s):
        return True
    if ',' in step and re.search(r'x\s*[=\-]', s):
        return True
    fragments = re.findall(r'x\s*[\-=][^\s,]+', s)
    return len(fragments) >= 2


def is_or_step(step: str) -> bool:
    return is_multi_solution_step(step)


def solve_clause(clause: str):
    """Solve a single equation clause for x. Returns a set of SymPy values."""
    clause = normalize_step(clause.strip())
    if '=' in clause:
        parts = clause.split('=', 1)
        lhs_s = parts[0].strip()
        rhs_s = parts[1].strip()
    else:
        lhs_s = clause
        rhs_s = '0'

    lhs = sympy_digitize(lhs_s)
    rhs = sympy_digitize(rhs_s) if rhs_s else sp.Integer(0)
    if lhs is None:
        return set()
    rhs = rhs if rhs is not None else sp.Integer(0)
    try:
        return set(sp.solve(lhs - rhs, x))
    except Exception:
        return set()


def split_into_clauses(step: str) -> list:
    """Split a multi-solution step into individual clauses."""
    if re.search(r'\bor\b', step, re.IGNORECASE):
        return [c.strip() for c in re.split(r'\s+or\s+', step, flags=re.IGNORECASE) if c.strip()]
    if ',' in step:
        return [c.strip() for c in step.split(',') if c.strip()]
    fragments = re.findall(r'x\s*[\-=][^\s]*(?:\s*=\s*[^\s]+)?', step)
    if len(fragments) >= 2:
        return [f.strip() for f in fragments]
    return [step.strip()]


def extract_solutions(step: str):
    """
    Parse a multi-solution step into the full set of solutions.
    Handles ± steps, OR, comma, and space-separated clauses.
    Returns None if nothing could be parsed.
    """
    # Handle ± steps specially
    if is_plus_minus_step(step):
        sols = extract_plus_minus_solutions(step)
        return sols if sols else None

    clauses = split_into_clauses(step)
    solutions = set()
    for clause in clauses:
        solutions |= solve_clause(clause)
    return solutions if solutions else None


def solutions_from_expr(expr) -> set:
    try:
        return set(sp.solve(expr, x))
    except Exception:
        return set()


# ── core validation ───────────────────────────────────────────────────────────

def validate_step_pair(step_prev: str, step_curr: str) -> dict:
    """
    Validate that step_curr is a correct transformation of step_prev.
    Handles ± sqrt, dot-multiplication, OR/comma/space-separated solutions.
    """
    step_prev_norm = normalize_step(step_prev)
    step_curr_norm = normalize_step(step_curr)

    curr_is_multi = is_multi_solution_step(step_curr)
    prev_is_multi = is_multi_solution_step(step_prev)

    # ── Both steps are multi-solution ────────────────────────────────────────
    if curr_is_multi and prev_is_multi:
        curr_sols = extract_solutions(step_curr)
        prev_sols = extract_solutions(step_prev)
        if curr_sols and prev_sols:
            if curr_sols == prev_sols:
                return {"valid": True, "reason": "solution_sets_match"}
            else:
                return {"valid": False, "reason": "solution_sets_differ"}

    # ── Current step is multi-solution, previous is an expression ────────────
    if curr_is_multi and not prev_is_multi:
        curr_sols = extract_solutions(step_curr)
        if curr_sols is None:
            return {"valid": False, "reason": "parse_error_curr"}

        prev_sym = digitize_step(step_prev_norm)
        if prev_sym is None:
            return {"valid": False, "reason": "parse_error_prev"}

        expected = solutions_from_expr(prev_sym)
        if not expected:
            return {"valid": False, "reason": "could_not_solve_prev"}

        if curr_sols == expected:
            return {"valid": True, "reason": "solution_sets_match"}
        return {"valid": False, "reason": "solution_sets_differ"}

    # ── Previous step is multi-solution, current is single value ─────────────
    if prev_is_multi and not curr_is_multi:
        prev_sols = extract_solutions(step_prev)
        curr_sols = extract_solutions(step_curr)
        if prev_sols and curr_sols and curr_sols.issubset(prev_sols):
            return {"valid": True, "reason": "subset_of_solutions"}

    # ── Standard symbolic equivalence ────────────────────────────────────────
    sym_prev = digitize_step(step_prev_norm)
    sym_curr = digitize_step(step_curr_norm)

    if sym_prev is None:
        return {"valid": False, "reason": "parse_error_prev"}
    if sym_curr is None:
        return {"valid": False, "reason": "parse_error_curr"}

    is_eq = expressions_equivalent(sym_prev, sym_curr)
    return {"valid": is_eq, "reason": "equivalent" if is_eq else "not_equivalent"}


# ── full list validation ──────────────────────────────────────────────────────

def validate_all_steps(steps: list) -> list:
    if not steps:
        return []
    results = [{"step_index": 0, "step": steps[0], "valid": True, "reason": "reference"}]
    for i in range(1, len(steps)):
        r = validate_step_pair(steps[i - 1], steps[i])
        results.append({"step_index": i, "step": steps[i], **r})
    return results