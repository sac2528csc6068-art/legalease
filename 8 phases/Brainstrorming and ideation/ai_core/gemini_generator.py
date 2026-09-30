from __future__ import annotations

import time

from config import get_settings


class GeminiGenerationError(RuntimeError):
    """Raised when Gemini cannot generate a document."""


class GeminiDocumentGenerator:
    """
    Generates legal documents using Google's Gemini API.

    Supports:
    - Gemini API key configuration
    - Configurable Gemini model
    - Automatic retries for temporary 503/429 errors
    - Clear error messages
    """

    def __init__(self, settings=None):
        """
        Initialize the Gemini document generator.

        The settings argument is optional so the class works with:
            GeminiDocumentGenerator()
        or:
            GeminiDocumentGenerator(settings)
        """

        self.settings = settings or get_settings()
        self.client = None

        if not self.settings.gemini_api_key:
            return

        try:
            from google import genai

            self.client = genai.Client(
                api_key=self.settings.gemini_api_key
            )

        except ImportError as exc:
            raise GeminiGenerationError(
                "The google-genai package is not installed. "
                "Run: python -m pip install google-genai"
            ) from exc

        except Exception as exc:
            raise GeminiGenerationError(
                f"Could not initialize Gemini client: {exc}"
            ) from exc

    def build_prompt(
        self,
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
    ) -> str:
        """Build the prompt sent to Gemini."""

        return f"""
You are LegalEase, an AI assistant that drafts structured legal documents.

Create a professional draft of the requested legal document.

IMPORTANT:
- This is a draft/template and not a substitute for advice from a qualified lawyer.
- Do not invent names, addresses, dates, amounts, jurisdictions, registration numbers,
  signatures, or other facts that were not provided.
- If important information is missing, use a clear placeholder such as:
  [PARTY NAME], [ADDRESS], [DATE], [AMOUNT], [JURISDICTION].
- Use clear professional legal language.
- Organize the document into logical sections and numbered clauses.
- Include signature blocks where appropriate.
- Do not include explanations about how you generated the document.
- Return ONLY the legal document text.
- Do not wrap the response in Markdown code fences.

DOCUMENT TYPE:
{document_type}

PARTIES:
{parties}

EFFECTIVE DATE:
{effective_date}

TERMS / REQUIREMENTS:
{terms}

Create the complete draft now.
""".strip()

    @staticmethod
    def _is_retryable_error(error: Exception) -> bool:
        """Check whether an error is temporary and should be retried."""

        error_text = str(error).upper()

        retryable_markers = (
            "503",
            "UNAVAILABLE",
            "SERVICE_UNAVAILABLE",
            "429",
            "RESOURCE_EXHAUSTED",
            "TOO_MANY_REQUESTS",
            "500",
            "INTERNAL",
            "TIMEOUT",
            "TIMED OUT",
            "DEADLINE_EXCEEDED",
            "CONNECTION RESET",
            "CONNECTION ERROR",
        )

        return any(
            marker in error_text
            for marker in retryable_markers
        )

    def _generate_with_retry(
        self,
        prompt: str,
        max_attempts: int = 4,
    ):
        """
        Send the request to Gemini with exponential backoff.

        Attempts:
            1 -> immediately
            2 -> after 2 seconds
            3 -> after 4 seconds
            4 -> after 8 seconds
        """

        if self.client is None:
            raise GeminiGenerationError(
                "Gemini API key is not configured. "
                "Please add GEMINI_API_KEY to your .env file."
            )

        try:
            from google.genai import types
        except ImportError as exc:
            raise GeminiGenerationError(
                "The google-genai package is not installed. "
                "Run: python -m pip install google-genai"
            ) from exc

        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.settings.gemini_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=self.settings.gemini_temperature,
                        max_output_tokens=self.settings.gemini_max_output_tokens,
                        candidate_count=1,
                    ),
                )

                return response

            except Exception as exc:
                last_error = exc

                print(
                    f"Gemini request failed "
                    f"(attempt {attempt}/{max_attempts}): {exc}"
                )

                if not self._is_retryable_error(exc):
                    raise GeminiGenerationError(
                        f"Gemini generation failed: {exc}"
                    ) from exc

                if attempt >= max_attempts:
                    break

                delay = 2 ** attempt

                print(
                    f"Temporary Gemini error detected. "
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)

        raise GeminiGenerationError(
            "Gemini is temporarily unavailable after "
            f"{max_attempts} attempts. "
            "Please try generating the document again in a little while. "
            f"Last error: {last_error}"
        ) from last_error

    def generate_document(
        self,
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
    ) -> str:
        """Generate the requested legal document."""

        if not self.settings.gemini_api_key:
            raise GeminiGenerationError(
                "GEMINI_API_KEY is missing. "
                "Please add your Gemini API key to the .env file."
            )

        prompt = self.build_prompt(
            document_type=document_type,
            parties=parties,
            terms=terms,
            effective_date=effective_date,
        )

        response = self._generate_with_retry(prompt)

        try:
            text = response.text
        except Exception:
            text = None

        if not text or not text.strip():
            raise GeminiGenerationError(
                "Gemini returned an empty response. "
                "Please try again."
            )

        return text.strip()