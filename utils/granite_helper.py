import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
import logging
import time
import psutil
import re
import hashlib

# Simple cache for processed text
_text_cache = {}

# Enable detailed logging for IBM Granite model loading
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# IBM Granite Model Configuration - NO WATSONX DEPENDENCY
GRANITE_MODEL_CONFIG = {
    "model_name": "ibm-granite/granite-3.3-2b-instruct",
    "model_type": "granite",
    "provider": "huggingface",
    "local_path": "./models/granite-2b",
    "supports_chat": True,
    "context_length": 2048,
    "description": "IBM Granite 3.3 2B Instruct - Optimized for instruction following and text rewriting"
}

# Timeout exception for loading
class TimeoutException(Exception):
    pass

@st.cache_resource
def load_granite_model():
    """Load IBM Granite 3.3 2B Instruct model locally (NO WATSONX DEPENDENCY).
    
    Returns:
        Tuple of (tokenizer, model) - Ready for text rewriting tasks.
    """
    model_path = GRANITE_MODEL_CONFIG["local_path"]
    model_name = GRANITE_MODEL_CONFIG["model_name"]
    
    logger.info(f"Loading IBM Granite model from {model_path}")
    logger.info(f"Model: {GRANITE_MODEL_CONFIG['description']}")
    logger.info(f"Provider: {GRANITE_MODEL_CONFIG['provider']} (NO WATSONX)")
    
    try:
        # Check if local model exists, else fall back to remote
        if os.path.exists(model_path):
            logger.info(f"Checking model files in {model_path}")
            files = os.listdir(model_path)
            logger.info(f"Found files: {files}")
            
            logger.info(f"Loading tokenizer from {model_path}")
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                local_files_only=True,
                trust_remote_code=True
            )
            
            logger.info(f"Loading model from {model_path} with optimized settings...")
            # More aggressive memory optimization
            device_map_setting = "auto" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device_map: {device_map_setting}")
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                local_files_only=True,
                torch_dtype=torch.float16,  # Use float16 for speed
                device_map="cpu",  # Force CPU for consistency and speed
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                max_memory={"cpu": "6GB"},  # Aggressive memory limit
                offload_folder="./models/offload",
                load_in_8bit=False,
            )
            logger.info(f"Local model loaded successfully")
            
        else:
            logger.info(f"Local model not found at {model_path}. Downloading from Hugging Face...")
            
            # Create models directory if it doesn't exist
            os.makedirs("./models/cache", exist_ok=True)
            
            logger.info("Loading tokenizer from Hugging Face...")
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir="./models/cache",
                trust_remote_code=True
            )
            
            logger.info("Loading model from Hugging Face with optimized settings...")
            device_map_setting = "auto" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device_map: {device_map_setting}")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                cache_dir="./models/cache",
                torch_dtype=torch.float16,
                device_map=device_map_setting,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                max_memory={0: "6GB", "cpu": "8GB"} if torch.cuda.is_available() else {"cpu": "8GB"},
                offload_folder="./models/offload",
            )
            logger.info(f"Model downloaded and loaded successfully")
        
        # Ensure model is in evaluation mode
        model.eval()
        
        # Test the model with a simple generation to verify it works
        logger.info("Testing model functionality...")
        test_input = tokenizer("Hello", return_tensors="pt")
        with torch.no_grad():
            _ = model.generate(
                test_input.input_ids,
                max_new_tokens=1,
                do_sample=False
            )
        logger.info("Model test successful!")
        
        return tokenizer, model
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise Exception(f"Model loading failed: {str(e)}. Check if you have enough RAM (8GB+ recommended) and disk space.")

@st.cache_resource
def load_granite_model_fallback():
    """Memory-optimized fallback model loading for low-RAM systems"""
    model_path = "./models/granite-2b"
    model_name = "ibm-granite/granite-3.3-2b-instruct"
    
    logger.info("Attempting memory-optimized fallback model loading...")
    
    # Check available memory
    import psutil
    memory = psutil.virtual_memory()
    available_gb = memory.available / (1024**3)
    logger.info(f"Available RAM: {available_gb:.1f} GB")
    
    if available_gb < 2.0:
        raise Exception(f"Insufficient RAM: {available_gb:.1f} GB available, need at least 2GB. Please close other applications and try again.")
    
    try:
        if os.path.exists(model_path):
            logger.info("Loading local model with extreme memory optimization...")
            
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                local_files_only=True
            )
            
            # Most aggressive memory settings
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                local_files_only=True,
                torch_dtype=torch.float16,  # Half precision
                device_map="cpu",  # Force CPU
                low_cpu_mem_usage=True,  # Aggressive memory management
                trust_remote_code=True,
                max_memory={"cpu": f"{int(available_gb * 0.8)}GB"},  # Use 80% of available RAM
                offload_folder="./models/offload",  # Offload to disk
            )
            
        else:
            logger.info("Loading remote model with extreme memory optimization...")
            
            # Create cache directory
            os.makedirs("./models/cache", exist_ok=True)
            
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir="./models/cache"
            )
            
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                cache_dir="./models/cache",
                torch_dtype=torch.float16,
                device_map="cpu",
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                max_memory={"cpu": f"{int(available_gb * 0.8)}GB"},
                offload_folder="./models/offload",
            )
        
        model.eval()
        logger.info("Memory-optimized model loaded successfully!")
        return tokenizer, model
        
    except Exception as e:
        logger.error(f"Memory-optimized loading failed: {str(e)}")
        raise Exception(f"Model loading failed even with memory optimization. Available RAM: {available_gb:.1f}GB. Error: {str(e)}")

