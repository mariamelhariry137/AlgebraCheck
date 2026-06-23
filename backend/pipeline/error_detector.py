"""Stage 7 — Error Detection (Groq)"""
import re, json, time
from sympy import symbols, expand, simplify
from sympy.parsing.sympy_parser import parse_expr, standard_transformations

x = symbols("x")

ERROR_TYPES = [
    "Sign error", "Wrong factors", "Missing root", "Incorrect coefficient",
    "Quadratic formula misuse", "Discriminant error", "Radical simplification error",
    "Incorrect zero product application", "Arithmetic mistake",
    "Wrong sequence of steps", "Incomplete procedure", "Other"
]

SYSTEM_PROMPT = (
    'Output ONLY a JSON object. No reasoning, no explanation, no other text.\n'
    'Format: {"error_type":"<type>","error_detail":"<one sentence>","confidence":<0-1>}\n'
    'error_type must be one of: Sign error, Wrong factors, Missing root, Incorrect coefficient, '
    'Quadratic formula misuse, Discriminant error, Radical simplification error, '
    'Incorrect zero product application, Arithmetic mistake, Wrong sequence of steps, '
    'Incomplete procedure, Other.'
)

FEW_SHOT = [
   {"role": "user",      "content": "Op:Factorization\nPrev:x^2-5x+6=0\nWrong:(x-2)(x+3)=0\nCorrect:(x-2)(x-3)=0"},
    {"role": "assistant", "content": '{"error_type":"Wrong factors","error_detail":"Second factor should be (x-3) not (x+3); correct factors multiply to +6 and sum to -5.","confidence":0.97}'},
    {"role": "user",      "content": "Op:Apply Zero Product Rule\nPrev:(x-2)(x-3)=0\nWrong:x=2\nCorrect:x=2 OR x=3"},
    {"role": "assistant", "content": '{"error_type":"Missing root","error_detail":"Both factors must be set to zero; student only solved one, missing x=3.","confidence":0.98}'},
    {"role": "user",      "content": "Op:Simplify Radical\nPrev:x=(5+-sqrt(1))/2\nWrong:sqrt(12)=12\nCorrect:sqrt(12)=2*sqrt(3)"},
    {"role": "assistant", "content": '{"error_type":"Radical simplification error","error_detail":"sqrt(12) equals 2*sqrt(3) approximately 3.46, not 12.","confidence":0.97}'},
    # Arithmetic after correct formula setup
    {"role": "user",      "content": "Op:Evaluate Discriminant\nPrev:x=(-(-6)±√(36-0))/2\nWrong:36-0=40\nCorrect:36-0=36"},
    {"role": "assistant", "content": '{"error_type":"Arithmetic mistake","error_detail":"36 minus 0 equals 36, not 40; basic subtraction error.","confidence":0.98}'},
    # Incomplete procedure (stopped after factoring)
    {"role": "user",      "content": "Op:Apply Zero Product Rule\nPrev:x^2-5x+6=0\nWrong:(x-2)(x-3)=0\nCorrect:x=2 OR x=3"},
    {"role": "assistant", "content": '{"error_type":"Incomplete procedure","error_detail":"Student correctly factored but stopped without applying the zero product rule to find x.","confidence":0.95}'},
    # Quadratic formula used instead of factoring — method choice error
    {"role": "user",      "content": "Op:Factorization\nPrev:x^2+6x+5=0\nWrong:x=(-6±√(36-20))/2\nCorrect:(x+1)(x+5)=0"},
    {"role": "assistant", "content": '{"error_type":"Quadratic formula misuse","error_detail":"Student applied the quadratic formula instead of factoring; the equation factors cleanly as (x+1)(x+5)=0.","confidence":0.95}'},
    {"role":"user", "content":"Op:Apply Quadratic Formula\nPrev:x=(5±1)/2\nWrong:x=3\nCorrect:x=3 OR x=2"},
    {"role":"assistant","content":'{"error_type":"Missing root","error_detail":"One solution was omitted.","confidence":0.98}'},
    {"role":"user","content":"Op:Apply Quadratic Formula\nPrev:x=(-(-4)±√16)/2\nWrong:x=(4±5)/2\nCorrect:x=(4±4)/2"},
    {"role":"assistant","content":'{"error_type":"Arithmetic mistake","error_detail":"sqrt(16)=4 not 5.","confidence":0.98}'},
    {"role":"user","content":"Op:Apply Quadratic Formula\nPrev:x^2-5x+6=0\nWrong:x=(5±√(25+24))/2\nCorrect:x=(5±√(25-24))/2"},
    {"role":"assistant","content":'{"error_type":"Discriminant error","error_detail":"Used the wrong sign in the discriminant.","confidence":0.98}'},
    {"role":"user","content":"Op:Simplify Radical\nPrev:x=(4±√49)/2\nWrong:x=(4±49)/2\nCorrect:x=(4±7)/2"},
    {"role":"user", "content":"Op:Apply Quadratic Formula\nPrev:x=(-(-4)±√16)/2\nWrong:x=(-4±4)/2\nCorrect:x=(4±4)/2"},
    # √N written as N (forgot to take square root)
    {"role": "user",      "content": "Op:Simplify Radical\nPrev:(x+1)^2=64\nWrong:x+1=±64\nCorrect:x+1=±8"},
    {"role": "assistant", "content": '{"error_type":"Radical simplification error","error_detail":"sqrt(64)=8 not 64; student used the radicand instead of its square root.","confidence":0.98}'},
    # Discriminant sign error
    {"role": "user",      "content": "Op:Apply Quadratic Formula\nPrev:x^2-5x+4=0\nWrong:x=(5±√(25+16))/2\nCorrect:x=(5±√(25-16))/2"},
    {"role": "assistant", "content": '{"error_type":"Discriminant error","error_detail":"Used b^2+4ac instead of b^2-4ac in the discriminant; sign should be minus.","confidence":0.97}'},
]


