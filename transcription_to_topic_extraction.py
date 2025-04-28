import gtts
from playsound import playsound
from dotenv import load_dotenv
import os
import asyncio
import aiohttp
import json
import pyaudio
import numpy as np
import streamlit as st
from groq import Groq

load_dotenv()
full_results = ""
is_listening = False  # Flag to control listening

def process_with_groq(transcript):
    global full_results
    client = Groq(
        #api_key="NA(Your groq api key)"
        api_key=os.getenv("GROQ_API_KEY")
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Extract key topics and create a hierarchical topic tree from it: {transcript}"
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    full_results += chat_completion.choices[0].message.content
    st.write("Processed Results:", chat_completion.choices[0].message.content)

#api_key = "NA(Your deepgram api key )"
api_key = os.getenv("DEEPGRAM_API_KEY")
headers = {
    "Authorization": f"Token {api_key}",
}

deepgram_ws_url = "wss://api.deepgram.com/v1/listen"

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 4096
all_transcripts = []
current_transcript = ""

async def stream_microphone_to_websocket():
    global is_listening

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    st.write("Microphone stream opened. Listening... Press 'Stop' button to end.")

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(
            f"{deepgram_ws_url}?encoding=linear16&sample_rate={RATE}",
            headers=headers
        ) as ws:
            print("WebSocket connection established.")

            async def send_microphone_data():
                try:
                    while is_listening:
                        data = stream.read(CHUNK, exception_on_overflow=False)
                        await ws.send_bytes(data)
                        await asyncio.sleep(0.01)
                except Exception as e:
                    print(f"Error sending microphone data: {e}")
                finally:
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    print("Microphone stream closed.")

            async def receive_transcripts():
                try:
                    async for message in ws:
                        if not is_listening:
                            break
                        try:
                            response = json.loads(message.data)
                            if response.get("type") == "Results":
                                transcript = response["channel"]["alternatives"][0].get("transcript", "")
                                if transcript:
                                    all_transcripts.append(transcript)
                                    st.write("Live Transcript:", transcript)
                                    process_with_groq(transcript)
                                    st.write("Transcript:", transcript)
                        except json.JSONDecodeError as e:
                            print(f"Error decoding JSON message: {e}")
                        except KeyError as e:
                            print(f"Key error: {e}")
                except Exception as e:
                    print(f"WebSocket error: {e}")

            try:
                await asyncio.gather(send_microphone_data(), receive_transcripts())
            finally:
                await close_websocket(ws)

async def close_websocket(ws):
    close_msg = '{"type": "CloseStream"}'
    await ws.send_str(close_msg)
    await ws.close()

def main():
    global is_listening
    st.title("Real-Time Speech-to-Topic Tree Extractor")

    if "run" not in st.session_state:
        st.session_state.run = False

    if st.button("Start Listening"):
        st.session_state.run = True
        is_listening = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(stream_microphone_to_websocket())

    if st.button("Stop Listening"):
        st.session_state.run = False
        is_listening = False
        full_text = " ".join(all_transcripts)
        st.write("Final Full Transcript:", full_text)
        st.write("Full Processed Results:", full_results)
        print(full_text)
        print(full_results)
        print("Process interrupted. Closing connections.")

if __name__ == "__main__":
    main()
