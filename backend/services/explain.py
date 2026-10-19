import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Always load backend/.env regardless of process cwd.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

_client = None
_executor = ThreadPoolExecutor(max_workers=2)
GEMINI_TIMEOUT_SEC = float(os.getenv("GEMINI_TIMEOUT_SEC", "4"))
# Kids mode should never spin for long in the UI.
KIDS_GEMINI_TIMEOUT_SEC = float(os.getenv("KIDS_GEMINI_TIMEOUT_SEC", "3"))


class ExplanationServiceUnavailable(RuntimeError):
    pass


def _get_client():
    global _client

    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")

        if (
            not api_key
            or api_key.strip() in {"", "your_gemini_api_key_here"}
            or api_key.lower().startswith("your_")
        ):
            raise ExplanationServiceUnavailable(
                "GEMINI_API_KEY is missing from .env"
            )

        _client = genai.Client(api_key=api_key)

    return _client


def _run_with_timeout(fn, timeout: float = GEMINI_TIMEOUT_SEC):
    future = _executor.submit(fn)
    try:
        return future.result(timeout=timeout)
    except FuturesTimeout as exc:
        future.cancel()
        raise ExplanationServiceUnavailable(
            f"Gemini timed out after {timeout:.0f}s"
        ) from exc


def generate_explanation(
    selected_text: str,
    context: list,
):
    """Generate an educational explanation using Gemini."""
    client = _get_client()
    context_text = "\n".join(item["text"] for item in context)

    prompt = f"""
You are an educational assistant helping a student
understand a textbook.

The student selected:

"{selected_text}"

Nearby text from the textbook:

{context_text}

Explain the selected text in simple,
student-friendly language.

Rules:

1. Focus mainly on the selected text.
2. Use the nearby textbook text to understand its context.
3. Do not explain unrelated text.
4. If the selected text is part of a poem, story,
   dialogue, example, or passage, explain its meaning
   in that context.
5. If the selected text is a phrase, explain what
   the phrase means.
6. Do not invent information.
7. Keep the explanation concise and easy to understand.
8. Give a simple example when useful.

Return only the explanation.
"""

    def _call():
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt,
        )
        return interaction.output_text

    return _run_with_timeout(_call)


def generate_rhyme_kids_explanation(
    selected_text: str,
    selected_type: str,
    context: list,
    rhyme_title: str | None = None,
    rhyme_text: str | None = None,
    object_meta: dict | None = None,
):
    """Child-friendly rhyme / illustration explanation."""
    client = _get_client()
    context_text = "\n".join(
        item.get("text", "") for item in context if item.get("text")
    )
    title = rhyme_title or "this rhyme"
    full = rhyme_text or context_text
    meta = object_meta or {}

    if selected_type == "object":
        category = (meta.get("attributes") or {}).get("category", "thing")
        hint = meta.get("relation_hint") or "in the picture"
        prompt = f"""
You help young children (ages 5-8) learn English from nursery rhyme picture books.

The child tapped a picture of: "{selected_text}"
Category hint: {category}
Where it is in the picture/rhyme: {hint}
Rhyme title: {title}
Rhyme text:
{full}

Nearby words:
{context_text}

Write 2-4 short sentences a child can understand.
Explain what the tapped thing is (for example: it is a monkey, which is an animal)
and how it relates to the rhyme picture (for example: it is sitting on the tree / bed).
Use warm, simple words. No scary language. Return only the explanation.
"""
    else:
        prompt = f"""
You help young children (ages 5-8) learn English from nursery rhyme picture books.

The child tapped the word: "{selected_text}"
Rhyme title: {title}
Full rhyme:
{full}

Nearby words from the page:
{context_text}

Explain what this word means in this rhyme, in 2-4 short sentences.
Use the rhyme context. Keep language playful and simple.
Return only the explanation.
"""

    def _call():
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt,
        )
        return interaction.output_text

    return _run_with_timeout(_call, timeout=KIDS_GEMINI_TIMEOUT_SEC)


def fallback_rhyme_kids_explanation(
    selected_text: str,
    selected_type: str,
    object_meta: dict | None = None,
    rhyme_title: str | None = None,
) -> str:
    """Offline-friendly explanation when Gemini is unavailable."""
    title = rhyme_title or "the rhyme"
    if selected_type == "object":
        meta = object_meta or {}
        category = (meta.get("attributes") or {}).get("category", "thing")
        hint = meta.get("relation_hint") or "in the picture"
        pretty = {
            "animal": "an animal",
            "character": "a character in the rhyme",
            "place": "a place",
            "object": "a thing",
            "sky": "something in the sky",
            "weather": "weather",
        }.get(category, "something in the picture")
        return (
            f"This is a {selected_text}. It is {pretty}. "
            f"In {title}, you can see it {hint}. "
            f"Tap words in the rhyme to learn what they mean!"
        )
    return (
        f'In {title}, the word "{selected_text}" is part of the rhyme. '
        f"Say it out loud and look at the picture to understand the story."
    )


def fallback_text_explanation(selected_text: str, context: list) -> str:
    """Fallback when Gemini fails on uploaded documents."""
    neighbors = [
        item.get("text", "").strip()
        for item in context
        if item.get("text") and item.get("text") != selected_text
    ][:6]
    nearby = ", ".join(neighbors) if neighbors else "the surrounding text"
    return (
        f'The selected word is "{selected_text}". '
        f"Nearby words on the page include: {nearby}. "
        f"Read those words together to understand what this part of the page means."
    )