def _get_groq_client():
    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()
        return Groq()
    except Exception:
        return None


def _clean_raw(raw: str) -> str:
    """Strip thinking tags and markdown fences."""
    raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL)
    raw = re.sub(r'</?think[^>]*>', '', raw)
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                return part
    return raw.strip()


def _extract_json(raw: str) -> dict:
    """Parse JSON robustly — direct parse, then regex extraction."""
    raw = _clean_raw(raw)
    if not raw:
        raise ValueError("Empty response after cleaning")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    matches = list(re.finditer(r'\{[^{}]+\}', raw, re.DOTALL))
    if matches:
        for m in reversed(matches):
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                continue
    raise ValueError(f"No valid JSON found in: {raw[:200]}")


# ── SymPy helpers ─────────────────────────────────────────────────────────────

def to_sympy_notation(expr: str) -> str:
    expr = re.sub(r"=\s*0", "", expr).strip()
    expr = expr.replace("^", "**")
    expr = re.sub(r"\)\s*\(", ")*(", expr)
    expr = re.sub(r"(\d)\s*\(", r"\1*(", expr)
    expr = re.sub(r"(\d)\s*([a-zA-Z])", r"\1*\2", expr)
    return expr.strip()


def validate_arithmetic(expr: str):
    try:
        m = re.match(r"^([\d\s\+\-\*\/\.]+)=([\d\s\.]+)$", expr.strip())
        if m:
            return abs(eval(m.group(1)) - float(m.group(2))) < 0.01
        m = re.match(r"^sqrt(\d+)\s*=\s*([\d\.]+)$", expr.strip())
        if m:
            import math
            return abs(math.sqrt(float(m.group(1))) - float(m.group(2))) < 0.01
        return None
    except Exception:
        return None


def validate_factorization(equation: str, factored: str):
    try:
        orig = parse_expr(to_sympy_notation(equation), transformations=standard_transformations, local_dict={"x": x})
        fact = parse_expr(to_sympy_notation(factored),  transformations=standard_transformations, local_dict={"x": x})
        return simplify(expand(fact) - orig) == 0
    except Exception:
        return None


def detect_first_error(validation: list) -> dict:
    for item in validation:
        if item.get("status") == "incorrect":
            return {"all_correct": False, "first_error_index": item["step_index"], "steps": validation}
    return {"all_correct": True, "first_error_index": None, "steps": validation}


def get_retained_steps(steps: list, err_idx: int) -> list:
    return steps[:err_idx]


def get_error_context(steps: list, err_idx: int) -> dict:
    return {
        "step_prev":  steps[err_idx - 1] if err_idx > 0 else "",
        "step_wrong": steps[err_idx]
    }


def _rule_fallback(step_prev, step_wrong, operation, correct_continuation):
    """
    Rule-based fallback matching classifier.py fallback for consistency.
    Returns error_detector shaped dict.
    """
    correct = correct_continuation[0] if correct_continuation else "unknown"
    op = (operation or "").lower()

    if "zero product" in op:
        etype = "Missing root"
    elif "factor" in op:
        etype = "Wrong factors"
    elif "discriminant" in op or "quadratic formula" in op:
        etype = "Discriminant error"
    elif "radical" in op or "sqrt" in op or "simplif" in op:
        etype = "Radical simplification error"
    elif "completing" in op or "square" in op:
        etype = "Incomplete procedure"
    else:
        etype = "Other"

    return {
        "error_type":     etype,
        "specific_error": f"'{step_wrong}' is not a valid transformation of '{step_prev}'.",
        "correct_step":   correct,
        "reasoning":      f"{operation} was applied incorrectly."
    }


def detect_error_o1(step_prev: str, step_wrong: str, operation: str,
                    correct_continuation: list, retries: int = 3) -> dict:
    client = _get_groq_client()
    if client is None:
        return _rule_fallback(step_prev, step_wrong, operation, correct_continuation)

    correct_str = " -> ".join(correct_continuation) if correct_continuation else "unknown"
    user_msg = (
        f"Op:{operation}\n"
        f"Prev:{step_prev}\n"
        f"Wrong:{step_wrong}\n"
        f"Correct:{correct_str}"
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *FEW_SHOT,
        {"role": "user", "content": user_msg},
    ]

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=messages,
                temperature=0,
                max_tokens=200,   # increased from 120 to prevent truncation
            )
            raw = response.choices[0].message.content.strip()
            result = _extract_json(raw)

            if result.get("error_type") not in ERROR_TYPES:
                result["error_type"] = "Other"

            result.setdefault("specific_error", result.get("error_detail", ""))
            result.setdefault("correct_step",   correct_continuation[0] if correct_continuation else "")
            result.setdefault("reasoning",      result.get("error_detail", ""))
            return result

        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"[error_detector] Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"[error_detector] All retries failed: {e}")
                return _rule_fallback(step_prev, step_wrong, operation, correct_continuation)