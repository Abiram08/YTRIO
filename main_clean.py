#!/usr/bin/env python3
"""
🎧 EchoVerse - Clean & Simple AI Audiobook Creator
================================================
Simple, professional interface for hackathon demos
All 5 solutions in a clean, easy-to-use package
"""

import streamlit as st
import logging
import time
from datetime import datetime
from utils.granite_helper import load_granite_model, load_granite_model_fallback, rewrite_with_tone
from utils.tts_helper import ultra_fast_tts, get_voice_info, get_estimated_audio_duration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="🎧 EchoVerse - AI Audiobook Creator",
    page_icon="🎧",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "past_narrations" not in st.session_state:
    st.session_state.past_narrations = []

# Simple, clean CSS
st.markdown("""
<style>
.main-title {
    text-align: center;
    color: #2E4057;
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}
.subtitle {
    text-align: center;
    color: #666;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}
.solution-badge {
    background: linear-gradient(90deg, #667eea, #764ba2);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    margin: 0.2rem;
    display: inline-block;
}
.demo-container {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1rem 0;
    border-left: 4px solid #667eea;
}
.comparison-box {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.original {
    border-left: 4px solid #dc3545;
}
.rewritten {
    border-left: 4px solid #28a745;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-title">🎧 EchoVerse</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI Audiobook Creator - All 5 Solutions in One</p>', unsafe_allow_html=True)

# Solution badges
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <span class="solution-badge">1️⃣ Tone Rewriting</span>
    <span class="solution-badge">2️⃣ Premium Voices</span>
    <span class="solution-badge">3️⃣ Audio Output</span>
    <span class="solution-badge">4️⃣ Text Comparison</span>
    <span class="solution-badge">5️⃣ Simple UI</span>
</div>
""", unsafe_allow_html=True)

# Load model (simplified)
if "tokenizer" not in st.session_state or "model" not in st.session_state:
    with st.spinner("🚀 Loading IBM Granite AI Model..."):
        try:
            st.session_state.tokenizer, st.session_state.model = load_granite_model()
            st.success("✅ AI Model Ready!")
        except Exception as e:
            try:
                st.session_state.tokenizer, st.session_state.model = load_granite_model_fallback()
                st.success("✅ AI Model Ready (Fallback)!")
            except Exception:
                st.error("❌ Model loading failed. Please restart.")
                st.stop()

# Demo Mode Toggle (prominent)
demo_mode = st.toggle("🏆 **Hackathon Demo Mode** (Under 30s!)", value=True)
if demo_mode:
    st.info("⚡ **Demo Mode Active**: Ultra-fast processing for live demonstrations")

# Quick demo sample
if demo_mode:
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🎯 Load Demo Text", use_container_width=True):
            st.session_state.demo_text = "Artificial intelligence is transforming our world. Smart homes anticipate our needs, self-driving cars navigate complex traffic, and machine learning algorithms process vast amounts of data to identify patterns that were impossible just a few years ago. The future of technology is bright with endless possibilities for innovation and growth."

# Main Input
st.markdown("### 📝 Step 1: Enter Your Text")
text_input = st.text_area(
    "Enter text to convert to audiobook:",
    height=120,
    placeholder="Paste your text here or use the demo text above...",
    value=st.session_state.get('demo_text', '')
)

# Simple Configuration
st.markdown("### ⚙️ Step 2: Choose Settings")
col1, col2 = st.columns(2)

with col1:
    tone = st.selectbox(
        "🎨 **Tone** (Solution 1: AI Rewriting)",
        ["Neutral", "Suspenseful", "Inspiring"],
        help="IBM Granite AI will rewrite your text in this tone"
    )

with col2:
    voice_options = list(get_voice_info().keys())
    voice = st.selectbox(
        "🎤 **Voice** (Solution 2: Premium TTS)",
        voice_options,
        help="Choose voice for narration"
    )

