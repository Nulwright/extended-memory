"""Text Processing Utilities"""

import re
import string
from typing import List, Optional, Set
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# Common stop words for keyword extraction
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
    'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'will', 'with',
    'the', 'this', 'but', 'they', 'have', 'had', 'what', 'said', 'each', 'which',
    'their', 'time', 'if', 'up', 'out', 'many', 'then', 'them', 'these', 'so',
    'some', 'her', 'would', 'make', 'like', 'into', 'him', 'has', 'two', 'more',
    'very', 'after', 'words', 'long', 'than', 'first', 'been', 'call', 'who',
    'oil', 'sit', 'now', 'find', 'down', 'day', 'did', 'get', 'come', 'made',
    'may', 'part'
}


def clean_and_process_text(text: str) -> str:
    """Clean and normalize text for processing"""
    try:
        if not text:
            return ""
        
        # Convert to string if not already
        text = str(text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters but keep newlines
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize common unicode characters
        text = text.replace('\u2019', "'")  # Smart apostrophe
        text = text.replace('\u2018', "'")  # Smart apostrophe
        text = text.replace('\u201c', '"')  # Smart quote
        text = text.replace('\u201d', '"')  # Smart quote
        text = text.replace('\u2013', '-')  # En dash
        text = text.replace('\u2014', '-')  # Em dash
        text = text.replace('\u00a0', ' ')  # Non-breaking space
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
        
    except Exception as e:
        logger.error(f"Text cleaning failed: {e}")
        return str(text) if text else ""


def extract_keywords(text: str, max_keywords: int = 10, min_length: int = 3) -> List[str]:
    """Extract important keywords from text"""
    try:
        if not text:
            return []
        
        # Clean the text
        cleaned_text = clean_and_process_text(text)
        
        # Convert to lowercase and remove punctuation
        text_lower = cleaned_text.lower()
        
        # Split into words and remove punctuation
        words = re.findall(r'\b[a-zA-Z]+\b', text_lower)
        
        # Filter out stop words and short words
        meaningful_words = [
            word for word in words 
            if word not in STOP_WORDS and len(word) >= min_length
        ]
        
        # Count word frequency
        word_counts = Counter(meaningful_words)
        
        # Get most common words
        keywords = [word for word, count in word_counts.most_common(max_keywords)]
        
        return keywords
        
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        return []


def highlight_text(text: str, keywords: List[str], max_length: int = 200) -> Optional[str]:
    """Create highlighted snippet of text with keywords"""
    try:
        if not text or not keywords:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        text_lower = text.lower()
        
        # Find first occurrence of any keyword
        first_match = len(text)
        best_keyword = None
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            pos = text_lower.find(keyword_lower)
            if pos != -1 and pos < first_match:
                first_match = pos
                best_keyword = keyword_lower
        
        if best_keyword is None:
            # No keywords found, return beginning of text
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # Calculate snippet boundaries
        snippet_start = max(0, first_match - max_length // 4)
        snippet_end = min(len(text), snippet_start + max_length)
        
        # Adjust to word boundaries
        if snippet_start > 0:
            space_pos = text.find(' ', snippet_start)
            if space_pos != -1 and space_pos - snippet_start < 20:
                snippet_start = space_pos + 1
        
        if snippet_end < len(text):
            space_pos = text.rfind(' ', snippet_start, snippet_end)
            if space_pos != -1 and snippet_end - space_pos < 20:
                snippet_end = space_pos
        
        snippet = text[snippet_start:snippet_end]
        
        # Add ellipses if needed
        if snippet_start > 0:
            snippet = "..." + snippet
        if snippet_end < len(text):
            snippet = snippet + "..."
        
        return snippet
        
    except Exception as e:
        logger.error(f"Text highlighting failed: {e}")
        return text[:max_length] + "..." if len(text) > max_length else text


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks"""
    try:
        if not text or chunk_size <= 0:
            return [text] if text else []
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If this isn't the last chunk, try to break at word boundary
            if end < len(text):
                # Look for space within last 50 characters
                space_pos = text.rfind(' ', end - 50, end)
                if space_pos > start:
                    end = space_pos
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start forward by chunk_size minus overlap
            start = end - overlap
            
            # Ensure we make progress
            if start <= chunks[-1:] and len(chunks) > 1:
                start = end
        
        return chunks
        
    except Exception as e:
        logger.error(f"Text chunking failed: {e}")
        return [text] if text else []


def extract_sentences(text: str) -> List[str]:
    """Extract sentences from text"""
    try:
        if not text:
            return []
        
        # Simple sentence splitting (can be improved with NLTK)
        sentences = re.split(r'[.!?]+(?:\s+|$)', text)
        
        # Clean sentences
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 5:  # Filter very short fragments
                clean_sentences.append(sentence)
        
        return clean_sentences
        
    except Exception as e:
        logger.error(f"Sentence extraction failed: {e}")
        return [text]


def count_words(text: str) -> int:
    """Count words in text"""
    try:
        if not text:
            return 0
        
        # Simple word counting
        words = re.findall(r'\b\w+\b', text)
        return len(words)
        
    except Exception as e:
        logger.error(f"Word counting failed: {e}")
        return 0


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    try:
        if not text or len(text) <= max_length:
            return text
        
        if max_length <= len(suffix):
            return suffix
        
        truncated_length = max_length - len(suffix)
        
        # Try to break at word boundary
        space_pos = text.rfind(' ', 0, truncated_length)
        if space_pos > truncated_length * 0.8:  # If we can break reasonably close
            return text[:space_pos] + suffix
        else:
            return text[:truncated_length] + suffix
            
    except Exception as e:
        logger.error(f"Text truncation failed: {e}")
        return text


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text"""
    try:
        if not text:
            return ""
        
        # Replace multiple whitespace with single space
        normalized = re.sub(r'\s+', ' ', text.strip())
        return normalized
        
    except Exception as e:
        logger.error(f"Whitespace normalization failed: {e}")
        return text


def remove_html_tags(text: str) -> str:
    """Remove HTML tags from text"""
    try:
        if not text:
            return ""
        
        # Simple HTML tag removal
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Replace common HTML entities
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"')
        clean_text = clean_text.replace('&#39;', "'")
        clean_text = clean_text.replace('&nbsp;', ' ')
        
        return clean_text
        
    except Exception as e:
        logger.error(f"HTML tag removal failed: {e}")
        return text


def calculate_readability_score(text: str) -> float:
    """Calculate simple readability score (0-100, higher is more readable)"""
    try:
        if not text:
            return 0.0
        
        sentences = extract_sentences(text)
        words = re.findall(r'\b\w+\b', text)
        
        if not sentences or not words:
            return 0.0
        
        # Simple readability metrics
        avg_sentence_length = len(words) / len(sentences)
        
        # Count syllables (very simple approximation)
        total_syllables = 0
        for word in words:
            syllables = max(1, len(re.findall(r'[aeiouAEIOU]', word)))
            total_syllables += syllables
        
        avg_syllables_per_word = total_syllables / len(words)
        
        # Simplified Flesch Reading Ease formula
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        
        # Clamp to 0-100 range
        return max(0.0, min(100.0, score))
        
    except Exception as e:
        logger.error(f"Readability calculation failed: {e}")
        return 50.0  # Return neutral score on error
