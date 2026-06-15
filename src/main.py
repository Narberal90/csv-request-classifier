"""
FastAPI service for classifying internal team requests via Gemini LLM.

Endpoints:
  GET  /health         — health check
  POST /classify-file  — upload a CSV file, get structured JSON + report back
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import csv
import json
from datetime import datetime
from io import StringIO

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from llm import classify_batch
from report import generate_report

BASE_DIR = Path(__file__).parent.parent  # project root
RESULTS_DIR = BASE_DIR / "results"

app = FastAPI(
    title="Request Classifier",
    description="Classifies internal team requests via Gemini LLM.",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/classify-file")
async def classify_file(file: UploadFile = File(...)):
    """Upload a CSV file (id, channel, timestamp, raw_text) and classify its rows."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    rows = list(csv.DictReader(StringIO(text)))
    if not rows:
        raise HTTPException(
            status_code=400, detail="CSV file is empty or has no data rows"
        )

    results, errors = await classify_batch(rows)

    timestamp = datetime.now().strftime("%H_%M_%S-%d-%m-%Y")
    RESULTS_DIR.mkdir(exist_ok=True)

    output_file = RESULTS_DIR / f"output_{timestamp}.json"
    output_file.write_text(
        json.dumps(results + errors, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report_text = generate_report(
        results, errors, RESULTS_DIR / f"report_{timestamp}.md"
    )

    return JSONResponse(
        {
            "total_rows": len(rows),
            "classified": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
            "report": report_text,
        }
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
