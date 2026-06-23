"""Stage 6 — Corrector (pure SymPy)"""
import re
import sympy as sp
from .digitizer import normalize_expression, sympy_digitize

x = sp.symbols('x')


def _parse_full_equation(step: str):
    """
    Parse a full equation 'LHS = RHS' into a SymPy expression (LHS - RHS).
    Handles both '= 0' and non-zero RHS (e.g. 'x^2 + 6x = -5').
    Returns None if unparseable.
    """
    step = step.strip()
    norm = normalize_expression(step)

    if '=' in norm:
        parts = norm.split('=', 1)
        lhs = sympy_digitize(parts[0].strip())
        rhs = sympy_digitize(parts[1].strip())
        if lhs is None or rhs is None:
            return None
        return lhs - rhs
    else:
        return sympy_digitize(norm)


def _format_factor(expr) -> str:
    """
    Convert SymPy factored expression to clean student-readable string.
    e.g.  (x - 2)*(x - 3)  →  (x - 2)(x - 3)
          2*(x - 3)*(x + 1) →  2(x - 3)(x + 1)
    """
    s = str(expr)
    # Remove multiplication signs between closing and opening parens
    s = re.sub(r'\)\s*\*\s*\(', ')(', s)
    # Remove * between coefficient and opening paren: 2*(x →  2(x
    s = re.sub(r'(\d)\s*\*\s*\(', r'\1(', s)
    return s


def generate_correct_steps(last_valid_step: str) -> list:
    """
    Generate correct solution steps from the last valid step string.
    Handles:
      - Standard quadratic:      x^2 - 5x + 6 = 0
      - Non-zero RHS:            x^2 + 6x = -5
      - Completing-the-square:   (x+3)^2 = 4
      - Already factored:        (x-2)(x-3) = 0
    """
    sym_expr = _parse_full_equation(last_valid_step)
    if sym_expr is None:
        return []

    steps = []
    try:
        factored  = sp.factor(sym_expr)
        expanded  = sp.expand(sym_expr)

        # Only show factored form if it's meaningfully different from expanded
        if factored != expanded and factored != sym_expr:
            steps.append(f"{_format_factor(factored)} = 0")

        solutions = sp.solve(sym_expr, x)
        if not solutions:
            return steps

        # Sort solutions for deterministic output
        try:
            solutions = sorted(solutions, key=lambda s: float(s.evalf()))
        except Exception:
            pass

        if len(solutions) == 1:
            # Repeated root — still show it clearly
            steps.append(f"x = {solutions[0]}")
        else:
            steps.append(" OR ".join(f"x = {s}" for s in solutions))

    except Exception:
        pass

    return steps


def format_correction(retained_steps: list, correct_continuation: list) -> dict:
    return {
        "retained":      retained_steps,
        "continuation":  correct_continuation,
        "full_solution": retained_steps + correct_continuation
    }