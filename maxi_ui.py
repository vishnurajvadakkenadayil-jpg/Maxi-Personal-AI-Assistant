import os
import threading
import speech_recognition as sr
import webbrowser
import datetime
import subprocess
import re
import requests
import xml.etree.ElementTree as ET
import cv2
import ctypes
from pathlib import Path
from groq import Groq
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv
import webview
import time

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GROQ_KEY = os.getenv("GROQ_API_KEY", "")
WEATHER_KEY = os.getenv("WEATHER_KEY", "")
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

app = Flask(__name__)
stop_speaking = False
camera_running = False
messages = []
status = {"text": "INITIALIZING...", "state": "sleeping"}

HTML = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Maxi</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');

* { margin:0; padding:0; box-sizing:border-box; }

body {
  background: #000008;
  color: #fff;
  font-family: 'Rajdhani', sans-serif;
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.grid-bg {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  background-image:
    linear-gradient(rgba(0,180,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,180,255,0.04) 1px, transparent 1px);
  background-size: 50px 50px;
  pointer-events: none;
  z-index: 0;
}

.container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 520px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
}

.title {
  font-family: 'Orbitron', monospace;
  font-size: 48px;
  font-weight: 900;
  letter-spacing: 16px;
  color: #fff;
  text-shadow:
    0 0 10px rgba(0,180,255,1),
    0 0 30px rgba(0,180,255,0.8),
    0 0 60px rgba(0,180,255,0.5),
    0 0 100px rgba(0,180,255,0.3);
  margin-top: 16px;
}

.subtitle {
  font-family: 'Rajdhani', sans-serif;
  font-size: 11px;
  letter-spacing: 6px;
  color: rgba(0,180,255,0.5);
  margin-top: 4px;
  text-transform: uppercase;
}

.orb-wrap {
  position: relative;
  width: 220px;
  height: 220px;
  margin: 12px 0;
  perspective: 800px;
}

.ring {
  position: absolute;
  border-radius: 50%;
  border: 1.5px solid rgba(0,180,255,0.5);
  top: 50%; left: 50%;
  transform-origin: center;
}

.ring1 {
  width: 220px; height: 220px;
  margin-left: -110px; margin-top: -110px;
  border-color: rgba(0,180,255,0.3);
  animation: spin1 6s linear infinite;
  box-shadow: 0 0 8px rgba(0,180,255,0.3);
}

.ring2 {
  width: 180px; height: 180px;
  margin-left: -90px; margin-top: -90px;
  border-color: rgba(0,220,255,0.5);
  animation: spin2 4s linear infinite;
  box-shadow: 0 0 8px rgba(0,220,255,0.4);
}

.ring3 {
  width: 140px; height: 140px;
  margin-left: -70px; margin-top: -70px;
  border-color: rgba(100,200,255,0.6);
  animation: spin3 3s linear infinite;
  box-shadow: 0 0 8px rgba(100,200,255,0.5);
}

.ring4 {
  width: 100px; height: 100px;
  margin-left: -50px; margin-top: -50px;
  border-color: rgba(150,220,255,0.7);
  animation: spin1 2s linear infinite reverse;
  box-shadow: 0 0 10px rgba(150,220,255,0.6);
}

@keyframes spin1 {
  from { transform: rotateX(70deg) rotateZ(0deg); }
  to   { transform: rotateX(70deg) rotateZ(360deg); }
}
@keyframes spin2 {
  from { transform: rotateX(60deg) rotateZ(0deg) rotateY(20deg); }
  to   { transform: rotateX(60deg) rotateZ(360deg) rotateY(20deg); }
}
@keyframes spin3 {
  from { transform: rotateX(50deg) rotateZ(0deg) rotateY(40deg); }
  to   { transform: rotateX(50deg) rotateZ(360deg) rotateY(40deg); }
}

.waveform {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  height: 50px;
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
}

.bar {
  width: 3px;
  background: rgba(0,180,255,0.8);
  border-radius: 2px;
  animation: wave 1.2s ease-in-out infinite;
  box-shadow: 0 0 6px rgba(0,180,255,0.8);
}

.bar:nth-child(1) { animation-delay: 0.0s; }
.bar:nth-child(2) { animation-delay: 0.1s; }
.bar:nth-child(3) { animation-delay: 0.2s; }
.bar:nth-child(4) { animation-delay: 0.3s; }
.bar:nth-child(5) { animation-delay: 0.4s; }
.bar:nth-child(6) { animation-delay: 0.3s; }
.bar:nth-child(7) { animation-delay: 0.2s; }
.bar:nth-child(8) { animation-delay: 0.1s; }
.bar:nth-child(9) { animation-delay: 0.0s; }

