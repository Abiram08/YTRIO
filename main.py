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

# Clean, simple CSS with modern design
st.markdown("""
<style>
/* Pure black theme with white text */
.stApp {
    background: #000000;
    min-height: 100vh;
    color: #ffffff;
}

.main {
    background: #000000;
    border-radius: 15px;
    padding: 2rem;
    margin: 1rem auto;
    max-width: 900px;
    box-shadow: none;
    border: none;
}

.main-title {
    text-align: center;
    color: #ffffff !important;
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 1rem;
    text-shadow: none;
}

.subtitle {
    text-align: center;
    color: #cccccc !important;
    font-size: 1.1rem;
    font-weight: 400;
    margin-bottom: 3rem;
}

/* Remove solution badges for cleaner look */
.solution-badge {
    display: none;
}

.demo-container {
    background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
    padding: 2rem;
    border-radius: 15px;
    margin: 1.5rem 0;
    border: 2px solid #0ea5e9;
    box-shadow: 0 4px 16px rgba(14, 165, 233, 0.2);
}

.demo-container h4 {
    color: #0c4a6e !important;
    font-weight: bold;
}

.demo-container p {
    color: #164e63 !important;
    font-size: 1rem;
    line-height: 1.6;
}

.comparison-box {
    background: rgba(255, 255, 255, 0.9);
    padding: 1.5rem;
    border-radius: 12px;
    margin: 0.8rem 0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    color: #1a1a1a !important;
    font-size: 1rem;
    line-height: 1.5;
}

.original {
    border-left: 5px solid #ef4444;
    background: linear-gradient(135deg, #fef2f2, #fee2e2);
}

.original::before {
    content: "📄 Original";
    font-weight: bold;
    color: #dc2626;
    display: block;
    margin-bottom: 0.5rem;
}

.rewritten {
    border-left: 5px solid #10b981;
    background: linear-gradient(135deg, #f0fdf4, #dcfce7);
}

.rewritten::before {
    content: "✨ Rewritten";
    font-weight: bold;
    color: #059669;
    display: block;
    margin-bottom: 0.5rem;
}

/* Dark theme input styling - Gray boxes with visible text */
.stTextArea textarea {
    background-color: #333333 !important;
    color: #ffffff !important;
    border: 2px solid #555555 !important;
    border-radius: 8px !important;
    font-size: 1rem !important;
    padding: 1rem !important;
    font-weight: normal !important;
}

.stTextArea textarea:focus {
    border-color: #777777 !important;
    box-shadow: 0 0 0 2px rgba(119, 119, 119, 0.3) !important;
}

.stTextArea textarea::placeholder {
    color: #999999 !important;
    font-weight: normal !important;
}

/* Ensure disabled text areas are visible */
.stTextArea textarea[disabled] {
    background-color: #2a2a2a !important;
    color: #ffffff !important; /* Force white text for visibility */
    border: 2px solid #666666 !important;
    border-radius: 8px !important;
    font-size: 1.1rem !important;
    font-weight: 500 !important;
    line-height: 1.6 !important;
    padding: 1.2rem !important;
    opacity: 1 !important;
}

.stTextArea textarea[disabled]:focus {
    border-color: #888888 !important;
    box-shadow: 0 0 0 2px rgba(136, 136, 136, 0.3) !important;
}

/* Button styling - Black theme */
.stButton button {
    background: #444444 !important;
    color: white !important;
    border: 2px solid #666666 !important;
    border-radius: 8px !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
}

.stButton button:hover {
    background: #555555 !important;
    border-color: #777777 !important;
}

/* Selectbox styling - Dark theme */
.stSelectbox > div > div {
    background-color: #333333 !important;
    border: 2px solid #555555 !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-weight: normal !important;
}

.stSelectbox div[data-baseweb="select"] {
    background-color: #333333 !important;
    border: 2px solid #555555 !important;
    color: #ffffff !important;
}

.stSelectbox div[data-baseweb="select"]:hover {
    border-color: #777777 !important;
}

/* File uploader styling - Dark theme */
.stFileUploader {
    background: #333333 !important;
    border: 2px dashed #666666 !important;
    border-radius: 8px !important;
    padding: 1.5rem !important;
}

.stFileUploader label {
    color: #ffffff !important;
    font-weight: bold !important;
    font-size: 1rem !important;
}

.stFileUploader div {
    color: #ffffff !important;
}

.stFileUploader section {
    color: #ffffff !important;
    font-weight: 500 !important;
}

.stFileUploader [data-testid="stFileUploaderDropzone"] {
    background-color: #333333 !important;
    border: 2px dashed #666666 !important;
    color: #ffffff !important;
}

.stFileUploader [data-testid="stFileUploaderDropzone"] div {
    color: #ffffff !important;
}

/* Progress bar */
.stProgress .st-bo {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
}

/* Success/Error messages */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
    padding: 1rem 1.5rem !important;
    font-weight: 500 !important;
}

/* White text for black background */
.streamlit-expanderHeader {
    color: #ffffff !important;
    font-weight: bold !important;
}

/* All headings - White text */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
    font-weight: bold !important;
}

/* All text elements - White text */
p, div, span, label {
    color: #ffffff !important;
}

/* Streamlit specific text elements */
.stMarkdown, .stMarkdown p, .stMarkdown div {
    color: #ffffff !important;
}

.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
    color: #ffffff !important;
}

/* Form labels and inputs */
.stSelectbox label, .stTextArea label, .stFileUploader label {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Step headers */
.stMarkdown h3 {
    color: #ffffff !important;
    font-weight: bold !important;
    font-size: 1.3rem !important;
}

/* Option labels */
.stMarkdown strong {
    color: #ffffff !important;
    font-weight: bold !important;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background: #000000 !important;
}

.stTabs [data-baseweb="tab"] {
    background: #000000 !important;
    color: #ffffff !important;
    border-bottom: 2px solid #333333 !important;
}

.stTabs [data-baseweb="tab"]:hover {
    background: #222222 !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #000000 !important;
    color: #ffffff !important;
    border-bottom: 2px solid #ffffff !important;
}

/* Metric styling - High visibility with fixed text colors */
.metric-container {
    background: rgba(255, 255, 255, 1) !important;
    padding: 1rem;
    border-radius: 12px;
    text-align: center;
    border: 2px solid #4f46e5;
    color: #000000 !important;
}

/* Streamlit metrics styling - Force all text to be black on white */
.stMetric {
    background: rgba(255, 255, 255, 1) !important;
    padding: 1rem !important;
    border-radius: 12px !important;
    border: 2px solid #e5e7eb !important;
    color: #000000 !important;
}

.stMetric > div {
    background: rgba(255, 255, 255, 1) !important;
    color: #000000 !important;
}

.stMetric [data-testid="metric-container"] {
    background: rgba(255, 255, 255, 1) !important;
    border: 2px solid #e5e7eb !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}

.stMetric [data-testid="metric-container"] > div {
    background: rgba(255, 255, 255, 1) !important;
    color: #000000 !important;
    font-weight: bold !important;
}

/* Force all metric text elements to be black */
.stMetric div, .stMetric span, .stMetric p, .stMetric label {
    color: #000000 !important;
    background: transparent !important;
}

/* Metric value styling */
.stMetric [data-testid="metric-container"] [data-testid="metric-value"] {
    color: #000000 !important;
    font-size: 1.5rem !important;
    font-weight: bold !important;
}

/* Metric label styling */
.stMetric [data-testid="metric-container"] [data-testid="metric-label"] {
    color: #000000 !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
}

/* Additional overrides for metric content */
.stMetric * {
    color: #000000 !important;
}

/* Target specific Streamlit metric data elements - STRONGEST OVERRIDES */
[data-testid="metric-container"] {
    background: rgba(255, 255, 255, 1) !important;
    color: #000000 !important;
    border: 2px solid #e5e7eb !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}

[data-testid="metric-container"] * {
    color: #000000 !important;
    background: transparent !important;
}

[data-testid="metric-value"] {
    color: #000000 !important;
    font-size: 1.8rem !important;
    font-weight: bold !important;
}

[data-testid="metric-label"] {
    color: #333333 !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}

/* Force visibility for all metric content */
.stMetric span, .stMetric div[data-testid] {
    color: #000000 !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* ADDITIONAL STRONG OVERRIDES FOR METRIC VISIBILITY */
.stMetric [data-testid="metric-container"] div {
    color: #000000 !important;
    font-weight: bold !important;
}

.stMetric [data-testid="metric-container"] span {
    color: #000000 !important;
    font-weight: bold !important;
}

/* Override any inherited styles from containers */
div[data-testid="metric-container"] > div > div {
    color: #000000 !important;
}

/* Specific targeting for metric text elements */
.metric-container div, .metric-container span, .metric-container p {
    color: #000000 !important;
    background: transparent !important;
}

/* Ultimate fallback - target all elements within metrics */
[data-testid="metric-container"] > * > * {
    color: #000000 !important;
}

/* NOTE: Metric visibility issues resolved by using HTML metrics instead of st.metric() */
/* All metric displays now use custom HTML with inline styles for guaranteed visibility */

/* Keep these rules for any remaining st.metric instances */
.stMetric {
    background: #ffffff !important;
    color: #000000 !important;
    border: 2px solid #333333 !important;
    border-radius: 8px !important;
    padding: 1rem !important;
}

.stMetric * {
    color: #000000 !important;
    background: transparent !important;
    font-weight: bold !important;
}

.upload-info {
    background: #333333;
    padding: 1.5rem;
    border-radius: 8px;
    border: 2px solid #666666;
    margin: 1rem 0;
    color: #ffffff !important;
    font-weight: bold !important;
}

.upload-info strong {
    color: #ffffff !important;
    font-weight: bold !important;
}

/* Alert messages - Dark theme */
.stInfo, .stWarning, .stSuccess, .stError {
    background-color: #333333 !important;
    color: #ffffff !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    border: 2px solid #666666 !important;
}

.stInfo div, .stWarning div, .stSuccess div, .stError div {
    color: #ffffff !important;
}

/* Success messages - Green accent */
.stSuccess {
    border-color: #4ade80 !important;
}

/* Warning messages - Orange accent */
.stWarning {
    border-color: #fb923c !important;
}

/* Error messages - Red accent */
.stError {
    border-color: #f87171 !important;
}

/* Info messages - Blue accent */
.stInfo {
    border-color: #60a5fa !important;
}

/* Better visibility for all text in containers */
.stContainer, .stContainer div, .stContainer p {
    color: #ffffff !important;
}

/* Column content */
.stColumn, .stColumn div, .stColumn p {
    color: #ffffff !important;
}

/* Make comparison text boxes stand out more */
.stMarkdown h3:contains("Text Comparison") {
    font-size: 1.5rem !important;
    margin-bottom: 1.5rem !important;
    color: #ffffff !important;
}

/* Make column headers more visible */
.stMarkdown strong {
    font-size: 1.1rem !important;
    color: #ffffff !important;
    margin-bottom: 0.5rem !important;
    display: block !important;
}

/* Expandable sections text visibility */
.streamlit-expanderContent {
    background: #000000 !important;
    color: #ffffff !important;
}

.streamlit-expanderContent p, 
.streamlit-expanderContent div, 
.streamlit-expanderContent span {
    color: #ffffff !important;
}

.streamlit-expanderContent .stMarkdown {
    color: #ffffff !important;
}

.streamlit-expanderContent .stMarkdown p {
    color: #ffffff !important;
}

.streamlit-expanderContent .stMarkdown strong {
    color: #ffffff !important;
    font-weight: bold !important;
}

/* Analysis section specific styling */
.streamlit-expanderContent .stWrite {
    color: #ffffff !important;
}

.streamlit-expanderContent .stWrite p {
    color: #ffffff !important;
}

/* Ensure bullet points are visible */
.streamlit-expanderContent li {
    color: #ffffff !important;
}

/* Force visibility for nested elements */
[data-testid="stExpander"] * {
    color: #ffffff !important;
}

/* Override any inherited styles that might hide text */
[data-testid="stExpander"] .element-container * {
    color: #ffffff !important;
    visibility: visible !important;
}
</style>
""", unsafe_allow_html=True)

