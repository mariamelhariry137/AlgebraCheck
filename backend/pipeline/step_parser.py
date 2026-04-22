"""Stage 2 — Step Parser"""
import re, json, time, os

MODEL = "llama-3.3-70b-versatile"

ALLOWED_OPERATIONS = [
    "Factorization","Expand","Apply Zero Product Rule","Solve Linear Equation",
    "Apply Quadratic Formula","Complete the Square","Simplify","Collect Like Terms",
    "Move Terms","Calculate Discriminant","Simplify Radical","Other"
]

SYSTEM_PROMPT = ("Identify the algebra operation between two steps. "
    "Choose from: Factorization,Expand,Apply Zero Product Rule,Solve Linear Equation,"
    "Apply Quadratic Formula,Complete the Square,Simplify,Collect Like Terms,"
    "Move Terms,Calculate Discriminant,Simplify Radical,Other. "
    'Respond ONLY with JSON: {"op":"<n>","conf":<0-1>}')


def _is_multi_solution(step: str) -> bool:
    """Detect any multi-solution format: OR, comma, space-separated x-clauses, or ± steps."""
    s = step.lower()
    if re.search(r'\bor\b', s):
        return True
    if '±' in step or re.search(r'\+\s*[-/]', step):
        return True
    if ',' in step and re.search(r'x\s*[=\-]', s):
        return True
    fragments = re.findall(r'x\s*[\-=][^\s,]+', s)
    return len(fragments) >= 2


def _is_plus_minus_step(step: str) -> bool:
    """Detect ± steps: x = ±√(4), x = ±2, x = +-sqrt(4)"""
    return bool(re.search(r'[±]|[+]\s*[-/]', step) and re.search(r'x\s*=', step, re.IGNORECASE))


def _regex_fallback(step_prev: str, step_curr: str) -> dict:
    cl = step_curr.lower()

    # ± step (taking square root of both sides)
    if _is_plus_minus_step(step_curr):
        return {"operation": "Simplify Radical", "confidence": 0.9}

    # Multi-solution output → zero product rule
    if _is_multi_solution(step_curr):
        return {"operation": "Apply Zero Product Rule", "confidence": 0.9}

    # Single x= solution
    if re.match(r'^\s*x\s*=', cl):
        return {"operation": "Solve Linear Equation", "confidence": 0.9}

    # Factored form with dot notation: (x-2).(x-3)
    if re.search(r'\(x[\+\-][^)]+\)\s*[.\*]\s*\(x[\+\-]', step_curr):
        return {"operation": "Factorization", "confidence": 0.85}

    # Factored form standard: (x±...)(x±...)
    if '(' in step_curr and re.search(r'\(x[\+\-]', step_curr):
        return {"operation": "Factorization", "confidence": 0.85}

    if 'sqrt' in cl or '√' in cl:
        return {"operation": "Simplify Radical", "confidence": 0.8}

    return {"operation": "Other", "confidence": 0.5}


def parse_operation(step_prev: str, step_curr: str, retries: int = 3) -> dict:
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        return _regex_fallback(step_prev, step_curr)

    for attempt in range(retries):
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Step1:{step_prev}\nStep2:{step_curr}"}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content.strip()
            result = json.loads(raw)
            op = result.get("op") or result.get("operation", "Other")
            if op not in ALLOWED_OPERATIONS:
                op = "Other"
            return {"operation": op, "confidence": result.get("conf", result.get("confidence", 1.0))}
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return _regex_fallback(step_prev, step_curr)


def parse_all_operations(steps: list) -> list:
    results = []
    for i in range(1, len(steps)):
        op = parse_operation(steps[i - 1], steps[i])
        results.append({
            "step_index": i,
            "step_prev":  steps[i - 1],
            "step_curr":  steps[i],
            "operation":  op["operation"],
            "confidence": op.get("confidence", 1.0)
        })
    return results