@keyframes wave {
  0%, 100% { height: 4px; opacity: 0.4; }
  50%       { height: 40px; opacity: 1; }
}

.bar.sleeping { animation: none; height: 3px; opacity: 0.2; }
.bar.thinking {
  background: rgba(255,180,0,0.9);
  box-shadow: 0 0 6px rgba(255,180,0,0.8);
  animation: wave 0.4s ease-in-out infinite;
}

.core {
  position: absolute;
  width: 60px; height: 60px;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0,180,255,0.95) 0%, rgba(0,100,200,0.5) 50%, transparent 70%);
  box-shadow: 0 0 20px rgba(0,180,255,1), 0 0 50px rgba(0,180,255,0.7), 0 0 100px rgba(0,180,255,0.4);
  animation: corepulse 2s ease-in-out infinite;
}

.core.listening {
  background: radial-gradient(circle, rgba(0,255,150,0.95) 0%, rgba(0,180,100,0.5) 50%, transparent 70%);
  box-shadow: 0 0 20px rgba(0,255,150,1), 0 0 50px rgba(0,255,150,0.7), 0 0 100px rgba(0,255,150,0.4);
  animation: corepulse 0.6s ease-in-out infinite;
}

.core.thinking {
  background: radial-gradient(circle, rgba(255,180,0,0.95) 0%, rgba(200,120,0,0.5) 50%, transparent 70%);
  box-shadow: 0 0 20px rgba(255,180,0,1), 0 0 50px rgba(255,180,0,0.7), 0 0 100px rgba(255,180,0,0.4);
  animation: corepulse 0.3s ease-in-out infinite;
}

@keyframes corepulse {
  0%,100% { transform: translate(-50%,-50%) scale(1); }
  50%      { transform: translate(-50%,-50%) scale(1.2); }
}

.status {
  font-family: 'Orbitron', monospace;
  font-size: 10px;
  letter-spacing: 4px;
  color: rgba(0,180,255,0.7);
  text-transform: uppercase;
  margin: 4px 0;
}
.status.listening { color: rgba(0,255,150,0.9); }
.status.thinking  { color: rgba(255,180,0,0.9); }

.chat-area {
  flex: 1;
  width: 100%;
  overflow-y: auto;
  padding: 6px 0;
  scrollbar-width: none;
}
.chat-area::-webkit-scrollbar { display: none; }

.message {
  width: 100%;
  margin: 5px 0;
  display: flex;
  flex-direction: column;
  animation: fadein 0.3s ease;
}
@keyframes fadein {
  from { opacity:0; transform:translateY(8px); }
  to   { opacity:1; transform:translateY(0); }
}
.message.maxi { align-items: flex-start; }
.message.user { align-items: flex-end; }

