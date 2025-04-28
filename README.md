🎤 Real-Time Speech-to-Topic Tree Extractor
This is a real-time speech recognition and topic extraction application built with:

Deepgram (for live speech-to-text)

Groq API (for extracting hierarchical topic trees from transcripts)

Streamlit (for the web interface)

🚀 It listens to your microphone in real-time, transcribes the audio, sends the transcript to Groq for processing, and displays the structured topics immediately.

✨ Features

Real-time transcription from your microphone

Automatic topic extraction using LLAMA-3 model from Groq

Streamlit web interface to display live results

🛠️ Installation
First, clone this repository and install the required libraries:

git clone [https://github.com/your-username/real-time-topic-extractor.git
cd real-time-topic-extractor](https://github.com/HamnaCh456/audio_to_transcription_to_topic_extraction.git)

pip install -r requirements.txt
You need to install:

streamlit

python-dotenv

pyaudio

aiohttp

numpy

groq

🧪 Environment Variables
You can set your API keys inside a .env file:

GROQ_API_KEY=your_groq_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
OR directly edit them inside the script if testing.

🚀 Running the Application
After installing dependencies, simply run:

streamlit run app.py
You will see a Streamlit web app with:

▶️ Start Listening button to begin.

⏹️ Stop Listening button to end.

Live Transcripts displayed.

Processed Topic Trees displayed.
