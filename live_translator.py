import os
import sys
import asyncio

# 1. Alias PyAudioWPatch so SpeechRecognition/PyAudio works natively on Python 3.14
try:
    import pyaudiowpatch as pyaudio
    sys.modules["pyaudio"] = pyaudio
except ImportError:
    import pyaudio

from google import genai
from google.genai import types

# Initialize Gemini Client (reads GEMINI_API_KEY from environment)
client = genai.Client()

# Live Native Audio WebSocket Endpoint
MODEL_ID = "gemini-2.5-flash-native-audio-preview-12-2025"

# Optimized Audio Settings for Micro-Latency (16kHz PCM input / 24kHz output)
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK_SIZE = 1024


async def audio_input_stream(session, p, stop_event):
    """Captures microphone PCM chunks continuously and streams them over WebSockets."""
    loop = asyncio.get_running_loop()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )
    print("\n🎤 ULTRA-FAST SIMULTANEOUS TRANSLATOR ACTIVE!")
    print("👉 Speak continuously in French, Hindi, German, Spanish, Japanese, etc.\n")
    
    try:
        while not stop_event.is_set():
            data = await loop.run_in_executor(None, stream.read, CHUNK_SIZE, False)
            if data:
                try:
                    await session.send_realtime_input(
                        audio=types.Blob(
                            data=data,
                            mime_type="audio/pcm;rate=16000"
                        )
                    )
                except Exception:
                    break
            await asyncio.sleep(0.001)  # Yield control to event loop
    except asyncio.CancelledError:
        pass
    finally:
        stream.stop_stream()
        stream.close()


async def audio_output_stream(session, p, stop_event):
    """Receives translated audio chunks and plays them directly without delaying."""
    out_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=24000,
        output=True
    )
    
    try:
        async for response in session.receive():
            if stop_event.is_set():
                break
            if response.server_content and response.server_content.model_turn:
                for part in response.server_content.model_turn.parts:
                    # Stream raw PCM audio directly to earphones/speakers
                    if part.inline_data and part.inline_data.data:
                        out_stream.write(part.inline_data.data)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"\n[Connection Notice: {e}]")
    finally:
        out_stream.stop_stream()
        out_stream.close()


async def run_translation_session():
    p = pyaudio.PyAudio()
    stop_event = asyncio.Event()

    # Zero-Fluff System Instruction to eliminate inner thought commentary
    system_prompt = (
        "CRITICAL INSTRUCTION: You are an ultra-fast live speech interpreter. "
        "Listen continuously to speech in ANY language (Hindi, French, Spanish, German, Japanese, etc.) "
        "and translate it instantly into natural spoken English. "
        "Output ONLY the direct English translation audio. NEVER output commentary, intro phrases, "
        "meta-text, or explanations (such as 'I have translated' or 'Translating a Name'). "
        "Do not speak your thoughts. Stay active and keep translating every spoken segment continuously."
    )

    # Enforce pure AUDIO modality for maximum streaming speed
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=system_prompt
    )

    try:
        async with client.aio.live.connect(model=MODEL_ID, config=config) as session:
            input_task = asyncio.create_task(audio_input_stream(session, p, stop_event))
            output_task = asyncio.create_task(audio_output_stream(session, p, stop_event))
            
            await asyncio.gather(input_task, output_task)
    except Exception as e:
        stop_event.set()
        print(f"\n[Session Reconnecting... Reason: {e}]")
    finally:
        p.terminate()


async def main():
    print("=" * 65)
    print("      REAL-TIME SIMULTANEOUS MULTI-LANGUAGE TRANSLATOR      ")
    print("=" * 65)
    
    # Outer infinite loop keeps script online across all consecutive turns
    while True:
        try:
            await run_translation_session()
        except Exception as e:
            print(f"Session Error: {e}")
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    if "GEMINI_API_KEY" not in os.environ:
        print("Error: GEMINI_API_KEY environment variable not found.")
        print("Set it in PowerShell: $env:GEMINI_API_KEY='your_api_key_here'")
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\nShutting down translator.")