"""Stage 8 — Misconception Classifier"""
import json, time

TAXONOMY = {
    "Conceptual Error": [
        "Misunderstanding of zero product rule",
        "Misunderstanding of factorization",
        "Incorrect application of algebraic identity",
        "Other conceptual misunderstanding",
    ],
    "Computational Error": [
        "Sign error",
        "Arithmetic mistake",
        "Incorrect substitution into formula",
    ],
    "Procedural Error": [
        "Incorrect factorization",
        "Incorrect zero product application",
        "Incomplete application of Zero Product Rule",
        "Wrong sequence of steps",
        "Incomplete procedure",
    ],
    "Radical & Simplification Error": [
        "Incorrect square root simplification",
        "Discriminant calculation error",
        "Incorrect radical arithmetic",
    ],
    "Common Factor Error": [
        "Incorrect extraction of common factor",
        "Missed common factor",
    ],
}

_tax = "\n".join(f"{c}: {', '.join(s)}" for c, s in TAXONOMY.items())

SYSTEM_PROMPT = f"""Classify a student algebra error into the taxonomy below.

TAXONOMY:
{_tax}

RULES (apply in order, stop at first match):
1. error_type is "Arithmetic mistake" OR error is a wrong numerical calculation
   → Computational Error / Arithmetic mistake
2. error_type is "Missing root" OR student stated one solution when two exist
   → Procedural Error / Incomplete application of Zero Product Rule
3. error_type is "Incomplete procedure" OR student stopped before reaching final answer
   → Procedural Error / Incomplete procedure
4. error_type is "Wrong factors" OR student chose incorrect factor pair
   → Procedural Error / Incorrect factorization
5. error_type is "Incorrect coefficient" OR student dropped/ignored the leading coefficient
   → Common Factor Error / Incorrect extraction of common factor
6. error_type is "Sign error" in a factoring or zero-product step
   → Computational Error / Sign error
7. error_type is "Quadratic formula misuse" AND student used the formula instead of
   completing the square or factoring (method choice error)
   → Procedural Error / Wrong sequence of steps
8. error_type is "Wrong sequence of steps"
   → Procedural Error / Wrong sequence of steps
9. Confidence < 0.6 → Conceptual Error / Other conceptual misunderstanding

KEY DISTINCTION:
- "Conceptual Error / Misunderstanding of factorization" means the student does NOT
  understand what factoring is at all.
- Picking the wrong numbers for factors (Wrong factors) = Procedural Error / Incorrect factorization
- Dropping the leading coefficient = Common Factor Error / Incorrect extraction of common factor
- These are NEVER Conceptual Errors.

Respond ONLY with JSON: {{"category":"<c>","subcategory":"<s>","confidence":<0-1>}}"""

