import streamlit as st  
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration  
import queue  
import threading  
import websocket  
import json  
import numpy as np  
import time  
from dotenv import load_dotenv  
import os  
from groq import Groq  
  
load_dotenv()  
  
# Global variables  
audio_queue = queue.Queue()  
all_transcripts = []  
full_results = ""  
  
# Placeholders for dynamic content  
transcript_placeholder = st.empty()  
processed_placeholder = st.empty()  
  
# Deepgram API setup  
api_key = os.getenv("DEEPGRAM_API_KEY")  
headers = {  
    "Authorization": f"Token {api_key}",  
}  
deepgram_ws_url = "wss://api.deepgram.com/v1/listen"  
  
# Groq processing function  
def process_with_groq(transcript):  
    global full_results  
    client = Groq(  
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
    result = chat_completion.choices[0].message.content  
    full_results += result  
    processed_placeholder.write(f"Processed Results: {result}")  
  
# WebSocket callbacks  
def on_message(ws, message):  
    try:  
        response = json.loads(message)  
        if response.get("type") == "Results":  
            transcript = response["channel"]["alternatives"][0].get("transcript", "")  
            if transcript:  
                all_transcripts.append(transcript)  
                transcript_placeholder.write(f"Live Transcript: {transcript}")  
                process_with_groq(transcript)  
    except Exception as e:  
        print(f"Error processing message: {e}")  
  
def on_error(ws, error):  
    print(f"WebSocket error: {error}")  
  
def on_close(ws, close_status_code, close_msg):  
    print(f"WebSocket closed: {close_msg}")  
  
def on_open(ws):  
    print("WebSocket connection established")  
  
# Audio processing thread  
def process_audio_queue():  
    # Create WebSocket connection  
    ws = websocket.WebSocketApp(  
        f"{deepgram_ws_url}?encoding=linear16&sample_rate=16000",  
        header=headers,  
        on_message=on_message,  
        on_error=on_error,  
        on_close=on_close,  
        on_open=on_open  
    )  
      
    # Start WebSocket in a separate thread  
    ws_thread = threading.Thread(target=ws.run_forever)  
    ws_thread.daemon = True  
    ws_thread.start()  
      
    # Process audio chunks  
    while True:  
        if not audio_queue.empty():  
            audio_chunk = audio_queue.get()  
            if ws.sock and ws.sock.connected:  
                ws.send(audio_chunk, websocket.ABNF.OPCODE_BINARY)  
        else:  
            time.sleep(0.01)  
  
# WebRTC audio callback  
def audio_frame_callback(frame):  
    sound = frame.to_ndarray()  
    sound = sound.astype(np.int16)  
    audio_queue.put(sound.tobytes())  
    return frame  
  
# Main Streamlit app  
def main():  
    st.title("Real-Time Speech-to-Topic Tree Extractor")  
      
    # Start audio processing thread  
    if "processing_thread_started" not in st.session_state:  
        processing_thread = threading.Thread(target=process_audio_queue, daemon=True)  
        processing_thread.start()  
        st.session_state.processing_thread_started = True  
      
    # WebRTC streamer  
    webrtc_ctx = webrtc_streamer(  
        key="speech-to-text",  
        mode=WebRtcMode.SENDONLY,  
        audio_frame_callback=audio_frame_callback,  
        rtc_configuration=RTCConfiguration(  
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}  
        ),  
        media_stream_constraints={"video": False, "audio": True},  
    )  
      
    # Show results button  
    if st.button("Show Results"):  
        full_text = " ".join(all_transcripts)  
        st.write("Final Full Transcript:", full_text)  
        st.write("Full Processed Results:", full_results)  
  
if __name__ == "__main__":  
    main()
