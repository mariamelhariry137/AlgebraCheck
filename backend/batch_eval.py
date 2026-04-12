"""
batch_eval.py — Run the full pipeline on the dataset, 50 entries at a time.

Resumes exactly where it left off — safe to stop and restart anytime.
Progress is saved after EVERY entry so nothing is lost.

Usage (from backend/ folder):
    python batch_eval.py

Each run processes the next 50 unprocessed entries.
Run again and again until all entries are done.

Output:
    eval_results.json   — all results so far
    eval_progress.json  — tracks completed indices
    eval_summary.json   — stats overview
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
SUMMARY_PATH  = r"C:\mariam\uni\bachelor\algebra-error-detector\eval_summary2.json"
PROGRESS_PATH = r"C:\mariam\uni\bachelor\algebra-error-detector\eval_progress2.json"

BATCH_SIZE    = 50
DELAY_SECONDS = 2.0   # pause between entries — increase if hitting API rate limits


# ── Load dataset ──────────────────────────────────────────────────────────────

with open(DATASET_PATH, encoding="utf-8") as f:
    dataset = json.load(f)

total_dataset = len(dataset)

# ── Load progress ─────────────────────────────────────────────────────────────

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
    # handle both plain list and wrapped format
    if isinstance(results, dict):
        results = results.get("results", [])
    print(f"Loaded {len(results)} existing results")
else:
    results = []

# ── Find next batch of unprocessed entries ────────────────────────────────────

todo = [i for i in range(total_dataset) if i not in completed]

if not todo:
    print(f"All {total_dataset} entries already processed.")
    sys.exit(0)

batch = todo[:BATCH_SIZE]
start_idx = batch[0]
end_idx   = batch[-1]

print(f"AlgebraCheck — Batch Evaluation")
print(f"{'─' * 60}")
print(f"Dataset total:    {total_dataset} entries")
print(f"Already done:     {len(completed)}")
print(f"This batch:       entries {start_idx} – {end_idx}  ({len(batch)} entries)")
print(f"Remaining after:  {len(todo) - len(batch)}")
print(f"Mode:             {'GPT-4 Active' if os.getenv('OPENAI_API_KEY') else 'Rule-Based Fallback'}")
print(f"{'─' * 60}\n")


# ── Helper: save progress + results after each entry ─────────────────────────

def save_all(results, completed):
    # Save results
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Save progress
    with open(PROGRESS_PATH, "w") as f:
        json.dump({
            "completed_indices": sorted(list(completed)),
            "total_dataset":     total_dataset,
            "total_done":        len(completed),
            "remaining":         total_dataset - len(completed),
            "last_updated":      datetime.now().isoformat(),
        }, f, indent=2)


# ── Run pipeline on each entry in batch ───────────────────────────────────────

pipeline_errors = []

for i, idx in enumerate(batch):
    entry    = dataset[idx]
    equation = entry.get("equation", "")
    steps    = entry.get("steps", [])

    print(f"[{i+1:>2}/{len(batch)}] #{idx:<4}  {equation[:50]}", end="  ")
    sys.stdout.flush()

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
            print(f"✗ step {result.get('error_step_num')} — {result.get('error_analysis', {}).get('error_type', '?')}")
        else:
            print("✓ correct")

        results.append(record)

    except Exception as e:
        print(f"⚠ FAILED: {e}")
        pipeline_errors.append({"entry_index": idx, "equation": equation, "error": str(e)})
        results.append({
            "entry_index":    idx,
            "equation":       equation,
            "student_steps":  steps,
            "all_correct":    None,
            "pipeline_error": str(e)
        })

    # Save after every single entry
    completed.add(idx)
    save_all(results, completed)

    if DELAY_SECONDS and i < len(batch) - 1:
        time.sleep(DELAY_SECONDS)


# ── Build and save summary ────────────────────────────────────────────────────

total_correct = sum(1 for r in results if r.get("all_correct") is True)
total_errors  = sum(1 for r in results if r.get("all_correct") is False and "pipeline_error" not in r)
total_failed  = sum(1 for r in results if "pipeline_error" in r)
total_done    = len(results)

error_types    = Counter(r.get("error_type")    for r in results if r.get("error_type"))
misconceptions = Counter(r.get("misconception") for r in results if r.get("misconception"))
operations     = Counter(r.get("operation")     for r in results if r.get("operation"))

valid = total_done - total_failed
detection_rate = f"{total_errors / valid * 100:.1f}%" if valid > 0 else "N/A"

summary = {
    "last_updated":      datetime.now().isoformat(),
    "total_dataset":     total_dataset,
    "total_processed":   total_done,
    "remaining":         total_dataset - len(completed),
    "correct":           total_correct,
    "errors_detected":   total_errors,
    "pipeline_failures": total_failed,
    "detection_rate":    detection_rate,
    "error_type_counts":    dict(error_types.most_common()),
    "misconception_counts": dict(misconceptions.most_common()),
    "operation_counts":     dict(operations.most_common()),
    "pipeline_errors":      pipeline_errors,
}

with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)


# ── Print summary ─────────────────────────────────────────────────────────────

remaining_after = total_dataset - len(completed)
batches_left    = (remaining_after + BATCH_SIZE - 1) // BATCH_SIZE

print(f"\n{'─' * 60}")
print(f"Batch complete — entries {start_idx}–{end_idx} saved")
print(f"\n  Total processed:   {total_done} / {total_dataset}")
print(f"  ✓ Correct:         {total_correct}")
print(f"  ✗ Errors detected: {total_errors}")
print(f"  ⚠ Failed:          {total_failed}")
print(f"  Detection rate:    {detection_rate}")

if error_types:
    print(f"\n  Error type breakdown:")
    for k, v in error_types.most_common():
        print(f"    {v:4d}  {k}")

if misconceptions:
    print(f"\n  Misconception breakdown:")
    for k, v in misconceptions.most_common():
        print(f"    {v:4d}  {k}")

print(f"\n  Results:  {OUTPUT_PATH}")
print(f"  Summary:  {SUMMARY_PATH}")
print(f"  Progress: {PROGRESS_PATH}")

if remaining_after > 0:
    print(f"\n  {remaining_after} entries remaining ({batches_left} batch{'es' if batches_left > 1 else ''} of {BATCH_SIZE})")
    print(f"  Run again to continue.")
else:
    print(f"\n  All {total_dataset} entries complete!")