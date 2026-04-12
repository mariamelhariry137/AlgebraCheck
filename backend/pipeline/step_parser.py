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
    'Respond ONLY with JSON: {"op":"<name>","conf":<0-1>}')


def _regex_fallback(step_prev: str, step_curr: str) -> dict:
    cl = step_curr.lower()
    if re.search(r'\bor\b', cl) and re.search(r'x\s*=', cl):
        return {"operation": "Apply Zero Product Rule", "confidence": 0.9}
    if re.match(r'^\s*x\s*=', cl) and 'or' not in cl:
        return {"operation": "Solve Linear Equation", "confidence": 0.9}
    if '(' in step_curr and re.search(r'\(x[\+\-]', step_curr):
        return {"operation": "Factorization", "confidence": 0.85}
    if 'sqrt' in cl or '√' in cl:
        return {"operation": "Apply Quadratic Formula", "confidence": 0.8}
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