FEW_SHOT = [
    # ── Arithmetic after correct formula setup → Computational ────────────────
    {
        "role": "user",
        "content": (
            "Prev:x = (-(-6) ± √((-6)^2 - 4(1)(0)))/(2*1)\n"
            "Wrong:x = (6 ± √36)/(2)  →  36 - 0 = 40\n"
            "Op:Evaluate Discriminant\n"
            "ErrorType:Arithmetic mistake\n"
            "Detail:Student computed 36 - 0 = 40 instead of 36"
        ),
    },
    {"role": "assistant", "content": '{"category":"Computational Error","subcategory":"Arithmetic mistake","confidence":0.97}'},

    # ── Missing root → Procedural ─────────────────────────────────────────────
    {
        "role": "user",
        "content": (
            "Prev:(x - 6)(x - 0) = 0\n"
            "Wrong:x = 6\n"
            "Op:Apply Zero Product Rule\n"
            "ErrorType:Missing root\n"
            "Detail:Student only solved one factor, missing x = 0"
        ),
    },
    {"role": "assistant", "content": '{"category":"Procedural Error","subcategory":"Incomplete application of Zero Product Rule","confidence":0.97}'},

    # ── Incomplete procedure → Procedural ─────────────────────────────────────
    {
        "role": "user",
        "content": (
            "Prev:x^2 - 5x + 6 = 0\n"
            "Wrong:(x-2)(x-3) = 0\n"
            "Op:Apply Zero Product Rule\n"
            "ErrorType:Incomplete procedure\n"
            "Detail:Student factored correctly but stopped without solving for x"
        ),
    },
    {"role": "assistant", "content": '{"category":"Procedural Error","subcategory":"Incomplete procedure","confidence":0.95}'},

    # ── Wrong factors → Procedural (NOT Conceptual) ───────────────────────────
    {
        "role": "user",
        "content": (
            "Prev:x^2 - 5x + 6 = 0\n"
            "Wrong:(x-2)(x+3) = 0\n"
            "Op:Factorization\n"
            "ErrorType:Wrong factors\n"
            "Detail:Correct form is (x-2)(x-3); student used wrong sign on second factor"
        ),
    },
    {"role": "assistant", "content": '{"category":"Procedural Error","subcategory":"Incorrect factorization","confidence":0.95}'},

    # ── Wrong factors, different equation → still Procedural ─────────────────
    {
        "role": "user",
        "content": (
            "Prev:1x^2 + -19x + 90 = 0\n"
            "Wrong:(x + 9)(x + 10) = 0\n"
            "Op:Factorization\n"
            "ErrorType:Wrong factors\n"
            "Detail:Correct factors are (x-9)(x-10); student used wrong signs"
        ),
    },
    {"role": "assistant", "content": '{"category":"Procedural Error","subcategory":"Incorrect factorization","confidence":0.95}'},

    # ── Incorrect coefficient → Common Factor Error (NOT Conceptual) ──────────
    {
        "role": "user",
        "content": (
            "Prev:2x^2 + -8x + -10 = 0\n"
            "Wrong:(x - -1)(x - 5) = 0\n"
            "Op:Factorization\n"
            "ErrorType:Incorrect coefficient\n"
            "Detail:Student dropped the leading coefficient 2; correct form is 2(x+1)(x-5)=0"
        ),
    },
    {"role": "assistant", "content": '{"category":"Common Factor Error","subcategory":"Incorrect extraction of common factor","confidence":0.95}'},

    # ── Incorrect coefficient, another example → Common Factor Error ──────────
    {
        "role": "user",
        "content": (
            "Prev:3x^2 + -45x + 132 = 0\n"
            "Wrong:(x - 12)(x - 10) = 0\n"
            "Op:Factorization\n"
            "ErrorType:Incorrect coefficient\n"
            "Detail:Forgot to factor out 3; correct form is 3(x-12)(x-11)=0"
        ),
    },
    {"role": "assistant", "content": '{"category":"Common Factor Error","subcategory":"Incorrect extraction of common factor","confidence":0.96}'},

    # ── Sign error in factoring → Computational ───────────────────────────────
    {
        "role": "user",
        "content": (
            "Prev:x^2 + 20x + 96 = 0\n"
            "Wrong:(x - 12)(x - -8) = 0\n"
            "Op:Factorization\n"
            "ErrorType:Sign error\n"
            "Detail:Both factors should be positive (x+8)(x+12); student used wrong signs"
        ),
    },
    {"role": "assistant", "content": '{"category":"Computational Error","subcategory":"Sign error","confidence":0.94}'},

    # ── Quadratic formula used instead of completing the square → Procedural ──
    {
        "role": "user",
        "content": (
            "Prev:x^2 + 6x + 5 = 0\n"
            "Wrong:x = (-6 ± √(36 - 20)) / 2\n"
            "Op:Factorization\n"
            "ErrorType:Quadratic formula misuse\n"
            "Detail:Student applied quadratic formula instead of factoring or completing the square"
        ),
    },
    {"role": "assistant", "content": '{"category":"Procedural Error","subcategory":"Wrong sequence of steps","confidence":0.93}'},

    # ── Discriminant error → Radical & Simplification ─────────────────────────
    {
        "role": "user",
        "content": (
            "Prev:x^2 - 5x + 4 = 0\n"
            "Wrong:x = (5 ± √(25 + 16)) / 2\n"
            "Op:Apply Quadratic Formula\n"
            "ErrorType:Discriminant error\n"
            "Detail:Used + instead of - in discriminant: b^2 + 4ac instead of b^2 - 4ac"
        ),
    },
    {"role": "assistant", "content": '{"category":"Radical & Simplification Error","subcategory":"Discriminant calculation error","confidence":0.96}'},

    # ── Wrong sequence of steps → Procedural ─────────────────────────────────
    {
        "role": "user",
        "content": (
            "Prev:x^2 + 6x + 9 = -5 + 9\n"
            "Wrong:(x + 3)^2 = 4  →  x + 3 = ±4\n"
            "Op:Simplify Radical\n"
            "ErrorType:Wrong sequence of steps\n"
            "Detail:Should take √4=2 then write x+3=±2; instead skipped simplification"
        ),
    },
    {"role": "assistant", "content": '{"category":"Procedural Error","subcategory":"Wrong sequence of steps","confidence":0.94}'},

    # ── Misunderstanding of zero product rule → Conceptual (equating factors) ─
    {
        "role": "user",
        "content": (
            "Prev:(x - 3)(x - 4) = 0\n"
            "Wrong:x - 3 = x - 4\n"
            "Op:Apply Zero Product Rule\n"
            "ErrorType:Incorrect zero product application\n"
            "Detail:Student equated the two factors instead of setting each to zero"
        ),
    },
    {"role": "assistant", "content": '{"category":"Conceptual Error","subcategory":"Misunderstanding of zero product rule","confidence":0.97}'},
]


def _get_groq_client():
    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()
        return Groq()
    except Exception:
        return None