# Clean Header
st.markdown('<h1 class="main-title">🎧 EchoVerse</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI Audiobook Creator</p>', unsafe_allow_html=True)

# Load model (quietly in background)
if "tokenizer" not in st.session_state or "model" not in st.session_state:
    with st.spinner("Loading AI Model..."):
        try:
            st.session_state.tokenizer, st.session_state.model = load_granite_model()
        except Exception as e:
            try:
                st.session_state.tokenizer, st.session_state.model = load_granite_model_fallback()
            except Exception:
                st.error("❌ Model loading failed. Please restart.")
                st.stop()

# Main Input Section - Clean and Simple
st.markdown("### 📝 Enter Your Text")

# Unified input area
tab1, tab2 = st.tabs(["📝 Paste Text", "📁 Upload File"])

with tab1:
    # Quick demo options
    demo_col1, demo_col2 = st.columns([1, 3])
    
    with demo_col1:
        if st.button("🎯 Load Demo", help="Load sample text for quick testing", use_container_width=True):
            demo_sample = "Artificial intelligence is transforming our world. Smart homes anticipate our needs, self-driving cars navigate complex traffic, and machine learning algorithms process vast amounts of data to identify patterns that were impossible just a few years ago. The future of technology is bright with endless possibilities for innovation and growth. Machine learning models are becoming more sophisticated every day, enabling new breakthroughs in healthcare, education, and scientific research. These technological advances are creating opportunities we never thought possible just a decade ago."
            st.session_state.demo_text = demo_sample
            st.success("✅ Demo text loaded!")
    
    with demo_col2:
        if "demo_text" in st.session_state and st.session_state.demo_text:
            st.info(f"📝 Demo text ready: {len(st.session_state.demo_text)} characters")
    
    text_input = st.text_area(
        "Text to convert:",
        height=200,
        placeholder="Paste your text here or click 'Load Demo' above...",
        value=st.session_state.get('uploaded_text', st.session_state.get('demo_text', '')),
        max_chars=10000,
        help="Maximum 10,000 characters",
        key="main_text_input"
    )

