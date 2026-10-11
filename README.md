# Maxi

A personal voice assistant for Windows, inspired by Jarvis. Maxi listens to your voice, answers questions with an LLM (Groq, Llama 3.3 70B), and controls your PC.

## Features

- Voice commands and spoken replies
- AI answers via Groq, with a Google search handoff for current topics
- Weather (OpenWeatherMap) and news headlines
- Open websites and apps (YouTube, Google, Instagram, WhatsApp Web, Netflix, Notepad, Calculator, Chrome, Explorer)
- System volume (via NirCmd) and screen brightness control
- Webcam photos
- Desktop UI (Flask + pywebview) on `localhost:5000`

## Files

- `maxi_ui.py`: main app with the desktop UI
- `maxi.py`: simple console version
- `record_voice.py`: records a personal voice profile

## Setup (Windows)

1. Create and activate a virtual environment:
```
   python -m venv .venv
   .venv\Scripts\activate
```
2. Install dependencies:
```
   pip install -r requirements.txt
```
3. Copy `.env.example` to `.env` and fill in your keys:
```
   GROQ_API_KEY=your_key_here
   WEATHER_KEY=your_key_here
```
   - Groq key: https://console.groq.com
   - Weather key (free): https://openweathermap.org
4. Download NirCmd from https://www.nirsoft.net/utils/nircmd.html and put `nircmd.exe` in the project folder (needed for volume control).
5. Optional: run `python record_voice.py` to create a voice profile.

## Run

```
python maxi_ui.py
```

## Notes

Never commit your `.env`, `voice_profile.pkl`, or captured photos. They are listed in `.gitignore`. Windows only.