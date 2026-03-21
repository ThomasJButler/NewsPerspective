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

COMPARISON_SYSTEM_PROMPT = """You are NewsPerspective, an AI that helps readers understand how the same news story is framed differently across sources and countries.

Your job:
1. Summarise what the story is about in 2-3 sentences
2. Identify the key differences in how each source frames the story (tone, emphasis, word choice, what is highlighted or downplayed)
3. Describe the tone each source uses

Rules:
- NEVER fabricate facts or add information not present in the articles
- Focus on observable framing differences, not speculation about intent
- Be specific — cite headline wording or emphasis differences, not vague generalities
- If sources are largely aligned, say so honestly rather than inventing differences

Respond with valid JSON only."""

COMPARISON_USER_PROMPT_TEMPLATE = """Compare how these sources cover the same story:

{articles_block}

Respond with this exact JSON structure:
{{
  "summary": "<2-3 sentence summary of the underlying story>",
  "framing_differences": ["<specific difference 1>", "<specific difference 2>", ...],
  "source_tones": [
    {{"source_name": "<source>", "country": "<country code>", "tone": "<1-2 sentence tone description>"}},
    ...
  ]
}}"""

COMPARISON_DEFAULTS = {
    "summary": "Analysis unavailable.",
    "framing_differences": [],
    "source_tones": [],
}

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

    def analyse_comparison_group(
        self, articles: list[dict],
    ) -> dict:
        """Analyse a group of related articles to compare framing across sources.

        *articles* is a list of dicts with keys: original_title, source_name,
        country, original_description, original_sentiment.
        Returns a dict with keys: summary, framing_differences, source_tones.
        On failure returns comparison defaults.
        """
        lines: list[str] = []
        for i, a in enumerate(articles, 1):
            lines.append(
                f"Article {i}:\n"
                f"  Headline: \"{a['original_title']}\"\n"
                f"  Source: \"{a['source_name']}\" ({a['country'].upper()})\n"
                f"  Description: \"{a.get('original_description') or 'No description available'}\"\n"
                f"  Sentiment: {a.get('original_sentiment', 'unknown')}"
            )
        articles_block = "\n\n".join(lines)

        user_prompt = COMPARISON_USER_PROMPT_TEMPLATE.format(
            articles_block=articles_block,
        )

        if self.client is None:
            logger.warning(
                "OPENAI_API_KEY is not configured; using defaults for comparison analysis"
            )
            return dict(COMPARISON_DEFAULTS)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": COMPARISON_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
            )

            content = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            result = json.loads(content)
            self._validate_comparison_result(result)
            logger.info(f"Comparison analysis completed for {len(articles)} articles")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON from OpenAI for comparison: {e}")
            return dict(COMPARISON_DEFAULTS)
        except Exception as e:
            logger.error(f"Comparison analysis failed: {e}")
            return dict(COMPARISON_DEFAULTS)

    def _validate_comparison_result(self, result: dict) -> None:
        """Coerce types and fill missing keys for comparison results."""
        if "summary" not in result or not isinstance(result["summary"], str):
            result["summary"] = COMPARISON_DEFAULTS["summary"]
        if "framing_differences" not in result or not isinstance(
            result["framing_differences"], list
        ):
            result["framing_differences"] = []
        else:
            result["framing_differences"] = [
                str(d) for d in result["framing_differences"] if d
            ]
        if "source_tones" not in result or not isinstance(
            result["source_tones"], list
        ):
            result["source_tones"] = []
        else:
            result["source_tones"] = [
                t for t in result["source_tones"]
                if isinstance(t, dict)
                and "source_name" in t
                and "country" in t
                and "tone" in t
            ]

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

        # Normalize rewrite consistency: needs_rewrite requires a non-empty title
        rewritten = result.get("rewritten_title")
        if result["needs_rewrite"] and (not rewritten or not rewritten.strip()):
            result["needs_rewrite"] = False
            result["rewritten_title"] = None
