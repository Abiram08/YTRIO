# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**EchoVerse** is an AI-powered audiobook creation tool that implements all 5 required solutions:
1. **Tone-Adaptive Text Rewriting** using IBM Granite 3.3 2B model
2. **Premium Voice Narration** with 6 high-quality voice options  
3. **Audio Output** with streaming and download capabilities
4. **Side-by-Side Text Comparison** for verification
5. **User-Friendly Interface** with document upload support

## 🚀 Quick Start Commands

### Development Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run the main application
streamlit run main.py

# Run with specific port
streamlit run main.py --server.port 8501

# Run tests (if available)
python check_system.py
```

### Development Workflow
```bash
# Start development server (auto-reload enabled)
streamlit run main.py

# Test individual components
python -c "from utils.granite_helper import load_granite_model; print('Model loading test')"
python -c "from utils.tts_helper import get_voice_info; print('TTS test:', list(get_voice_info().keys()))"

# Check system requirements
python check_system.py
```

## 🏗️ Architecture Overview

### Core Architecture Patterns

**1. Modular Component Design**
- `main.py`: Primary Streamlit application with UI and orchestration
- `utils/granite_helper.py`: IBM Granite 3.3 2B model management and text rewriting
- `utils/tts_helper.py`: Text-to-Speech processing with multiple voice options
- `utils/chunking_strategy.py`: Advanced document chunking for large texts
- `utils/progressive_processor.py`: Streaming processing for long documents
- `utils/adaptive_optimizer.py`: Performance optimization strategies
- `utils/smart_fallback.py`: Automatic fallback for slow systems

**2. Processing Pipeline**
```
Text Input → Preprocessing → AI Rewriting → TTS Generation → Audio Output
     ↓              ↓            ↓              ↓            ↓
