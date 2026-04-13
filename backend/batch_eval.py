"""
batch_eval.py — Run the full pipeline on a curated set of 100 entries
spread evenly across the dataset (25 per error type) for expert review.

Usage (from backend/ folder):
    python batch_eval.py

Output:
    eval_results.json   — all results so far, appended each run
    eval_summary.json   — counts and stats
    eval_progress.json  — tracks which indices have been completed
"""

import json
import time
import sys
import os
from datetime import datetime
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from pipeline.runner import run_pipeline

# ── Config ────────────────────────────────────────────────────────────────────

DATASET_PATH  = r"C:\mariam\uni\bachelor\algebra-error-detector\dataset\quadratic_dataset.json"
OUTPUT_PATH   = r"C:\mariam\uni\bachelor\algebra-error-detector\eval_results2.json"
SUMMARY_PATH  = r"C:\mariam\uni\bachelor\algebra-error-detector\eval_summary.json"
PROGRESS_PATH = r"C:\mariam\uni\bachelor\algebra-error-detector\eval_progress2.json"

DELAY_SECONDS = 2.0   # pause between entries — increase if hitting rate limits

# ── Selected indices — 25 per error type, spread across full dataset ──────────

SELECTED_INDICES = sorted([
    # Arithmetic errors (25 original + 13 + 5 new = 43)
    402, 465, 528, 591, 654, 717, 780, 843, 906, 969,
    1032, 1095, 1158, 1221, 1284, 1347, 1410, 1473, 1536, 1599,
    1662, 1725, 1788, 1851, 1914,
    3, 150, 297, 451, 619, 787, 948, 1116, 1277, 1445, 1613, 1774, 1942,
    472, 801, 1130, 1459, 1795,
    # Radical errors (25 original + 13 + 5 new = 43)
    400, 467, 533, 600, 666, 733, 799, 866, 932, 999,
    1065, 1132, 1198, 1265, 1331, 1398, 1464, 1531, 1597, 1664,
    1730, 1797, 1863, 1930, 1996,
    1, 155, 309, 470, 631, 792, 957, 1118, 1282, 1443, 1608, 1769, 1933,
    218, 789, 1114, 1440, 1765,
    # Factorization errors (25 original + 12 + 4 new = 41)
    401, 468, 534, 601, 667, 734, 800, 867, 933, 1000,
    1066, 1133, 1199, 1266, 1332, 1399, 1465, 1532, 1598, 1665,
    1731, 1798, 1864, 1931, 1997,
    2, 167, 331, 503, 678, 849, 1024, 1196, 1371, 1546, 1717, 1892,
    58, 877, 1287, 1696,
    # Correct / incomplete (25 original — unchanged)
    403, 469, 536, 602, 669, 735, 802, 868, 935, 1001,
    1068, 1134, 1201, 1267, 1334, 1400, 1467, 1533, 1600, 1666,
    1733, 1799, 1866, 1932, 1999,
])

# ── Load dataset ──────────────────────────────────────────────────────────────

with open(DATASET_PATH, encoding="utf-8") as f:
    dataset = json.load(f)

# ── Load progress — find which indices are already done ───────────────────────

if os.path.exists(PROGRESS_PATH):
    with open(PROGRESS_PATH) as f:
        progress = json.load(f)
    completed = set(progress.get("completed_indices", []))
else:
    completed = set()

# ── Load existing results ─────────────────────────────────────────────────────

if os.path.exists(OUTPUT_PATH):
    with open(OUTPUT_PATH, encoding="utf-8") as f:
        results = json.load(f)
    print(f"Loaded {len(results)} existing results")
else:
    results = []

# ── Filter to only indices not yet done ───────────────────────────────────────

todo = [idx for idx in SELECTED_INDICES if idx not in completed]

if not todo:
    print("All selected entries have been processed!")
    sys.exit(0)

print(f"Selected indices: {len(SELECTED_INDICES)} total")
print(f"Already done:     {len(completed)}")
print(f"Remaining:        {len(todo)}")
print(f"Starting at:      {datetime.now().strftime('%H:%M:%S')}")
print("-" * 60)

# ── Run pipeline ──────────────────────────────────────────────────────────────

errors = []

