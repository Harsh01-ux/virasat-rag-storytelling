import streamlit as st
import time
import re
import requests
from rag_query import get_rag_response

# Page configurations
st.set_page_config(
    page_title="Heritage Storytelling Engine",
    page_icon="🏛️",
    layout="centered"
)

# Helper to fetch monument image from Wikimedia Commons
def get_monument_image_url(monument_name):
    if not monument_name:
        return None
    
    # Map key monument names to more specific search terms if needed
    search_name = monument_name
    if search_name.lower() == "jaigarh":
        search_name = "Jaigarh Fort"
        
    url = "https://commons.wikimedia.org/w/api.php"
    headers = {
        "User-Agent": "HeritageStorytellingEngine/1.0 (contact: harsh@example.com)"
    }
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": search_name,
        "gsrnamespace": 6,  # File namespace
        "gsrlimit": 5,
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "format": "json",
        "formatversion": 2
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", [])
            for page in pages:
                imageinfo = page.get("imageinfo", [])
                if imageinfo:
                    info = imageinfo[0]
                    mime = info.get("mime", "")
                    url_val = info.get("url", "")
                    if mime.startswith("image/") and url_val:
                        # Avoid non-photographic formats
                        if not any(ext in url_val.lower() for ext in [".svg", ".gif", ".tif", ".tiff"]):
                            return url_val
    except Exception:
        pass
    return None

# Initialize Session State
if "selected_site" not in st.session_state:
    st.session_state.selected_site = None
if "last_selected_site" not in st.session_state:
    st.session_state.last_selected_site = None
if "custom_question" not in st.session_state:
    st.session_state.custom_question = ""
if "custom_question_key" not in st.session_state:
    st.session_state.custom_question_key = ""
if "generated_story" not in st.session_state:
    st.session_state.generated_story = None
if "generated_sources" not in st.session_state:
    st.session_state.generated_sources = None
if "generated_image" not in st.session_state:
    st.session_state.generated_image = None
if "generated_language" not in st.session_state:
    st.session_state.generated_language = None
if "generated_audio" not in st.session_state:
    st.session_state.generated_audio = None
if "show_mic_recorder" not in st.session_state:
    st.session_state.show_mic_recorder = False

# Sync user typed changes back to custom_question storage
if st.session_state.get("custom_question_key"):
    st.session_state.custom_question = st.session_state.custom_question_key

# Track monument selection changes
if st.session_state.selected_site != st.session_state.last_selected_site:
    st.session_state.last_selected_site = st.session_state.selected_site

# Custom CSS for Premium Design & Shifting Sandstone Gradient
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,600&family=Poppins:wght@300;400;500;600;700&display=swap');

/* Dynamic Shifting Sandstone/Terracotta Gradient Background */
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.stApp {
    background: 
        radial-gradient(circle at 50% 50%, transparent 45%, rgba(139, 69, 19, 0.05) 45%, rgba(139, 69, 19, 0.05) 55%, transparent 55%) 0 0 / 40px 40px,
        radial-gradient(circle at 0 0, transparent 45%, rgba(139, 69, 19, 0.05) 45%, rgba(139, 69, 19, 0.05) 55%, transparent 55%) 20px 20px / 40px 40px,
        linear-gradient(-45deg, #601a0a, #9e3e2b, #d88e60, #b84c30);
    background-size: 400% 400%;
    animation: gradientShift 20s ease infinite;
    color: #24140a !important;
    font-family: 'Poppins', sans-serif !important;
}

/* Base Fonts & Headings */
h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: #4a2511 !important;
    font-weight: 700 !important;
    text-shadow: none !important;
}

/* Subtle Fade-in on load */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Glassmorphic Container Cards */
.glass-card {
    background: rgba(255, 255, 255, 0.72) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(255, 255, 255, 0.45) !important;
    border-radius: 20px !important;
    padding: 30px !important;
    box-shadow: 0 10px 35px 0 rgba(96, 26, 10, 0.12) !important;
    margin-bottom: 25px !important;
    animation: fadeIn 0.8s ease-out forwards;
}