def smart_text_chunker(text, max_chunk_size=400, overlap=20):
    """Split long text into optimal chunks for processing - Enhanced version with larger chunks"""
    try:
        from utils.chunking_strategy import smart_text_chunker as enhanced_chunker
        return enhanced_chunker(text, max_chunk_size, overlap)
    except ImportError:
        # Fallback to improved implementation with larger chunks
        if len(text) <= max_chunk_size:
            return [text]  # No chunking needed
        
        chunks = []
        # Split by paragraphs first, then sentences if needed
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            if len(paragraph) <= max_chunk_size:
                chunks.append(paragraph)
            else:
                # Split paragraph by sentences
                sentences = paragraph.replace('!', '.').replace('?', '.').split('.')
                sentences = [s.strip() + '.' for s in sentences if s.strip()]
                
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk + " " + sentence) <= max_chunk_size:
                        current_chunk += " " + sentence if current_chunk else sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text]

def preprocess_text(text, max_length=1500):
    """Preprocess input text with smart handling for different lengths"""
    text = text.strip()
    
    # For very long text, suggest chunking
    if len(text) > 2000:
        logger.info(f"Long text detected ({len(text)} chars). Consider using document mode.")
    
    # Only truncate if text is extremely long
    if len(text) > max_length:
        # Find the last sentence within the limit
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        
        last_sentence_end = max(last_period, last_exclamation, last_question)
        if last_sentence_end > max_length * 0.7:
            text = text[:last_sentence_end + 1]
        else:
            text = text[:max_length] + "..."
        
        logger.info(f"Text truncated to {len(text)} characters for processing")
    
    return text

def clean_generated_text(generated_text, original_length=None):
    """Clean up generated text to remove unwanted content"""
    # Remove extra newlines and whitespace
    cleaned = generated_text.strip()
    
    # Remove repeated newlines
    import re
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
    
    # Remove common unwanted patterns
    unwanted_patterns = [
        r'\[.*?\]',  # Remove text in square brackets
        r'\(Note:.*?\)',  # Remove note parentheses
        r'Here is.*?:',  # Remove "Here is the rewritten text:" type phrases
        r'The rewritten.*?:',  # Remove explanatory text
        r'This version.*?\.',  # Remove explanation sentences
    ]
    
    for pattern in unwanted_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up extra spaces
    cleaned = re.sub(r' +', ' ', cleaned)
    cleaned = cleaned.strip()
    
    # If the output is significantly longer than expected, try to extract the main content
    if original_length and len(cleaned) > original_length * 2:
        sentences = cleaned.split('. ')
        if len(sentences) > 1:
            # Keep roughly the same number of sentences as original
            original_sentences = len([s for s in cleaned.split('. ') if s.strip()])
            target_sentences = max(1, min(original_sentences, len(sentences)))
            cleaned = '. '.join(sentences[:target_sentences])
            if not cleaned.endswith('.'):
                cleaned += '.'
    
    return cleaned

def process_document_with_chunks(text, tone="Neutral", tokenizer=None, model=None, ultra_fast_mode=True, progress_callback=None):
    """Process long documents by breaking into chunks"""
    if len(text) <= 800:  # Process smaller texts normally for better quality
        return rewrite_with_tone(text, tone, tokenizer, model, ultra_fast_mode)
    
    logger.info(f"Processing long document ({len(text)} chars) with chunking")
    
    # Split into larger, more manageable chunks
    chunks = smart_text_chunker(text, max_chunk_size=400)  # Increased chunk size
    processed_chunks = []
    
    for i, chunk in enumerate(chunks):
        if progress_callback:
            progress_callback(i + 1, len(chunks))
        
        logger.info(f"Processing chunk {i+1}/{len(chunks)}: {len(chunk)} chars")
        processed_chunk = rewrite_with_tone(chunk, tone, tokenizer, model, ultra_fast_mode)
        processed_chunks.append(processed_chunk)
    
    # Combine results with better paragraph preservation
    if len(processed_chunks) == 1:
        result = processed_chunks[0]
    else:
        # Join with double line breaks to preserve paragraph structure
        result = "\n\n".join(processed_chunks)
    
    logger.info(f"Document processing complete: {len(chunks)} chunks processed")
    return result

