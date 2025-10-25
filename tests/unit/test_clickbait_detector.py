"""
@author Tom Butler
@date 2025-10-25
@description Unit tests for clickbait detection functionality.
"""

import pytest
import json
from pathlib import Path
from clickbait_detector import ClickbaitDetector


class TestClickbaitDetector:
    """Test clickbait detection functionality."""

    def setup_method(self):
        """Set up test instance before each test."""
        self.detector = ClickbaitDetector()

    def test_detector_initialization(self):
        """Test detector initializes with pattern dictionary."""
        assert hasattr(self.detector, 'clickbait_patterns')
        assert 'exaggeration' in self.detector.clickbait_patterns
        assert 'curiosity_gap' in self.detector.clickbait_patterns
        assert 'urgency' in self.detector.clickbait_patterns

    def test_detect_clickbait_with_obvious_clickbait(self):
        """Test detection of obvious clickbait headline."""
        headline = "You Won't Believe What Happened Next! Shocking Truth Revealed!"
        result = self.detector.detect_clickbait_score(headline)

        assert result['clickbait_score'] > 50
        assert result['is_clickbait'] is True
        assert len(result['reasons']) > 0
        assert 'confidence' in result

    def test_detect_clickbait_with_clean_headline(self):
        """Test detection returns low score for factual headline."""
        headline = "UK Parliament Approves New Climate Legislation"
        result = self.detector.detect_clickbait_score(headline)

        assert result['clickbait_score'] < 30
        assert result['is_clickbait'] is False

    def test_exaggeration_patterns(self):
        """Test exaggeration pattern detection."""
        headlines = [
            "Shocking Discovery Changes Everything",
            "Unbelievable Results from Latest Study",
            "Incredible News That Will Blow Your Mind"
        ]

        for headline in headlines:
            result = self.detector.detect_clickbait_score(headline)
            assert result['clickbait_score'] > 30
            assert any('exaggeration' in str(reason).lower() for reason in result['reasons'])

    def test_curiosity_gap_patterns(self):
        """Test curiosity gap pattern detection."""
        headlines = [
            "Scientists Discovered This One Trick",
            "What Happened Next Will Surprise You",
            "The Secret They Don't Want You To Know"
        ]

        for headline in headlines:
            result = self.detector.detect_clickbait_score(headline)
            assert result['clickbait_score'] > 30
            reasons_text = ' '.join(result['reasons']).lower()
            assert 'curiosity' in reasons_text or 'gap' in reasons_text

    def test_urgency_patterns(self):
        """Test urgency pattern detection."""
        headlines = [
            "BREAKING: Major Event Happening Now",
            "URGENT: Immediate Action Required",
            "Just In: Latest Development Unfolds"
        ]

        for headline in headlines:
            result = self.detector.detect_clickbait_score(headline)
            assert result['clickbait_score'] > 20

    def test_listicle_patterns(self):
        """Test listicle pattern detection."""
        headlines = [
            "10 Ways To Improve Your Life",
            "5 Reasons Why This Matters",
            "Top 7 Things You Need To Know"
        ]

        for headline in headlines:
            result = self.detector.detect_clickbait_score(headline)
            # Listicles should have moderate scores
            assert result['clickbait_score'] < 80

    def test_source_reliability_tracking(self, temp_data_dir):
        """Test source reliability tracking persistence."""
        # Temporarily override data directory
        original_file = self.detector.reliability_file
        self.detector.reliability_file = temp_data_dir / "source_reliability.json"

        self.detector.track_source_reliability("Test Source", 75, True)
        self.detector.track_source_reliability("Test Source", 80, True)
        self.detector.track_source_reliability("Test Source", 20, False)

        # Load the saved data
        with open(self.detector.reliability_file, 'r') as f:
            data = json.load(f)

        assert "Test Source" in data
        assert data["Test Source"]["total_analyzed"] == 3
        assert data["Test Source"]["clickbait_count"] == 2

        # Restore original
        self.detector.reliability_file = original_file

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        # Strong clickbait should have high confidence
        strong_clickbait = "SHOCKING: You Won't Believe This URGENT News!"
        result1 = self.detector.detect_clickbait_score(strong_clickbait)
        assert result1['confidence'] > 70

        # Borderline case should have lower confidence
        borderline = "Interesting Development in Technology"
        result2 = self.detector.detect_clickbait_score(borderline)
        assert result2['confidence'] < 70

    def test_multiple_pattern_detection(self):
        """Test headline with multiple clickbait patterns."""
        headline = "BREAKING: You Won't Believe This Shocking Secret!"
        result = self.detector.detect_clickbait_score(headline)

        assert result['clickbait_score'] > 70
        assert len(result['reasons']) >= 2  # Should detect multiple patterns

    def test_empty_headline(self):
        """Test handling of empty headline."""
        result = self.detector.detect_clickbait_score("")
        assert result['clickbait_score'] == 0
        assert result['is_clickbait'] is False

    def test_none_headline(self):
        """Test handling of None headline."""
        result = self.detector.detect_clickbait_score(None)
        assert result['clickbait_score'] == 0
        assert result['is_clickbait'] is False

    def test_recommendation_output(self):
        """Test recommendation is provided in results."""
        result = self.detector.detect_clickbait_score("Test Headline")
        assert 'recommendation' in result
        assert isinstance(result['recommendation'], str)

    def test_case_insensitive_detection(self):
        """Test pattern detection is case-insensitive."""
        headline_lower = "you won't believe this shocking news"
        headline_upper = "YOU WON'T BELIEVE THIS SHOCKING NEWS"
        headline_mixed = "You Won't Believe This Shocking News"

        result1 = self.detector.detect_clickbait_score(headline_lower)
        result2 = self.detector.detect_clickbait_score(headline_upper)
        result3 = self.detector.detect_clickbait_score(headline_mixed)

        # All should detect clickbait similarly
        assert result1['is_clickbait'] == result2['is_clickbait'] == result3['is_clickbait']
        assert abs(result1['clickbait_score'] - result2['clickbait_score']) < 5
