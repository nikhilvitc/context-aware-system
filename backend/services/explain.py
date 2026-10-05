import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

_client = None


class ExplanationServiceUnavailable(RuntimeError):
    pass


def _get_client():
    global _client

    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ExplanationServiceUnavailable(
                "GEMINI_API_KEY is missing from .env"
            )

        _client = genai.Client(api_key=api_key)

    return _client


def generate_explanation(
    selected_text: str,
    context: list,
):
    """
    Generate an educational explanation using Gemini.
    """

    client = _get_client()

    context_text = "\n".join(
        item["text"]
        for item in context
    )

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

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
    )

    return interaction.output_text
