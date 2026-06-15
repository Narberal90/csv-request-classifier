import asyncio

from google import genai
from google.genai import types
from pydantic import ValidationError

from models import ClassifiedRequest, LLMClassification
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from settings import settings

_LLM_SCHEMA = LLMClassification.model_json_schema()
_client = genai.Client(api_key=settings.gemini_api_key)


async def classify_request(row: dict) -> ClassifiedRequest | str:
    """
    Classify a single CSV row via Gemini.
    Returns a ClassifiedRequest on success, or an error string on failure.
    Retries on any error according to settings.retry_delays.
    """
    user_prompt = USER_PROMPT_TEMPLATE.format(
        channel=row.get("channel", "unknown"),
        timestamp=row.get("timestamp", "unknown"),
        raw_text=row.get("raw_text", ""),
    )

    last_error = ""

    for attempt in range(settings.max_retries):
        try:
            response = await asyncio.to_thread(
                _client.models.generate_content,
                model=settings.gemini_model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_json_schema=_LLM_SCHEMA,
                ),
            )

            llm_data = LLMClassification.model_validate_json(response.text)

            return ClassifiedRequest(
                id=str(row.get("id", "")),
                channel=str(row.get("channel", "")),
                timestamp=str(row.get("timestamp", "")),
                **llm_data.model_dump(),
            )

        except ValidationError as e:
            return f"schema_mismatch: {e.error_count()} field(s) invalid"

        except Exception as e:
            last_error = str(e)

            if attempt < settings.max_retries - 1:
                delay = settings.retry_delays[attempt]
                print(
                    f"[WARN] id={row.get('id')} — error, retry "
                    + f"{attempt + 1}/{settings.max_retries - 1} in {delay}s"
                )
                await asyncio.sleep(delay)
                continue

            print(f"[ERROR] id={row.get('id')} — {last_error}")
            return last_error

    return last_error


async def classify_batch(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Classify a list of rows concurrently.
    Returns (results, errors) where both are plain dicts for JSON serialisation.
    """
    semaphore = asyncio.Semaphore(settings.concurrency)

    async def _bounded(row: dict):
        async with semaphore:
            return await classify_request(row)

    outputs = await asyncio.gather(*[_bounded(row) for row in rows])

    results, errors = [], []
    for row, result in zip(rows, outputs):
        if isinstance(result, ClassifiedRequest):
            results.append(result.model_dump(mode="json"))
        else:
            errors.append(
                {
                    "id": row.get("id"),
                    "error": True,
                    "reason": result,
                    "raw_text": row.get("raw_text"),
                }
            )

    return results, errors
