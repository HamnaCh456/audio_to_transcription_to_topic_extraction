from dotenv import load_dotenv  
import os  
import asyncio  
import json  
import numpy as np  
import streamlit as st  
from groq import Groq  
import queue  
import threading  
import av  
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration  
  
load_dotenv()  
full_results = ""  
  
# Create a queue for audio chunks  
audio_queue = queue.Queue()  
result_placeholder = st.empty()  
transcript_placeholder = st.empty()  
processed_placeholder = st.empty()  
  
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
  
api_key = os.getenv("DEEPGRAM_API_KEY")  
headers = {  
    "Authorization": f"Token {api_key}",  
}  
  
deepgram_ws_url = "wss://api.deepgram.com/v1/listen"  
all_transcripts = []  
  
# Function to process audio chunks from the queue  
def process_audio_queue():  
    import websocket  
    import threading  
    import time  
      
    # Create a WebSocket connection to Deepgram  
    ws = websocket.WebSocketApp(  
        f"{deepgram_ws_url}?encoding=linear16&sample_rate=16000",  
        header=headers,  
        on_message=on_message,  
        on_error=on_error,  
        on_close=on_close  
    )  
      
    # Define WebSocket callbacks  
    def on_message(ws, message):  
        try:  
            response = json.loads(message)  
            if response.get("type") == "Results":  
                transcript = response["channel"]["alternatives"][0].get("transcript", "")  
                if transcript:  
                    all_transcripts.append(transcript)  
                    transcript_placeholder.write(f"Live Transcript: {transcript}")  
                    process_with_groq(transcript)  
        except json.JSONDecodeError as e:  
            print(f"Error decoding JSON message: {e}")  
        except KeyError as e:  
            print(f"Key error: {e}")  
      
    def on_error(ws, error):  
        print(f"WebSocket error: {error}")  
      
    def on_close(ws, close_status_code, close_msg):  
        print(f"WebSocket closed: {close_msg}")  
      
    # Start the WebSocket connection in a separate thread  
    ws_thread = threading.Thread(target=ws.run_forever)  
    ws_thread.daemon = True  
    ws_thread.start()  
      
    # Process audio chunks as they arrive  
    while True:  
        if not audio_queue.empty():  
            audio_chunk = audio_queue.get()  
            if ws.sock and ws.sock.connected:  
                ws.send(audio_chunk, websocket.ABNF.OPCODE_BINARY)  
        else:  
            time.sleep(0.01)  
  
# Start audio processing in a separate thread  
processing_thread = threading.Thread(target=process_audio_queue, daemon=True)  
processing_thread.start()  
  
# WebRTC audio callback  
def audio_frame_callback(frame):  
    # Convert the audio frame to the format Deepgram expects  
    sound = frame.to_ndarray()  
    sound = sound.astype(np.int16)  
      
    # Add to queue for processing  
    audio_queue.put(sound.tobytes())  
      
    return frame  
  
def main():  
    st.title("Real-Time Speech-to-Topic Tree Extractor")  
      
    # WebRTC streamer for audio capture  
    webrtc_ctx = webrtc_streamer(  
        key="speech-to-text",  
        mode=WebRtcMode.SENDONLY,  
        audio_frame_callback=audio_frame_callback,  
        rtc_configuration=RTCConfiguration(  
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}  
        ),  
        media_stream_constraints={"video": False, "audio": True},  
    )  
      
    # Stop button  
    if st.button("Stop and Show Results"):  
        full_text = " ".join(all_transcripts)  
        st.write("Final Full Transcript:", full_text)  
        st.write("Full Processed Results:", full_results)  
  
if __name__ == "__main__":  
    main()
