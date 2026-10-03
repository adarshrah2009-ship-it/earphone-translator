import os
import streamlit as st
from google import genai
from google.genai import types
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="Live Earphone Translator", page_icon="🎧", layout="centered")

st.title("🎧 Live Earphone Translator")

# 1. Check API Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Enter Gemini API Key:", type="password")

if not api_key:
    st.warning("Please provide a Gemini API Key to continue.")
    st.stop()

client = genai.Client(api_key=api_key)

# 2. Selectors
col1, col2 = st.columns(2)
with col1:
    source_lang = st.selectbox("Speaker Language", ["Auto-Detect", "Spanish", "French", "German", "Hindi", "Japanese"])
with col2:
    target_lang = st.selectbox("Translate To", ["English", "French", "Spanish", "German", "Hindi"])

st.markdown("---")

# 3. Mic Audio Recorder
st.subheader("🎤 Speak into Microphone")
audio_record = mic_recorder(
    start_prompt="▶️ Start Recording",
    stop_prompt="⏹️ Stop & Translate",
    key="recorder"
)

if audio_record and "bytes" in audio_record:
    audio_bytes = audio_record["bytes"]
    
    st.write("🎙️ **Recorded Audio:**")
    st.audio(audio_bytes, format="audio/wav")
    
    with st.spinner("Translating..."):
        try:
            prompt = (
                f"You are a real-time translator. Listen to this audio (spoken in {source_lang}). "
                f"Translate it directly into {target_lang}. "
                f"Provide the translated text transcript and speak it back clearly."
            )

            # Using gemini-2.0-flash model for reliable audio generation
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "AUDIO"]
                )
            )

            translated_text = ""
            audio_found = False

            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        translated_text += part.text
                    if part.inline_data and part.inline_data.data:
                        st.success("⚡ **Audio Translation:**")
                        st.audio(part.inline_data.data, format="audio/mp3", autoplay=True)
                        audio_found = True

            if translated_text:
                st.info(f"💬 **Translated Text:** {translated_text}")

            if not audio_found and not translated_text:
                st.warning("Gemini received audio but returned no translation. Speak louder or longer (3–5 seconds).")

        except Exception as e:
            st.error(f"Translation Error: {e}")