.sender {
  font-size: 9px;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 2px;
  opacity: 0.5;
}
.message.maxi .sender { color: #00b4ff; }
.message.user .sender { color: #00ff96; }

.bubble {
  max-width: 82%;
  padding: 8px 14px;
  font-size: 13px;
  line-height: 1.5;
  letter-spacing: 0.3px;
}
.message.maxi .bubble {
  background: rgba(0,180,255,0.07);
  border: 1px solid rgba(0,180,255,0.2);
  border-left: 2px solid rgba(0,180,255,0.9);
  color: rgba(180,225,255,0.95);
}
.message.user .bubble {
  background: rgba(0,255,150,0.05);
  border: 1px solid rgba(0,255,150,0.15);
  border-right: 2px solid rgba(0,255,150,0.9);
  color: rgba(180,255,220,0.95);
}

.scanline {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 3px;
  background: linear-gradient(90deg, transparent, rgba(0,180,255,0.4), transparent);
  animation: scan 4s linear infinite;
  pointer-events: none;
  z-index: 999;
}
@keyframes scan {
  from { transform: translateY(0); }
  to   { transform: translateY(100vh); }
}

.corner {
  position: fixed;
  width: 40px; height: 40px;
  border-color: rgba(0,180,255,0.4);
  border-style: solid;
}
.corner.tl { top:8px; left:8px; border-width: 2px 0 0 2px; }
.corner.tr { top:8px; right:8px; border-width: 2px 2px 0 0; }
.corner.bl { bottom:8px; left:8px; border-width: 0 0 2px 2px; }
.corner.br { bottom:8px; right:8px; border-width: 0 2px 2px 0; }
</style>
</head>
<body>
<div class="grid-bg"></div>
<div class="scanline"></div>
<div class="corner tl"></div>
<div class="corner tr"></div>
<div class="corner bl"></div>
<div class="corner br"></div>

<div class="container">
  <div class="title">MAXI</div>
  <div class="subtitle">Advanced AI Assistant &nbsp;|&nbsp; Online</div>

  <div class="orb-wrap">
    <div class="ring ring1"></div>
    <div class="ring ring2"></div>
    <div class="ring ring3"></div>
    <div class="ring ring4"></div>
    <div class="core" id="core"></div>
    <div class="waveform" id="wave">
      <div class="bar sleeping"></div>
      <div class="bar sleeping"></div>
      <div class="bar sleeping"></div>
      <div class="bar sleeping"></div>
      <div class="bar sleeping"></div>
      <div class="bar sleeping"></div>
      <div class="bar sleeping"></div>
      <div class="bar sleeping"></div>
      <div class="bar sleeping"></div>
    </div>
  </div>

  <div class="status" id="status">INITIALIZING</div>
  <div class="chat-area" id="chat"></div>
</div>

<script>
function updateUI() {
  fetch('/status')
    .then(r => r.json())
    .then(data => {
      const status = document.getElementById('status');
      const core = document.getElementById('core');
      const bars = document.querySelectorAll('.bar');
      status.textContent = data.text;
      status.className = 'status ' + data.state;
      core.className = 'core ' + data.state;
      bars.forEach(b => {
        b.className = 'bar';
        if(data.state === 'sleeping') b.classList.add('sleeping');
        if(data.state === 'thinking') b.classList.add('thinking');
      });
    });

  fetch('/messages')
    .then(r => r.json())
    .then(data => {
      const chat = document.getElementById('chat');
      chat.innerHTML = '';
      data.forEach(msg => {
        const div = document.createElement('div');
        div.className = 'message ' + msg.sender.toLowerCase();
        div.innerHTML = `
          <div class="sender">${msg.sender}</div>
          <div class="bubble">${msg.text}</div>
        `;
        chat.appendChild(div);
      });
      chat.scrollTop = chat.scrollHeight;
    });
}
setInterval(updateUI, 400);
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/status')
def get_status():
    return jsonify(status)

@app.route('/messages')
def get_messages():
    return jsonify(messages)

def add_message(sender, text):
    messages.append({"sender": sender, "text": text})
    if len(messages) > 50:
        messages.pop(0)

is_speaking = False

def speak(text):
    global is_speaking
    is_speaking = True
    add_message("Maxi", text)
    clean_text = text.replace('"', '').replace("'", '').replace("'", '')
    subprocess.run([
        'powershell', '-Command',
        f'Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate = 3; $s.Speak("{clean_text}")'
    ])
    is_speaking = False

def clean(text):
    text = re.sub(r'[*#\-•\_]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def ask_ai(question):
    if not client:
        print("Groq API key not configured.")
        return "Sorry, I could not get a response because the Groq API key is not configured."

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": """You are Maxi, a personal AI assistant. Reply in maximum 3 short sentences. No bullet points, no symbols, no markdown. Plain spoken English only.
If the question is about latest, newest, current, recent, or today's information — start your reply with SEARCH: followed by a good Google search query.

Here are details about your owner:
Name: Vishnuraj
College: CUSAT Ernakulam
Course: B.Tech CSE, 1st year
Interests: coding, front-end development, UI/UX
Laptop: Asus
Location: Kerala, India
Assistant name: Maxi"""},
                {"role": "user", "content": question}
            ]
        )
        reply = clean(response.choices[0].message.content)
        if reply.startswith("SEARCH:"):
            query = reply.replace("SEARCH:", "").strip()
            speak("Let me search that for you.")
            webbrowser.open(f"https://google.com/search?q={query}")
            return f"Searching for {query}"
        return reply
    except Exception as e:
        print("Error:", e)
        return "Sorry, I could not get a response."

def get_weather():
    if not WEATHER_KEY:
        speak("Weather API key is not configured.")
        return

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q=Ernakulam&appid={WEATHER_KEY}&units=metric"
        r = requests.get(url, timeout=10)
        data = r.json()
        temp = data['main']['temp']
        feels = data['main']['feels_like']
        desc = data['weather'][0]['description']
        speak(f"Current weather in Ernakulam is {desc}. Temperature is {temp} degrees and feels like {feels} degrees.")
    except Exception as e:
        print("Weather error:", e)
        speak("Sorry I could not get the weather right now.")

def get_news():
    global stop_speaking
    stop_speaking = False

    def listen_for_stop_command():
        global stop_speaking
        r = sr.Recognizer()
        r.energy_threshold = 150
        r.dynamic_energy_threshold = False
        with sr.Microphone() as source:
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=3)
                text = r.recognize_google(audio).lower()
                print("During news heard:", text)
                if "stop" in text:
                    stop_speaking = True
            except:
                pass

    try:
        url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
        r = requests.get(url, timeout=10)
        root_xml = ET.fromstring(r.content)
        items = root_xml.findall('./channel/item')
        if not items:
            speak("No news found right now.")
            return
        speak("Here are today's top news headlines. Say stop anytime.")
        time.sleep(5)
        for i, item in enumerate(items[:5]):
            if stop_speaking:
                speak("Okay stopping.")
                break
            title = item.find('title').text
            clean_title = title.replace('"', '').replace("'", '')
            add_message("Maxi", f"Headline {i+1}: {title}")
            stop_thread = threading.Thread(target=listen_for_stop_command, daemon=True)
            stop_thread.start()
            subprocess.run([
                'powershell', '-Command',
                f'Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate = 2; $s.Speak("Headline {i+1}. {clean_title}")'
            ])
            stop_thread.join(timeout=0.5)
            time.sleep(0.5)
    except Exception as e:
        print("News error:", e)
        speak("Sorry I could not get the news right now.")

def set_volume(level=None, action=None):
    try:
        nircmd = str(BASE_DIR / "nircmd.exe")
        if level is not None:
            level = max(0, min(100, level))
            vol = int(level * 655.35)
            subprocess.run([nircmd, "setsysvolume", str(vol)], capture_output=True)
            speak(f"Volume set to {level} percent")
        elif action == "up":
            subprocess.run([nircmd, "changesysvolume", "6553"], capture_output=True)
            speak("Volume increased")
        elif action == "down":
            subprocess.run([nircmd, "changesysvolume", "-6553"], capture_output=True)
            speak("Volume decreased")
        elif action == "mute":
            subprocess.run([nircmd, "mutesysvolume", "1"], capture_output=True)
            speak("Muted")
        elif action == "unmute":
            subprocess.run([nircmd, "mutesysvolume", "0"], capture_output=True)
            speak("Unmuted")
    except Exception as e:
        print("Volume error:", e)
        speak("Sorry could not change volume")
camera_running = False
camera_thread = None

def open_camera():
    global camera_running
    camera_running = True
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    while camera_running:
        ret, frame = cap.read()
        if ret:
            cv2.imshow("Maxi Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    camera_running = False

def take_photo():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        filename = f"photo_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        cv2.imwrite(filename, frame)
        speak(f"Photo saved as {filename}")
    else:
        speak("Sorry could not take photo")
    cap.release()
    cv2.destroyAllWindows()

def set_brightness(level=None, action=None):
    try:
        if level is not None:
            level = max(0, min(100, level))
            subprocess.run([
                'powershell', '-Command',
                f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})'
            ], capture_output=True)
            speak(f"Brightness set to {level} percent")
        elif action == "up":
            subprocess.run([
                'powershell', '-Command',
                '$b = (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness; $nb = [math]::Min(100, $b + 10); (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,$nb)'
            ], capture_output=True)
            speak("Brightness increased")
        elif action == "down":
            subprocess.run([
                'powershell', '-Command',
                '$b = (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness; $nb = [math]::Max(0, $b - 10); (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,$nb)'
            ], capture_output=True)
            speak("Brightness decreased")
    except Exception as e:
        print("Brightness error:", e)
        speak("Sorry could not change brightness")

def handle(cmd):
    global stop_speaking, camera_running, camera_thread
    if "open youtube" in cmd:
        speak("Opening YouTube")
        webbrowser.open("https://youtube.com")
    elif "open google" in cmd:
        speak("Opening Google")
        webbrowser.open("https://google.com")
    elif "open instagram" in cmd:
        speak("Opening Instagram")
        webbrowser.open("https://instagram.com")
    elif "open whatsapp" in cmd:
        speak("Opening WhatsApp")
        webbrowser.open("https://web.whatsapp.com")
    elif "open netflix" in cmd:
        speak("Opening Netflix")
        webbrowser.open("https://netflix.com")
    elif "search" in cmd:
        query = cmd.replace("search", "").strip()
        speak("Searching for " + query)
        webbrowser.open("https://google.com/search?q=" + query)
    elif "open notepad" in cmd:
        speak("Opening Notepad")
        subprocess.Popen("notepad.exe")
    elif "open calculator" in cmd:
        speak("Opening Calculator")
        subprocess.Popen("calc.exe")
    elif "open chrome" in cmd:
        speak("Opening Chrome")
        subprocess.Popen("chrome.exe")
    elif "open files" in cmd or "open file explorer" in cmd:
        speak("Opening File Explorer")
        subprocess.Popen("explorer.exe")
    elif "time" in cmd:
        t = datetime.datetime.now().strftime("%I:%M %p")
        speak("The time is " + t)
    elif "date" in cmd:
        d = datetime.datetime.now().strftime("%B %d, %Y")
        speak("Today is " + d)
    elif "weather" in cmd:
        get_weather()
    elif "news" in cmd:
        get_news()
    elif "open camera" in cmd:
        if not camera_running:
            speak("Opening camera")
            camera_thread = threading.Thread(target=open_camera, daemon=True)
            camera_thread.start()
        else:
            speak("Camera is already open")
    elif "close camera" in cmd:
        speak("Closing camera")
        camera_running = False
    elif "take photo" in cmd or "click photo" in cmd or "take picture" in cmd:
        speak("Say cheese!")
        time.sleep(1)
        take_photo()
    elif any(word in cmd for word in ["volume", "sound", "louder", "quieter"]) or (any(word in cmd for word in ["increase", "set", "make", "put"]) and any(word in cmd for word in ["it", "to"]) and re.findall(r'\d+', cmd)):
        numbers = re.findall(r'\d+', cmd)
        if numbers:
            level = int(numbers[0])
            set_volume(level=level)
        elif any(word in cmd for word in ["up", "increase", "louder", "raise", "more", "high", "higher"]):
            set_volume(action="up")
        elif any(word in cmd for word in ["down", "decrease", "quieter", "lower", "less", "reduce"]):
            set_volume(action="down")
        elif "unmute" in cmd:
            set_volume(action="unmute")
        elif "mute" in cmd:
            set_volume(action="mute")
        else:
            set_volume(action="up")
    elif "mute" in cmd:
        set_volume(action="mute")
    elif "unmute" in cmd:
        set_volume(action="unmute")
    elif any(word in cmd for word in ["brightness", "brighter", "dimmer", "dim"]):
        numbers = re.findall(r'\d+', cmd)
        if numbers:
            level = int(numbers[0])
            set_brightness(level=level)
        elif any(word in cmd for word in ["up", "increase", "brighter", "more", "high", "higher"]):
            set_brightness(action="up")
        elif any(word in cmd for word in ["down", "decrease", "dimmer", "lower", "less", "dim", "reduce"]):
            set_brightness(action="down")
        else:
            set_brightness(action="up")
    elif "stop" in cmd:
        stop_speaking = True
        speak("Okay stopping.")
    else:
        reply = ask_ai(cmd)
        speak(reply)

def listen_for_command():
    global is_speaking
    # Wait until Maxi finishes speaking
    while is_speaking:
        time.sleep(0.1)
    r = sr.Recognizer()
    r.energy_threshold = 150
    r.dynamic_energy_threshold = False
    r.pause_threshold = 0.6
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = r.listen(source, timeout=8, phrase_time_limit=8)
            print("Processing...")
            command = r.recognize_google(audio).lower()
            print("Heard:", command)
            add_message("You", command)
            return command
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print("Listen error:", e)
            return ""
def maxi_loop():
    time.sleep(2)
    print("Maxi loop started")
    status["text"] = "ONLINE — LISTENING"
    status["state"] = "listening"
    speak("Hi Vishnuraj! How can I help you?")
    while True:
        print("Waiting for command...")
        status["text"] = "LISTENING..."
        status["state"] = "listening"
        command = listen_for_command()
        print(f"Command: '{command}'")
        if command:
            if "goodbye" in command or "shut down maxi" in command:
                speak("Goodbye Vishnuraj!")
                break
            status["text"] = "THINKING..."
            status["state"] = "thinking"
            handle(command)

def start_flask():
    app.run(port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    maxi_thread = threading.Thread(target=maxi_loop, daemon=True)
    maxi_thread.start()

    import webbrowser
    import time
    time.sleep(1)
    webbrowser.open("http://localhost:5000")

    # Keep running
    while True:
        time.sleep(1)