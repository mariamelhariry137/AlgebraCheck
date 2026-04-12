"""Stage 3 — Symbolic Validation Engine"""
import re
import sympy as sp
from .digitizer import digitize_step, normalize_expression, sympy_digitize

x = sp.symbols('x')


# ── helpers ───────────────────────────────────────────────────────────────────

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


def is_or_step(step: str) -> bool:
    return bool(re.search(r'\bor\b', step, re.IGNORECASE))


def solve_clause(clause: str):
    """
    Solve a single equation clause for x.
    Handles:
      'x=2'       → {2}
      'x-2=0'     → {2}
      'x-2'       → {2}   (no equals sign, treat as =0)
    Returns a set of SymPy values, or empty set on failure.
    """
    clause = clause.strip()
    # Normalize unicode chars
    clause = clause.replace('−', '-').replace('·', '*').replace('^', '**')

    if '=' in clause:
        parts = clause.split('=', 1)        # split on first = only
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


def extract_solutions(step: str):
    """
    Parse an OR step into the full set of solutions.
    e.g. 'x=2 OR x=3'       → {2, 3}
         'x-2=0 OR x-3=0'   → {2, 3}
         'x=3 OR x=-3'       → {3, -3}
    Returns None if nothing could be parsed.
    """
    clauses = re.split(r'\s+or\s+', step, flags=re.IGNORECASE)
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
    Handles OR solution steps by comparing solution sets (order-independent).
    """

    curr_is_or = is_or_step(step_curr)
    prev_is_or = is_or_step(step_prev)

    # ── Both steps are OR steps ──────────────────────────────────────────────
    if curr_is_or and prev_is_or:
        curr_sols = extract_solutions(step_curr)
        prev_sols = extract_solutions(step_prev)
        if curr_sols is None or prev_sols is None:
            # Fall through to symbolic comparison as last resort
            pass
        elif curr_sols == prev_sols:
            return {"valid": True, "reason": "solution_sets_match"}
        else:
            return {"valid": False, "reason": "solution_sets_differ"}

    # ── Current step is OR, previous is an expression ────────────────────────
    if curr_is_or and not prev_is_or:
        curr_sols = extract_solutions(step_curr)
        if curr_sols is None:
            return {"valid": False, "reason": "parse_error_curr"}

        prev_sym = digitize_step(step_prev)
        if prev_sym is None:
            return {"valid": False, "reason": "parse_error_prev"}

        expected = solutions_from_expr(prev_sym)
        if not expected:
            return {"valid": False, "reason": "could_not_solve_prev"}

        if curr_sols == expected:
            return {"valid": True, "reason": "solution_sets_match"}
        return {"valid": False, "reason": "solution_sets_differ"}

    # ── Previous step is OR, current is single value ─────────────────────────
    if prev_is_or and not curr_is_or:
        prev_sols = extract_solutions(step_prev)
        curr_sols = extract_solutions(step_curr)
        if prev_sols and curr_sols and curr_sols.issubset(prev_sols):
            return {"valid": True, "reason": "subset_of_solutions"}

    # ── Standard symbolic equivalence ────────────────────────────────────────
    sym_prev = digitize_step(step_prev)
    sym_curr = digitize_step(step_curr)

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