def _rule_fallback(operation: str, error_type: str = "") -> dict:
    """Rule-based fallback matching the RULES block in the system prompt."""
    et = (error_type or "").lower()

    if "arithmetic" in et:
        return {"category": "Computational Error",  "subcategory": "Arithmetic mistake",                          "confidence": 0.85}
    if "missing root" in et:
        return {"category": "Procedural Error",     "subcategory": "Incomplete application of Zero Product Rule", "confidence": 0.85}
    if "incomplete procedure" in et:
        return {"category": "Procedural Error",     "subcategory": "Incomplete procedure",                        "confidence": 0.85}
    if "wrong factors" in et:
        return {"category": "Procedural Error",     "subcategory": "Incorrect factorization",                     "confidence": 0.85}
    if "incorrect coefficient" in et:
        return {"category": "Common Factor Error",  "subcategory": "Incorrect extraction of common factor",       "confidence": 0.85}
    if "sign error" in et:
        return {"category": "Computational Error",  "subcategory": "Sign error",                                   "confidence": 0.85}
    if "quadratic formula misuse" in et or "wrong sequence" in et:
        return {"category": "Procedural Error",                "subcategory": "Wrong sequence of steps",                    "confidence": 0.80}
    if "radical simplification" in et:
        return {"category": "Radical & Simplification Error",  "subcategory": "Incorrect square root simplification",       "confidence": 0.85}
    if "discriminant" in et:
        return {"category": "Radical & Simplification Error",  "subcategory": "Discriminant calculation error",             "confidence": 0.85}

    op = (operation or "").lower()
    if "factori" in op:
        return {"category": "Procedural Error",               "subcategory": "Incorrect factorization",            "confidence": 0.75}
    if "zero product" in op:
        return {"category": "Procedural Error",               "subcategory": "Incorrect zero product application", "confidence": 0.75}
    if "linear" in op:
        return {"category": "Computational Error",            "subcategory": "Sign error",                         "confidence": 0.70}
    if "quadratic" in op:
        return {"category": "Radical & Simplification Error", "subcategory": "Discriminant calculation error",     "confidence": 0.70}
    if "complet" in op or "square" in op:
        return {"category": "Procedural Error",               "subcategory": "Wrong sequence of steps",            "confidence": 0.65}
    return {"category": "Conceptual Error", "subcategory": "Other conceptual misunderstanding", "confidence": 0.50}


# Hard-coded overrides: when error_detector is confident, skip the LLM entirely.
# Maps error_type → (category, subcategory)
_FORCED = {
    "Wrong factors":                  ("Procedural Error",                "Incorrect factorization"),
    "Incorrect coefficient":          ("Common Factor Error",             "Incorrect extraction of common factor"),
    "Missing root":                   ("Procedural Error",                "Incomplete application of Zero Product Rule"),
    "Incomplete procedure":           ("Procedural Error",                "Incomplete procedure"),
    "Arithmetic mistake":             ("Computational Error",             "Arithmetic mistake"),
    "Sign error":                     ("Computational Error",             "Sign error"),
    "Wrong sequence of steps":        ("Procedural Error",                "Wrong sequence of steps"),
    "Quadratic formula misuse":       ("Procedural Error",                "Wrong sequence of steps"),
    "Radical simplification error":   ("Radical & Simplification Error",  "Incorrect square root simplification"),
    "Discriminant error":             ("Radical & Simplification Error",  "Discriminant calculation error"),
}


def classify_misconception(
    step_prev: str,
    step_wrong: str,
    operation: str,
    error_analysis: dict = None,
    retries: int = 3,
) -> dict:
    error_type = (error_analysis or {}).get("error_type", "")

    # ── Hard override: deterministic mappings that the LLM keeps getting wrong ─
    if error_type in _FORCED:
        cat, sub = _FORCED[error_type]
        return {"category": cat, "subcategory": sub, "confidence": 0.97}

    client = _get_groq_client()
    if client is None:
        return _rule_fallback(operation, error_type)

    user_msg = f"Prev:{step_prev}\nWrong:{step_wrong}\nOp:{operation}"
    if error_analysis:
        et = error_analysis.get("error_type", "")
        se = error_analysis.get("specific_error", "")
        if et: user_msg += f"\nErrorType:{et}"
        if se: user_msg += f"\nDetail:{se}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *FEW_SHOT,
        {"role": "user", "content": user_msg},
    ]

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            result = json.loads(raw)

            cat = result.get("category", "")
            sub = result.get("subcategory", "")
            if cat not in TAXONOMY:
                return _rule_fallback(operation, error_type)
            if sub not in TAXONOMY.get(cat, []):
                result["subcategory"] = TAXONOMY[cat][0]
                result["confidence"]  = max(0.0, float(result.get("confidence", 0.5)) - 0.1)

            return result

        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"[classifier] Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"[classifier] All retries failed: {e}")
                return _rule_fallback(operation, error_type)