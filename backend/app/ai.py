import httpx
from .config import settings


DISCLAIMER = "Informational only; this is not a medical diagnosis."


class AssessmentFailure(Exception):
    pass


async def assess_blood_values(glucose: float, haemoglobin: float, cholesterol: float) -> str:
    if not settings.ai_api_key:
        raise AssessmentFailure("AI provider is not configured. Set AI_API_KEY in the backend environment.")
    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": "You explain possible risk indicators from three blood values only. Do not diagnose disease, claim certainty, or invent patient context. Return one or two short plain-language sentences. Mention that clinical interpretation depends on units, reference ranges, and patient context."},
            {"role": "user", "content": f"Glucose: {glucose}; haemoglobin: {haemoglobin}; cholesterol: {cholesterol}. Identify possible risk indicators without a diagnosis."},
        ],
        "temperature": 0.2,
        "max_tokens": 160,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{settings.ai_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.ai_api_key}"},
                json=payload,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
    except httpx.TimeoutException:
        raise AssessmentFailure("AI provider timed out. Try again later.") from None
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status in (401, 403):
            message = "AI provider authentication failed. Check backend configuration."
        elif status == 429:
            message = "AI provider rate limit reached. Try again later."
        elif status == 404:
            message = "AI model or endpoint is unavailable. Check AI_MODEL and AI_BASE_URL."
        else:
            message = "AI provider request failed. Try again later."
        raise AssessmentFailure(message) from None
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        raise AssessmentFailure("AI provider returned an invalid response or could not be reached.") from None
    if not isinstance(content, str) or not content.strip() or len(content) > 2000:
        raise AssessmentFailure("AI provider returned an invalid assessment.")
    return f"{content.strip()} {DISCLAIMER}"
