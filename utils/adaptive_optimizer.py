import time
import logging
from typing import Dict, Tuple, Optional, List
from enum import Enum
from utils.chunking_strategy import DocumentChunker, analyze_text_for_chunking
from utils.progressive_processor import ProgressiveProcessor, StreamingProcessor, estimate_processing_time
from utils.granite_helper import rewrite_with_tone

logger = logging.getLogger(__name__)

class ProcessingStrategy(Enum):
    """Available processing strategies"""
    MICRO = "micro"           # <50 chars - instant string replacement
    EXPRESS = "express"       # 50-150 chars - ultra-fast AI 
    STANDARD = "standard"     # 150-500 chars - standard processing
    CHUNKED = "chunked"       # 500-2000 chars - chunk processing
    PROGRESSIVE = "progressive" # >2000 chars - progressive streaming
    BATCH = "batch"           # Multiple texts - batch processing

class TextClassifier:
    """Classify text to determine optimal processing strategy"""
    
    def __init__(self):
        # Strategy thresholds
        self.thresholds = {
            ProcessingStrategy.MICRO: 50,
            ProcessingStrategy.EXPRESS: 150,
            ProcessingStrategy.STANDARD: 500,
            ProcessingStrategy.CHUNKED: 2000,
            ProcessingStrategy.PROGRESSIVE: float('inf')
        }
        
        # Quality vs Speed preferences
        self.quality_weights = {
            ProcessingStrategy.MICRO: 0.3,      # Low quality, max speed
            ProcessingStrategy.EXPRESS: 0.6,    # Good quality, high speed
            ProcessingStrategy.STANDARD: 0.8,   # High quality, medium speed
            ProcessingStrategy.CHUNKED: 0.85,   # High quality, lower speed
            ProcessingStrategy.PROGRESSIVE: 0.9  # Highest quality, varies speed
        }
    
    def classify_text(self, text: str, ultra_fast_mode: bool = True, 
                     quality_preference: float = 0.5) -> Dict:
        """
        Classify text and recommend processing strategy
        
        Args:
            text: Input text to classify
            ultra_fast_mode: User preference for speed vs quality
            quality_preference: 0.0 = max speed, 1.0 = max quality
            
        Returns:
            Classification dictionary with strategy and parameters
        """
        text_length = len(text)
        word_count = len(text.split())
        
        # Get text structure analysis
        analysis = analyze_text_for_chunking(text)
        
        # Base strategy from length
        base_strategy = self._get_base_strategy(text_length)
        
        # Adjust based on preferences
        adjusted_strategy = self._adjust_for_preferences(
            base_strategy, ultra_fast_mode, quality_preference, analysis
        )
        
        # Calculate processing parameters
        processing_params = self._calculate_processing_params(
            adjusted_strategy, text_length, analysis
        )
        
        return {
            'strategy': adjusted_strategy,
            'base_strategy': base_strategy,
            'text_length': text_length,
            'word_count': word_count,
            'complexity_score': analysis.get('complexity_score', 0),
            'estimated_time': processing_params['estimated_time'],
            'chunk_count': processing_params['chunk_count'],
            'processing_params': processing_params,
            'quality_score': self.quality_weights[adjusted_strategy],
            'speed_score': 1.0 - self.quality_weights[adjusted_strategy]
        }
    
    def _get_base_strategy(self, text_length: int) -> ProcessingStrategy:
        """Get base strategy from text length"""
        for strategy, threshold in self.thresholds.items():
            if text_length <= threshold:
                return strategy
        return ProcessingStrategy.PROGRESSIVE
    
    def _adjust_for_preferences(self, base_strategy: ProcessingStrategy, 
                               ultra_fast_mode: bool, quality_preference: float,
                               analysis: Dict) -> ProcessingStrategy:
        """Adjust strategy based on user preferences and text characteristics"""
        
        # If ultra-fast mode is enabled, prefer faster strategies
        if ultra_fast_mode and quality_preference < 0.7:
            if base_strategy == ProcessingStrategy.STANDARD:
                return ProcessingStrategy.EXPRESS
            elif base_strategy == ProcessingStrategy.CHUNKED:
                return ProcessingStrategy.STANDARD
            elif base_strategy == ProcessingStrategy.PROGRESSIVE:
                return ProcessingStrategy.CHUNKED
        
        # If high quality is preferred, upgrade strategy
        elif quality_preference > 0.8:
            if base_strategy == ProcessingStrategy.MICRO:
                return ProcessingStrategy.EXPRESS
            elif base_strategy == ProcessingStrategy.EXPRESS:
                return ProcessingStrategy.STANDARD
        
        # Consider text complexity
        complexity = analysis.get('complexity_score', 0)
        if complexity > 0.7 and quality_preference > 0.6:
            # Complex text benefits from better processing
            if base_strategy == ProcessingStrategy.EXPRESS:
                return ProcessingStrategy.STANDARD
            elif base_strategy == ProcessingStrategy.STANDARD:
                return ProcessingStrategy.CHUNKED
        
        return base_strategy
    
    def _calculate_processing_params(self, strategy: ProcessingStrategy, 
                                   text_length: int, analysis: Dict) -> Dict:
        """Calculate processing parameters for the chosen strategy"""
        
        # Estimate word count from text length if not available
        word_count = analysis.get('word_count', text_length // 5)
        
        if strategy == ProcessingStrategy.MICRO:
            return {
                'estimated_time': 0.1,
                'chunk_count': 1,
                'max_tokens': 10,
                'use_ai': False,
                'concurrent_chunks': 1
            }
        
        elif strategy == ProcessingStrategy.EXPRESS:
            return {
                'estimated_time': min(3, text_length / 50),
                'chunk_count': 1,
                'max_tokens': min(30, word_count + 10),
                'use_ai': True,
                'concurrent_chunks': 1,
                'temperature': 0.1
            }
        
        elif strategy == ProcessingStrategy.STANDARD:
            return {
                'estimated_time': min(8, text_length / 30),
                'chunk_count': 1,
                'max_tokens': min(80, word_count * 2),
                'use_ai': True,
                'concurrent_chunks': 1,
                'temperature': 0.3
            }
        
        elif strategy == ProcessingStrategy.CHUNKED:
            chunk_count = max(1, text_length // 200)
            return {
                'estimated_time': chunk_count * 4,
                'chunk_count': chunk_count,
                'max_tokens': 50,
                'use_ai': True,
                'concurrent_chunks': min(2, chunk_count),
                'temperature': 0.2
            }
        
        else:  # PROGRESSIVE
            chunk_count = max(1, text_length // 150)
            return {
                'estimated_time': chunk_count * 3,
                'chunk_count': chunk_count,
                'max_tokens': 60,
                'use_ai': True,
                'concurrent_chunks': 2,
                'temperature': 0.2,
                'streaming': True
            }

class AdaptiveProcessor:
    """Main adaptive processor that selects and executes optimal processing strategy"""
    
    def __init__(self):
        self.classifier = TextClassifier()
        self.progressive_processor = ProgressiveProcessor()
        self.streaming_processor = StreamingProcessor()
        self.performance_cache = {}
    
    def process_text_adaptive(self, text: str, tone: str, tokenizer, model,
                            ultra_fast_mode: bool = True,
                            quality_preference: float = 0.5,
                            streamlit_container=None) -> Tuple[str, Dict]:
        """
        Process text using adaptive strategy selection
        
        Returns:
            Tuple of (processed_text, processing_info)
        """
        
        # Classify text and determine strategy
        classification = self.classifier.classify_text(text, ultra_fast_mode, quality_preference)
        strategy = classification['strategy']
        
        logger.info(f"Using {strategy.value} strategy for {len(text)} char text")
        
        # Record start time
        start_time = time.time()
        
        try:
            # Execute strategy
            if strategy == ProcessingStrategy.MICRO:
                result = self._process_micro(text, tone)
                
            elif strategy == ProcessingStrategy.EXPRESS:
                result = self._process_express(text, tone, tokenizer, model, classification)
                
            elif strategy == ProcessingStrategy.STANDARD:
                result = self._process_standard(text, tone, tokenizer, model, classification)
                
            elif strategy == ProcessingStrategy.CHUNKED:
                result = self._process_chunked(text, tone, tokenizer, model, classification)
                
            else:  # PROGRESSIVE
                if streamlit_container:
                    result = self._process_progressive_streaming(
                        text, tone, tokenizer, model, classification, streamlit_container
                    )
                else:
                    result = self._process_progressive(text, tone, tokenizer, model, classification)
            
            processing_time = time.time() - start_time
            
            # Update performance cache
            self._update_performance_cache(strategy, len(text), processing_time)
            
            # Prepare processing info
            processing_info = {
                'strategy_used': strategy.value,
                'processing_time': processing_time,
                'text_length': len(text),
                'estimated_time': classification['estimated_time'],
                'time_saved': max(0, classification['estimated_time'] - processing_time),
                'efficiency_ratio': classification['estimated_time'] / max(processing_time, 0.1),
                'quality_score': classification['quality_score'],
                'chunk_count': classification.get('chunk_count', 1)
            }
            
            return result, processing_info
            
        except Exception as e:
            logger.error(f"Error in adaptive processing: {e}")
            processing_time = time.time() - start_time
            
            # Return original text on error
            processing_info = {
                'strategy_used': strategy.value,
                'processing_time': processing_time,
                'error': str(e),
                'text_length': len(text)
            }
            
            return text, processing_info
    
    def _process_micro(self, text: str, tone: str) -> str:
        """Ultra-fast string replacement processing"""
        tone_lower = tone.lower()
        
        # Enhanced micro processing for longer texts when AI is too slow
        if len(text) > 50:
            sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]
            processed_sentences = []
            
            for sentence in sentences:
                if tone_lower == "suspenseful":
                    if "danger" not in sentence.lower() and "threat" not in sentence.lower():
                        sentence = sentence.replace(" ", " mysterious ", 1)  # Add suspense
                    processed_sentences.append(sentence + "...")
                elif tone_lower == "inspiring":
                    if "will" not in sentence.lower() and "can" not in sentence.lower():
                        sentence = sentence.replace(" ", " incredible ", 1)  # Add inspiration
                    processed_sentences.append(sentence + "!")
                else:  # neutral
                    processed_sentences.append(sentence + ".")
            
            return " ".join(processed_sentences)
        
        # Original micro processing for short texts
        if tone_lower == "suspenseful":
            if not text.endswith('...'):
                return text.rstrip('.!?') + "..."
            return text
            
        elif tone_lower == "inspiring":
            # Add motivational language
            if text.endswith('.'):
                return text[:-1] + "!"
            elif not text.endswith('!'):
                return text + "!"
            return text
            
        else:  # neutral
            # Clean up punctuation
            return text.replace('!', '.').replace('...', '.')
    
    def _process_express(self, text: str, tone: str, tokenizer, model, classification: Dict) -> str:
        """Express AI processing with minimal tokens"""
        return rewrite_with_tone(text, tone, tokenizer, model, ultra_fast_mode=True)
    
    def _process_standard(self, text: str, tone: str, tokenizer, model, classification: Dict) -> str:
        """Standard AI processing"""
        return rewrite_with_tone(text, tone, tokenizer, model, ultra_fast_mode=False)
    
    def _process_chunked(self, text: str, tone: str, tokenizer, model, classification: Dict) -> str:
        """Chunked processing without streaming"""
        chunker = DocumentChunker(max_chunk_size=200)
        chunks = chunker.smart_chunk(text)
        chunks = chunker.optimize_chunk_sizes(chunks)
        
        results = []
        for chunk in chunks:
            result = rewrite_with_tone(chunk['text'], tone, tokenizer, model, ultra_fast_mode=True)
            results.append(result)
        
        return ' '.join(results)
    
    def _process_progressive(self, text: str, tone: str, tokenizer, model, classification: Dict) -> str:
        """Progressive processing without UI updates"""
        final_result = None
        
        for update in self.progressive_processor.process_text_progressive(
            text, tone, tokenizer, model, ultra_fast_mode=True
        ):
            if update['type'] == 'complete':
                final_result = update['result']
                break
        
        return final_result if final_result else text
    
    def _process_progressive_streaming(self, text: str, tone: str, tokenizer, model, 
                                     classification: Dict, streamlit_container) -> str:
        """Progressive processing with Streamlit streaming updates"""
        return self.streaming_processor.process_with_streaming_updates(
            text, tone, tokenizer, model, ultra_fast_mode=True, 
            streamlit_container=streamlit_container
        )
    
    def _update_performance_cache(self, strategy: ProcessingStrategy, text_length: int, 
                                processing_time: float):
        """Update performance cache for future strategy optimization"""
        key = f"{strategy.value}_{text_length//100*100}"  # Group by 100-char buckets
        
        if key not in self.performance_cache:
            self.performance_cache[key] = []
        
        self.performance_cache[key].append(processing_time)
        
        # Keep only recent performance data (last 10 measurements)
        if len(self.performance_cache[key]) > 10:
            self.performance_cache[key] = self.performance_cache[key][-10:]
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        stats = {}
        
        for key, times in self.performance_cache.items():
            strategy, length_bucket = key.split('_')
            length_bucket = int(length_bucket)
            
            if strategy not in stats:
                stats[strategy] = {}
            
            stats[strategy][length_bucket] = {
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'sample_count': len(times)
            }
        
        return stats
    
    def recommend_strategy(self, text: str, time_budget: float = None) -> Dict:
        """Recommend optimal strategy given constraints"""
        classification = self.classifier.classify_text(text)
        
        recommendation = {
            'recommended_strategy': classification['strategy'].value,
            'estimated_time': classification['estimated_time'],
            'quality_score': classification['quality_score'],
            'alternatives': []
        }
        
        # If there's a time budget, suggest alternatives
        if time_budget:
            all_strategies = [ProcessingStrategy.MICRO, ProcessingStrategy.EXPRESS, 
                            ProcessingStrategy.STANDARD, ProcessingStrategy.CHUNKED, 
                            ProcessingStrategy.PROGRESSIVE]
            
            for strategy in all_strategies:
                test_classification = self.classifier.classify_text(text)
                test_classification['strategy'] = strategy
                test_params = self.classifier._calculate_processing_params(
                    strategy, len(text), analyze_text_for_chunking(text)
                )
                
                if test_params['estimated_time'] <= time_budget:
                    recommendation['alternatives'].append({
                        'strategy': strategy.value,
                        'estimated_time': test_params['estimated_time'],
                        'quality_score': self.classifier.quality_weights[strategy],
                        'fits_budget': True
                    })
        
        return recommendation

# Convenience functions for easy integration
def process_text_optimally(text: str, tone: str, tokenizer, model,
                         ultra_fast_mode: bool = True,
                         quality_preference: float = 0.5,
                         streamlit_container=None) -> Tuple[str, Dict]:
    """
    Process text using optimal adaptive strategy
    
    Args:
        text: Input text
        tone: Target tone
        tokenizer: Model tokenizer
        model: AI model
        ultra_fast_mode: Speed vs quality preference
        quality_preference: 0.0 = max speed, 1.0 = max quality
        streamlit_container: Optional Streamlit container for progress updates
    
    Returns:
        Tuple of (processed_text, processing_info)
    """
    processor = AdaptiveProcessor()
    return processor.process_text_adaptive(
        text, tone, tokenizer, model, ultra_fast_mode, quality_preference, streamlit_container
    )

def analyze_processing_options(text: str, time_budget: float = None) -> Dict:
    """Analyze processing options for given text"""
    processor = AdaptiveProcessor()
    return processor.recommend_strategy(text, time_budget)

def get_processing_estimates(texts: List[str]) -> List[Dict]:
    """Get processing time estimates for multiple texts"""
    classifier = TextClassifier()
    estimates = []
    
    for text in texts:
        classification = classifier.classify_text(text)
        estimates.append({
            'text_length': len(text),
            'strategy': classification['strategy'].value,
            'estimated_time': classification['estimated_time'],
            'quality_score': classification['quality_score']
        })
    
    return estimates