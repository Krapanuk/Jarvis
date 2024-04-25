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
    if not dialog_history:  # Überprüfe, ob der Dialogverlauf leer ist und füge ggf. die Systemnachricht hinzu
        system_message = {"role": "system", "content": "Du bist mein privater Chatbot-Assistent namens Jarvis. Bitte antworte auf alle meine Eingaben kurz und knapp immer in deutscher Sprache."}
        dialog_history.append(system_message)

    dialog_history.append({"role": "user", "content": text})  # Füge den gesprochenen Text als Benutzer-Nachricht hinzu
    
    url = 'http://localhost:11434/api/chat'
    headers = {'Content-Type': 'application/json'}
    data = {
        "model": "llama3",
        #"model": "phi3",
        "messages": dialog_history,
        "stream": True
    }
    json_data = json.dumps(data)
    
    response = requests.post(url, data=json_data, headers=headers, stream=True)
    full_sentence = ""
    
    if response.status_code == 200:
        try:
            for line in response.iter_lines():
                if line:
                    decoded_line = json.loads(line.decode('utf-8'))
                    if decoded_line.get("done", False):
                        break  # Beende das Lesen von Daten, wenn die finale Nachricht erhalten wurde
                    response_text = decoded_line.get('message', {}).get('content', '')
                    if response_text and response_text.strip():
                        full_sentence += response_text
                        if response_text.strip()[-1] in ".!?":  # Prüfe das Ende eines Satzes
                            print(full_sentence)
                            speak(full_sentence)
                            dialog_history.append({"role": "assistant", "content": full_sentence})  # Füge die Antwort des Assistenten hinzu
                            full_sentence = ""
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