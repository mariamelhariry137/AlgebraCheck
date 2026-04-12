"""Stage 10 — Feedback Generator"""
import json, time

SYSTEM_PROMPT = ('Math tutor. Explain algebra mistake in 3 steps, conversational and warm.\n'
    'Structure:\nStep 1: what went wrong and why\nStep 2: rule/concept to understand\nStep 3: how to get correct answer\n'
    'Rules: 1-2 sentences per step, no LaTeX, use ^ for powers, encouraging tone.\n'
    'Respond ONLY with JSON: {"feedback":"Step 1: ...\\nStep 2: ...\\nStep 3: ..."}')


def _get_groq_client():
    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()
        return Groq()
    except Exception as e:
        print(f"[feedback] Groq client error: {e}")
        return None


def _template_fallback(step_prev, step_wrong, step_num, operation,
                        misconception_category, misconception_subcategory,
                        correct_continuation) -> str:
    print("[feedback] USING TEMPLATE FALLBACK")
    correct_str = " → ".join(correct_continuation) if correct_continuation else "see correct steps above"
    return (f"Step 1: At step {step_num}, {misconception_subcategory} occurred during {operation}.\n"
            f"Step 2: Make sure each transformation is mathematically valid.\n"
            f"Step 3: From '{step_prev}', the correct path is: {correct_str}.")


def generate_feedback(step_prev: str, step_wrong: str, step_num: int,
                       operation: str, misconception_category: str,
                       misconception_subcategory: str, correct_continuation: list,
                       error_analysis: dict = None, retries: int = 3) -> str:
    client = _get_groq_client()
    if client is None:
        return _template_fallback(step_prev, step_wrong, step_num, operation,
                                  misconception_category, misconception_subcategory,
                                  correct_continuation)

    print(f"[feedback] Calling Groq — op={operation}, cat={misconception_category}")

    correct_str = " → ".join(correct_continuation) if correct_continuation else "N/A"

    # Compact user message
    user_msg = (f"Step {step_num} error.\n"
                f"Prev:{step_prev}\nWrong:{step_wrong}\n"
                f"Op:{operation}\nError:{misconception_category}—{misconception_subcategory}\n"
                f"Correct:{correct_str}")

    if error_analysis:
        se = error_analysis.get('specific_error', '') or error_analysis.get('error_detail', '')
        if se: user_msg += f"\nDetail:{se}"

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content.strip()
            print(f"[feedback] Raw: {raw[:80]}")
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"): raw = raw[4:]
                raw = raw.strip()
            return json.loads(raw)["feedback"]

        except Exception as e:
            if attempt < retries - 1:
                print(f"[feedback] Attempt {attempt+1} failed: {e}. Retrying in {2**attempt}s...")
                time.sleep(2 ** attempt)
            else:
                print(f"[feedback] All retries failed: {e}")
                return _template_fallback(step_prev, step_wrong, step_num, operation,
                                          misconception_category, misconception_subcategory,
                                          correct_continuation)