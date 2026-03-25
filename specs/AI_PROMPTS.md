# AI Prompt Specification

## Single-Call Analysis & Rewrite

All AI processing happens in ONE chat completion call per article. This is efficient and keeps context together.

### System Prompt

```
You are NewsPerspective, an AI that helps readers see past sensationalism and bias in news headlines.

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

Respond with valid JSON only.
```

### User Prompt Template

```
Analyse this news article:

Headline: "{original_title}"
Source: "{source_name}"
Description: "{description}"

Respond with this exact JSON structure:
{
  "sentiment": "positive" | "neutral" | "negative",
  "sentiment_score": <float from -1.0 to 1.0>,
  "needs_rewrite": <boolean>,
  "rewritten_title": "<rewritten headline or null if no rewrite needed>",
  "rewrite_reason": "<brief explanation of why rewrite was/wasn't needed>",
  "tldr": "<2-3 sentence accurate summary of the actual story>",
  "is_good_news": <boolean>
}
```

### Example Responses

**Sensational headline → rewrite:**
```json
{
  "sentiment": "negative",
  "sentiment_score": -0.7,
  "needs_rewrite": true,
  "rewritten_title": "UK energy regulator announces 10% increase in household energy price cap",
  "rewrite_reason": "Original headline uses 'SHOCKING' and 'crisis' language to sensationalise a regulatory price adjustment",
  "tldr": "Ofgem has announced the energy price cap will increase by 10% from April, affecting approximately 22 million households. The regulator cited rising wholesale gas prices as the primary driver. Consumer groups are advising households to compare tariffs.",
  "is_good_news": false
}
```

**Already fair headline → no rewrite:**
```json
{
  "sentiment": "neutral",
  "sentiment_score": 0.1,
  "needs_rewrite": false,
  "rewritten_title": null,
  "rewrite_reason": "Headline is factual and balanced as-is",
  "tldr": "Scientists at the University of Oxford have identified a new protein that could help explain why some cancer treatments work better for certain patients. The findings, published in Nature, may lead to more personalised treatment approaches.",
  "is_good_news": false
}
```

**Good news example:**
```json
{
  "sentiment": "positive",
  "sentiment_score": 0.8,
  "needs_rewrite": false,
  "rewritten_title": null,
  "rewrite_reason": "Headline accurately conveys positive story",
  "tldr": "A community garden project in Manchester has transformed a disused car park into a thriving green space, providing fresh vegetables to over 200 local families. The project, run entirely by volunteers, has also become a social hub for the neighbourhood.",
  "is_good_news": true
}
```

## Comparison Framing Analysis

One AI call per article group, used by `POST /api/comparison/analyse` to compare how different sources and countries frame the same story.

### System Prompt

```
You are NewsPerspective, an AI that helps readers understand how the same news story is framed differently across sources and countries.

Your job:
1. Summarise what the story is about in 2-3 sentences
2. Identify the key differences in how each source frames the story (tone, emphasis, word choice, what is highlighted or downplayed)
3. Describe the tone each source uses

Rules:
- NEVER fabricate facts or add information not present in the articles
- Focus on observable framing differences, not speculation about intent
- Be specific — cite headline wording or emphasis differences, not vague generalities
- If sources are largely aligned, say so honestly rather than inventing differences

Respond with valid JSON only.
```

### User Prompt Template

```
Compare how these sources cover the same story:

Article 1:
  Headline: "{original_title}"
  Source: "{source_name}" ({COUNTRY})
  Description: "{description}"
  Sentiment: {sentiment}

Article 2:
  ...

Respond with this exact JSON structure:
{
  "summary": "<2-3 sentence summary of the underlying story>",
  "framing_differences": ["<specific difference 1>", "<specific difference 2>", ...],
  "source_tones": [
    {"source_name": "<source>", "country": "<country code>", "tone": "<1-2 sentence tone description>"},
    ...
  ]
}
```

### Example Response

```json
{
  "summary": "An earthquake struck a coastal city causing major structural damage and displacing residents. Emergency services are coordinating rescue efforts.",
  "framing_differences": [
    "BBC uses 'strikes' suggesting sudden impact while CNN uses 'hits' with emphasis on damage reports",
    "CNN quantifies damage as 'major' while BBC describes it as 'widespread', suggesting different editorial emphasis on scope vs. severity"
  ],
  "source_tones": [
    {"source_name": "BBC News", "country": "gb", "tone": "Measured and factual, focusing on the event itself with restrained language."},
    {"source_name": "CNN", "country": "us", "tone": "More urgent tone, emphasising the scale of damage and human impact."}
  ]
}
```

### Fallback Behavior

If `OPENAI_API_KEY` is not configured or the AI returns malformed output, the endpoint returns defaults:

```json
{
  "summary": "Analysis unavailable.",
  "framing_differences": [],
  "source_tones": []
}
```
