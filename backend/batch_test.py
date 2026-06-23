"""
batch_test.py — Run quadratic_1200.json through the AlgebraCheck pipeline.

Features:
  - Resumes from last saved entry (safe to re-run after interruption)
  - Saves progress after every entry
  - Outputs results in the same format as the original results.json
  - Prints a live summary as it runs

Usage:
  python batch_test.py
  python batch_test.py --input quadratic_1200.json --output batch_results.json
  python batch_test.py --limit 50          # test first 50 entries only
  python batch_test.py --delay 0.5         # add 0.5s between calls (rate limiting)
"""

import json
import time
import argparse
import os
import sys
import traceback
from pathlib import Path
from datetime import datetime

# ── Make sure the project root is on sys.path so pipeline imports work ───────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from pipeline.runner import run_pipeline


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_dataset(path: str) -> list:
    with open(path, "r") as f:
        return json.load(f)


def load_progress(path: str) -> list:
    """Load existing results file (returns [] if not found or empty)."""
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []


def save_progress(results: list, path: str):
    """Atomically write results to disk."""
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(results, f, indent=2)
    os.replace(tmp, path)  # atomic on all major OS


def format_result(entry_index: int, entry: dict, pipeline_output: dict) -> dict:
    """
    Map the pipeline output dict → the target result format.
    """
    equation   = entry["equation"]
    steps      = entry["steps"]
    all_correct = pipeline_output.get("all_correct", False)

    # ── Correct submission ────────────────────────────────────────────────────
    if all_correct:
        return {
            "entry_index": entry_index,
            "equation":    equation,
            "student_steps": steps,
            "all_correct": True,
            "error_at_step": None,
            "wrong_step":    None,
            "operation":     None,
            "error_type":    None,
            "misconception": None,
            "misconception_sub": None,
            "confidence":    None,
            "correct_steps": None,
            "feedback":      None,
        }

    # ── Incorrect submission ──────────────────────────────────────────────────
    err_idx     = pipeline_output.get("first_error_index")
    error_analysis  = pipeline_output.get("error_analysis", {})
    misconception   = pipeline_output.get("misconception", {})
    correction      = pipeline_output.get("correction", {})

    return {
        "entry_index":      entry_index,
        "equation":         equation,
        "student_steps":    steps,
        "all_correct":      False,
        "error_at_step":    err_idx,
        "wrong_step":       pipeline_output.get("error_step_text", ""),
        "operation":        pipeline_output.get("operation", ""),
        "error_type":       error_analysis.get("error_type", ""),
        "misconception":    misconception.get("category", ""),
        "misconception_sub": misconception.get("subcategory", ""),
        "confidence":       misconception.get("confidence", 0.0),
        "correct_steps":    correction.get("full_solution", []),
        "feedback":         pipeline_output.get("feedback", ""),
    }


def print_summary_row(idx: int, total: int, result: dict, elapsed: float):
    status = "✓" if result["all_correct"] else "✗"
    misc   = result.get("misconception") or "-"
    print(
        f"[{idx:>4}/{total}] {status}  "
        f"{result['equation'][:35]:<35}  "
        f"{misc:<30}  "
        f"{elapsed:.1f}s"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Batch test AlgebraCheck pipeline")
    parser.add_argument("--input",   default="quadratic_1200.json",  help="Dataset JSON file")
    parser.add_argument("--output",  default="batch_results.json",   help="Output results JSON file")
    parser.add_argument("--limit",   type=int, default=None,          help="Only process first N entries")
    parser.add_argument("--delay",   type=float, default=0.0,         help="Seconds to wait between entries")
    parser.add_argument("--restart", action="store_true",             help="Ignore saved progress and start fresh")
    args = parser.parse_args()

    # ── Load dataset ──────────────────────────────────────────────────────────
    print(f"\n{'─'*70}")
    print(f"  AlgebraCheck Batch Tester")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'─'*70}")

    dataset = load_dataset(args.input)
    if args.limit:
        dataset = dataset[: args.limit]
    total = len(dataset)
    print(f"  Dataset:  {args.input}  ({total} entries)")
    print(f"  Output:   {args.output}")

    # ── Resume or restart ─────────────────────────────────────────────────────
    if args.restart:
        results = []
        print("  Mode:     fresh start (--restart)\n")
    else:
        results = load_progress(args.output)
        done_indices = {r["entry_index"] for r in results}
        print(f"  Resumed:  {len(results)} entries already done\n")

    done_indices = {r["entry_index"] for r in results}

    # ── Stats counters ────────────────────────────────────────────────────────
    n_correct  = sum(1 for r in results if r.get("all_correct"))
    n_error    = sum(1 for r in results if not r.get("all_correct"))
    n_failed   = 0   # pipeline exceptions

    print(f"  {'IDX':>4}  ST  {'EQUATION':<35}  {'MISCONCEPTION':<30}  TIME")
    print(f"  {'─'*4}  ──  {'─'*35}  {'─'*30}  ────")

    for entry in dataset:
        # dataset entries have "id" key; use 1-based index matching entry["id"]
        entry_index = entry.get("id", dataset.index(entry) + 1)

        if entry_index in done_indices:
            continue  # already processed

        t0 = time.time()
        try:
            # The pipeline expects the problem string and a list of steps
            pipeline_out = run_pipeline(
                problem=entry["equation"],
                steps=entry["steps"],
            )
            result = format_result(entry_index, entry, pipeline_out)

            if result["all_correct"]:
                n_correct += 1
            else:
                n_error += 1

        except Exception as exc:
            n_failed += 1
            result = {
                "entry_index":   entry_index,
                "equation":      entry["equation"],
                "student_steps": entry["steps"],
                "pipeline_error": str(exc),
                "traceback":     traceback.format_exc(),
            }
            print(f"  [{'ERR':>4}] ✗  {entry['equation'][:35]:<35}  PIPELINE EXCEPTION")
            traceback.print_exc()

        elapsed = time.time() - t0
        results.append(result)
        done_indices.add(entry_index)

        # ── Save after every single entry ─────────────────────────────────────
        save_progress(results, args.output)

        print_summary_row(entry_index, total, result, elapsed)

        if args.delay > 0:
            time.sleep(args.delay)

    # ── Final summary ─────────────────────────────────────────────────────────
    processed = n_correct + n_error + n_failed
    print(f"\n{'─'*70}")
    print(f"  Done.  {processed}/{total} entries processed")
    print(f"  ✓ Correct:    {n_correct}")
    print(f"  ✗ Incorrect:  {n_error}")
    if n_failed:
        print(f"  ⚠ Errors:     {n_failed}  (see 'pipeline_error' field in output)")
    print(f"  Saved to:     {args.output}")
    print(f"{'─'*70}\n")


if __name__ == "__main__":
    main()