"""
@author Tom Butler
@date 2025-10-24
@description Azure AI Document Intelligence service for content extraction from URLs.
             Extracts text, headlines, and problematic phrases from article pages.
"""

import os
import requests
import json
from dotenv import load_dotenv
from logger_config import setup_logger
import time

load_dotenv()

logger = setup_logger("NewsPerspective.DocumentIntelligence")


class AzureDocumentIntelligence:
    """Content extraction from article URLs using Azure Document Intelligence."""
    
    def __init__(self):
        self.endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        
        if not self.endpoint or not self.key:
            logger.warning("Azure Document Intelligence credentials not found. Rich content extraction will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Azure Document Intelligence service initialized successfully")
    
    def extract_content_from_url(self, url):
        """
        Extract rich content from article URL using Azure Document Intelligence
        
        Args:
            url (str): Article URL to analyze
            
        Returns:
            dict: Extracted content with structure, text, and metadata
        """
        if not self.enabled:
            return self._fallback_extraction(url)
        
        try:
            # Prepare the request for Document Intelligence
            headers = {
                'Ocp-Apim-Subscription-Key': self.key,
                'Content-Type': 'application/json'
            }
            
            # Request body for URL-based analysis
            body = {
                "urlSource": url
            }
            
            analyze_url = f"{self.endpoint}/documentintelligence/v4.0-preview/documentModels/prebuilt-layout:analyze?api-version=2024-07-31-preview"

            logger.debug(f"Starting document analysis for URL: {url}")

            try:
                response = requests.post(analyze_url, headers=headers, json=body, timeout=30)

                if response.status_code == 202:
                    operation_location = response.headers.get('Operation-Location')
                    return self._wait_for_analysis_result(operation_location, headers, url)
                else:
                    logger.error(f"Document Intelligence API error: {response.status_code} - {response.text}")
                    return self._fallback_extraction(url)
            except requests.exceptions.Timeout:
                logger.error(f"Timeout starting document analysis for URL: {url}")
                return self._fallback_extraction(url)
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error starting document analysis: {str(e)}")
                return self._fallback_extraction(url)
                
        except Exception as e:
            logger.error(f"Error in Document Intelligence analysis: {str(e)}")
            return self._fallback_extraction(url)
    
    def _wait_for_analysis_result(self, operation_location, headers, url, max_attempts=30):
        """Wait for document analysis to complete"""
        for attempt in range(max_attempts):
            try:
                try:
                    response = requests.get(operation_location, headers=headers, timeout=15)

                    if response.status_code == 200:
                        result = response.json()
                        status = result.get('status', '')

                        if status == 'succeeded':
                            return self._parse_document_result(result, url)
                        elif status == 'failed':
                            logger.error(f"Document analysis failed: {result.get('error', 'Unknown error')}")
                            return self._fallback_extraction(url)
                        else:
                            time.sleep(2)
                            continue
                    else:
                        logger.error(f"Error checking analysis status: {response.status_code}")
                        return self._fallback_extraction(url)
                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout checking analysis status (attempt {attempt+1}/{max_attempts})")
                    time.sleep(3)
                    continue
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error waiting for analysis result: {str(e)}")
                    return self._fallback_extraction(url)

            except Exception as e:
                logger.error(f"Error waiting for analysis result: {str(e)}")
                return self._fallback_extraction(url)
        
        logger.warning("Document analysis timed out")
        return self._fallback_extraction(url)
    
    def _parse_document_result(self, result, url):
        """Parse the document analysis result"""
        extraction = {
            'url': url,
            'content_extracted': True,
            'full_text': '',
            'headlines': [],
            'paragraphs': [],
            'key_quotes': [],
            'structure_analysis': {},
            'content_summary': ''
        }
        
        try:
            # Extract the analysis result
            analyze_result = result.get('analyzeResult', {})
            
            # Get all text content
            content_parts = []
            headlines = []
            paragraphs = []
            
            # Process pages
            pages = analyze_result.get('pages', [])
            for page in pages:
                lines = page.get('lines', [])
                for line in lines:
                    text = line.get('content', '').strip()
                    if text:
                        content_parts.append(text)
                        
                        # Try to identify headlines (usually larger text or at top)
                        bounding_box = line.get('polygon', [])
                        if self._is_likely_headline(text, bounding_box, page):
                            headlines.append(text)
                        else:
                            paragraphs.append(text)
            
            # Combine all text
            extraction['full_text'] = '\n'.join(content_parts)
            extraction['headlines'] = headlines[:5]  # Top 5 headlines
            extraction['paragraphs'] = paragraphs[:10]  # Top 10 paragraphs
            
            # Extract key quotes (sentences that might explain headline tone)
            extraction['key_quotes'] = self._extract_key_quotes(extraction['full_text'])
            
            # Structure analysis
            extraction['structure_analysis'] = {
                'total_lines': len(content_parts),
                'headline_count': len(headlines),
                'paragraph_count': len(paragraphs),
                'word_count': len(extraction['full_text'].split())
            }
            
            # Generate content summary
            extraction['content_summary'] = self._generate_content_summary(extraction)
            
            logger.info(f"Successfully extracted content from {url}: {len(content_parts)} lines, {len(headlines)} headlines")
            return extraction
            
        except Exception as e:
            logger.error(f"Error parsing document result: {str(e)}")
            return self._fallback_extraction(url)
    
    def _is_likely_headline(self, text, bounding_box, page):
        """Heuristic to determine if text is likely a headline"""
        # Headlines are typically:
        # 1. Shorter than 200 characters
        # 2. Don't end with periods (usually)
        # 3. Located in upper part of page
        # 4. Have certain formatting patterns
        
        if len(text) > 200:
            return False
        
        # Check if it looks like a headline pattern
        headline_indicators = [
            text.isupper(),  # All caps
            text.istitle(),  # Title case
            not text.endswith('.'),  # No period
            len(text.split()) <= 15,  # Reasonable length
            any(word in text.lower() for word in ['breaking', 'exclusive', 'update', 'news'])
        ]
        
        return sum(headline_indicators) >= 2
    
    def _extract_key_quotes(self, full_text):
        """Extract sentences that might explain negative tone"""
        if not full_text:
            return []
        
        sentences = full_text.split('.')
        key_quotes = []
        
        # Words that often indicate problematic content
        negative_indicators = [
            'threatens', 'crisis', 'disaster', 'fails', 'collapse', 'scandal',
            'outrage', 'fury', 'slams', 'blasts', 'attacks', 'destroys',
            'chaos', 'panic', 'fear', 'violence', 'death', 'killed'
        ]
        
        for sentence in sentences[:20]:  # Check first 20 sentences
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:  # Reasonable length
                for indicator in negative_indicators:
                    if indicator in sentence.lower():
                        key_quotes.append({
                            'quote': sentence,
                            'trigger_word': indicator,
                            'context': 'negative_language'
                        })
                        break
                        
                if len(key_quotes) >= 3:  # Limit to 3 quotes
                    break
        
        return key_quotes
    
    def _generate_content_summary(self, extraction):
        """Generate a summary of the extracted content"""
        structure = extraction['structure_analysis']
        headlines = extraction['headlines']
        quotes = extraction['key_quotes']
        
        summary_parts = []
        
        if structure['word_count'] > 0:
            summary_parts.append(f"Article contains {structure['word_count']} words")
        
        if headlines:
            summary_parts.append(f"Found {len(headlines)} potential headlines")
        
        if quotes:
            summary_parts.append(f"Identified {len(quotes)} problematic phrases that may justify rewriting")
        
        return '. '.join(summary_parts) if summary_parts else "Basic content extraction completed"
    
    def _fallback_extraction(self, url):
        """Fallback when Document Intelligence is unavailable"""
        return {
            'url': url,
            'content_extracted': False,
            'full_text': '',
            'headlines': [],
            'paragraphs': [],
            'key_quotes': [],
            'structure_analysis': {},
            'content_summary': 'Enhanced content extraction unavailable - using basic analysis'
        }
    
    def enhance_rewrite_reasoning(self, headline, content_extraction):
        """Use extracted content to provide better rewrite reasoning"""
        if not content_extraction.get('content_extracted'):
            return None
        
        reasoning_parts = []
        
        # Check if headline matches article content
        full_text = content_extraction.get('full_text', '').lower()
        headline_lower = headline.lower()
        
        # Look for headline words in content
        headline_words = set(headline_lower.split())
        content_words = set(full_text.split())
        
        overlap = len(headline_words.intersection(content_words))
        total_headline_words = len(headline_words)
        
        if total_headline_words > 0:
            overlap_percentage = (overlap / total_headline_words) * 100
            
            if overlap_percentage < 30:
                reasoning_parts.append(f"Headline has low content alignment ({overlap_percentage:.0f}% word overlap)")
        
        # Include specific problematic quotes
        key_quotes = content_extraction.get('key_quotes', [])
        if key_quotes:
            quote_examples = [f"'{q['quote'][:100]}...'" for q in key_quotes[:2]]
            reasoning_parts.append(f"Article contains negative language: {', '.join(quote_examples)}")
        
        # Structure analysis
        structure = content_extraction.get('structure_analysis', {})
        if structure.get('word_count', 0) < 100:
            reasoning_parts.append("Article appears to be very short, headline may be sensationalized")
        
        if reasoning_parts:
            enhanced_reason = '. '.join(reasoning_parts)
            return f"Enhanced analysis: {enhanced_reason}"
        
        return None

# Initialize global instance
document_intelligence = AzureDocumentIntelligence()
