"""Stage 1 — Digitizer"""
import re
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application
)

x = sp.symbols('x')
TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)

SUP_MAP = {'²':'2','³':'3','⁴':'4','⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9','¹':'1','⁰':'0'}


def normalize_expression(expr: str) -> str:
    s = expr.strip()
    # Unicode superscripts
    def replace_sups(m):
        return m.group(1) + '**' + ''.join(SUP_MAP.get(c, c) for c in m.group(2))
    s = re.sub(r'(\w)([²³⁴⁵⁶⁷⁸⁹¹⁰]+)', replace_sups, s)
    # Unicode chars
    s = s.replace('−', '-').replace('–', '-').replace('·', '*')
    # sqrt
    s = re.sub(r'√\s*\(', 'sqrt(', s)
    s = re.sub(r'√\s*(\w)', r'sqrt(\1)', s)
    # ^ to **
    s = s.replace('^', '**')
    # Implied multiplication
    s = re.sub(r'\)\s*\(', ')*(', s)
    s = re.sub(r'(\d)\s*([a-zA-Z])', r'\1*\2', s)
    return s


def sympy_digitize(expr: str):
    norm = normalize_expression(expr)
    try:
        return parse_expr(norm, transformations=TRANSFORMATIONS)
    except Exception:
        try:
            return sp.sympify(norm)
        except Exception:
            return None


def digitize_equation(equation: str):
    lhs = equation.split('=')[0] if '=' in equation else equation
    return sympy_digitize(lhs.strip())


def digitize_step(step: str):
    # First OR clause only
    step = re.split(r'\s+or\s+', step, flags=re.IGNORECASE)[0]
    lhs  = step.split('=')[0] if '=' in step else step
    return sympy_digitize(lhs.strip())


def digitize_steps(steps: list) -> list:
    return [digitize_step(s) for s in steps]