import speech_recognition as sr
import pyttsx3
import webbrowser
import datetime
import subprocess
import re
from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def speak(text):
    print("Maxi:", text)
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    engine.setProperty('rate', 170)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

def clean(text):
    text = re.sub(r'[*#\-•\_]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def ask_ai(question):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": """You are Maxi, a personal AI assistant. Reply in maximum 3 short sentences. No bullet points, no symbols, no markdown. Plain spoken English only.

Here are details about your owner:
Name: Vishnuraj
College: CUSAT Ernakulam
Course: B.Tech CSE, 1st year
Interests: coding, front-end development, UI/UX
Laptop: Asus
Location: Kerala, India
Assistant name: Maxi

Use these details when the user asks personal questions about themselves."""},
                {"role": "user", "content": question}
            ]
        )
        return clean(response.choices[0].message.content)
    except Exception as e:
        print("Error:", e)
        return "Sorry, I could not get a response."

def listen_for_wake_word():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Sleeping... say 'Maxi' to wake up")
        r.adjust_for_ambient_noise(source, duration=0.3)
        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=3)
            text = r.recognize_google(audio).lower()
            print("Heard:", text)
            if "maxi" in text:
                return True
        except:
            pass
    return False

def listen_for_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for command...")
        r.adjust_for_ambient_noise(source, duration=0.3)
        try:
            audio = r.listen(source, timeout=6, phrase_time_limit=8)
            command = r.recognize_google(audio).lower()
            print("You said:", command)
            return command
        except sr.WaitTimeoutError:
            speak("I didn't hear anything")
            return ""
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that")
            return ""
        except sr.RequestError:
            speak("Internet connection issue")
            return ""

def handle(cmd):
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

    elif "stop" in cmd or "exit" in cmd or "bye" in cmd:
        speak("Goodbye! Have a great day!")
        exit()

    else:
        reply = ask_ai(cmd)
        speak(reply)

speak("Hi, I am Maxi. Say my name to wake me up!")

while True:
    woke = listen_for_wake_word()
    if woke:
        speak("Yes?")
        command = listen_for_command()
        if command:
            handle(command)

# opening and closing of tabs
#an app thats is always open and you dont need to openn the program