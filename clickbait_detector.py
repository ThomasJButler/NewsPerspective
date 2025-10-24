"""
@author Tom Butler
@date 2025-10-24
@description Clickbait detection engine that compares headlines to article content.
             Calculates clickbait scores, tracks source reliability, and identifies misleading patterns.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from logger_config import setup_logger
from azure_ai_language import ai_language
from azure_document_intelligence import document_intelligence

load_dotenv()

logger = setup_logger("NewsPerspective.ClickbaitDetector")


class ClickbaitDetector:
    """
    Detects clickbait by comparing headline sentiment to actual article content.
    Tracks source reliability and identifies misleading patterns.
    """

    def __init__(self):
        """Initialise clickbait detector with pattern databases."""
        self.clickbait_patterns = self._load_clickbait_patterns()
        self.source_stats = self._load_source_stats()
        logger.info("Clickbait detector initialised")

    def _load_clickbait_patterns(self):
        """
        Load known clickbait patterns and indicators.
        @return {dict} Dictionary of clickbait patterns by category
        """
        return {
            'exaggeration': [
                'shocking', 'unbelievable', 'incredible', 'amazing', 'stunning',
                'mind-blowing', 'jaw-dropping', 'explosive', 'massive', 'epic'
            ],
            'curiosity_gap': [
                'you won\'t believe', 'what happened next', 'this is what',
                'the reason why', 'here\'s why', 'find out', 'the truth about',
                'what really', 'secret', 'revealed'
            ],
            'urgency': [
                'breaking', 'just in', 'urgent', 'alert', 'warning', 'now',
                'immediately', 'must see', 'don\'t miss'
            ],
            'emotional_manipulation': [
                'heartbreaking', 'devastating', 'tragic', 'horrifying',
                'outrageous', 'infuriating', 'disgusting', 'terrifying'
            ],
            'listicles': [
                'reasons why', 'ways to', 'things you', 'facts about',
                'tips for', 'tricks to'
            ],
            'sensationalism': [
                'slams', 'blasts', 'destroys', 'obliterates', 'annihilates',
                'demolishes', 'crushes', 'hammers', 'rips into'
            ]
        }

    def _load_source_stats(self):
        """
        Load historical source reliability statistics.
        @return {dict} Dictionary of source stats or empty dict if file doesn't exist
        """
        stats_file = 'data/source_reliability.json'
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load source stats: {str(e)}")
        return {}

    def _save_source_stats(self):
        """Save source reliability statistics to file."""
        os.makedirs('data', exist_ok=True)
        try:
            with open('data/source_reliability.json', 'w') as f:
                json.dump(self.source_stats, f, indent=2)
            logger.debug("Source stats saved successfully")
        except Exception as e:
            logger.error(f"Could not save source stats: {str(e)}")

    def detect_clickbait_score(self, headline, article_content=None, article_url=None):
        """
        Calculate clickbait score for a headline.
        @param {str} headline - Article headline to analyse
        @param {str} article_content - Optional full article content
        @param {str} article_url - Optional article URL for content extraction
        @return {dict} Clickbait analysis including score, reasons, and recommendations
        """
        logger.debug(f"Analysing headline for clickbait: {headline[:50]}")

        analysis = {
            'clickbait_score': 0,
            'is_clickbait': False,
            'confidence': 0,
            'reasons': [],
            'pattern_matches': [],
            'headline_sentiment': {},
            'content_sentiment': {},
            'sentiment_mismatch': False,
            'mismatch_severity': 0,
            'recommendation': 'keep'
        }

        # Step 1: Analyse headline sentiment
        headline_analysis = ai_language.analyze_text(headline)
        analysis['headline_sentiment'] = {
            'sentiment': headline_analysis.get('sentiment', 'neutral'),
            'positive': headline_analysis.get('confidence_scores', {}).get('positive', 0),
            'neutral': headline_analysis.get('confidence_scores', {}).get('neutral', 0),
            'negative': headline_analysis.get('confidence_scores', {}).get('negative', 0)
        }

        # Step 2: Check for clickbait patterns
        pattern_score, matches = self._check_clickbait_patterns(headline.lower())
        analysis['pattern_matches'] = matches
        analysis['clickbait_score'] += pattern_score

        # Step 3: Compare to article content if available
        if article_content or article_url:
            content_analysis = self._analyse_content_mismatch(
                headline,
                article_content,
                article_url,
                analysis['headline_sentiment']
            )
            analysis.update(content_analysis)

        # Step 4: Calculate final score and recommendation
        analysis['clickbait_score'] = min(100, analysis['clickbait_score'])
        analysis['is_clickbait'] = analysis['clickbait_score'] >= 70
        analysis['confidence'] = self._calculate_confidence(analysis)
        analysis['recommendation'] = self._get_recommendation(analysis)

        logger.info(f"Clickbait score: {analysis['clickbait_score']}, Recommendation: {analysis['recommendation']}")

        return analysis

    def _check_clickbait_patterns(self, headline_lower):
        """
        Check headline against known clickbait patterns.
        @param {str} headline_lower - Lowercase headline text
        @return {tuple} (score, list of matches)
        """
        score = 0
        matches = []

        for category, patterns in self.clickbait_patterns.items():
            for pattern in patterns:
                if pattern in headline_lower:
                    score += 10
                    matches.append({
                        'category': category,
                        'pattern': pattern,
                        'severity': self._get_pattern_severity(category)
                    })

        # Cap pattern-based score at 50
        return min(50, score), matches

    def _get_pattern_severity(self, category):
        """
        Get severity level for pattern category.
        @param {str} category - Pattern category name
        @return {str} Severity level (low, medium, high)
        """
        severity_map = {
            'curiosity_gap': 'high',
            'emotional_manipulation': 'high',
            'exaggeration': 'medium',
            'sensationalism': 'medium',
            'urgency': 'medium',
            'listicles': 'low'
        }
        return severity_map.get(category, 'low')

    def _analyse_content_mismatch(self, headline, article_content, article_url, headline_sentiment):
        """
        Analyse mismatch between headline and article content.
        @param {str} headline - Article headline
        @param {str} article_content - Article content (optional)
        @param {str} article_url - Article URL (optional)
        @param {dict} headline_sentiment - Pre-analysed headline sentiment
        @return {dict} Content mismatch analysis
        """
        result = {
            'sentiment_mismatch': False,
            'mismatch_severity': 0,
            'content_sentiment': {},
            'reasons': []
        }

        # Extract content if URL provided and content not given
        if article_url and not article_content:
            extraction = document_intelligence.extract_content_from_url(article_url)
            if extraction.get('content_extracted'):
                article_content = extraction.get('full_text', '')[:5000]

        if not article_content:
            logger.debug("No article content available for comparison")
            return result

        # Analyse content sentiment
        content_analysis = ai_language.analyze_text(article_content[:5000])
        result['content_sentiment'] = {
            'sentiment': content_analysis.get('sentiment', 'neutral'),
            'positive': content_analysis.get('confidence_scores', {}).get('positive', 0),
            'neutral': content_analysis.get('confidence_scores', {}).get('neutral', 0),
            'negative': content_analysis.get('confidence_scores', {}).get('negative', 0)
        }

        # Compare sentiments
        headline_sent = headline_sentiment['sentiment']
        content_sent = result['content_sentiment']['sentiment']

        # Calculate mismatch score
        if headline_sent != content_sent:
            result['sentiment_mismatch'] = True

            # Severe mismatch: headline negative but content positive
            if headline_sent == 'negative' and content_sent == 'positive':
                result['mismatch_severity'] = 40
                result['reasons'].append('Headline is negative but article content is positive')
                result['reasons'].append('Likely clickbait to attract attention')

            # Moderate mismatch: headline positive but content negative
            elif headline_sent == 'positive' and content_sent == 'negative':
                result['mismatch_severity'] = 30
                result['reasons'].append('Headline is positive but article content is negative')
                result['reasons'].append('Possible misleading framing')

            # Minor mismatch: neutral vs positive/negative
            else:
                result['mismatch_severity'] = 15
                result['reasons'].append(f'Sentiment mismatch: headline {headline_sent}, content {content_sent}')

        # Check confidence score differences
        headline_neg = headline_sentiment.get('negative', 0)
        content_neg = result['content_sentiment'].get('negative', 0)

        if abs(headline_neg - content_neg) > 30:
            result['mismatch_severity'] += 10
            result['reasons'].append(f'Large negative sentiment gap: headline {headline_neg:.0f}%, content {content_neg:.0f}%')

        return result

    def _calculate_confidence(self, analysis):
        """
        Calculate confidence in clickbait detection.
        @param {dict} analysis - Full analysis results
        @return {int} Confidence score (0-100)
        """
        confidence = 50

        # More pattern matches = higher confidence
        if len(analysis['pattern_matches']) >= 3:
            confidence += 30
        elif len(analysis['pattern_matches']) >= 1:
            confidence += 15

        # Sentiment mismatch increases confidence
        if analysis['sentiment_mismatch']:
            confidence += 20

        # Strong sentiment scores increase confidence
        headline_sent = analysis['headline_sentiment']
        max_sentiment = max(
            headline_sent.get('positive', 0),
            headline_sent.get('negative', 0),
            headline_sent.get('neutral', 0)
        )
        if max_sentiment > 70:
            confidence += 10

        return min(100, confidence)

    def _get_recommendation(self, analysis):
        """
        Get recommendation based on clickbait analysis.
        @param {dict} analysis - Full analysis results
        @return {str} Recommendation (keep, rewrite_minor, rewrite_major, reject)
        """
        score = analysis['clickbait_score']

        if score >= 85:
            return 'reject'
        elif score >= 70:
            return 'rewrite_major'
        elif score >= 40:
            return 'rewrite_minor'
        else:
            return 'keep'

    def track_source_reliability(self, source, clickbait_score, was_clickbait):
        """
        Track source reliability over time.
        @param {str} source - News source name
        @param {int} clickbait_score - Clickbait score for this article
        @param {bool} was_clickbait - Whether article was classified as clickbait
        """
        if source not in self.source_stats:
            self.source_stats[source] = {
                'total_articles': 0,
                'clickbait_count': 0,
                'total_score': 0,
                'average_score': 0,
                'reliability_rating': 'unknown',
                'last_updated': None
            }

        stats = self.source_stats[source]
        stats['total_articles'] += 1
        stats['clickbait_count'] += 1 if was_clickbait else 0
        stats['total_score'] += clickbait_score
        stats['average_score'] = stats['total_score'] / stats['total_articles']
        stats['last_updated'] = datetime.now().isoformat()

        # Calculate reliability rating
        if stats['total_articles'] >= 10:
            if stats['average_score'] < 30:
                stats['reliability_rating'] = 'excellent'
            elif stats['average_score'] < 50:
                stats['reliability_rating'] = 'good'
            elif stats['average_score'] < 70:
                stats['reliability_rating'] = 'moderate'
            else:
                stats['reliability_rating'] = 'poor'

        # Save stats periodically (every 10 articles)
        if stats['total_articles'] % 10 == 0:
            self._save_source_stats()

        logger.debug(f"Updated stats for {source}: avg score {stats['average_score']:.1f}, rating {stats['reliability_rating']}")

    def get_source_reliability_report(self):
        """
        Generate source reliability report.
        @return {dict} Report with source rankings and statistics
        """
        if not self.source_stats:
            return {
                'total_sources': 0,
                'sources': [],
                'generated_at': datetime.now().isoformat()
            }

        # Sort sources by average score (lower is better)
        sorted_sources = sorted(
            self.source_stats.items(),
            key=lambda x: x[1]['average_score']
        )

        report = {
            'total_sources': len(sorted_sources),
            'sources': [],
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'excellent': 0,
                'good': 0,
                'moderate': 0,
                'poor': 0,
                'unknown': 0
            }
        }

        for source, stats in sorted_sources:
            if stats['total_articles'] >= 5:
                report['sources'].append({
                    'name': source,
                    'total_articles': stats['total_articles'],
                    'clickbait_count': stats['clickbait_count'],
                    'clickbait_percentage': (stats['clickbait_count'] / stats['total_articles'] * 100),
                    'average_score': round(stats['average_score'], 1),
                    'reliability_rating': stats['reliability_rating'],
                    'last_updated': stats['last_updated']
                })
                report['summary'][stats['reliability_rating']] += 1

        return report

    def get_daily_report(self, articles_analysed):
        """
        Generate daily clickbait detection report.
        @param {list} articles_analysed - List of analysis results from today
        @return {dict} Daily summary report
        """
        if not articles_analysed:
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total_articles': 0,
                'clickbait_detected': 0,
                'average_score': 0
            }

        total = len(articles_analysed)
        clickbait_count = sum(1 for a in articles_analysed if a.get('is_clickbait', False))
        total_score = sum(a.get('clickbait_score', 0) for a in articles_analysed)

        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_articles': total,
            'clickbait_detected': clickbait_count,
            'clickbait_percentage': (clickbait_count / total * 100) if total > 0 else 0,
            'average_score': (total_score / total) if total > 0 else 0,
            'breakdown': {
                'reject': sum(1 for a in articles_analysed if a.get('recommendation') == 'reject'),
                'rewrite_major': sum(1 for a in articles_analysed if a.get('recommendation') == 'rewrite_major'),
                'rewrite_minor': sum(1 for a in articles_analysed if a.get('recommendation') == 'rewrite_minor'),
                'keep': sum(1 for a in articles_analysed if a.get('recommendation') == 'keep')
            }
        }


# Singleton instance
clickbait_detector = ClickbaitDetector()