File Upload → Chunking → Tone Adaptation → Voice Synthesis → MP3 Download
```

**3. Performance Optimization Strategy**
- **Hackathon Demo Mode**: <30 second processing guarantee
- **Smart Chunking**: Automatic text segmentation for large documents  
- **Progressive Processing**: Real-time streaming updates for long texts
- **Adaptive Optimization**: Automatic strategy selection based on text characteristics
- **Caching System**: Results cached to avoid reprocessing

### Key Architectural Decisions

**IBM Granite 3.3 2B Model Integration**
- Local model loading with HuggingFace transformers
- CPU-optimized with memory management
- Fallback loading for low-RAM systems
- No WatsonX dependency - fully local processing

**Text-to-Speech Architecture**
- Google TTS (gTTS) integration with 6 premium voices
- Voice characteristics: US, UK, Australian, Canadian, South African, Irish accents
- Streaming audio player + downloadable MP3 files
- Automatic text preprocessing and optimization

**Document Processing System**
- Multi-encoding support (UTF-8, UTF-16, Latin-1, CP1252)
- Intelligent chunking based on document structure
- Progress tracking for long document processing
- File size and character limits with warnings

## 🔧 Technical Implementation Details

### Text Processing Limits & Capabilities

**Character Limits:**
- **Demo Mode**: 800 characters (auto-truncation)
- **Full Mode**: 50,000 characters (chunked processing)
- **File Upload**: 10MB limit (.txt, .md, .rtf)
- **TTS Processing**: 8,000 characters per generation

**Processing Strategies:**
- **Micro** (<50 chars): Instant string replacement
- **Express** (50-150 chars): Ultra-fast AI processing
- **Standard** (150-500 chars): Standard AI processing  
- **Chunked** (500-2000 chars): Intelligent chunking
- **Progressive** (>2000 chars): Streaming with progress updates

### Memory and Performance Requirements

**System Requirements:**
- **RAM**: 8GB+ recommended (model requires ~2-5GB)
- **Storage**: 5GB+ free space for model cache
- **Internet**: Required for TTS generation and initial model download
- **CPU**: Multi-core processor recommended for faster processing

**Performance Characteristics:**
- **Model Loading**: 10-30 seconds (first run only)
- **Text Processing**: 3-30 seconds depending on length and mode
- **Audio Generation**: 5-15 seconds depending on text length
- **Total Demo Mode**: <30 seconds guaranteed

### Error Handling & Fallbacks

**Model Loading Fallbacks:**
1. Primary loading with optimized settings
2. Fallback loading with memory optimization
3. Error reporting with specific guidance

**TTS Fallbacks:**
1. Primary TTS with selected voice
2. Fallback to default voice on error
3. Truncated text fallback for large content
4. Clear error messages with retry suggestions

**File Processing Fallbacks:**
- Multiple encoding detection and conversion
- Graceful handling of unsupported formats
- File size validation with user warnings
- Detailed error reporting for debugging

## 🎯 Usage Patterns & Best Practices

### For Hackathon Demos
1. **Enable Demo Mode** - guarantees <30 second processing
2. **Use Demo Sample Text** - optimized 400-character AI-themed content
3. **Select any tone** - all work efficiently (Neutral, Suspenseful, Inspiring)
4. **Choose any voice** - all 6 voices tested and working
5. **Total demo time**: 15-25 seconds typical

### For Production Use
1. **Disable Demo Mode** for full-quality processing
2. **Upload documents** up to 10MB in size
3. **Use chunked processing** for documents >500 characters
4. **Monitor progress** with real-time updates for long texts
5. **Download MP3 files** for offline use

### Document Upload Best Practices
- **Supported formats**: .txt, .md, .rtf files
- **Encoding**: UTF-8 recommended (auto-detection available)
- **Size limits**: 10MB file size, 50,000 character processing limit
- **Structure**: Well-structured documents chunk better (paragraphs, sentences)

## 📁 File Structure & Organization

```
IBM - A/
├── main.py                     # Main Streamlit application
├── main_clean.py              # Clean version without optimizations  
├── main_backup.py             # Backup with all optimization features
├── requirements.txt           # Python dependencies
├── check_system.py           # System verification script
├── test_document.txt         # Test document for upload feature
├── utils/                    # Core utility modules
│   ├── __init__.py
│   ├── granite_helper.py     # IBM Granite model management
│   ├── tts_helper.py        # Text-to-Speech processing
│   ├── chunking_strategy.py # Advanced document chunking
│   ├── progressive_processor.py # Streaming processing
│   ├── adaptive_optimizer.py # Performance optimization
│   └── smart_fallback.py    # Automatic fallback systems
├── HACKATHON_OPTIMIZATION.md # Hackathon-specific optimizations
├── SOLUTIONS_SUMMARY.md     # Summary of all 5 solutions
├── UI_CLEANUP.md            # UI improvements documentation
└── README.md               # Project documentation
```

## 🐛 Common Issues & Troubleshooting

### Model Loading Issues
- **Out of Memory**: Close other applications, model requires 2-5GB RAM
- **Slow Loading**: First run downloads ~2GB model files, subsequent runs faster
- **Import Errors**: Run `pip install -r requirements.txt` to ensure all dependencies

### TTS Generation Issues  
- **No Internet**: TTS requires internet connection for Google TTS service
- **Audio Generation Fails**: Check internet connection, try fallback voice
- **Large Text Errors**: Enable chunked processing or reduce text size

### UI/Display Issues
- **Text Not Visible**: Refresh page, high contrast mode implemented for accessibility
- **File Upload Not Working**: Ensure file is .txt/.md/.rtf format, check file size <10MB
- **Slow Performance**: Enable Demo Mode for faster processing, check system resources

## 🚀 Development Guidelines

### Adding New Features
1. **Follow modular design** - create new utility modules in `utils/`
2. **Implement error handling** - always provide fallbacks and clear error messages  
3. **Add progress tracking** - for any operations >5 seconds
4. **Test with Demo Mode** - ensure new features work within 30-second limit
5. **Update documentation** - modify this WARP.md file accordingly

### Performance Optimization
- **Use caching** for expensive operations (model loading, repeated text processing)
- **Implement chunking** for large data processing
- **Provide progress feedback** for long-running operations
- **Add fallback modes** for resource-constrained environments
- **Test memory usage** especially for model operations

### UI/UX Guidelines  
- **High contrast text** - use #000000 for maximum visibility on gradient background
- **Clear error messages** with specific guidance for resolution
- **Progressive disclosure** - use expandable sections for advanced features
- **Responsive design** - ensure functionality works across different screen sizes
- **Accessibility focus** - text must be readable by all users

## 🔒 Security & Privacy

- **Local Processing**: IBM Granite model runs locally, no data sent to external APIs
- **No Data Storage**: Text and audio not stored permanently, session-only storage  
- **TTS Privacy**: Google TTS processes text for audio generation only
- **File Handling**: Uploaded files processed in memory only, not saved to disk
- **Model Security**: Model files cached locally, verified integrity on download

## 📈 Performance Metrics & Monitoring

### Key Performance Indicators
- **Model Loading Time**: Target <30s first run, <5s subsequent runs
- **Text Processing Time**: <10s for <500 chars, <30s for larger texts  
- **Audio Generation Time**: <15s for typical text lengths
- **Total Demo Time**: <30s guaranteed in Demo Mode
- **Memory Usage**: <8GB total system memory recommended

### Monitoring Recommendations
- Monitor processing times in logs
- Track memory usage during model operations
- Log error rates and fallback usage
- Measure user session completion rates
- Monitor file upload success rates

---

**EchoVerse v2.0** - All 5 Solutions Implemented • Hackathon-Optimized • Production-Ready