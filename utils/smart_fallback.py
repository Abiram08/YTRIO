#!/usr/bin/env python3
"""Smart fallback processor that detects slow AI and switches to fast mode"""

import time
import logging
from typing import Tuple
from utils.adaptive_optimizer import AdaptiveProcessor

logger = logging.getLogger(__name__)

class SmartFallbackProcessor:
    """Processor that automatically falls back to fast mode when AI is too slow"""
    
    def __init__(self):
        self.adaptive_processor = AdaptiveProcessor()
        self.ai_is_slow = None  # Cache the AI speed detection
        self.slow_threshold = 15.0  # If AI takes >15s for a small chunk, it's slow
    
    def detect_ai_speed(self, tokenizer, model) -> bool:
        """Test if AI processing is fast enough for real-time use"""
        if self.ai_is_slow is not None:
            return not self.ai_is_slow
        
        logger.info("🔍 Testing AI processing speed...")
        
        # Test with a small text sample
        test_text = "This is a test to measure AI processing speed."
        
        try:
            start_time = time.time()
            result, info = self.adaptive_processor.process_text_adaptive(
                test_text, "neutral", tokenizer, model, 
                ultra_fast_mode=True, quality_preference=0.3
            )
            processing_time = time.time() - start_time
            
            logger.info(f"⏱️ AI speed test: {processing_time:.1f}s for {len(test_text)} chars")
            
            # If it takes more than the threshold, AI is too slow
            self.ai_is_slow = processing_time > self.slow_threshold
            
            if self.ai_is_slow:
                logger.warning(f"🐌 AI processing is slow ({processing_time:.1f}s). Will use fast fallback mode.")
            else:
                logger.info(f"⚡ AI processing is fast ({processing_time:.1f}s). Will use AI optimization.")
            
            return not self.ai_is_slow
            
        except Exception as e:
            logger.error(f"❌ AI speed test failed: {e}")
            # Assume AI is slow if we can't test it
            self.ai_is_slow = True
            return False
    
    def process_with_smart_fallback(self, text: str, tone: str, tokenizer, model, 
                                   ultra_fast_mode: bool = True) -> Tuple[str, dict]:
        """Process text with automatic fallback to fast mode if AI is slow"""
        
        # Check if AI is fast enough
        ai_is_fast = self.detect_ai_speed(tokenizer, model)
        
        if not ai_is_fast:
            # Use ultra-fast string processing instead of slow AI
            logger.info("🚀 Using ultra-fast string processing (AI too slow)")
            return self._process_with_string_optimization(text, tone)
        else:
            # Use normal AI processing
            logger.info("🧠 Using AI optimization (AI is fast enough)")
            return self.adaptive_processor.process_text_adaptive(
                text, tone, tokenizer, model, ultra_fast_mode, quality_preference=0.5
            )
    
    def _process_with_string_optimization(self, text: str, tone: str) -> Tuple[str, dict]:
        """Ultra-fast string-based processing for slow systems"""
        start_time = time.time()
        
        tone_lower = tone.lower()
        
        # Split into sentences for better processing
        sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        processed_sentences = []
        
        for sentence in sentences:
            if tone_lower == "suspenseful":
                # Add suspenseful elements
                suspenseful_words = ["mysterious", "ominous", "threatening", "dark", "foreboding"]
                # Replace first occurrence of "the" or "a" with a suspenseful word
                for word in ["the ", "a ", "an ", " and ", " but "]:
                    if word in sentence.lower() and len(processed_sentences) < 3:
                        sentence = sentence.replace(word, f" {suspenseful_words[len(processed_sentences) % len(suspenseful_words)]} ", 1)
                        break
                processed_sentences.append(sentence + "...")
                
            elif tone_lower == "inspiring":
                # Add inspiring elements
                inspiring_words = ["incredible", "amazing", "extraordinary", "remarkable", "powerful"]
                # Replace first occurrence of common words
                for word in ["the ", "a ", "an ", " and ", " but "]:
                    if word in sentence.lower() and len(processed_sentences) < 3:
                        sentence = sentence.replace(word, f" {inspiring_words[len(processed_sentences) % len(inspiring_words)]} ", 1)
                        break
                processed_sentences.append(sentence + "!")
                
            else:  # neutral
                # Clean up for neutral tone
                sentence = sentence.replace("...", ".").replace("!!", "!")
                processed_sentences.append(sentence + ".")
        
        result = " ".join(processed_sentences)
        processing_time = time.time() - start_time
        
        # Create info dict
        processing_info = {
            'strategy_used': 'ultra_fast_string',
            'processing_time': processing_time,
            'text_length': len(text),
            'estimated_time': processing_time,
            'time_saved': max(0, 300 - processing_time),  # Compared to 5+ minutes
            'efficiency_ratio': 300 / max(processing_time, 0.1),  # How much faster than slow AI
            'quality_score': 0.4  # Lower quality but much faster
        }
        
        logger.info(f"⚡ Ultra-fast processing completed in {processing_time:.1f}s")
        return result, processing_info

# Convenience function for easy integration
def process_with_smart_fallback(text: str, tone: str, tokenizer, model, 
                               ultra_fast_mode: bool = True) -> Tuple[str, dict]:
    """
    Process text with smart fallback to ultra-fast mode if AI is slow
    
    This function automatically detects if your AI processing is too slow 
    (>15 seconds for simple text) and falls back to fast string processing
    """
    processor = SmartFallbackProcessor()
    return processor.process_with_smart_fallback(text, tone, tokenizer, model, ultra_fast_mode)