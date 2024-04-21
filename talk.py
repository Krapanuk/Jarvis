import speech_recognition as sr
import requests
import pyttsx3
import json

# Initialisiere die SpeechRecognition-Bibliothek
recognizer = sr.Recognizer()

# Initialisiere Text-to-Speech mit der spezifischen Stimme "Microsoft Hedda Desktop - German"
tts_engine = pyttsx3.init()
voices = tts_engine.getProperty('voices')
for voice in voices:
    if 'Hedda' in voice.name:  # Suche nach der Stimme "Microsoft Hedda Desktop - German"
        tts_engine.setProperty('voice', voice.id)

# Ein einfacher Kontext-Speicher, der den Dialogverlauf hält
dialog_history = []

def listen():
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        try:
            # Verwende die deutsche Spracherkennung
            text = recognizer.recognize_google(audio, language='de-DE')
            print("You said: " + text)
            return text
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return None

def query_llm(text):
    global dialog_history
    dialog_history.append(text)  # Füge den gesprochenen Text dem Dialogverlauf hinzu
    url = 'http://localhost:11434/api/generate'
    headers = {'Content-Type': 'application/json'}
    data = {
        "model": "llama3",
        "prompt": " ".join(dialog_history)  # Übergebe den gesamten Dialogverlauf als Prompt
    }
    json_data = json.dumps(data)
    
    response = requests.post(url, data=json_data, headers=headers, stream=True)
    full_sentence = ""
    
    if response.status_code == 200:
        try:
            for line in response.iter_lines():
                if line:
                    decoded_line = json.loads(line.decode('utf-8'))
                    response_text = decoded_line.get('response', '')
                    if response_text and response_text.strip():  # Überprüfe ob response_text nicht leer ist
                        full_sentence += response_text
                        # Stelle sicher, dass response_text nicht nur aus Leerzeichen besteht
                        if response_text.strip() and response_text.strip()[-1] in ".!?":
                            print(full_sentence)
                            speak(full_sentence)
                            dialog_history.append(full_sentence)  # Füge die Antwort des LLM dem Dialogverlauf hinzu
                            full_sentence = ""  # Setze für den nächsten Satz zurück
        except json.JSONDecodeError as e:
            print("Fehler beim Parsen der JSON-Antwort:", e)
        except IndexError as e:
            print("IndexError, möglicherweise wegen fehlender Daten:", e)
    else:
        print(f"Error: {response.status_code}, Message: {response.text}")

def speak(text):
    if text:
        tts_engine.say(text)
        tts_engine.runAndWait()

def main():
    while True:
        text = listen()
        if text:
            query_llm(text)

if __name__ == '__main__':
    main()