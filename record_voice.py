import speech_recognition as sr
import pickle

print("We will record your voice 3 times to create your voice profile.")
print("Say any sentence clearly each time when prompted.\n")

r = sr.Recognizer()
samples = []

for i in range(3):
    input(f"Press Enter to record sample {i+1}...")
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        print("Recording... speak now!")
        audio = r.listen(source, timeout=5, phrase_time_limit=4)
        samples.append(audio.get_raw_data())
        print(f"Sample {i+1} recorded!\n")

with open("voice_profile.pkl", "wb") as f:
    pickle.dump(samples, f)

print("Voice profile saved! You can now run maxi_app.py")