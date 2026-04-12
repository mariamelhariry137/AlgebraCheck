"""Stage 8 — Misconception Classifier"""
import json, time

TAXONOMY = {
    "Conceptual Error": ["Misunderstanding of zero product rule","Misunderstanding of factorization","Incorrect application of algebraic identity","Other conceptual misunderstanding"],
    "Computational Error": ["Sign error","Arithmetic mistake","Missing root","Incorrect substitution into formula"],
    "Procedural Error": ["Incorrect factorization","Incorrect zero product application","Wrong sequence of steps","Incomplete procedure"],
    "Radical & Simplification Error": ["Incorrect square root simplification","Discriminant calculation error","Incorrect radical arithmetic"],
    "Common Factor Error": ["Incorrect extraction of common factor","Missed common factor"]
}

_tax = "\n".join(f"{c}:{','.join(s)}" for c, s in TAXONOMY.items())

SYSTEM_PROMPT = (f"Classify algebra error. Taxonomy:\n{_tax}\n"
    "Pick best category+subcategory. Confidence<0.6→use 'Other conceptual misunderstanding'.\n"
    'Respond ONLY with JSON: {"category":"<c>","subcategory":"<s>","confidence":<0-1>}')


def _get_groq_client():
    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()
        return Groq()
    except Exception:
        return None


def _rule_fallback(operation: str) -> dict:
    if operation == "Factorization":
        return {"category": "Procedural Error", "subcategory": "Incorrect factorization", "confidence": 0.8}
    if operation == "Apply Zero Product Rule":
        return {"category": "Procedural Error", "subcategory": "Incorrect zero product application", "confidence": 0.8}
    if operation == "Solve Linear Equation":
        return {"category": "Computational Error", "subcategory": "Sign error", "confidence": 0.7}
    if "Quadratic" in operation:
        return {"category": "Radical & Simplification Error", "subcategory": "Discriminant calculation error", "confidence": 0.7}
    return {"category": "Conceptual Error", "subcategory": "Other conceptual misunderstanding", "confidence": 0.5}


def classify_misconception(step_prev: str, step_wrong: str, operation: str,
                            error_analysis: dict = None, retries: int = 3) -> dict:
    client = _get_groq_client()
    if client is None:
        return _rule_fallback(operation)

    # Compact user message — only include what's needed
    user_msg = f"Prev:{step_prev}\nWrong:{step_wrong}\nOp:{operation}"
    if error_analysis:
        et = error_analysis.get('error_type', '')
        se = error_analysis.get('specific_error', '')
        if et: user_msg += f"\nErrorType:{et}"
        if se: user_msg += f"\nDetail:{se}"

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"): raw = raw[4:]
                raw = raw.strip()
            return json.loads(raw)

        except Exception as e:
            if attempt < retries - 1:
                print(f"[classifier] Attempt {attempt+1} failed: {e}. Retrying in {2**attempt}s...")
                time.sleep(2 ** attempt)
            else:
                print(f"[classifier] All retries failed: {e}")
                return _rule_fallback(operation)