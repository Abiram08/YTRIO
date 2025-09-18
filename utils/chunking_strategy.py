import re
import logging
from typing import List, Dict, Tuple
import hashlib

logger = logging.getLogger(__name__)

class DocumentChunker:
    """Advanced document chunking with intelligent text segmentation"""
    
    def __init__(self, max_chunk_size: int = 200, min_chunk_size: int = 50, overlap: int = 30):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap = overlap
        
        # Sentence boundary patterns (improved)
        self.sentence_endings = re.compile(r'[.!?]+(?=\s|$)')
        self.paragraph_break = re.compile(r'\n\s*\n')
        self.clause_separators = re.compile(r'[;,](?=\s)')
        
    def analyze_text_structure(self, text: str) -> Dict:
        """Analyze text structure to determine optimal chunking strategy"""
        text_length = len(text)
        word_count = len(text.split())
        sentence_count = len(self.sentence_endings.findall(text))
        paragraph_count = len(self.paragraph_break.split(text))
        
        # Calculate average metrics
        avg_sentence_length = word_count / max(sentence_count, 1)
        avg_paragraph_length = text_length / max(paragraph_count, 1)
        
        return {
            'text_length': text_length,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'avg_sentence_length': avg_sentence_length,
            'avg_paragraph_length': avg_paragraph_length,
            'complexity_score': self._calculate_complexity(text)
        }
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity score (0-1)"""
        # Factors that increase complexity
        long_words = len([w for w in text.split() if len(w) > 7])
        punctuation_density = len(re.findall(r'[,;:()\[\]{}"]', text)) / max(len(text), 1)
        sentence_length_variance = self._sentence_length_variance(text)
        
        # Normalize to 0-1 scale
        complexity = (
            (long_words / max(len(text.split()), 1)) * 0.4 +
            min(punctuation_density * 10, 1) * 0.3 +
            min(sentence_length_variance / 50, 1) * 0.3
        )
        
        return min(complexity, 1.0)
    
    def _sentence_length_variance(self, text: str) -> float:
        """Calculate variance in sentence lengths"""
        sentences = self.sentence_endings.split(text)
        if len(sentences) < 2:
            return 0
            
        lengths = [len(s.split()) for s in sentences if s.strip()]
        if not lengths:
            return 0
            
        avg = sum(lengths) / len(lengths)
        variance = sum((x - avg) ** 2 for x in lengths) / len(lengths)
        return variance ** 0.5  # Standard deviation
    
    def smart_chunk(self, text: str) -> List[Dict]:
        """Intelligently chunk text based on structure analysis"""
        analysis = self.analyze_text_structure(text)
        
        # Determine chunking strategy based on analysis
        if analysis['text_length'] < self.max_chunk_size:
            return [{'text': text, 'index': 0, 'type': 'single'}]
        
        # Choose chunking method based on text characteristics
        if analysis['paragraph_count'] > 1 and analysis['avg_paragraph_length'] < self.max_chunk_size * 1.5:
            return self._chunk_by_paragraphs(text, analysis)
        elif analysis['avg_sentence_length'] < self.max_chunk_size * 0.8:
            return self._chunk_by_sentences(text, analysis)
        else:
            return self._chunk_by_semantic_boundaries(text, analysis)
    
    def _chunk_by_paragraphs(self, text: str, analysis: Dict) -> List[Dict]:
        """Chunk text by paragraph boundaries"""
        paragraphs = self.paragraph_break.split(text)
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # If paragraph fits in current chunk
            if len(current_chunk + para) <= self.max_chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append({
                        'text': current_chunk,
                        'index': chunk_index,
                        'type': 'paragraph'
                    })
                    chunk_index += 1
                
                # If single paragraph is too long, chunk it by sentences
                if len(para) > self.max_chunk_size:
                    sentence_chunks = self._chunk_by_sentences(para, analysis)
                    for chunk in sentence_chunks:
                        chunk['index'] = chunk_index
                        chunk['type'] = 'paragraph_sentence'
                        chunks.append(chunk)
                        chunk_index += 1
                    current_chunk = ""
                else:
                    current_chunk = para
        
        # Add remaining chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk,
                'index': chunk_index,
                'type': 'paragraph'
            })
        
        return chunks
    
    def _chunk_by_sentences(self, text: str, analysis: Dict) -> List[Dict]:
        """Chunk text by sentence boundaries"""
        sentences = [s.strip() + '.' for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            # Test if adding this sentence would exceed limit
            test_chunk = (current_chunk + " " + sentence).strip()
            
            if len(test_chunk) <= self.max_chunk_size:
                current_chunk = test_chunk
            else:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append({
                        'text': current_chunk,
                        'index': chunk_index,
                        'type': 'sentence'
                    })
                    chunk_index += 1
                
                # Handle very long sentences
                if len(sentence) > self.max_chunk_size:
                    sub_chunks = self._chunk_long_sentence(sentence)
                    for sub_chunk in sub_chunks:
                        chunks.append({
                            'text': sub_chunk,
                            'index': chunk_index,
                            'type': 'sub_sentence'
                        })
                        chunk_index += 1
                    current_chunk = ""
                else:
                    current_chunk = sentence
        
        # Add remaining chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk,
                'index': chunk_index,
                'type': 'sentence'
            })
        
        return chunks
    
    def _chunk_by_semantic_boundaries(self, text: str, analysis: Dict) -> List[Dict]:
        """Chunk by semantic boundaries (clauses, phrases)"""
        # Split by major clause separators first
        clauses = re.split(r'[;]', text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue
                
            if len(current_chunk + clause) <= self.max_chunk_size:
                current_chunk += (";" if current_chunk else "") + clause
            else:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk,
                        'index': chunk_index,
                        'type': 'semantic'
                    })
                    chunk_index += 1
                
                # If single clause is still too long, split by commas
                if len(clause) > self.max_chunk_size:
                    comma_chunks = self._split_by_commas(clause)
                    for chunk in comma_chunks:
                        chunks.append({
                            'text': chunk,
                            'index': chunk_index,
                            'type': 'comma_split'
                        })
                        chunk_index += 1
                    current_chunk = ""
                else:
                    current_chunk = clause
        
        if current_chunk:
            chunks.append({
                'text': current_chunk,
                'index': chunk_index,
                'type': 'semantic'
            })
        
        return chunks
    
    def _chunk_long_sentence(self, sentence: str) -> List[str]:
        """Break very long sentences at natural points"""
        # First try splitting by commas
        parts = [p.strip() for p in sentence.split(',') if p.strip()]
        
        if len(parts) == 1:
            # If no commas, split by conjunctions
            conjunctions = r'\b(and|or|but|yet|so|because|although|while|since|if|when|where)\b'
            parts = re.split(conjunctions, sentence, flags=re.IGNORECASE)
            parts = [p.strip() for p in parts if p.strip() and not re.match(conjunctions, p, re.IGNORECASE)]
        
        if len(parts) == 1:
            # Last resort: split by word count
            words = sentence.split()
            target_words = self.max_chunk_size // 6  # Approximate words per chunk
            parts = []
            for i in range(0, len(words), target_words):
                part = ' '.join(words[i:i + target_words])
                parts.append(part)
        
        return parts
    
    def _split_by_commas(self, text: str) -> List[str]:
        """Split text by commas and group into chunks"""
        parts = [p.strip() for p in text.split(',') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for part in parts:
            test_chunk = (current_chunk + "," + part).strip() if current_chunk else part
            
            if len(test_chunk) <= self.max_chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = part
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def add_overlap(self, chunks: List[Dict], overlap_size: int = None) -> List[Dict]:
        """Add overlapping content between chunks for context"""
        if len(chunks) <= 1:
            return chunks
            
        overlap_size = overlap_size or self.overlap
        enhanced_chunks = []
        
        for i, chunk in enumerate(chunks):
            enhanced_text = chunk['text']
            
            # Add context from previous chunk
            if i > 0:
                prev_words = chunks[i-1]['text'].split()
                if len(prev_words) > overlap_size // 2:
                    overlap_text = ' '.join(prev_words[-(overlap_size//2):])
                    enhanced_text = f"...{overlap_text} {enhanced_text}"
            
            # Add context from next chunk
            if i < len(chunks) - 1:
                next_words = chunks[i+1]['text'].split()
                if len(next_words) > overlap_size // 2:
                    overlap_text = ' '.join(next_words[:overlap_size//2])
                    enhanced_text = f"{enhanced_text} {overlap_text}..."
            
            enhanced_chunk = chunk.copy()
            enhanced_chunk['text'] = enhanced_text
            enhanced_chunk['original_text'] = chunk['text']  # Keep original
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def optimize_chunk_sizes(self, chunks: List[Dict]) -> List[Dict]:
        """Optimize chunk sizes by merging small chunks"""
        if not chunks:
            return chunks
            
        optimized = []
        current_chunk = None
        
        for chunk in chunks:
            if current_chunk is None:
                current_chunk = chunk.copy()
            elif (len(current_chunk['text']) < self.min_chunk_size and 
                  len(current_chunk['text'] + ' ' + chunk['text']) <= self.max_chunk_size):
                # Merge with current chunk
                current_chunk['text'] += ' ' + chunk['text']
                current_chunk['type'] = 'merged'
            else:
                # Save current and start new
                optimized.append(current_chunk)
                current_chunk = chunk.copy()
        
        if current_chunk:
            optimized.append(current_chunk)
        
        # Update indices
        for i, chunk in enumerate(optimized):
            chunk['index'] = i
            
        return optimized

# Convenience functions for backward compatibility
def smart_text_chunker(text: str, max_chunk_size: int = 200, overlap: int = 30) -> List[str]:
    """Enhanced version of the original smart_text_chunker"""
    chunker = DocumentChunker(max_chunk_size=max_chunk_size, overlap=overlap)
    chunks = chunker.smart_chunk(text)
    chunks = chunker.optimize_chunk_sizes(chunks)
    
    # Return just the text strings for compatibility
    return [chunk['text'] for chunk in chunks]

def analyze_text_for_chunking(text: str) -> Dict:
    """Analyze text to provide chunking recommendations"""
    chunker = DocumentChunker()
    analysis = chunker.analyze_text_structure(text)
    
    # Add recommendations
    if analysis['text_length'] < 200:
        analysis['recommendation'] = 'single_pass'
    elif analysis['paragraph_count'] > 1:
        analysis['recommendation'] = 'paragraph_chunking'
    elif analysis['complexity_score'] > 0.7:
        analysis['recommendation'] = 'semantic_chunking'
    else:
        analysis['recommendation'] = 'sentence_chunking'
    
    # Estimate processing time
    chunk_count = max(1, analysis['text_length'] // 200)
    analysis['estimated_chunks'] = chunk_count
    analysis['estimated_processing_time'] = chunk_count * 3  # 3 seconds per chunk estimate
    
    return analysis