with tab2:
    uploaded_file = st.file_uploader(
        "Choose a text file", 
        type=['txt', 'md', 'rtf'],
        help="Upload .txt, .md, or .rtf files (Max: 5MB)"
    )
    
    # Process uploaded file
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.read()
            
            # Try different encodings
            encodings_to_try = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            decoded_content = None
            
            for encoding in encodings_to_try:
                try:
                    decoded_content = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if decoded_content is not None:
                char_count = len(decoded_content)
                if char_count > 10000:
                    st.warning("⚠️ File too large. Using first 10,000 characters.")
                    decoded_content = decoded_content[:10000]
                    char_count = 10000
                
                st.session_state.uploaded_text = decoded_content
                st.success(f"✅ File loaded: {char_count:,} characters")
            else:
                st.error("❌ Could not read file. Please ensure it's a valid text file.")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    else:
        if "uploaded_text" in st.session_state:
            del st.session_state.uploaded_text
            st.rerun()

# IMPORTANT: Use the actual text_input value from the text area widget
# This ensures we process what the user has actually typed/modified
# Don't override with stored values unless the text area is completely empty

# Text Processing Helpers
if text_input and text_input.strip():
    # Calculate comprehensive statistics first
    char_count = len(text_input)
    word_count = len(text_input.split())
    sentence_count = len([s for s in text_input.replace('!', '.').replace('?', '.').split('.') if s.strip()])
    paragraph_count = len([p for p in text_input.split('\n\n') if p.strip()])
    avg_word_length = sum(len(word.strip('.,!?;:')) for word in text_input.split()) / max(word_count, 1)
    
    # Reading time calculations
    reading_time_min = word_count / 200  # ~200 words per minute reading
    listening_time_min = word_count / 150  # ~150 words per minute audio
    
    # Compact header with key stats
    st.markdown("### 📊 Text Analysis")
    
    # Quick stats in compact format with forced visibility
    quick_col1, quick_col2, quick_col3 = st.columns(3)
    
    with quick_col1:
        st.markdown(f"""
        <div style="background: white; border: 2px solid #333; border-radius: 8px; padding: 1rem; text-align: center;">
            <div style="color: #000; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">📝 Words</div>
            <div style="color: #000; font-size: 1.5rem; font-weight: bold;">{word_count:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with quick_col2:
        st.markdown(f"""
        <div style="background: white; border: 2px solid #333; border-radius: 8px; padding: 1rem; text-align: center;">
            <div style="color: #000; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">📚 Read Time</div>
            <div style="color: #000; font-size: 1.5rem; font-weight: bold;">{reading_time_min:.1f}m</div>
        </div>
        """, unsafe_allow_html=True)
    
    with quick_col3:
        st.markdown(f"""
        <div style="background: white; border: 2px solid #333; border-radius: 8px; padding: 1rem; text-align: center;">
            <div style="color: #000; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">🎧 Audio Time</div>
            <div style="color: #000; font-size: 1.5rem; font-weight: bold;">{listening_time_min:.1f}m</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Expandable detailed statistics
    with st.expander("📈 Detailed Statistics", expanded=False):
        detail_col1, detail_col2 = st.columns(2)
        
        with detail_col1:
            # Use HTML metrics for guaranteed visibility
            st.markdown(f"""
            <div style="background: white; border: 1px solid #ddd; border-radius: 6px; padding: 0.8rem; margin: 0.3rem 0; text-align: center;">
                <div style="color: #000; font-size: 0.8rem; font-weight: 600;">📄 Characters</div>
                <div style="color: #000; font-size: 1.3rem; font-weight: bold;">{char_count:,}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background: white; border: 1px solid #ddd; border-radius: 6px; padding: 0.8rem; margin: 0.3rem 0; text-align: center;">
                <div style="color: #000; font-size: 0.8rem; font-weight: 600;">💬 Sentences</div>
                <div style="color: #000; font-size: 1.3rem; font-weight: bold;">{sentence_count}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background: white; border: 1px solid #ddd; border-radius: 6px; padding: 0.8rem; margin: 0.3rem 0; text-align: center;">
                <div style="color: #000; font-size: 0.8rem; font-weight: 600;">📄 Paragraphs</div>
                <div style="color: #000; font-size: 1.3rem; font-weight: bold;">{paragraph_count}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with detail_col2:
            st.markdown(f"""
            <div style="background: white; border: 1px solid #ddd; border-radius: 6px; padding: 0.8rem; margin: 0.3rem 0; text-align: center;">
                <div style="color: #000; font-size: 0.8rem; font-weight: 600;">📏 Avg Word Length</div>
                <div style="color: #000; font-size: 1.3rem; font-weight: bold;">{avg_word_length:.1f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Processing prediction
            if char_count <= 1000:
                processing_est = "Fast (<30s)"
                est_color = "#22c55e"  # green
            elif char_count <= 3000:
                processing_est = "Medium (30-60s)"
                est_color = "#3b82f6"  # blue
            else:
                processing_est = "Longer (60s+)"
                est_color = "#f59e0b"  # yellow
                
            st.markdown(f"""
            <div style="background: white; border: 1px solid #ddd; border-radius: 6px; padding: 0.8rem; margin: 0.3rem 0; text-align: center;">
                <div style="color: #000; font-size: 0.8rem; font-weight: 600;">⚙️ Processing Est.</div>
                <div style="color: {est_color}; font-size: 1.3rem; font-weight: bold;">{processing_est}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Expandable text analysis details
    with st.expander("🔍 Text Quality Analysis", expanded=False):
        analysis_col1, analysis_col2 = st.columns(2)
        
        with analysis_col1:
            st.markdown("**Readability Assessment:**")
            
            # Readability indicators
            if avg_word_length < 4.5:
                readability = "👶 Simple (Easy to read)"
                readability_color = "success"
            elif avg_word_length < 5.5:
                readability = "📚 Moderate (Standard reading)"
                readability_color = "info"
            else:
                readability = "🎩 Complex (Advanced reading)"
                readability_color = "warning"
            
            if readability_color == "success":
                st.success(f"🎩 {readability}")
            elif readability_color == "info":
                st.info(f"📚 {readability}")
            else:
                st.warning(f"👶 {readability}")
            
            st.write(f"• **Average word length**: {avg_word_length:.1f} characters")
            st.write(f"• **Text complexity**: {'High' if avg_word_length > 5.5 else 'Medium' if avg_word_length > 4.5 else 'Low'}")
        
        with analysis_col2:
            st.markdown("**Processing Recommendations:**")
            
            # Text length recommendations with appropriate styling
            if char_count > 8000:
                st.warning("⚠️ Very long text detected")
                st.write("• Consider breaking into 2-3 smaller sections")
                st.write("• Processing time may exceed 2 minutes")
            elif char_count > 5000:
                st.info("📋 Medium length text")
                st.write("• Will use intelligent chunked processing")
                st.write("• Optimal balance of speed and quality")
            elif char_count < 100:
                st.info("📜 Very short text")
                st.write("• Ultra-fast processing expected")
                st.write("• Consider adding more content for richer audio")
            else:
                st.success("✅ Optimal length for processing")
                st.write("• Perfect size for fast, quality results")
                st.write("• Expected processing time: 30-60 seconds")
    
    # Character limit info (always visible but compact)
    char_limit = 10000
    remaining_chars = char_limit - char_count
    if remaining_chars < 1000:
        if remaining_chars > 0:
            st.warning(f"⚠️ {remaining_chars:,} characters remaining (limit: {char_limit:,})")
        else:
            st.error(f"❌ Exceeds limit by {abs(remaining_chars):,} characters")
    
    # Text tools in expandable section
    with st.expander("🚀 Text Processing Tools", expanded=False):
        st.markdown("**Quick Actions:**")
        tool_col1, tool_col2, tool_col3 = st.columns(3)
        
        with tool_col1:
            if st.button("🧹 Clean Spaces", help="Remove extra whitespace and line breaks", use_container_width=True):
                import re
                cleaned_text = re.sub(r'\s+', ' ', text_input).strip()
                cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
                st.session_state.cleaned_text = cleaned_text
                chars_removed = len(text_input) - len(cleaned_text)
                st.success(f"✅ Cleaned! Removed {chars_removed} characters")
        
        with tool_col2:
            if st.button("🔢 Word Frequency", help="Analyze most common words", use_container_width=True):
                import re
                from collections import Counter
                
                # Clean and count words
                words = re.findall(r'\b\w+\b', text_input.lower())
                # Filter out common stop words
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'shall', 'this', 'that', 'these', 'those'}
                content_words = [word for word in words if len(word) > 3 and word not in stop_words]
                
                if content_words:
                    word_freq = Counter(content_words).most_common(10)
                    st.session_state.word_freq = word_freq
                    freq_text = ", ".join([f"{word}({count})" for word, count in word_freq[:3]])
                    st.success(f"✅ Top: {freq_text}...")
        
        with tool_col3:
            if st.button("📏 Processing Time", help="Detailed time estimate", use_container_width=True):
                # More detailed processing estimation
                chunks_needed = max(1, char_count // 800)
                base_time_per_chunk = 8  # seconds
                model_overhead = 5  # seconds
                
                total_estimate = (chunks_needed * base_time_per_chunk) + model_overhead
                
                st.session_state.processing_estimate = {
                    'total_time': total_estimate,
                    'chunks': chunks_needed,
                    'per_chunk': base_time_per_chunk
                }
                
                st.success(f"✅ Est: ~{total_estimate}s ({chunks_needed} chunks)")
        
        # Show results within the same expandable section for better organization
        if hasattr(st.session_state, 'cleaned_text'):
            st.markdown("---")
            st.markdown("**🧹 Cleaned Text Result:**")
            result_col1, result_col2 = st.columns([3, 1])
            with result_col1:
                st.text_area("Cleaned version:", st.session_state.cleaned_text, height=80, disabled=True, key="cleaned_preview")
            with result_col2:
                st.write("\n")  # spacing
                if st.button("✨ Use This", key="use_cleaned", use_container_width=True, help="Replace current text with cleaned version"):
                    # Clear existing stored text and set cleaned text as the new demo text
                    if "uploaded_text" in st.session_state:
                        del st.session_state.uploaded_text
                    st.session_state.demo_text = st.session_state.cleaned_text
                    st.session_state.main_text_input = st.session_state.cleaned_text
                    st.success("✨ Cleaned text loaded into editor!")
                    st.rerun()
        
        if hasattr(st.session_state, 'word_freq'):
            st.markdown("---")
            st.markdown("**🔢 Word Frequency Results:**")
            freq_cols = st.columns(2)
            for i, (word, count) in enumerate(st.session_state.word_freq[:10]):
                col_idx = i % 2
                with freq_cols[col_idx]:
                    st.write(f"• **{word}**: {count}x")
        
        if hasattr(st.session_state, 'processing_estimate'):
            st.markdown("---")
            st.markdown("**📏 Processing Time Breakdown:**")
            est = st.session_state.processing_estimate
            
            est_col1, est_col2 = st.columns(2)
            with est_col1:
                st.write(f"• **Total time**: {est['total_time']}s")
                st.write(f"• **Chunks needed**: {est['chunks']}")
            with est_col2:
                st.write(f"• **Per chunk**: {est['per_chunk']}s")
                st.write(f"• **Model setup**: ~5s")
            
            if est['total_time'] > 120:
                st.warning("⚠️ Long processing expected - consider shorter text")
            elif est['total_time'] < 30:
                st.success("✅ Fast processing expected!")

# Settings Section - Simple
st.markdown("### ⚙️ Choose Settings")
col1, col2 = st.columns(2)

with col1:
    tone = st.selectbox(
        "🎨 Tone Style",
        ["Neutral", "Suspenseful", "Inspiring"]
    )

with col2:
    voice_options = list(get_voice_info().keys())
    voice = st.selectbox(
        "🎤 Voice",
        voice_options
    )

# Voice Preview Section
with st.expander("🎤 Voice Preview & Testing", expanded=False):
    st.markdown("**Test different voices to hear the differences:**")
    
    test_col1, test_col2 = st.columns([2, 1])
    
    with test_col1:
        # Quick test phrase
        test_phrase = "Hello! This is a voice test. How does this sound to you?"
        st.write(f"**Test phrase:** '{test_phrase}'")
        
        # Show voice details
        if voice in get_voice_info():
            voice_info = get_voice_info()[voice]
            st.write(f"**Selected voice details:**")
            st.write(f"• {voice_info['description']}")
            st.write(f"• Speed: {voice_info['speed']} | Gender: {voice_info['gender'].title()}")
    
    with test_col2:
        if st.button("🎵 Test Voice", use_container_width=True, help="Generate a quick audio sample"):
            with st.spinner("Generating voice test..."):
                try:
                    test_audio = ultra_fast_tts(test_phrase, voice)
                    st.audio(test_audio, format="audio/mp3")
                    st.success(f"✅ {voice} sample ready!")
                except Exception as e:
                    st.error(f"❌ Voice test failed: {str(e)}")
    
    # Voice comparison info
    st.markdown("---")
    st.markdown("**🎯 Voice Differences:**")
    
    voice_comp_col1, voice_comp_col2 = st.columns(2)
    with voice_comp_col1:
        st.write("**Female Voices (Faster pace):**")
        st.write("• Sarah - American professional")
        st.write("• Emma - Australian friendly")
        st.write("• Lisa - South African expressive")
    
    with voice_comp_col2:
        st.write("**Male Voices (Slower pace):**")
        st.write("• James - British authoritative")
        st.write("• David - Canadian neutral")
        st.write("• Michael - Irish melodic")

# Generate Button
st.markdown("---")
if st.button("🚀 Generate Audiobook", type="primary", use_container_width=True):
    if not text_input.strip():
        st.error("⚠️ Please enter some text first!")
    else:
        text = text_input
        
        # Smart text length handling
        original_length = len(text)
        if len(text) > 10000:  # Enforce our 10k limit
            text = text[:10000]
            last_period = text.rfind('.')
            if last_period > 8000:  # Try to end on a sentence
                text = text[:last_period + 1]
            st.warning(f"⚠️ Text truncated from {original_length:,} to {len(text):,} characters (10,000 max)")
        elif len(text) > 5000:
            st.info(f"📄 Large text ({len(text):,} chars) will be processed in chunks for optimal results")
        
        # Progress tracking
        total_start = time.time()
        
        # Step 1: Text Rewriting (Solution 1)
        with st.spinner("✨ Rewriting text with AI..."):
            rewrite_start = time.time()
            
            # Use chunked processing for very large text only
            if len(text) > 1200:  # Increased threshold to allow more single-pass processing
                from utils.granite_helper import process_document_with_chunks
                
                # Create progress callback for chunked processing
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def progress_callback(current, total):
                    progress = current / total
                    progress_bar.progress(progress)
                    status_text.text(f"Processing chunk {current}/{total}...")
                
                rewritten_text = process_document_with_chunks(
                    text, tone, st.session_state.tokenizer, st.session_state.model, 
                    ultra_fast_mode=True, progress_callback=progress_callback
                )
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
            else:
                # Standard processing for smaller to medium text - this should handle most cases
                rewritten_text = rewrite_with_tone(
                    text, tone, st.session_state.tokenizer, st.session_state.model, ultra_fast_mode=True
                )
            
            rewrite_time = time.time() - rewrite_start
        
        st.success(f"✅ Text rewritten in {rewrite_time:.1f}s")
        
        # Text Comparison
        st.markdown("### 🔀 Text Comparison")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📄 Original Text**")
            st.text_area(
                "Original", 
                value=text, 
                height=300, 
                disabled=True, 
                key="orig",
                help="Your original text"
            )
        
        with col2:
            st.markdown(f"**✨ {tone} Version**")
            st.text_area(
                "Rewritten", 
                value=rewritten_text, 
                height=300, 
                disabled=True, 
                key="rewrite",
                help=f"Text rewritten in {tone.lower()} tone"
            )
        
        
        # Step 2: Audio Generation (Solutions 2 & 3)
        with st.spinner("🎤 Generating audio..."):
            audio_start = time.time()
            try:
                from utils.tts_helper import text_to_speech
                # For large text, show progress
                if len(rewritten_text) > 2000:
                    st.info(f"🎤 Generating audio for {len(rewritten_text):,} characters. This may take a moment...")
                
                # Use optimized TTS for better performance
                if len(rewritten_text) > 1000:
                    audio_bytes = ultra_fast_tts(rewritten_text, voice)
                else:
                    audio_bytes = text_to_speech(rewritten_text, voice_name=voice, speed_optimization=True)
                
                audio_time = time.time() - audio_start
                
                # Validate audio output
                if not audio_bytes or len(audio_bytes) < 1000:  # Less than 1KB suggests an error
                    raise Exception("Generated audio file is too small or empty")
                    
            except Exception as e:
                st.error(f"❌ Audio generation failed: {str(e)}")
                st.info("🔄 Attempting fallback audio generation...")
                
                # Fallback: Try with shorter text
                try:
                    fallback_text = rewritten_text[:500] + "..." if len(rewritten_text) > 500 else rewritten_text
                    audio_bytes = ultra_fast_tts(fallback_text, "Sarah (Female)")
                    audio_time = time.time() - audio_start
                    st.warning("⚠️ Used fallback audio generation with truncated text")
                except Exception as fallback_error:
                    st.error(f"❌ Fallback audio generation also failed: {str(fallback_error)}")
                    st.error("🎤 Audio generation is currently unavailable. Please check your internet connection and try again.")
                    st.stop()
        
        total_time = time.time() - total_start
        
        st.success(f"✅ Audio generated in {audio_time:.1f}s | **Total: {total_time:.1f}s**")
        
        # Audio Output with Enhanced Player
        st.markdown("### 🎧 Your Audiobook")
        
        # Audio Player - Main focus
        st.audio(audio_bytes, format="audio/mp3")
        
        # Compact audio info
        audio_size_mb = len(audio_bytes) / (1024 * 1024)
        duration_estimate = len(rewritten_text.split()) / 150  # ~150 words per minute
        
        # Quick audio stats with HTML for guaranteed visibility
        quick_audio_col1, quick_audio_col2, quick_audio_col3 = st.columns(3)
        
        with quick_audio_col1:
            st.markdown(f"""
            <div style="background: white; border: 2px solid #333; border-radius: 8px; padding: 1rem; text-align: center;">
                <div style="color: #000; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">📄 File Size</div>
                <div style="color: #000; font-size: 1.5rem; font-weight: bold;">{audio_size_mb:.1f} MB</div>
            </div>
            """, unsafe_allow_html=True)
        
        with quick_col2:
            st.markdown(f"""
            <div style="background: white; border: 2px solid #333; border-radius: 8px; padding: 1rem; text-align: center;">
                <div style="color: #000; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">⏱️ Duration</div>
                <div style="color: #000; font-size: 1.5rem; font-weight: bold;">~{duration_estimate:.1f} min</div>
            </div>
            """, unsafe_allow_html=True)
        
        with quick_col3:
            st.markdown(f"""
            <div style="background: white; border: 2px solid #333; border-radius: 8px; padding: 1rem; text-align: center;">
                <div style="color: #000; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">🎵 Quality</div>
                <div style="color: #000; font-size: 1.5rem; font-weight: bold;">{voice.split(' ')[0]}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Expandable audio controls and info
        with st.expander("🎵 Audio Controls & Info", expanded=False):
            controls_col1, controls_col2 = st.columns(2)
            
            with controls_col1:
                st.markdown("**🔊 Playback Controls:**")
                st.write("• Use browser controls to adjust speed")
                st.write("• Right-click for additional options (loop, save)")
                st.write("• **Recommended speeds:**")
                st.write("  • 0.75x - Slow & clear listening")
                st.write("  • 1.0x - Normal speed")
                st.write("  • 1.25x - Faster learning pace")
            
            with controls_col2:
                st.markdown("**📈 Audio Details:**")
                words_per_sec = len(rewritten_text.split()) / (duration_estimate * 60) if duration_estimate > 0 else 0
                st.write(f"• **Voice**: {voice}")
                st.write(f"• **Tone Style**: {tone}")
                st.write(f"• **Total Words**: {len(rewritten_text.split()):,}")
                st.write(f"• **Speech Rate**: ~{words_per_sec:.1f} words/sec")
                st.write(f"• **File Format**: MP3")
                st.write(f"• **Compression**: Standard quality")
        
        # Expandable download section
        with st.expander("📎 Download Options", expanded=True):  # Expanded by default as users likely want to download
            # Auto-generate filename
            auto_filename = f"echoverse_{tone.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            
            dl_col1, dl_col2 = st.columns([2, 1])
            
            with dl_col1:
                # Custom filename option
                custom_filename = st.text_input(
                    "Custom filename (optional):",
                    value="",
                    placeholder=f"echoverse_{tone.lower()}_{datetime.now().strftime('%Y%m%d')}",
                    help="Leave blank for auto-generated name"
                )
                
                # Use custom filename if provided
                if custom_filename.strip():
                    filename = f"{custom_filename.strip()}.mp3"
                else:
                    filename = auto_filename
                    
                st.write(f"📝 **Final filename**: `{filename}`")
            
            with dl_col2:
                st.write("\n")  # spacing
                # Download button with file info
                st.download_button(
                    f"📎 Download\n({audio_size_mb:.1f}MB)",
                    data=audio_bytes,
                    file_name=filename,
                    mime="audio/mp3",
                    use_container_width=True,
                    help=f"Download as {filename}"
                )
        
        # Simple success message
        st.success(f"✅ Audiobook created successfully in {total_time:.1f} seconds!")
        
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