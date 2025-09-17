from gtts import gTTS
import io
import logging

logger = logging.getLogger(__name__)

def text_to_speech(text, lang="en"):
    """Convert text to speech using gTTS and return MP3 bytes"""
    try:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
            
        logger.info(f"Converting text to speech with language: {lang}")
        
        # Clean text for TTS (remove special characters that might cause issues)
        cleaned_text = text.replace('\n', ' ').replace('\r', ' ').strip()
        
        # Limit text length for TTS (gTTS has limits)
        if len(cleaned_text) > 5000:
            cleaned_text = cleaned_text[:5000] + "..."
            logger.warning("Text truncated for TTS due to length limit")
        
        tts = gTTS(text=cleaned_text, lang=lang, slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        
        logger.info("Text-to-speech conversion completed successfully")
        return audio_fp.read()
        
    except Exception as e:
        logger.error(f"Error in text-to-speech conversion: {str(e)}")
        raise Exception(f"TTS Error: {str(e)}")
