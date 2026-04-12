"""
AlgebraCheck — FastAPI Backend
"""
import os
import traceback
from dotenv import load_dotenv

load_dotenv()  # must be before any pipeline imports

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import List

from pipeline.runner import run_pipeline

print("GROQ_API_KEY loaded:", bool(os.getenv("GROQ_API_KEY")))

# ── Single app instance ───────────────────────────────────────────────────────

app = FastAPI(title="AlgebraCheck API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()  # full traceback in terminal
    return JSONResponse(status_code=500, content={"error": str(exc)})


# ── Schemas ───────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    problem: str
    steps: List[str]

    @validator("problem")
    def problem_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Problem cannot be empty")
        return v.strip()

    @validator("steps")
    def steps_not_empty(cls, v):
        cleaned = [s.strip() for s in v if s.strip()]
        if not cleaned:
            raise ValueError("At least one step is required")
        return cleaned


class PresetItem(BaseModel):
    label: str
    difficulty: str
    problem: str
    correct: List[str]
    error: List[str]


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "AlgebraCheck API"}


@app.get("/health")
def health():
    groq_configured = bool(os.getenv("GROQ_API_KEY", ""))
    return {
        "status": "ok",
        "groq_configured": groq_configured,
        # Keep this key so frontend doesn't break if it checks it
        "openai_configured": groq_configured,
        "mode": "full (Groq/Qwen3)" if groq_configured else "fallback (rule-based)"
    }


@app.get("/presets", response_model=List[PresetItem])
def get_presets():
    return [
        # ── Easy ──────────────────────────────────────────────────────────────
        {
            "difficulty": "Easy",
            "label":   "x² − 5x + 6 = 0",
            "problem": "x^2 - 5x + 6",
            "correct": ["x^2 - 5x + 6 = 0", "(x-2)*(x-3) = 0", "x-2=0 OR x-3=0", "x=2 OR x=3"],
            "error":   ["x^2 - 5x + 6 = 0", "(x-2)*(x+3) = 0", "x-2=0 OR x+3=0", "x=2 OR x=-3"],
        },
        {
            "difficulty": "Easy",
            "label":   "x² − 9 = 0",
            "problem": "x^2 - 9",
            "correct": ["x^2 - 9 = 0", "(x-3)*(x+3) = 0", "x=3 OR x=-3"],
            "error":   ["x^2 - 9 = 0", "(x-3)*(x-3) = 0", "x=3"],
        },
        {
            "difficulty": "Easy",
            "label":   "x² − 4 = 0",
            "problem": "x^2 - 4",
            "correct": ["x^2 - 4 = 0", "(x-2)*(x+2) = 0", "x=2 OR x=-2"],
            "error":   ["x^2 - 4 = 0", "(x-2)*(x-2) = 0", "x=2"],
        },
        {
            "difficulty": "Easy",
            "label":   "x² + 5x + 6 = 0",
            "problem": "x^2 + 5x + 6",
            "correct": ["x^2 + 5x + 6 = 0", "(x+2)*(x+3) = 0", "x=-2 OR x=-3"],
            "error":   ["x^2 + 5x + 6 = 0", "(x+2)*(x+3) = 0", "x+2=0 OR x+3=0", "x=2 OR x=3"],
        },
        # ── Medium ────────────────────────────────────────────────────────────
        {
            "difficulty": "Medium",
            "label":   "x² + 2x − 8 = 0",
            "problem": "x^2 + 2x - 8",
            "correct": ["x^2 + 2x - 8 = 0", "(x+4)*(x-2) = 0", "x=-4 OR x=2"],
            "error":   ["x^2 + 2x - 8 = 0", "(x+4)*(x+2) = 0", "x=-4 OR x=-2"],
        },
        {
            "difficulty": "Medium",
            "label":   "x² − x − 12 = 0",
            "problem": "x^2 - x - 12",
            "correct": ["x^2 - x - 12 = 0", "(x-4)*(x+3) = 0", "x=4 OR x=-3"],
            "error":   ["x^2 - x - 12 = 0", "(x+4)*(x-3) = 0", "x=-4 OR x=3"],
        },
        {
            "difficulty": "Medium",
            "label":   "x² + 3x − 10 = 0",
            "problem": "x^2 + 3x - 10",
            "correct": ["x^2 + 3x - 10 = 0", "(x+5)*(x-2) = 0", "x=-5 OR x=2"],
            "error":   ["x^2 + 3x - 10 = 0", "(x+5)*(x-2) = 0", "x+5=0 OR x-2=0", "x=5 OR x=-2"],
        },
        {
            "difficulty": "Medium",
            "label":   "2x² − 8 = 0",
            "problem": "2*x^2 - 8",
            "correct": ["2x^2 - 8 = 0", "x^2 - 4 = 0", "(x-2)*(x+2) = 0", "x=2 OR x=-2"],
            "error":   ["2x^2 - 8 = 0", "x^2 - 4 = 0", "(x-2)*(x-2) = 0", "x=2"],
        },
        # ── Hard ──────────────────────────────────────────────────────────────
        {
            "difficulty": "Hard",
            "label":   "x² − 4x + 4 = 0",
            "problem": "x^2 - 4x + 4",
            "correct": ["x^2 - 4x + 4 = 0", "(x-2)^2 = 0", "x=2"],
            "error":   ["x^2 - 4x + 4 = 0", "(x-2)*(x+2) = 0", "x=2 OR x=-2"],
        },
        {
            "difficulty": "Hard",
            "label":   "2x² − 5x + 3 = 0",
            "problem": "2*x^2 - 5*x + 3",
            "correct": ["2x^2 - 5x + 3 = 0", "(2x-3)*(x-1) = 0", "x=3/2 OR x=1"],
            "error":   ["2x^2 - 5x + 3 = 0", "(2x-3)*(x-1) = 0", "2x-3=0 OR x-1=0", "x=3 OR x=1"],
        },
        {
            "difficulty": "Hard",
            "label":   "x² + 6x + 9 = 0",
            "problem": "x^2 + 6x + 9",
            "correct": ["x^2 + 6x + 9 = 0", "(x+3)^2 = 0", "x=-3"],
            "error":   ["x^2 + 6x + 9 = 0", "(x+3)*(x-3) = 0", "x=-3 OR x=3"],
        },
        {
            "difficulty": "Hard",
            "label":   "3x² − 7x + 2 = 0",
            "problem": "3*x^2 - 7*x + 2",
            "correct": ["3x^2 - 7x + 2 = 0", "(3x-1)*(x-2) = 0", "x=1/3 OR x=2"],
            "error":   ["3x^2 - 7x + 2 = 0", "(3x-1)*(x-2) = 0", "3x-1=0 OR x-2=0", "x=1 OR x=2"],
        },
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    try:
        result = run_pipeline(problem=req.problem, steps=req.steps)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))