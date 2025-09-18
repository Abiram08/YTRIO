#!/usr/bin/env python3
"""
Test script to verify text rewriting improvements
"""

import time
from utils.granite_helper import load_granite_model, rewrite_with_tone

def test_text_rewriting():
    """Test the improved text rewriting function"""
    
    print("🧪 Loading model for testing...")
    try:
        tokenizer, model = load_granite_model()
        print("✅ Model loaded successfully")
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return
    
    # Test cases
    test_texts = [
        # Short text
        "Artificial intelligence is transforming our world.",
        
        # Medium text
        "Artificial intelligence is transforming our world. Smart homes anticipate our needs, self-driving cars navigate complex traffic, and machine learning algorithms process vast amounts of data to identify patterns that were impossible just a few years ago.",
        
        # Long text
        "Artificial intelligence is transforming our world. Smart homes anticipate our needs, self-driving cars navigate complex traffic, and machine learning algorithms process vast amounts of data to identify patterns that were impossible just a few years ago. The future of technology is bright with endless possibilities for innovation and growth. Machine learning models are becoming more sophisticated every day, enabling new breakthroughs in healthcare, education, and scientific research. These technological advances are creating opportunities we never thought possible just a decade ago."
    ]
    
    test_tones = ["Suspenseful", "Inspiring"]
    
    for i, text in enumerate(test_texts):
        print(f"\n📝 Test Case {i+1}: {len(text)} characters, {len(text.split())} words")
        print(f"Original: {text[:100]}{'...' if len(text) > 100 else ''}")
        
        for tone in test_tones:
            print(f"\n🎨 Testing {tone} tone:")
            start_time = time.time()
            
            try:
                rewritten = rewrite_with_tone(
                    text, tone, tokenizer, model, ultra_fast_mode=True
                )
                
                processing_time = time.time() - start_time
                
                print(f"✅ Success in {processing_time:.2f}s")
                print(f"📊 Length comparison: {len(text)} → {len(rewritten)} chars")
                print(f"📊 Word comparison: {len(text.split())} → {len(rewritten.split())} words")
                print(f"Rewritten: {rewritten[:150]}{'...' if len(rewritten) > 150 else ''}")
                
                # Quality checks
                if len(rewritten) < len(text) * 0.5:
                    print("⚠️  WARNING: Output significantly shorter than input")
                elif len(rewritten.split()) < len(text.split()) * 0.6:
                    print("⚠️  WARNING: Word count much lower than input")
                else:
                    print("✅ Length quality check passed")
                
            except Exception as e:
                print(f"❌ Failed: {e}")
        
        print("-" * 80)

if __name__ == "__main__":
    test_text_rewriting()