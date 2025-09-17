import streamlit as st
import base64
import logging
from datetime import datetime
from utils.granite_helper import load_granite_model, load_granite_model_fallback, rewrite_with_tone
from utils.tts_helper import text_to_speech

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="EchoVerse – AI Audiobook Tool",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state for past narrations
if "past_narrations" not in st.session_state:
    st.session_state.past_narrations = []

# Check system memory and show warning if needed
import psutil
memory = psutil.virtual_memory()
available_gb = memory.available / (1024**3)
if available_gb < 2.0:
    st.warning(f"⚠️ Low available RAM detected: {available_gb:.1f} GB. For best performance, close other applications before loading the model.")
    st.info("💡 Tip: The model requires ~2-5GB of RAM to load properly.")

# CSS for background and styling
def add_bg_from_local():
    """
    Adds background styling to the Streamlit app
    """
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main-header {
        text-align: center;
        color: white;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .section-container {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    .text-comparison {
        background: rgba(248, 249, 250, 0.8);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .narration-item {
        background: rgba(255, 255, 255, 0.8);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

add_bg_from_local()

# Main title
st.markdown('<h1 class="main-header">🎧 EchoVerse</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: white; font-size: 1.2rem; margin-bottom: 3rem;">AI-Powered Audiobook Creation Tool</p>', unsafe_allow_html=True)

# Initialize model with feedback (lazy loading)
with st.container():
    if "tokenizer" not in st.session_state or "model" not in st.session_state:
        with st.spinner("🚀 Initializing Granite 3.3 2B model... This may take a few minutes on first run."):
            try:
                logger.info("Loading Granite model...")
                st.session_state.tokenizer, st.session_state.model = load_granite_model()
                st.success("✅ Model loaded successfully!")
                logger.info("Model loaded successfully")
            except Exception as e:
                st.warning(f"⚠️ Optimized loading failed: {str(e)}")
                st.info("🔄 Trying fallback loading method...")
                try:
                    logger.info("Attempting fallback model loading...")
                    st.session_state.tokenizer, st.session_state.model = load_granite_model_fallback()
                    st.success("✅ Model loaded successfully with fallback method!")
                    logger.info("Fallback model loaded successfully")
                except Exception as fallback_e:
                    st.error(f"❌ Both loading methods failed!")
                    st.error(f"Primary error: {str(e)}")
                    st.error(f"Fallback error: {str(fallback_e)}")
                    st.error("Please check: 1) Available RAM (8GB+ recommended), 2) Disk space (5GB+), 3) Model files integrity")
                    st.stop()

# Input Section
with st.container():
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.header("📝 Text Input")
    
    # File upload
    uploaded_file = st.file_uploader("Upload .txt file", type=["txt"], help="Upload a text file to convert to audiobook")
    
    # Text area
    text_input = st.text_area(
        "Or paste your text here:",
        height=150,
        placeholder="Enter the text you want to convert to an audiobook...",
        help="Enter or paste the text content you want to transform into an audiobook"
    )
    
    # Determine input text
    if uploaded_file:
        try:
            text = uploaded_file.read().decode("utf-8")
            st.info(f"📁 File uploaded: {uploaded_file.name} ({len(text)} characters)")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            text = text_input
    else:
        text = text_input
    
    st.markdown('</div>', unsafe_allow_html=True)

# Configuration Section
with st.container():
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.header("⚙️ Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tone = st.selectbox(
            "Select Tone",
            ["Neutral", "Suspenseful", "Inspiring"],
            help="Choose the emotional tone for rewriting your text"
        )
    
    with col2:
        voice = st.selectbox(
            "Select Voice Style",
            ["Lisa (Female)", "Michael (Male)", "Allison (Female)", "Kate (Female)"],
            help="Choose the voice style for narration (Note: gTTS uses standard voices)"
        )
    
    # Language selection (simplified for gTTS)
    lang = st.selectbox(
        "Select Language",
        [("en", "English (US)"), ("en-uk", "English (UK)"), ("en-au", "English (AU)")],
        format_func=lambda x: x[1]
    )[0]
    
    st.markdown('</div>', unsafe_allow_html=True)

# Generation Section
with st.container():
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    
    generate_button = st.button(
        "🎵 Generate Audiobook",
        type="primary",
        help="Click to generate your audiobook",
        use_container_width=True
    )
    
    if generate_button:
        if not text.strip():
            st.error("⚠️ Please enter or upload text to continue.")
        else:
            try:
                # Show original text
                st.subheader("📄 Original Text")
                with st.expander("View Original Text", expanded=False):
                    st.write(text[:500] + "..." if len(text) > 500 else text)
                
                # Rewrite text with tone
                with st.spinner(f"✨ Rewriting text with {tone} tone using Granite 3.3 2B..."):
                    rewritten_text = rewrite_with_tone(
                        text, tone, st.session_state.tokenizer, st.session_state.model
                    )
                
                # Display rewritten text
                st.subheader("✏️ Rewritten Text")
                st.markdown('<div class="text-comparison">', unsafe_allow_html=True)
                st.write(rewritten_text)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Generate audio
                with st.spinner(f"🎤 Generating audio narration..."):
                    audio_bytes = text_to_speech(rewritten_text, lang=lang)
                
                # Audio playback
                st.subheader("🔊 Generated Audiobook")
                st.audio(audio_bytes, format="audio/mp3")
                
                # Download button
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"echoverse_audiobook_{tone.lower()}_{timestamp}.mp3"
                
                st.download_button(
                    "📥 Download MP3",
                    data=audio_bytes,
                    file_name=filename,
                    mime="audio/mp3",
                    help="Download your generated audiobook"
                )
                
                # Store in session state for past narrations
                narration_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "tone": tone,
                    "voice": voice,
                    "original_text": text[:200] + "..." if len(text) > 200 else text,
                    "rewritten_text": rewritten_text,
                    "audio_bytes": audio_bytes,
                    "filename": filename
                }
                
                st.session_state.past_narrations.insert(0, narration_data)
                
                # Keep only last 5 narrations to avoid memory issues
                if len(st.session_state.past_narrations) > 5:
                    st.session_state.past_narrations = st.session_state.past_narrations[:5]
                
                st.success("✅ Audiobook generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Error generating audiobook: {str(e)}")
                logger.error(f"Error in audiobook generation: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Past Narrations Section
if st.session_state.past_narrations:
    with st.container():
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        st.header("📚 Past Narrations")
        
        with st.expander(f"View {len(st.session_state.past_narrations)} Previous Narrations", expanded=False):
            for i, narration in enumerate(st.session_state.past_narrations):
                st.markdown(f'<div class="narration-item">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{narration['timestamp']}** - *{narration['tone']} tone, {narration['voice']}*")
                    st.write(f"Original: {narration['original_text']}")
                    
                with col2:
                    st.download_button(
                        "Download",
                        data=narration['audio_bytes'],
                        file_name=narration['filename'],
                        mime="audio/mp3",
                        key=f"download_{i}"
                    )
                
                # Audio player for past narrations
                st.audio(narration['audio_bytes'], format="audio/mp3")
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("---")
        
        # Clear history button
        if st.button("🗑️ Clear History", help="Clear all past narrations"):
            st.session_state.past_narrations = []
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: white; opacity: 0.8;">'
    'EchoVerse v1.0 - Powered by IBM Granite 3.3 2B & Google TTS'
    '</p>',
    unsafe_allow_html=True
)
