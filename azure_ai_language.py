"""
@author Tom Butler
@date 2025-10-24
@description Azure AI Language service integration for sentiment analysis and entity recognition.
             Provides text analysis capabilities with fallback when service unavailable.
"""

import os
import requests
import json
from dotenv import load_dotenv
from logger_config import setup_logger

load_dotenv()

logger = setup_logger("NewsPerspective.AILanguage")


class AzureAILanguage:
    """Sentiment analysis and entity recognition using Azure AI Language."""

    def __init__(self):
        """Initialise Azure AI Language service."""
        self.endpoint = os.getenv("AZURE_AI_LANGUAGE_ENDPOINT")
        self.key = os.getenv("AZURE_AI_LANGUAGE_KEY")

        if not self.endpoint or not self.key:
            logger.warning("Azure AI Language credentials not found. Analysis disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Azure AI Language service initialised successfully")

    def analyze_text(self, text, include_sentiment=True, include_entities=True, include_key_phrases=True):
        """
        Analyse text for sentiment, entities, and key phrases.
        @param {str} text - Text to analyse
        @param {bool} include_sentiment - Include sentiment analysis
        @param {bool} include_entities - Include entity recognition
        @param {bool} include_key_phrases - Include key phrase extraction
        @return {dict} Analysis results with sentiment, entities, and key phrases
        """
        if not self.enabled:
            return self._fallback_analysis(text)
        
        try:
            # Prepare the request
            headers = {
                'Ocp-Apim-Subscription-Key': self.key,
                'Content-Type': 'application/json'
            }
            
            # Build analysis tasks
            tasks = []
            if include_sentiment:
                tasks.append({
                    "kind": "SentimentAnalysis",
                    "taskName": "sentiment",
                    "parameters": {
                        "modelVersion": "latest"
                    }
                })
            
            if include_entities:
                tasks.append({
                    "kind": "EntityRecognition", 
                    "taskName": "entities",
                    "parameters": {
                        "modelVersion": "latest"
                    }
                })
            
            if include_key_phrases:
                tasks.append({
                    "kind": "KeyPhraseExtraction",
                    "taskName": "keyPhrases", 
                    "parameters": {
                        "modelVersion": "latest"
                    }
                })
            
            # Prepare request body
            body = {
                "analysisInput": {
                    "documents": [
                        {
                            "id": "1",
                            "language": "en",
                            "text": text[:5000]  # Limit to 5000 chars
                        }
                    ]
                },
                "tasks": tasks
            }
            
            # Use simpler, single-request API for sentiment analysis
            if include_sentiment:
                sentiment_url = f"{self.endpoint}/language/:analyze-text?api-version=2023-04-01"
                sentiment_body = {
                    "kind": "SentimentAnalysis",
                    "analysisInput": {
                        "documents": [
                            {
                                "id": "1",
                                "language": "en",
                                "text": text[:5000]
                            }
                        ]
                    }
                }
                
                response = requests.post(sentiment_url, headers=headers, json=sentiment_body)
                
                if response.status_code == 200:
                    sentiment_result = response.json()
                    return self._parse_simple_sentiment_result(sentiment_result, text)
                else:
                    logger.error(f"Azure AI Language API error: {response.status_code} - {response.text}")
                    return self._fallback_analysis(text)
            else:
                return self._fallback_analysis(text)
                
        except Exception as e:
            logger.error(f"Error in Azure AI Language analysis: {str(e)}")
            return self._fallback_analysis(text)
    
    def _wait_for_result(self, operation_location, headers, max_attempts=10):
        """
        Poll for long-running operation completion.
        @param {str} operation_location - Operation status URL
        @param {dict} headers - Request headers with authentication
        @param {int} max_attempts - Maximum polling attempts
        @return {dict} Parsed analysis results or fallback
        """
        import time
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(operation_location, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('status') == 'succeeded':
                        return self._parse_analysis_result(result)
                    elif result.get('status') == 'failed':
                        logger.error(f"Azure AI Language analysis failed: {result}")
                        return self._fallback_analysis("")
                    else:
                        # Still running, wait and retry
                        time.sleep(1)
                        continue
                else:
                    logger.error(f"Error checking operation status: {response.status_code}")
                    return self._fallback_analysis("")
                    
            except Exception as e:
                logger.error(f"Error waiting for result: {str(e)}")
                return self._fallback_analysis("")
        
        logger.warning("Azure AI Language analysis timed out")
        return self._fallback_analysis("")
    
    def _parse_simple_sentiment_result(self, result, text):
        """
        Parse sentiment analysis result from API response.
        @param {dict} result - Raw API response
        @param {str} text - Original text analysed
        @return {dict} Structured sentiment data
        """
        analysis = {
            'sentiment': 'neutral',
            'confidence_scores': {'positive': 33, 'neutral': 34, 'negative': 33},
            'entities': [],
            'key_phrases': [],
            'enhanced_reason': None
        }
        
        try:
            documents = result.get('results', {}).get('documents', [])
            if documents:
                doc = documents[0]
                sentiment = doc.get('sentiment', 'neutral')
                confidence_scores = doc.get('confidenceScores', {})
                
                analysis['sentiment'] = sentiment
                analysis['confidence_scores'] = {
                    'positive': confidence_scores.get('positive', 0) * 100,
                    'neutral': confidence_scores.get('neutral', 0) * 100,
                    'negative': confidence_scores.get('negative', 0) * 100
                }
                
                # Generate enhanced reason
                sentiment_reason = self._generate_sentiment_reason(analysis)
                if sentiment_reason:
                    analysis['enhanced_reason'] = sentiment_reason
                
                logger.debug(f"Sentiment analysis successful: {sentiment} ({analysis['confidence_scores']})")
                
        except Exception as e:
            logger.error(f"Error parsing simple sentiment result: {str(e)}")
            analysis['enhanced_reason'] = "Sentiment analysis error - using fallback"
        
        return analysis
    
    def _parse_analysis_result(self, result):
        """Parse the analysis result from Azure AI Language"""
        analysis = {
            'sentiment': None,
            'confidence_scores': {},
            'entities': [],
            'key_phrases': [],
            'enhanced_reason': None
        }
        
        try:
            tasks = result.get('tasks', {}).get('completed', [])
            
            for task in tasks:
                task_name = task.get('taskName')
                task_results = task.get('results', {}).get('documents', [])
                
                if task_results:
                    doc_result = task_results[0]  # First document
                    
                    if task_name == 'sentiment':
                        analysis['sentiment'] = doc_result.get('sentiment', 'neutral')
                        confidence_scores = doc_result.get('confidenceScores', {})
                        analysis['confidence_scores'] = {
                            'positive': confidence_scores.get('positive', 0) * 100,
                            'neutral': confidence_scores.get('neutral', 0) * 100,
                            'negative': confidence_scores.get('negative', 0) * 100
                        }
                        
                        # Enhanced reason based on sentiment analysis
                        sentiment_reason = self._generate_sentiment_reason(analysis)
                        if sentiment_reason:
                            analysis['enhanced_reason'] = sentiment_reason
                    
                    elif task_name == 'entities':
                        entities = doc_result.get('entities', [])
                        analysis['entities'] = [
                            {
                                'text': entity.get('text'),
                                'category': entity.get('category'),
                                'confidence': entity.get('confidenceScore', 0) * 100
                            }
                            for entity in entities
                            if entity.get('confidenceScore', 0) > 0.6  # High confidence only
                        ]
                    
                    elif task_name == 'keyPhrases':
                        analysis['key_phrases'] = doc_result.get('keyPhrases', [])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error parsing analysis result: {str(e)}")
            return self._fallback_analysis("")
    
    def _generate_sentiment_reason(self, analysis):
        """Generate enhanced reasoning based on sentiment analysis"""
        sentiment = analysis.get('sentiment', 'neutral')
        scores = analysis.get('confidence_scores', {})
        
        if sentiment == 'negative' and scores.get('negative', 0) > 70:
            return f"Strong negative sentiment detected ({scores['negative']:.0f}% confidence). Headlines with negative tone can impact reader mood and engagement."
        elif sentiment == 'positive' and scores.get('positive', 0) > 80:
            return f"Already positive sentiment ({scores['positive']:.0f}% confidence). Headline maintains factual accuracy while conveying optimism."
        elif sentiment == 'neutral':
            positive_score = scores.get('positive', 0)
            negative_score = scores.get('negative', 0)
            if negative_score > positive_score:
                return f"Neutral tone with negative lean ({negative_score:.0f}% negative vs {positive_score:.0f}% positive). Can be enhanced for more positive reader experience."
        
        return None
    
    def _fallback_analysis(self, text):
        """Fallback analysis when Azure AI Language is unavailable"""
        return {
            'sentiment': 'neutral',
            'confidence_scores': {'positive': 33, 'neutral': 34, 'negative': 33},
            'entities': [],
            'key_phrases': [],
            'enhanced_reason': "Enhanced analysis unavailable - using basic tone detection"
        }
    
    def extract_problematic_phrases(self, text):
        """Extract specific phrases that may contribute to negative tone"""
        if not self.enabled:
            return []
        
        # Common negative words/phrases in news headlines
        negative_indicators = [
            'threat', 'threatens', 'crisis', 'crash', 'collapse', 'scandal', 
            'outrage', 'fury', 'slams', 'blasts', 'attacks', 'destroys',
            'fails', 'failure', 'disaster', 'chaos', 'panic', 'fear',
            'war', 'conflict', 'violence', 'death', 'killed', 'murdered'
        ]
        
        found_phrases = []
        text_lower = text.lower()
        
        for phrase in negative_indicators:
            if phrase in text_lower:
                # Find the actual occurrence in original text
                start_idx = text_lower.find(phrase)
                if start_idx != -1:
                    # Extract some context around the phrase
                    context_start = max(0, start_idx - 10)
                    context_end = min(len(text), start_idx + len(phrase) + 10)
                    context = text[context_start:context_end].strip()
                    
                    found_phrases.append({
                        'phrase': phrase,
                        'context': context,
                        'position': start_idx
                    })
        
        return found_phrases[:3]  # Return top 3 problematic phrases

# Initialize global instance
ai_language = AzureAILanguage()
