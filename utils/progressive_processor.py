import asyncio
import time
import logging
from typing import List, Dict, Callable, Optional, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue, Empty
from utils.chunking_strategy import DocumentChunker, analyze_text_for_chunking
from utils.granite_helper import rewrite_with_tone

logger = logging.getLogger(__name__)

class ProgressiveProcessor:
    """Progressive processing system for long texts with streaming results"""
    
    def __init__(self, max_concurrent_chunks: int = 2):
        self.max_concurrent_chunks = max_concurrent_chunks
        self.chunker = DocumentChunker()
        self.progress_callbacks = []
        self.results_queue = Queue()
        self.stop_event = threading.Event()
        
    def add_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Add a callback for progress updates: callback(current, total, status)"""
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self, current: int, total: int, status: str):
        """Notify all progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(current, total, status)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    def process_text_progressive(self, text: str, tone: str, tokenizer, model, 
                                ultra_fast_mode: bool = True) -> Generator[Dict, None, Dict]:
        """
        Process text progressively, yielding results as they become available
        Returns generator of progress updates and final complete result
        """
        analysis = analyze_text_for_chunking(text)
        
        # Yield initial analysis
        yield {
            'type': 'analysis',
            'data': analysis,
            'status': 'starting'
        }
        
        if analysis['text_length'] < 300:
            # Short text - process directly
            yield {'type': 'progress', 'current': 0, 'total': 1, 'status': 'Processing short text...'}
            
            start_time = time.time()
            result = rewrite_with_tone(text, tone, tokenizer, model, ultra_fast_mode)
            processing_time = time.time() - start_time
            
            yield {'type': 'progress', 'current': 1, 'total': 1, 'status': 'Complete!'}
            yield {
                'type': 'complete',
                'result': result,
                'processing_time': processing_time,
                'chunks_processed': 1
            }
            return
        
        # Long text - use chunking with progressive processing
        chunks = self.chunker.smart_chunk(text)
        chunks = self.chunker.optimize_chunk_sizes(chunks)
        
        yield {
            'type': 'chunks_created', 
            'chunk_count': len(chunks),
            'chunks': [{'index': c['index'], 'length': len(c['text']), 'type': c['type']} for c in chunks]
        }
        
        # Process chunks progressively
        results = []
        start_time = time.time()
        
        for i, chunk_result in enumerate(self._process_chunks_concurrent(chunks, tone, tokenizer, model, ultra_fast_mode)):
            results.append(chunk_result)
            
            yield {
                'type': 'chunk_complete',
                'chunk_index': i,
                'chunk_result': chunk_result,
                'partial_text': ' '.join([r['text'] for r in results])
            }
            
            yield {
                'type': 'progress',
                'current': i + 1,
                'total': len(chunks),
                'status': f'Processed chunk {i + 1}/{len(chunks)}'
            }
        
        # Combine results
        combined_text = ' '.join([r['text'] for r in results])
        total_processing_time = time.time() - start_time
        
        yield {
            'type': 'complete',
            'result': combined_text,
            'processing_time': total_processing_time,
            'chunks_processed': len(chunks),
            'chunk_details': results
        }
    
    def _process_chunks_concurrent(self, chunks: List[Dict], tone: str, tokenizer, model, 
                                  ultra_fast_mode: bool) -> Generator[Dict, None, None]:
        """Process chunks concurrently while maintaining order"""
        
        # For small number of chunks, process sequentially for simplicity
        if len(chunks) <= 2:
            for chunk in chunks:
                start_time = time.time()
                result_text = rewrite_with_tone(chunk['text'], tone, tokenizer, model, ultra_fast_mode)
                processing_time = time.time() - start_time
                
                yield {
                    'text': result_text,
                    'original_text': chunk['text'],
                    'chunk_index': chunk['index'],
                    'chunk_type': chunk['type'],
                    'processing_time': processing_time
                }
            return
        
        # For larger number of chunks, use concurrent processing
        with ThreadPoolExecutor(max_workers=min(self.max_concurrent_chunks, len(chunks))) as executor:
            # Submit all tasks
            future_to_chunk = {}
            for chunk in chunks:
                future = executor.submit(self._process_single_chunk, chunk, tone, tokenizer, model, ultra_fast_mode)
                future_to_chunk[future] = chunk
            
            # Collect results in order
            results = [None] * len(chunks)
            completed_count = 0
            
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    result = future.result()
                    results[chunk['index']] = result
                    completed_count += 1
                    
                    # Yield results in order as they become available
                    while completed_count > 0 and results[len(results) - completed_count] is not None:
                        idx = len(results) - completed_count
                        yield results[idx]
                        completed_count -= 1
                        
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk['index']}: {e}")
                    # Return original text on error
                    error_result = {
                        'text': chunk['text'],
                        'original_text': chunk['text'],
                        'chunk_index': chunk['index'],
                        'chunk_type': chunk['type'],
                        'processing_time': 0,
                        'error': str(e)
                    }
                    results[chunk['index']] = error_result
            
            # Yield any remaining results
            for result in results:
                if result is not None:
                    yield result
    
    def _process_single_chunk(self, chunk: Dict, tone: str, tokenizer, model, ultra_fast_mode: bool) -> Dict:
        """Process a single chunk"""
        start_time = time.time()
        
        try:
            result_text = rewrite_with_tone(chunk['text'], tone, tokenizer, model, ultra_fast_mode)
            processing_time = time.time() - start_time
            
            return {
                'text': result_text,
                'original_text': chunk['text'],
                'chunk_index': chunk['index'],
                'chunk_type': chunk['type'],
                'processing_time': processing_time
            }
        except Exception as e:
            logger.error(f"Error in chunk processing: {e}")
            return {
                'text': chunk['text'],  # Return original on error
                'original_text': chunk['text'],
                'chunk_index': chunk['index'],
                'chunk_type': chunk['type'],
                'processing_time': time.time() - start_time,
                'error': str(e)
            }