/* Grid Buttons / Clickable Cards (Secondary) */
div.stButton > button[kind="secondary"] {
    width: 100% !important;
    height: 105px !important;
    background-color: rgba(255, 255, 255, 0.55) !important;
    border: 1.5px solid rgba(139, 69, 19, 0.15) !important;
    border-radius: 16px !important;
    color: #24140a !important;
    font-family: 'Poppins', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    white-space: pre-line !important;
    box-shadow: 0 4px 15px rgba(139, 69, 19, 0.05) !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
}
div.stButton > button[kind="secondary"]:hover {
    transform: translateY(-3px) !important;
    background-color: rgba(255, 255, 255, 0.85) !important;
    border-color: #D4A017 !important;
    box-shadow: 0 8px 25px rgba(212, 160, 23, 0.22) !important;
    color: #4a2511 !important;
}

/* Active Selected Monument Button (Primary) */
div.stButton > button[kind="primary"] {
    width: 100% !important;
    height: 105px !important;
    background: linear-gradient(135deg, #D4A017 0%, #B8860B 100%) !important;
    border: 1.5px solid #D4A017 !important;
    border-radius: 16px !important;
    color: #ffffff !important;
    font-family: 'Poppins', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    white-space: pre-line !important;
    box-shadow: 0 8px 25px rgba(212, 160, 23, 0.4) !important;
    transform: translateY(-2px) !important;
    transition: all 0.3s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #e5b028 0%, #c9971c 100%) !important;
    box-shadow: 0 10px 30px rgba(212, 160, 23, 0.5) !important;
    transform: translateY(-4px) !important;
}

/* Selection Indicator Banner */
.selected-banner {
    background: rgba(212, 160, 23, 0.12) !important;
    border: 1.5px solid #D4A017 !important;
    border-radius: 12px !important;
    padding: 12px 20px !important;
    font-family: 'Poppins', sans-serif !important;
    color: #4a2511 !important;
    font-size: 15px !important;
    margin-bottom: 25px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    animation: fadeIn 0.4s ease-out forwards;
}

/* Form inputs & dropdowns */
div[data-baseweb="input"], div[data-baseweb="select"] {
    background-color: rgba(255, 255, 255, 0.65) !important;
    border: 1px solid rgba(139, 69, 19, 0.2) !important;
    border-radius: 10px !important;
    color: #24140a !important;
}
input {
    color: #24140a !important;
}

/* Custom Gold Citation Badges */
.citation-badge {
    background: linear-gradient(135deg, #D4A017 0%, #B8860B 100%) !important;
    color: #ffffff !important;
    border-radius: 50% !important;
    padding: 1px 6px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    margin: 0 3px !important;
    display: inline-block !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.15) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    vertical-align: middle !important;
}

/* Interactive Accordions for Citations */
.streamlit-expanderHeader {
    background-color: rgba(255, 255, 255, 0.5) !important;
    border: 1px solid rgba(139, 69, 19, 0.12) !important;
    border-radius: 8px !important;
    color: #4a2511 !important;
    font-weight: 500 !important;
}
.streamlit-expanderContent {
    background-color: rgba(255, 255, 255, 0.3) !important;
    border: 1px solid rgba(139, 69, 19, 0.12) !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
    color: #24140a !important;
    padding: 15px !important;
}

/* Premium Animated Loader styles */
.loading-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
    padding: 40px !important;
}
.spinner {
    width: 35px;
    height: 35px;
    border: 4px solid rgba(212, 160, 23, 0.1);
    border-top: 4px solid #D4A017;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
.loading-text {
    font-family: 'Poppins', sans-serif;
    font-size: 17px;
    font-weight: 500;
    color: #4a2511;
}

/* Labels and subtext */
label, p, span, .stText {
    color: #24140a !important;
}

/* Footer Section */
.footer {
    text-align: center;
    padding: 25px 10px;
    font-family: 'Poppins', sans-serif;
    color: #4a2511;
    opacity: 0.75;
    font-size: 13px;
    margin-top: 50px;
    border-top: 1px solid rgba(139, 69, 19, 0.15);
}

/* Monument Image styling */
.monument-image {
    width: 100%;
    max-height: 380px;
    object-fit: cover;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.4);
    box-shadow: 0 8px 25px rgba(139, 69, 19, 0.15);
    margin-bottom: 20px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    animation: fadeIn 1s ease-out forwards;
}
.monument-image:hover {
    transform: scale(1.02);
    box-shadow: 0 12px 30px rgba(139, 69, 19, 0.25);
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 1. HERO SECTION
st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
st.markdown("<h1 style='margin-bottom: 5px; font-size: 2.5rem;'>🏛️ Heritage Storytelling Engine</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.1rem; opacity: 0.9;'>Explore India's monuments through AI-powered multilingual stories</p>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 2. SITE SELECTOR GRID (7 Monuments)
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("<h3 style='margin-top:0;'>📍 Select a Monument</h3>", unsafe_allow_html=True)
st.write("Click on any site to load it directly as the target of your search:")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🕌 Taj Mahal\nAgra, UP", key="btn_taj", type="primary" if st.session_state.selected_site == "Taj Mahal" else "secondary", use_container_width=True):
        st.session_state.selected_site = "Taj Mahal"
        st.rerun()
with col2:
    if st.button("🏰 Red Fort\nDelhi", key="btn_red", type="primary" if st.session_state.selected_site == "Red Fort" else "secondary", use_container_width=True):
        st.session_state.selected_site = "Red Fort"
        st.rerun()
with col3:
    if st.button("🧗 Ajanta Caves\nAurangabad, MH", key="btn_ajanta", type="primary" if st.session_state.selected_site == "Ajanta Caves" else "secondary", use_container_width=True):
        st.session_state.selected_site = "Ajanta Caves"
        st.rerun()

col4, col5, col6 = st.columns(3)
with col4:
    if st.button("🛕 Khajuraho\nChhatarpur, MP", key="btn_khaj", type="primary" if st.session_state.selected_site == "Khajuraho" else "secondary", use_container_width=True):
        st.session_state.selected_site = "Khajuraho"
        st.rerun()
with col5:
    if st.button("⚔️ Amber Fort\nJaipur, RJ", key="btn_amber", type="primary" if st.session_state.selected_site == "Amber Fort" else "secondary", use_container_width=True):
        st.session_state.selected_site = "Amber Fort"
        st.rerun()
with col6:
    if st.button("🪟 Hawa Mahal\nJaipur, RJ", key="btn_hawa", type="primary" if st.session_state.selected_site == "Hawa Mahal" else "secondary", use_container_width=True):
        st.session_state.selected_site = "Hawa Mahal"
        st.rerun()

col7, col8, col9 = st.columns(3)
with col8:
    if st.button("🛡️ Jaigarh Fort\nJaipur, RJ", key="btn_jai", type="primary" if st.session_state.selected_site == "Jaigarh" else "secondary", use_container_width=True):
        st.session_state.selected_site = "Jaigarh"
        st.rerun()

st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

# Selected site banner + Clear action
if st.session_state.selected_site:
    col_sel, col_clear = st.columns([5, 1.2])
    with col_sel:
        st.markdown(f'<div class="selected-banner"><span>📍 Selected: <b>{st.session_state.selected_site}</b></span></div>', unsafe_allow_html=True)
    with col_clear:
        if st.button("Clear ✕", key="btn_clear", type="secondary", use_container_width=True):
            st.session_state.selected_site = None
            st.session_state.generated_story = None
            st.session_state.generated_sources = None
            st.session_state.generated_image = None
            st.session_state.generated_audio = None
            st.session_state.custom_question = ""
            st.session_state.custom_question_key = ""
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# 3. CUSTOM QUESTIONS & CONTROLS
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("<h3 style='margin-top:0;'>🔧 Customize Search</h3>", unsafe_allow_html=True)

# Set placeholder contextually
if st.session_state.selected_site:
    q_placeholder = f"Ask something specific about {st.session_state.selected_site} (optional)..."
else:
    q_placeholder = "Ask a question about any monument (e.g., How was Taj Mahal built?)..."

# Voice Input row
col_input, col_mic = st.columns([6, 1])
with col_input:
    question = st.text_input(
        "Custom Question:", 
        placeholder=q_placeholder, 
        value=st.session_state.custom_question, 
        key="custom_question_key"
    )
with col_mic:
    st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
    use_mic = st.button("🎤", key="btn_mic", use_container_width=True, help="Record question via browser microphone")

if use_mic:
    st.session_state.show_mic_recorder = not st.session_state.show_mic_recorder

if st.session_state.show_mic_recorder:
    st.write("🎙️ Please record your question below:")
    audio_value = st.audio_input("Record Question", label_visibility="collapsed")
    if audio_value:
        with st.spinner("Transcribing your audio..."):
            try:
                import speech_recognition as sr
                r = sr.Recognizer()
                with sr.AudioFile(audio_value) as source:
                    audio_data = r.record(source)
                
                # Get language mapping
                lang_mic_mapping = {
                    "🇬🇧 English": "en-IN",
                    "🇮🇳 Hindi": "hi-IN",
                    "🇮🇳 Tamil": "ta-IN",
                    "🇮🇳 Bengali": "bn-IN"
                }
                lang_code = lang_mic_mapping.get(language_label, "en-IN")
                
                text = r.recognize_google(audio_data, language=lang_code)
                st.session_state.custom_question = text
                st.session_state.custom_question_key = text
                st.session_state.show_mic_recorder = False
                st.rerun()
            except Exception as e:
                st.error(f"🎙️ Failed to transcribe audio: {e}")

col_ctrl1, col_ctrl2 = st.columns(2)
with col_ctrl1:
    language_label = st.selectbox(
        "Response Language:",
        ["🇬🇧 English", "🇮🇳 Hindi", "🇮🇳 Tamil", "🇮🇳 Bengali"],
        index=0
    )

with col_ctrl2:
    # Use st.segmented_control (supported in v1.35+) for premium horizontal select
    level = st.segmented_control(
        "Expertise Level:",
        options=["beginner", "expert"],
        default="beginner",
        help="'beginner' crafts a simple, engaging overview. 'expert' generates a detailed historical narrative."
    )

# Cache Key Evaluation
# Define current cache key based on full combination of inputs
current_cache_key = f"{st.session_state.selected_site}_{question}_{language_label}_{level}"

if "last_cache_key" not in st.session_state:
    st.session_state.last_cache_key = None

# If any parameter changes, clear the story cache and audio narration
if st.session_state.last_cache_key != current_cache_key:
    st.session_state.generated_story = None
    st.session_state.generated_sources = None
    st.session_state.generated_image = None
    st.session_state.generated_audio = None
    st.session_state.last_cache_key = current_cache_key

st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)

# Main Gold Gradient Action Button
generate_clicked = st.button("Generate Story ✨", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# 4. PROCESSOR & RESULTS
if generate_clicked:
    # Determine query
    final_query = ""
    if question.strip():
        if st.session_state.selected_site:
            final_query = f"{st.session_state.selected_site}: {question}"
        else:
            final_query = question
    elif st.session_state.selected_site:
        final_query = f"Tell me about the history of {st.session_state.selected_site}"
    
    if not final_query:
        st.warning("Please select a monument from the grid or enter a custom question first!")
    else:
        # Load language code mapping
        lang_mapping = {
            "🇬🇧 English": "English",
            "🇮🇳 Hindi": "Hindi",
            "🇮🇳 Tamil": "Tamil",
            "🇮🇳 Bengali": "Bengali"
        }
        target_lang = lang_mapping.get(language_label, "English")
        
        # Premium Loader State
        status_placeholder = st.empty()
        messages = [
            "🏛️ Accessing historical vector database...",
            "📜 Retrieving relevant documents & archives...",
            "✨ Weaving your customized heritage story...",
            "🔍 Adding grounded citation benchmarks..."
        ]
        for msg in messages:
            status_placeholder.markdown(
                f"""
                <div class="glass-card loading-container">
                    <div class="spinner"></div>
                    <div class="loading-text">{msg}</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
            time.sleep(0.75)
        status_placeholder.empty()
        
        # Call RAG pipeline
        with st.spinner("Finalizing story..."):
            answer, sources = get_rag_response(final_query, target_lang, level)
            
        # Determine monument name for image fetching
        monument_name = st.session_state.selected_site
        if not monument_name and sources:
            first_site = sources[0].get("site")
            if first_site and first_site != "Unknown Site":
                monument_name = first_site
        
        # Fallback: check final_query for known monument names
        if not monument_name:
            known_monuments = ["Taj Mahal", "Red Fort", "Ajanta Caves", "Khajuraho", "Amber Fort", "Hawa Mahal", "Jaigarh"]
            query_lower = final_query.lower()
            for m in known_monuments:
                if m.lower() in query_lower:
                    monument_name = m
                    break
                    
        # Fetch monument image URL from Wikimedia Commons API
        img_url = None
        if monument_name:
            with st.spinner(f"Fetching image for {monument_name}..."):
                img_url = get_monument_image_url(monument_name)
                
        # Cache results in Session State
        st.session_state.generated_story = answer
        st.session_state.generated_sources = sources
        st.session_state.generated_image = img_url
        st.session_state.generated_language = target_lang
        st.session_state.generated_audio = None  # Clear old audio narration
        # Store the cache key of the generated result to avoid immediate invalidation
        st.session_state.last_cache_key = f"{st.session_state.selected_site}_{question}_{language_label}_{level}"

# Render stored RAG results if present
if st.session_state.generated_story:
    answer = st.session_state.generated_story
    sources = st.session_state.generated_sources
    img_url = st.session_state.generated_image
    target_lang = st.session_state.generated_language
    
    # Format citation numbers inside text into gold badges
    formatted_answer = re.sub(r'\[(\d+)\]', r"<span class='citation-badge'>\1</span>", answer)
    
    # Display Story Card
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if img_url:
        st.markdown(f'<img src="{img_url}" class="monument-image" alt="Monument Image">', unsafe_allow_html=True)
    st.markdown("### 📜 The Story")
    st.markdown(formatted_answer, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Audio narration controls
    col_audio1, col_audio2 = st.columns([2.5, 3.5])
    with col_audio1:
        listen_clicked = st.button("🔊 Listen to Story", key="btn_listen", use_container_width=True)
    
    if listen_clicked:
        with st.spinner("Generating audio narration..."):
            try:
                # Strip HTML tags and citations for clean speech synthesis
                clean_text = re.sub(r'<[^>]*>', '', answer)
                clean_text = re.sub(r'\[\d+\]', '', clean_text)
                
                from gtts import gTTS
                import io
                
                lang_tts_mapping = {
                    "English": "en",
                    "Hindi": "hi",
                    "Tamil": "ta",
                    "Bengali": "bn"
                }
                lang_code_tts = lang_tts_mapping.get(target_lang, "en")
                
                tts = gTTS(text=clean_text, lang=lang_code_tts, slow=False)
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                
                # Cache audio bytes in Session State and rerun
                st.session_state.generated_audio = fp.getvalue()
                st.rerun()
            except Exception as e:
                st.error(f"🔊 Failed to generate speech: {e}")
                
    if st.session_state.generated_audio:
        st.audio(st.session_state.generated_audio, format="audio/mp3", autoplay=True)
        st.success("🔊 Playing narration!")
                
    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
    
    # Display Sources & Citations
    if sources:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 Sources & Citations")
        for src in sources:
            with st.expander(f"📄 [{src['index']}] {src['site']} (File: {src['filename']})"):
                st.markdown(f"*{src['snippet']}*", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# 5. FOOTER
st.markdown(
    """
    <div class="footer">
        🏛️ Heritage Storytelling Engine | Built for Viraasat AI Hackathon
    </div>
    """,
    unsafe_allow_html=True
)
