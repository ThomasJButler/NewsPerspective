import json
import logging

from openai import OpenAI

from ..config import settings
from ..utils.logger import setup_logger

logger = setup_logger("AIService")

SYSTEM_PROMPT = """You are NewsPerspective, an AI that helps readers see past sensationalism and bias in news headlines.

Your job:
1. Assess the headline's sentiment and whether it's sensationalised, misleading, or unnecessarily negative
2. If needed, rewrite it to be factual, calm, and unbiased — preserving ALL facts
3. Write an accurate TLDR summary based on the article description
4. Determine if this is genuinely "good news"

Rules:
- NEVER fabricate facts or add information not in the original
- NEVER make bad news sound good — just make it sound factual
- A headline about a tragedy should still convey the gravity, just without sensationalism
- "Good news" means genuinely positive stories (breakthroughs, kindness, progress), not just neutral ones
- The TLDR must be accurate to the article content provided, not the headline
- If the headline is already fair and factual, mark needs_rewrite as false

Respond with valid JSON only."""

USER_PROMPT_TEMPLATE = """Analyse this news article:

Headline: "{original_title}"
Source: "{source_name}"
Description: "{description}"

Respond with this exact JSON structure:
{{
  "sentiment": "positive" | "neutral" | "negative",
  "sentiment_score": <float from -1.0 to 1.0>,
  "needs_rewrite": <boolean>,
  "rewritten_title": "<rewritten headline or null if no rewrite needed>",
  "rewrite_reason": "<brief explanation of why rewrite was/wasn't needed>",
  "tldr": "<2-3 sentence accurate summary of the actual story>",
  "is_good_news": <boolean>
}}"""

NEUTRAL_DEFAULTS = {
    "sentiment": "neutral",
    "sentiment_score": 0.0,
    "needs_rewrite": False,
    "rewritten_title": None,
    "rewrite_reason": "Analysis failed — returned neutral defaults",
    "tldr": "",
    "is_good_news": False,
}


class AIService:
    def __init__(self):
        self.model = settings.OPENAI_MODEL
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    def analyse_article(self, title: str, source: str, description: str) -> dict:
        """Analyse a single article: sentiment, rewrite decision, TLDR, good-news flag.

        Returns a dict with keys: sentiment, sentiment_score, needs_rewrite,
        rewritten_title, rewrite_reason, tldr, is_good_news.
        On failure returns neutral defaults.
        """
        user_prompt = USER_PROMPT_TEMPLATE.format(
            original_title=title,
            source_name=source,
            description=description or "No description available",
        )

        if self.client is None:
            logger.warning("OPENAI_API_KEY is not configured; using neutral defaults for article analysis")
            return dict(NEUTRAL_DEFAULTS)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )

            content = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            result = json.loads(content)
            self._validate_result(result)
            logger.info(f"Analysed: {title[:60]}... — sentiment={result['sentiment']}, rewrite={result['needs_rewrite']}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON from OpenAI for '{title[:60]}...': {e}")
            return dict(NEUTRAL_DEFAULTS)
        except Exception as e:
            logger.error(f"AI analysis failed for '{title[:60]}...': {e}")
            return dict(NEUTRAL_DEFAULTS)

    def _validate_result(self, result: dict) -> None:
        """Coerce types and fill missing keys with defaults."""
        for key, default in NEUTRAL_DEFAULTS.items():
            if key not in result:
                result[key] = default

        # Clamp sentiment_score to [-1.0, 1.0]
        score = result.get("sentiment_score", 0.0)
        if isinstance(score, (int, float)):
            result["sentiment_score"] = max(-1.0, min(1.0, float(score)))
        else:
            result["sentiment_score"] = 0.0

        # Normalise sentiment string
        if result["sentiment"] not in ("positive", "neutral", "negative"):
            result["sentiment"] = "neutral"

        # Ensure booleans
        result["needs_rewrite"] = bool(result.get("needs_rewrite"))
        result["is_good_news"] = bool(result.get("is_good_news"))