class StreamingProcessor:
    """Streaming processor with real-time updates for Streamlit"""
    
    def __init__(self):
        self.processor = ProgressiveProcessor()
    
    def process_with_streaming_updates(self, text: str, tone: str, tokenizer, model, 
                                     ultra_fast_mode: bool = True, 
                                     streamlit_container=None) -> str:
        """
        Process text with streaming updates displayed in Streamlit
        Returns the final processed text
        """
        import streamlit as st
        
        final_result = None
        progress_bar = None
        status_text = None
        partial_results_container = None
        
        if streamlit_container:
            with streamlit_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                partial_results_container = st.expander("🔄 Live Processing Results", expanded=False)
        
        try:
            for update in self.processor.process_text_progressive(text, tone, tokenizer, model, ultra_fast_mode):
                
                if update['type'] == 'analysis':
                    if status_text:
                        analysis = update['data']
                        status_text.info(f"📊 Analysis: {analysis['text_length']} chars, "
                                       f"~{analysis['estimated_chunks']} chunks, "
                                       f"strategy: {analysis['recommendation']}")
                
                elif update['type'] == 'chunks_created':
                    if status_text:
                        status_text.success(f"✂️ Created {update['chunk_count']} processing chunks")
                
                elif update['type'] == 'progress':
                    current = update['current']
                    total = update['total']
                    status = update['status']
                    
                    if progress_bar:
                        progress_bar.progress(current / total)
                    if status_text:
                        status_text.info(f"⚡ {status} ({current}/{total})")
                
                elif update['type'] == 'chunk_complete':
                    chunk_result = update['chunk_result']
                    partial_text = update.get('partial_text', '')
                    
                    if partial_results_container:
                        with partial_results_container:
                            st.markdown(f"**Chunk {chunk_result['chunk_index'] + 1} Complete** "
                                      f"({chunk_result['processing_time']:.1f}s)")
                            st.write(chunk_result['text'])
                            
                            if len(partial_text) > 100:
                                st.markdown("**Current Combined Result:**")
                                st.write(partial_text[:500] + "..." if len(partial_text) > 500 else partial_text)
                
                elif update['type'] == 'complete':
                    final_result = update['result']
                    processing_time = update['processing_time']
                    chunks_processed = update['chunks_processed']
                    
                    if progress_bar:
                        progress_bar.progress(1.0)
                    if status_text:
                        status_text.success(f"✅ Complete! Processed {chunks_processed} chunks "
                                          f"in {processing_time:.1f}s")
                    
                    break
        
        except Exception as e:
            logger.error(f"Streaming processing error: {e}")
            if status_text:
                status_text.error(f"❌ Error: {str(e)}")
            return text  # Return original on error
        
        return final_result if final_result else text

class BatchProcessor:
    """Batch processor for handling multiple texts efficiently"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.processor = ProgressiveProcessor(max_concurrent_chunks=2)
    
    def process_batch(self, texts: List[str], tone: str, tokenizer, model, 
                     ultra_fast_mode: bool = True) -> List[str]:
        """Process multiple texts in batch"""
        
        results = [None] * len(texts)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {}
            
            for i, text in enumerate(texts):
                future = executor.submit(self._process_single_text, text, tone, tokenizer, model, ultra_fast_mode)
                future_to_index[future] = i
            
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results[index] = result
                except Exception as e:
                    logger.error(f"Error processing text {index}: {e}")
                    results[index] = texts[index]  # Return original on error
        
        return results
    
    def _process_single_text(self, text: str, tone: str, tokenizer, model, ultra_fast_mode: bool) -> str:
        """Process a single text completely"""
        
        final_result = None
        
        for update in self.processor.process_text_progressive(text, tone, tokenizer, model, ultra_fast_mode):
            if update['type'] == 'complete':
                final_result = update['result']
                break
        
        return final_result if final_result else text

# Utility functions for integration
def process_text_with_progress(text: str, tone: str, tokenizer, model, 
                             ultra_fast_mode: bool = True, 
                             progress_callback: Optional[Callable] = None) -> str:
    """
    Simple function to process text with optional progress callback
    Callback signature: callback(current: int, total: int, status: str)
    """
    
    processor = ProgressiveProcessor()
    if progress_callback:
        processor.add_progress_callback(progress_callback)
    
    final_result = None
    
    for update in processor.process_text_progressive(text, tone, tokenizer, model, ultra_fast_mode):
        if update['type'] == 'complete':
            final_result = update['result']
            break
    
    return final_result if final_result else text

def estimate_processing_time(text: str) -> Dict:
    """Estimate processing time for given text"""
    analysis = analyze_text_for_chunking(text)
    
    # Base time estimates (in seconds)
    base_time_per_chunk = 3
    model_overhead = 1
    
    estimated_time = (analysis['estimated_chunks'] * base_time_per_chunk) + model_overhead
    
    return {
        'estimated_seconds': estimated_time,
        'estimated_minutes': estimated_time / 60,
        'chunk_count': analysis['estimated_chunks'],
        'text_length': analysis['text_length'],
        'processing_strategy': analysis['recommendation']
    }