# Generate Button
st.markdown("### 🎵 Step 3: Generate Audiobook")
if st.button("🚀 Generate Audiobook", type="primary", use_container_width=True):
    if not text_input.strip():
        st.error("⚠️ Please enter some text first!")
    else:
        text = text_input
        
        # Demo mode truncation
        if demo_mode and len(text) > 500:
            text = text[:500]
            last_period = text.rfind('.')
            if last_period > 300:
                text = text[:last_period + 1]
            st.warning(f"🏆 Demo mode: Text truncated to {len(text)} chars for speed")
        
        # Progress tracking
        total_start = time.time()
        
        # Step 1: Text Rewriting (Solution 1)
        with st.spinner("✨ Rewriting text with AI..."):
            rewrite_start = time.time()
            rewritten_text = rewrite_with_tone(
                text, tone, st.session_state.tokenizer, st.session_state.model, ultra_fast_mode=True
            )
            rewrite_time = time.time() - rewrite_start
        
        st.success(f"✅ Text rewritten in {rewrite_time:.1f}s")
        
        # Solution 4: Side-by-Side Comparison
        st.markdown("### 📊 Solution 4: Text Comparison")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📄 Original Text**")
            st.markdown(f'<div class="comparison-box original">{text}</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**✨ {tone} Version**")
            st.markdown(f'<div class="comparison-box rewritten">{rewritten_text}</div>', unsafe_allow_html=True)
        
        # Quick stats
        original_words = len(text.split())
        rewritten_words = len(rewritten_text.split())
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Original Words", original_words)
        with col2:
            st.metric("Rewritten Words", rewritten_words)
        with col3:
            change = ((rewritten_words - original_words) / original_words * 100) if original_words > 0 else 0
            st.metric("Change", f"{change:+.1f}%")
        
        # Step 2: Audio Generation (Solutions 2 & 3)
        with st.spinner("🎤 Generating audio..."):
            audio_start = time.time()
            if demo_mode:
                audio_bytes = ultra_fast_tts(rewritten_text, voice)
            else:
                from utils.tts_helper import text_to_speech
                audio_bytes = text_to_speech(rewritten_text, voice_name=voice, speed_optimization=True)
            audio_time = time.time() - audio_start
        
        total_time = time.time() - total_start
        
        st.success(f"✅ Audio generated in {audio_time:.1f}s | **Total: {total_time:.1f}s**")
        
        # Solution 3: Audio Output
        st.markdown("### 🎧 Solution 3: Audio Output")
        
        # 3a: Streamable Player
        st.markdown("**🔊 Play Audio** (Streamable)")
        st.audio(audio_bytes, format="audio/mp3")
        
        # 3b: Download
        st.markdown("**📥 Download Audio** (Offline Use)")
        filename = f"echoverse_{tone.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        st.download_button(
            "📥 Download MP3 File",
            data=audio_bytes,
            file_name=filename,
            mime="audio/mp3",
            use_container_width=True
        )
        
        # Success Summary
        st.markdown("---")
        st.markdown("""
        <div class="demo-container">
            <h4>🎉 Success! All 5 Solutions Demonstrated:</h4>
            <p>
                ✅ <strong>Solution 1:</strong> Text rewritten with AI tone adaptation<br>
                ✅ <strong>Solution 2:</strong> High-quality voice narration<br>
                ✅ <strong>Solution 3:</strong> Audio streaming + download capability<br>
                ✅ <strong>Solution 4:</strong> Side-by-side text comparison<br>
                ✅ <strong>Solution 5:</strong> Simple, user-friendly interface<br>
            </p>
            <p><strong>⏱️ Total Time: {:.1f} seconds</strong> {}</p>
        </div>
        """.format(total_time, "🏆 Perfect for hackathon demo!" if total_time < 30 else ""), 
        unsafe_allow_html=True)
        
        # Store for history
        narration_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tone": tone,
            "voice": voice,
            "original_text": text[:100] + "..." if len(text) > 100 else text,
            "rewritten_text": rewritten_text,
            "audio_bytes": audio_bytes,
            "filename": filename,
            "processing_time": total_time
        }
        st.session_state.past_narrations.insert(0, narration_data)
        if len(st.session_state.past_narrations) > 5:
            st.session_state.past_narrations = st.session_state.past_narrations[:5]

# Simple History Section
if st.session_state.past_narrations:
    with st.expander(f"📚 Recent Audiobooks ({len(st.session_state.past_narrations)})", expanded=False):
        for i, item in enumerate(st.session_state.past_narrations):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{item['timestamp']}** - {item['tone']} tone")
                st.write(f"📄 {item['original_text']}")
            with col2:
                st.metric("Time", f"{item['processing_time']:.1f}s")
            with col3:
                st.download_button(
                    "📥",
                    data=item['audio_bytes'],
                    file_name=item['filename'],
                    mime="audio/mp3",
                    key=f"dl_{i}"
                )
            if i < len(st.session_state.past_narrations) - 1:
                st.markdown("---")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem; margin-top: 2rem;">
    🎧 <strong>EchoVerse</strong> - Powered by IBM Granite AI + Advanced TTS<br>
    <small>All 5 solutions implemented • Hackathon-optimized • Under 30s processing</small>
</div>
""", unsafe_allow_html=True)