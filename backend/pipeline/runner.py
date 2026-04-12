"""Pipeline Runner — orchestrates all stages in order."""
import sympy as sp
from .digitizer          import digitize_equation
from .step_parser        import parse_all_operations
from .validator          import validate_all_steps
from .error_detector     import detect_first_error, get_retained_steps, get_error_context
from .error_detector  import detect_error_o1          # Stage 7 — o1
from .classifier         import classify_misconception    # Stage 8 — gpt-4o
from .corrector          import generate_correct_steps, format_correction
from .feedback           import generate_feedback         # Stage 10 — gpt-4o


def run_pipeline(problem: str, steps: list) -> dict:
    """
    Full pipeline:

    Stage 1  — Digitize (SymPy)
    Stage 2  — Step Parser (gpt-4o): label each operation
    Stage 3  — Symbolic Validation (SymPy): check each step
    Stage 4  — First Error Detection (Python): find first wrong step
    Stage 5  — Step Retention (Python): keep correct steps
    Stage 6  — Correction Generation (SymPy): generate correct answer
    Stage 7  — Error Detection (o1): identify specific mathematical error
    Stage 8  — Misconception Classification (gpt-4o): map to taxonomy
    Stage 9  — Correction formatting
    Stage 10 — Feedback Generation (gpt-4o): write student explanation
    """
    steps = [s.strip() for s in steps if s.strip()]
    if not steps:
        return {"error": "No steps provided"}

    # ── Stage 2: Label operations ────────────────────────────────────────────
    operations  = parse_all_operations(steps)
    op_by_index = {r["step_index"]: r["operation"] for r in operations}

    # ── Stage 3: Validate symbolically ──────────────────────────────────────
    validation  = validate_all_steps(steps)
    # Convert valid/invalid → status field that the rest of the pipeline expects
    for item in validation:
        item["status"] = "correct" if item.get("valid", False) else "incorrect"

    # ── Stage 4: Find first error ────────────────────────────────────────────
    detection   = detect_first_error(validation)

    err_idx = detection.get("first_error_index")

    annotated_steps = [
        {
            "step_index": s["step_index"],
            "step":       s["step"],
            "status": (
                s["status"]
                if err_idx is None or s["step_index"] < err_idx
                else "incorrect" if s["step_index"] == err_idx
                else "derived_from_error"
            ),
            "operation":  op_by_index.get(s["step_index"], "Initial"),
            "reason":     s.get("reason", "")
        }
        for s in detection["steps"]
    ]

    if detection["all_correct"]:
        return {
            "all_correct": True,
            "problem":     problem,
            "steps":       annotated_steps,
        }

    # ── Error found — gather context ─────────────────────────────────────────
    err_idx    = detection["first_error_index"]
    err_ctx    = get_error_context(steps, err_idx)
    step_prev  = err_ctx.get("step_prev", "")
    step_wrong = err_ctx.get("step_wrong", "")
    operation  = op_by_index.get(err_idx, "Unknown")

    # ── Stage 5 & 6: Retain correct steps, generate correction ───────────────
    retained     = get_retained_steps(steps, err_idx)
    continuation = generate_correct_steps(step_prev)
    correction   = format_correction(retained, continuation)

    # ── Stage 7: o1 identifies the specific mathematical error ───────────────
    error_analysis = detect_error_o1(
        step_prev=step_prev,
        step_wrong=step_wrong,
        operation=operation,
        correct_continuation=continuation
    )

    # ── Stage 8: Classify misconception (now with o1 context) ────────────────
    classification = classify_misconception(
        step_prev=step_prev,
        step_wrong=step_wrong,
        operation=operation,
        error_analysis=error_analysis      # ← richer context from o1
    )

    # ── Stage 10: Generate feedback (now with o1 context) ────────────────────
    feedback = generate_feedback(
        step_prev=step_prev,
        step_wrong=step_wrong,
        step_num=err_idx + 1,
        operation=operation,
        misconception_category=classification.get("category", ""),
        misconception_subcategory=classification.get("subcategory", ""),
        correct_continuation=continuation,
        error_analysis=error_analysis      # ← richer context from o1
    )

    return {
        "all_correct":       False,
        "problem":           problem,
        "steps":             annotated_steps,
        "first_error_index": err_idx,
        "error_step_num":    err_idx + 1,
        "error_step_text":   step_wrong,
        "operation":         operation,
        "error_analysis": {                # ← new: o1 output visible in response
            "error_type":     error_analysis.get("error_type", ""),
            "specific_error": error_analysis.get("specific_error", ""),
            "correct_step":   error_analysis.get("correct_step", ""),
            "reasoning":      error_analysis.get("reasoning", "")
        },
        "misconception": {
            "category":    classification.get("category", ""),
            "subcategory": classification.get("subcategory", ""),
            "confidence":  classification.get("confidence", 0.0)
        },
        "correction": {
            "retained":      correction["retained"],
            "continuation":  correction["continuation"],
            "full_solution": correction["full_solution"]
        },
        "feedback": feedback
    }