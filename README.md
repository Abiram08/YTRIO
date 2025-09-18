# 🎧 EchoVerse - AI-Powered Audiobook Creation Tool

**EchoVerse** is a Streamlit-based application that transforms user-provided text into expressive, downloadable audio content using IBM Granite 3.3 2B model for text rewriting and Google Text-to-Speech for audio generation.

## ✨ Features

- **Text Input**: Upload `.txt` files or paste text directly
- **Tone Rewriting**: Transform text using IBM Granite 3.3 2B with three tone options:
  - 🎯 **Neutral**: Clear and professional tone
  - 🎭 **Suspenseful**: Dramatic and engaging tone  
  - ✨ **Inspiring**: Motivational and uplifting tone
- **Audio Generation**: Convert rewritten text to speech using Google TTS
- **Multiple Languages**: Support for English (US/UK/AU)
- **Session History**: View and download past narrations
- **Modern UI**: Beautiful gradient background with responsive design

### 🚀 NEW: Performance Optimizations

- **🧠 Smart Adaptive Processing**: Automatically selects optimal processing strategy based on text characteristics
- **⚗️ Quality vs Speed Balance**: Fine-tune the balance between processing speed and output quality
- **✂️ Intelligent Document Chunking**: Advanced text segmentation for efficient processing of long documents
- **📋 Progressive Processing**: Real-time streaming updates for long texts with live progress indicators
- **📊 Performance Analytics**: Real-time processing statistics and optimization recommendations
- **⚡ Ultra-Fast Mode**: Reduces processing time from 18+ seconds to 3-8 seconds

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Internet connection (for model download on first run)

### Installation

1. **Clone or download the project**:
   ```bash
   cd "D:\Tech\Projects\IBM Gen AI\echoverse-x"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run main.py
   ```

4. **Open your browser** to the displayed URL (usually `http://localhost:8501`)

## 📖 How to Use

### Step 1: Input Text
- **Upload a file**: Click "Upload .txt file" and select your text file
- **Or paste text**: Directly enter text in the text area

### Step 2: Configure Settings
- **Select Tone**: Choose from Neutral, Suspenseful, or Inspiring
- **Select Voice Style**: Choose preferred voice (note: gTTS uses standard voices)
- **Select Language**: Choose from English variants

### Step 3: Generate Audiobook
- Click the **"🎵 Generate Audiobook"** button
- Wait for the model to rewrite your text (first run may take longer)
- Listen to the generated audio
- Download the MP3 file

### Step 4: Review Past Narrations
- View previously generated audiobooks in the "Past Narrations" section
- Re-download or replay any previous generation
- Clear history when needed

## 🔧 Technical Details

### Model Information
- **Text Rewriting**: IBM Granite 3.3 2B Instruct model
  - Downloaded from Hugging Face on first run
  - Cached locally for faster subsequent runs
  - CPU-optimized for broader compatibility

### Text-to-Speech
- **Engine**: Google Text-to-Speech (gTTS)
- **Output Format**: MP3
- **Languages**: English (US, UK, Australian)

### System Requirements
- **RAM**: 8GB+ recommended (for model loading)
- **Storage**: 5GB+ free space (for model cache)
- **CPU**: Multi-core processor recommended

## 🛠️ Troubleshooting

### Common Issues

1. **Model Loading Takes Long Time**
   - First run downloads ~2GB model files
   - Subsequent runs should be much faster
   - Ensure stable internet connection

2. **Out of Memory Errors**
   - Close other applications
   - The model is CPU-optimized but still memory-intensive
   - Consider using a machine with more RAM

3. **TTS Errors**
   - Check internet connection (gTTS requires internet)
   - Verify text content is not empty
   - Try shorter text if issues persist

4. **Import Errors**
   - Run `python test_imports.py` to check all dependencies
   - Reinstall requirements: `pip install -r requirements.txt`

### Getting Help
- Check the console output for detailed error messages
- Ensure all dependencies are properly installed
- Verify Python version compatibility

## 📁 Project Structure

```
echoverse-x/
├── main.py                 # Main Streamlit application
├── requirements.txt        # Python dependencies
├── utils/
│   ├── __init__.py
│   ├── granite_helper.py   # IBM Granite model utilities
│   └── tts_helper.py       # Google TTS utilities
├── test_imports.py         # Import verification script
└── README.md              # This file
```

## 🎯 Use Cases

- **Students**: Convert study notes to audio for mobile learning
- **Content Creators**: Transform blog posts into podcast-style content
- **Accessibility**: Provide audio versions of text content
- **Experimentation**: Test different tones and voices for creative projects

## 📋 Requirements

All required packages are listed in `requirements.txt`:
- streamlit
- transformers
- torch
- accelerate
- sentencepiece
- gTTS

## 🔮 Future Enhancements

- Support for additional languages
- More voice options
- Batch processing capabilities
- Export in multiple audio formats
- User account and persistent history

---

**EchoVerse v1.0** - Powered by IBM Granite 3.3 2B & Google TTS