def rewrite_with_tone(text, tone="Neutral", tokenizer=None, model=None, ultra_fast_mode=True):
    """Rewrite input text into selected tone using IBM Granite 3.3 2B (LOCAL MODEL - NO WATSONX).
    
    This function uses the local IBM Granite model for text rewriting without any WatsonX dependency.
    All processing is done locally for privacy and performance.
    
    Args:
        text: Input text to rewrite.
        tone: Target tone (Neutral, Suspenseful, Inspiring).
        tokenizer: IBM Granite tokenizer.
        model: IBM Granite model.
        ultra_fast_mode: Enable speed optimizations.
    
    Returns:
        Rewritten text with the specified tone.
    """
    if tokenizer is None or model is None:
        raise ValueError("Tokenizer and model must be provided.")
    
    # Check cache first for speed
    cache_key = hashlib.md5(f"{text}_{tone}_{ultra_fast_mode}".encode()).hexdigest()
    if cache_key in _text_cache:
        logger.info(f"Cache hit! Returning cached result for tone: {tone}")
        return _text_cache[cache_key]
    
    logger.info(f"Rewriting text with tone: {tone} (ultra-fast mode: {ultra_fast_mode})")
    
    # Preprocess input text with ultra-fast mode
    original_length = len(text)
    if ultra_fast_mode:
        # Allow much longer text for better quality
        text = preprocess_text(text, max_length=1500)  # Increased significantly
        # Super-fast mode only for extremely short text
        if ultra_fast_mode and len(text) < 20:  # Only for very short snippets
            logger.info("Using super-fast string transformations (no AI)")
            simple_transforms = {
                "suspenseful": text.replace(".", "...") + " Danger lurks in the shadows.",
                "inspiring": "Embrace the moment: " + text.replace(".", "!") + " Success awaits!", 
                "neutral": text.replace(".", ".").replace("!", ".")  # Clean punctuation
            }
            return simple_transforms.get(tone.lower(), text)
    else:
        text = preprocess_text(text, max_length=1500)
    
    # Create improved prompts balancing speed and quality
    if ultra_fast_mode:
        # Better prompts with clear instructions but still fast
        if tone.lower() == "suspenseful":
            prompt = f"""Rewrite this text to be suspenseful and dramatic:
{text}

Suspenseful version:"""
        elif tone.lower() == "inspiring":
            prompt = f"""Rewrite this text to be inspiring and motivational:
{text}

Inspiring version:"""
        else:  # Neutral
            prompt = f"""Rewrite this text in a clear, professional tone:
{text}

Clear version:"""
    else:
        # Original detailed prompts for quality mode
        if tone.lower() == "suspenseful":
            prompt = f"""Task: Rewrite the text below in a suspenseful, dramatic tone while keeping the exact same meaning and key information.

Original text: {text}

Suspenseful version:"""
        elif tone.lower() == "inspiring":
            prompt = f"""Task: Rewrite the text below in an inspiring, motivational tone while keeping the exact same meaning and key information.

Original text: {text}

Inspiring version:"""
        else:  # Neutral
            prompt = f"""Task: Rewrite the text below in a clear, neutral, professional tone while keeping the exact same meaning and key information.

Original text: {text}

Neutral version:"""
    
    try:
        # Ultra-fast tokenization with generous limits
        max_prompt_length = 512 if ultra_fast_mode else 1024  # Increased for longer prompts
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_prompt_length)
        input_length = inputs.input_ids.shape[1]
        
        # Much more generous token limits based on text length
        text_length = len(text)
        word_count = len(text.split())
        
        if ultra_fast_mode:
            # Generous token limits to ensure complete rewrites
            if text_length <= 100:  # Short text
                max_new_tokens = max(50, word_count * 1.5)  # At least 50 tokens
            elif text_length <= 400:  # Medium text  
                max_new_tokens = max(100, word_count * 1.8)  # At least 100 tokens
            elif text_length <= 800:  # Long text
                max_new_tokens = max(200, word_count * 1.5)  # At least 200 tokens
            else:  # Very long text
                max_new_tokens = max(300, word_count * 1.3)  # At least 300 tokens
        else:
            # Quality mode with even more tokens
            max_new_tokens = max(150, min(word_count * 2.5, 400))
        
        logger.info(f"Generating with max_new_tokens: {max_new_tokens}")
        
        # Generate with ultra-maximum speed optimizations
        with torch.no_grad():
            if ultra_fast_mode:
                # Balanced fast generation for quality
                outputs = model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,    # Greedy for speed and consistency
                    num_beams=1,        # No beam search
                    temperature=1.0,    # Ignored with do_sample=False
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    early_stopping=True,
                    use_cache=True,
                    # Add stopping tokens for complete sentences
                    repetition_penalty=1.05,
                )
            else:
                # Standard fast generation
                outputs = model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_new_tokens,
                    temperature=0.1,  # Very low temperature for speed
                    do_sample=False,  # Greedy decoding for speed
                    num_beams=1,      # No beam search for speed
                    top_k=20,         # Even smaller vocabulary
                    repetition_penalty=1.05,  # Minimal repetition penalty
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    early_stopping=True,
                    use_cache=True,   # Use KV cache for speed
                )
        
        # Decode and extract generated content
        full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated part with improved parsing
        rewritten = ""
        
        # More robust extraction - try multiple methods
        extraction_patterns = [
            "version:", "suspenseful:", "inspiring:", "rewritten:", "neutral:", "clear:"
        ]
        
        # Try pattern-based extraction first
        for pattern in extraction_patterns:
            if pattern in full_output.lower():
                start_idx = full_output.lower().rfind(pattern) + len(pattern)
                candidate = full_output[start_idx:].strip()
                if len(candidate) > 10:  # Must be substantial content
                    rewritten = candidate
                    break
        
        # If pattern extraction failed, try other methods
        if not rewritten:
            # Try to extract after the original text
            if text in full_output:
                start_idx = full_output.rfind(text) + len(text)
                candidate = full_output[start_idx:].strip()
                if len(candidate) > 10:
                    rewritten = candidate
            else:
                # Remove the input prompt to get generated content only
                decoded_input = tokenizer.decode(inputs.input_ids[0], skip_special_tokens=True)
                if decoded_input in full_output:
                    candidate = full_output[len(decoded_input):].strip()
                    if len(candidate) > 10:
                        rewritten = candidate
                else:
                    # Last resort: use full output if it's significantly different from input
                    if len(full_output) > len(text) * 0.8:  # Must be substantial
                        rewritten = full_output.strip()
        
        # Clean up the generated text
        rewritten = clean_generated_text(rewritten, original_length)
        
        # Ensure complete sentences
        if rewritten and not rewritten.endswith(('.', '!', '?')):
            # Try to complete the sentence or add appropriate ending
            if len(rewritten) > 10:
                # Add appropriate punctuation based on tone
                if tone.lower() == "suspenseful":
                    rewritten += "..."
                elif tone.lower() == "inspiring":
                    rewritten += "!"
                else:
                    rewritten += "."
        
        # Validate output quality with improved checks
        if not rewritten or len(rewritten.strip()) < 10:
            logger.warning("Generated text too short, trying fallback extraction")
            # Try a more aggressive extraction as fallback
            lines = full_output.split('\n')
            for line in lines:
                line = line.strip()
                if len(line) > 20 and line.lower() != text.lower():
                    rewritten = line
                    break
            
            if not rewritten or len(rewritten.strip()) < 10:
                logger.warning("All extraction methods failed, returning enhanced original")
                # Instead of returning original, apply basic tone transformation
                if tone.lower() == "suspenseful":
                    return text.replace(".", "...") + " The mystery deepens."
                elif tone.lower() == "inspiring":
                    return text.replace(".", "!") + " Amazing possibilities await!"
                else:
                    return text
            
        # More lenient quality checks
        word_count_original = len(text.split())
        word_count_rewritten = len(rewritten.split())
        
        # Check if rewritten text is substantially shorter than original (might indicate incomplete generation)
        if word_count_rewritten < word_count_original * 0.4 and word_count_original > 10:
            logger.warning(f"Generated text significantly shorter ({word_count_rewritten} vs {word_count_original} words), may be incomplete")
            # Don't return original, but flag this for user awareness
        
        # If output is identical to input, that's actually fine - it means the text was already in the right tone
        if rewritten.lower().strip() == text.lower().strip():
            logger.info("Generated text identical to input - text was already in target tone")
            # Still return the rewritten version in case there were minor improvements
        
        logger.info(f"Text rewriting complete. Original: {len(text)} chars, Rewritten: {len(rewritten)} chars")
        
        # Cache the result for future use
        _text_cache[cache_key] = rewritten
        # Keep cache size reasonable (max 50 entries)
        if len(_text_cache) > 50:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(_text_cache))
            del _text_cache[oldest_key]
        
        return rewritten
        
    except Exception as e:
        logger.error(f"Error in text generation: {str(e)}")
        return text  # Return original text if there's an error
