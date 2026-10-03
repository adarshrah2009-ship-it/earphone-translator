import os
import sys
import time
import asyncio
import tempfile
import pygame

# 1. Alias PyAudioWPatch for SpeechRecognition on Windows
try:
    import pyaudiowpatch as pyaudio
    sys.modules["pyaudio"] = pyaudio
except ImportError:
    pass

import speech_recognition as sr
import edge_tts
from google import genai
from google.genai import types

# Initialize Audio Output Engine & Gemini Client
pygame.mixer.init()
client = genai.Client()  # Reads GEMINI_API_KEY from environment

# TTS English Output Voice for Earphone
TARGET_VOICE = "en-US-AvaNeural"

async def speak_translation(text: str):
    """Synthesizes English text into spoken audio via Edge-TTS and plays it directly."""
    print(f"\n🎧 Earphone Output (English): {text}")
    
    communicate = edge_tts.Communicate(text, TARGET_VOICE)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_path = tmp_file.name

    await communicate.save(tmp_path)
    
    # Play translated speech directly to headphones / default output
    pygame.mixer.music.load(tmp_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    pygame.mixer.music.unload()
    try:
        os.remove(tmp_path)
    except PermissionError:
        pass

def listen_for_french() -> str:
    """Captures microphone audio specifically configured for French speech recognition."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎤 Listening for French speech...")
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        try:
            # Set language explicitly to French (fr-FR) so words aren't misheard
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)
            french_text = recognizer.recognize_google(audio, language="fr-FR")
            print(f"🇫🇷 Shopkeeper (French): {french_text}")
            return french_text
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return ""
        except Exception as e:
            print(f"Audio Capture Error: {e}")
            return ""

def translate_french_to_english(french_text: str) -> str:
    """Translates French text into natural English using Gemini Flash with multi-model failover."""
    system_prompt = (
        "You are an ultra-fast live translator in France. Translate incoming French speech "
        "into clear, natural, conversational English. Return ONLY the direct English translation. "
        "Do not add explanations, conversational filler, or quotes."
    )
    
    # Disable AFC/Tools to prevent automatic function calling warnings
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[]
    )

    # Active Gemini Flash models for robust fallback handling
    models_to_try = [
        'gemini-3.8-flash',
        'gemini-3.5-flash-lite',
        'gemini-3.1-flash-lite'
    ]
    
    for model_name in models_to_try:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=french_text,
                    config=config
                )
                if response.text:
                    return response.text.strip()
            except Exception as e:
                err_str = str(e)
                # If 503 UNAVAILABLE or high load occurs, wait briefly and retry / switch model
                if any(code in err_str for code in ["503", "UNAVAILABLE", "404", "NOT_FOUND"]):
                    time.sleep(0.5)
                    continue
                else:
                    break
                    
    return "Could not translate. Please repeat."

async def main_translator_loop():
    print("=" * 60)
    print("      LIVE FRANCE EARPHONE TRANSLATOR ONLINE      ")
    print("=" * 60)
    await speak_translation("French earphone translator active. Ready for French speech.")
    
    while True:
        french_speech = listen_for_french()
        if not french_speech:
            continue
            
        if any(word in french_speech.lower() for word in ["arrêt", "quitter", "stop"]):
            await speak_translation("Translation system shutting down.")
            break

        # 1. Translate French -> English
        english_text = translate_french_to_english(french_speech)
        
        # 2. Output translated voice directly to earphones
        await speak_translation(english_text)

if __name__ == "__main__":
    if "GEMINI_API_KEY" not in os.environ:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Run: $env:GEMINI_API_KEY='your_key' in PowerShell before running.")
    else:
        asyncio.run(main_translator_loop())