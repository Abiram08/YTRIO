import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
import logging
import time
import psutil

# Enable detailed logging for shard loading
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Timeout exception for loading
class TimeoutException(Exception):
    pass

@st.cache_resource
def load_granite_model():
    model_path = "./models/granite-2b"
    model_name = "ibm-granite/granite-3.3-2b-instruct"
    
    logger.info(f"Starting model load from {model_path}")
    
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
                torch_dtype=torch.float16,  # Use float16 for less memory
                device_map=device_map_setting,  # Let transformers decide optimal placement or force CPU
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                max_memory={0: "6GB", "cpu": "8GB"} if torch.cuda.is_available() else {"cpu": "8GB"},  # Limit memory usage
                offload_folder="./models/offload",  # Offload to disk if needed
                load_in_8bit=False,  # Disable for compatibility
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

def rewrite_with_tone(text, tone="Neutral", tokenizer=None, model=None):
    """Rewrite input text into selected tone using Granite 3.3 2B"""
    if tokenizer is None or model is None:
        raise ValueError("Tokenizer and model must be provided.")
    
    logger.info(f"Rewriting text with tone: {tone}")
    
    # Create a simple prompt for tone rewriting
    if tone.lower() == "suspenseful":
        prompt = f"Rewrite the following text to make it more suspenseful and dramatic while keeping the same meaning:\n\n{text}\n\nRewritten version:"
    elif tone.lower() == "inspiring":
        prompt = f"Rewrite the following text to make it more inspiring and motivational while keeping the same meaning:\n\n{text}\n\nRewritten version:"
    else:  # Neutral
        prompt = f"Rewrite the following text in a clear and neutral tone while keeping the same meaning:\n\n{text}\n\nRewritten version:"
    
    try:
        # Tokenize the input
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        
        # Generate text
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=300,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode the output
        full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated part (after the prompt)
        if "Rewritten version:" in full_output:
            rewritten = full_output.split("Rewritten version:")[-1].strip()
        else:
            rewritten = full_output[len(prompt):].strip()
            
        logger.info("Text rewriting complete")
        return rewritten if rewritten else text  # Return original if generation failed
        
    except Exception as e:
        logger.error(f"Error in text generation: {str(e)}")
        return text  # Return original text if there's an error
