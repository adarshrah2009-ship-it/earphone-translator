import os
import asyncio
import streamlit as st
from google import genai
from google.genai import types
from streamlit_mic_recorder import mic_recorder

# Page Configuration for Mobile Layout
st.set_page_config(
    page_title="Live Earphone Translator",
    page_icon="🎧",
    layout="centered"
)

st.title("🎧 Universal Live Earphone Translator")
st.caption("Turn any Bluetooth earphone into a live simultaneous interpreter.")

# 1. API Key Check
api_key = os.environ.get("GEMINI_API_KEY") or st.text_input("Enter Gemini API Key:", type="password")

if not api_key:
    st.warning("Please set GEMINI_API_KEY environment variable or enter it above.")
    st.stop()

# Initialize Gemini Client
client = genai.Client(api_key=api_key)

# 2. Controls
col1, col2 = st.columns(2)
with col1:
    source_lang = st.selectbox("Speaker Language", ["Auto-Detect", "German", "Spanish", "French", "Hindi", "Japanese"])
with col2:
    target_lang = st.selectbox("Translate To", ["English", "French", "Spanish", "German", "Hindi"])

system_prompt = (
    f"You are a real-time simultaneous audio interpreter. "
    f"Listen to incoming audio continuous speech in {source_lang} "
    f"and instantly translate and speak it back in natural {target_lang}. "
    f"Output ONLY spoken audio translation. Never output commentary, notes, or meta-text."
)

st.markdown("---")

# 3. Audio Recording Interface for Mobile
st.subheader("🎤 Speak or Play Audio")
st.info("Ensure your Bluetooth earphones are connected as your output device.")

audio_data = mic_recorder(
    start_prompt="▶️ Start Live Listening",
    stop_prompt="⏹️ Stop Listening",
    key="mobile_recorder"
)

# 4. Processing & Simultaneous Audio Output
if audio_data and "bytes" in audio_data:
    raw_pcm = audio_data["bytes"]
    st.audio(raw_pcm, format="audio/wav")
    
    with st.spinner("Translating live..."):
        try:
            # Send captured stream to Gemini Audio-to-Audio Model
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=raw_pcm,
                        mime_type="audio/wav"
                    ),
                    system_prompt
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"]
                )
            )

            # Play back audio result straight to connected earphones
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        st.success("⚡ Translated Output:")
                        st.audio(part.inline_data.data, format="audio/mp3", autoplay=True)
                        
        except Exception as e:
            st.error(f"Translation Error: {e}")