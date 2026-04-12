"""Stage 6 — Corrector (pure SymPy)"""
import sympy as sp
from .digitizer import digitize_step

x = sp.symbols('x')


def generate_correct_steps(last_valid_step: str) -> list:
    """Generate correct solution steps from the last valid step string."""
    sym_expr = digitize_step(last_valid_step)
    if sym_expr is None:
        return []

    steps = []
    try:
        factored = sp.factor(sym_expr)
        expanded = sp.expand(sym_expr)

        if factored != expanded and factored != sym_expr:
            steps.append(f"({factored}) = 0")

        solutions = sp.solve(sym_expr, x)
        if not solutions:
            return steps

        if len(solutions) == 1:
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