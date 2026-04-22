"""Stage 3 — Symbolic Validation Engine"""
import re
import sympy as sp
from .digitizer import digitize_step, normalize_expression, sympy_digitize

x = sp.symbols('x')


# ── helpers ───────────────────────────────────────────────────────────────────

def normalize_step(step: str) -> str:
    """
    Normalize common student notations before any parsing.
    - Dot multiplication: (x-2).(x-3) → (x-2)*(x-3)
    - Unicode minus/dot: − → -,  · → *
    - Caret power: x^2 → x**2
    """
    step = step.replace('−', '-').replace('·', '*').replace('^', '**')
    # dot between closing and opening paren: ).(  →  )*(
    step = re.sub(r'\)\s*\.\s*\(', ')*(', step)
    # dot between digit and paren: 2.(  →  2*(
    step = re.sub(r'(\d)\s*\.\s*\(', r'\1*(', step)
    # dot between two terms like x.y → x*y  (but not decimal: 3.14 stays)
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


def is_multi_solution_step(step: str) -> bool:
    """
    Detect any format where a student writes multiple solutions.
    Covers:
      x=2 OR x=3         (explicit OR)
      x=2 or x=3         (lowercase or)
      x=2, x=3           (comma)
      x=2 x=3            (space-separated)
      x-2=0 x-3=0        (space-separated equations)
    """
    s = step.lower().strip()
    if re.search(r'\bor\b', s):
        return True
    if ',' in step and re.search(r'x\s*[=\-]', s):
        return True
    # Two or more x=... or x-...=0 fragments
    fragments = re.findall(r'x\s*[\-=][^\s,]+', s)
    return len(fragments) >= 2


# keep old name as alias so nothing else breaks
def is_or_step(step: str) -> bool:
    return is_multi_solution_step(step)


def solve_clause(clause: str):
    """
    Solve a single equation clause for x.
    Handles: 'x=2', 'x-2=0', 'x-2' (treated as =0)
    Returns a set of SymPy values, or empty set on failure.
    """
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
    expr = lhs - rhs

    try:
        sols = sp.solve(expr, x)
        return set(sols)
    except Exception:
        return set()


def split_into_clauses(step: str) -> list:
    """
    Split a multi-solution step into individual clauses regardless of separator.
    Handles: OR, comma, or plain whitespace between x-clauses.
    e.g. 'x=2 OR x=3'   → ['x=2', 'x=3']
         'x=2, x=3'     → ['x=2', 'x=3']
         'x=2 x=3'      → ['x=2', 'x=3']
         'x-2=0 x-3=0'  → ['x-2=0', 'x-3=0']
    """
    # Split on OR
    if re.search(r'\bor\b', step, re.IGNORECASE):
        return [c.strip() for c in re.split(r'\s+or\s+', step, flags=re.IGNORECASE) if c.strip()]
    # Split on comma
    if ',' in step:
        return [c.strip() for c in step.split(',') if c.strip()]
    # Space-separated x clauses
    fragments = re.findall(r'x\s*[\-=][^\s]*(?:\s*=\s*[^\s]+)?', step)
    if len(fragments) >= 2:
        return [f.strip() for f in fragments]
    return [step.strip()]


def extract_solutions(step: str):
    """
    Parse a multi-solution step into the full set of solutions.
    Returns None if nothing could be parsed.
    """
    clauses = split_into_clauses(step)
    solutions = set()
    for clause in clauses:
        sols = solve_clause(clause)
        solutions |= sols
    return solutions if solutions else None


def solutions_from_expr(expr) -> set:
    """Solve a SymPy expression for x and return the solution set."""
    try:
        return set(sp.solve(expr, x))
    except Exception:
        return set()


# ── core validation ───────────────────────────────────────────────────────────

def validate_step_pair(step_prev: str, step_curr: str) -> dict:
    """
    Validate that step_curr is a correct transformation of step_prev.
    Handles dot-multiplication, OR/comma/space-separated solutions.
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

    # ── Standard symbolic equivalence (with normalized notation) ─────────────
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