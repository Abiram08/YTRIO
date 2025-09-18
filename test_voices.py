#!/usr/bin/env python3
"""
Quick test script to verify voice differences are working
"""
import os
from utils.tts_helper import get_voice_info, ultra_fast_tts

def test_voice_differences():
    """Test all voices with a sample phrase"""
    test_phrase = "Hello! This is a voice test to check if the voices sound different from each other."
    
    print("🎤 Testing Voice Differences...")
    print("=" * 50)
    
    voice_info = get_voice_info()
    
    for voice_name, config in voice_info.items():
        print(f"\n🔊 Testing: {voice_name}")
        print(f"   Gender: {config['gender'].title()}")
        print(f"   Accent: {config['accent']}")
        print(f"   Speed: {config['speed']} (slow={config['slow']})")
        
        try:
            # Generate audio sample
            audio_bytes = ultra_fast_tts(test_phrase, voice_name)
            
            if audio_bytes and len(audio_bytes) > 1000:
                # Save to file for manual testing
                filename = f"voice_test_{voice_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}.mp3"
                filepath = os.path.join("test_audio", filename)
                
                # Create directory if it doesn't exist
                os.makedirs("test_audio", exist_ok=True)
                
                with open(filepath, "wb") as f:
                    f.write(audio_bytes)
                
                print(f"   ✅ Success! Saved to: {filename}")
                print(f"   📄 Size: {len(audio_bytes)/1024:.1f} KB")
            else:
                print(f"   ❌ Failed: Audio too small or empty")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Complete!")
    print("Check the 'test_audio' folder for generated samples.")
    print("Play each file to verify they sound different.")

if __name__ == "__main__":
    test_voice_differences()