for i, idx in enumerate(todo):
    entry    = dataset[idx]
    equation = entry.get("equation", "")
    steps    = entry.get("steps", [])

    print(f"[{i+1}/{len(todo)}] (dataset #{idx}) {equation[:45]}", end="  ")

    try:
        result = run_pipeline(problem=equation, steps=steps)

        record = {
            "entry_index":   idx,
            "equation":      equation,
            "student_steps": steps,
            "all_correct":   result.get("all_correct", True),
        }

        if not result.get("all_correct", True):
            record.update({
                "error_at_step":     result.get("error_step_num"),
                "wrong_step":        result.get("error_step_text"),
                "operation":         result.get("operation"),
                "error_type":        result.get("error_analysis", {}).get("error_type"),
                "error_detail":      result.get("error_analysis", {}).get("specific_error"),
                "misconception":     result.get("misconception", {}).get("category"),
                "misconception_sub": result.get("misconception", {}).get("subcategory"),
                "confidence":        result.get("misconception", {}).get("confidence"),
                "correct_steps":     result.get("correction", {}).get("continuation", []),
                "feedback":          result.get("feedback"),
            })
            print(f"ERROR at step {result.get('error_step_num')} — {result.get('error_analysis', {}).get('error_type', '?')}")
        else:
            print("✓ correct")

        results.append(record)

    except Exception as e:
        print(f"FAILED: {e}")
        errors.append({"entry_index": idx, "equation": equation, "error": str(e)})
        results.append({
            "entry_index":    idx,
            "equation":       equation,
            "student_steps":  steps,
            "pipeline_error": str(e)
        })

    # Save results and progress after every single entry
    completed.add(idx)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    with open(PROGRESS_PATH, "w") as f:
        json.dump({
            "completed_indices": sorted(list(completed)),
            "total_selected":    len(SELECTED_INDICES),
            "total_done":        len(completed),
            "remaining":         len(SELECTED_INDICES) - len(completed),
            "last_updated":      datetime.now().isoformat(),
        }, f, indent=2)

    time.sleep(DELAY_SECONDS)

# ── Build and save summary ────────────────────────────────────────────────────

total_correct = sum(1 for r in results if r.get("all_correct") and "pipeline_error" not in r)
total_errors  = sum(1 for r in results if not r.get("all_correct") and "pipeline_error" not in r)
total_failed  = sum(1 for r in results if "pipeline_error" in r)
total_done    = len(results)

error_types    = Counter(r.get("error_type")    for r in results if r.get("error_type"))
misconceptions = Counter(r.get("misconception") for r in results if r.get("misconception"))
operations     = Counter(r.get("operation")     for r in results if r.get("operation"))

summary = {
    "last_updated":       datetime.now().isoformat(),
    "total_selected":     len(SELECTED_INDICES),
    "total_processed":    total_done,
    "remaining":          len(SELECTED_INDICES) - len(completed),
    "correct_solutions":  total_correct,
    "errors_detected":    total_errors,
    "pipeline_failures":  total_failed,
    "detection_rate":     f"{total_errors / (total_done - total_failed) * 100:.1f}%" if (total_done - total_failed) > 0 else "N/A",
    "error_type_counts":     dict(error_types.most_common()),
    "misconception_counts":  dict(misconceptions.most_common()),
    "operation_counts":      dict(operations.most_common()),
    "pipeline_errors":       errors,
}

with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

# ── Print summary ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print(f"DONE — {len(todo)} entries processed this run")
print(f"  Total selected:     {len(SELECTED_INDICES)}")
print(f"  Total done so far:  {len(completed)}")
print(f"  Remaining:          {len(SELECTED_INDICES) - len(completed)}")
print(f"  Correct:            {total_correct}")
print(f"  Errors detected:    {total_errors}")
print(f"  Pipeline failures:  {total_failed}")
print(f"  Detection rate:     {summary['detection_rate']}")
print(f"\nError type breakdown:")
for k, v in error_types.most_common():
    print(f"  {v:4d}  {k}")
print(f"\nMisconception breakdown:")
for k, v in misconceptions.most_common():
    print(f"  {v:4d}  {k}")
print(f"\nResults: {OUTPUT_PATH}")
print(f"Summary: {SUMMARY_PATH}")
print(f"Finished at: {datetime.now().strftime('%H:%M:%S')}")
if len(completed) < len(SELECTED_INDICES):
    print(f"\nRun again to continue from where you left off.")
else:
    print(f"\nAll {len(SELECTED_INDICES)} entries complete!")