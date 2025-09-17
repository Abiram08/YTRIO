#!/usr/bin/env python3
"""
System information checker for EchoVerse troubleshooting
"""

import os
import sys
import platform
import psutil
import torch
import subprocess

def check_system():
    """Check system requirements and provide diagnostics"""
    
    print("🔍 EchoVerse System Diagnostic")
    print("=" * 50)
    
    # Python version
    print(f"🐍 Python Version: {sys.version}")
    
    # Operating System
    print(f"💻 OS: {platform.system()} {platform.version()}")
    print(f"📱 Architecture: {platform.machine()}")
    
    # Memory Information
    memory = psutil.virtual_memory()
    print(f"💾 Total RAM: {memory.total / (1024**3):.1f} GB")
    print(f"💾 Available RAM: {memory.available / (1024**3):.1f} GB")
    print(f"💾 Memory Usage: {memory.percent}%")
    
    # Disk Space
    try:
        disk = psutil.disk_usage('.')
        print(f"💽 Disk Space (current dir): {disk.free / (1024**3):.1f} GB free of {disk.total / (1024**3):.1f} GB")
    except:
        print("💽 Disk Space: Could not determine")
    
    # PyTorch Information
    print(f"🔥 PyTorch Version: {torch.__version__}")
    print(f"🔥 CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"🔥 CUDA Version: {torch.version.cuda}")
        print(f"🔥 GPU Device: {torch.cuda.get_device_name()}")
    
    # Check model directory
    model_path = "./models/granite-2b"
    if os.path.exists(model_path):
        print(f"📁 Model Directory: Found at {model_path}")
        files = os.listdir(model_path)
        print(f"📁 Model Files: {len(files)} files")
        
        # Check for key files
        key_files = ['config.json', 'tokenizer.json', 'model.safetensors.index.json']
        for file in key_files:
            if file in files:
                print(f"  ✅ {file}")
            else:
                print(f"  ❌ {file} (missing)")
        
        # Check model file sizes
        safetensor_files = [f for f in files if f.endswith('.safetensors')]
        total_size = 0
        for file in safetensor_files:
            try:
                size = os.path.getsize(os.path.join(model_path, file))
                total_size += size
                print(f"  📦 {file}: {size / (1024**3):.2f} GB")
            except:
                print(f"  📦 {file}: Size unknown")
        
        print(f"📦 Total Model Size: {total_size / (1024**3):.2f} GB")
    else:
        print(f"📁 Model Directory: Not found at {model_path}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    
    if memory.available / (1024**3) < 8:
        print("  ⚠️ Low available RAM. Close other applications before running EchoVerse")
    else:
        print("  ✅ Sufficient RAM available")
    
    if os.path.exists(model_path):
        if total_size / (1024**3) < 2:
            print("  ⚠️ Model files seem incomplete. Consider re-downloading")
        else:
            print("  ✅ Model files appear complete")
    else:
        print("  ❌ Model directory not found. Model will be downloaded from Hugging Face")
    
    # Test basic imports
    print("\n🧪 Testing imports...")
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        print("  ✅ Transformers library working")
    except Exception as e:
        print(f"  ❌ Transformers import failed: {e}")
    
    try:
        import streamlit
        print("  ✅ Streamlit library working")
    except Exception as e:
        print(f"  ❌ Streamlit import failed: {e}")

if __name__ == "__main__":
    try:
        check_system()
    except Exception as e:
        print(f"❌ System check failed: {e}")
        import traceback
        traceback.print_exc()