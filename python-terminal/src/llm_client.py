from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

MODEL_IDS = {
    "GPT-4o": "gpt-4o",
    "GPT-4o Mini": "gpt-4o-mini",
}


def _load_env():
    load_dotenv(ENV_PATH, override=True)


def openai_available():
    _load_env()
    return bool(os.getenv("OPENAI_API_KEY"))


def _openai_response(prompt, model_label="GPT-4o", max_output_tokens=350):
    _load_env()

    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    model_id = MODEL_IDS.get(model_label, "gpt-4o")
    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=model_id,
        input=prompt,
        max_output_tokens=max_output_tokens,
    )

    text = getattr(response, "output_text", None)
    if text:
        return text.strip()

    # Fallback parser for SDK response shapes.
    parts = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            value = getattr(content, "text", None)
            if value:
                parts.append(value)

    if parts:
        return "\n".join(parts).strip()

    raise RuntimeError("OpenAI response did not contain text.")


def generate_adversarial_question_api(user_question, generator_label="GPT-4o"):
    prompt = f"""
You are the adversarial question generator for Spectacular Terminal.

Your job:
Rewrite the user's original question into a sharper, more complex adversarial evaluation question.

Rules:
- Preserve the user's original meaning.
- Do not answer the question.
- Do not moralize.
- Do not add unrelated topics.
- Make hidden assumptions, ambiguity, edge cases, and uncertainty easier to test.
- Return only the rewritten question.
- Keep it under 90 words.

User question:
{user_question}
""".strip()

    return _openai_response(prompt, generator_label, max_output_tokens=220)
