import os
import json
import datetime
import requests
import pyttsx3
import pyaudio
from vosk import Model, KaldiRecognizer

# ====== НАСТРОЙКИ ======
MODEL_PATH = "model_small"  # Папка с вашей моделью Vosk
RATE = 16000                               # Частота дискретизации
CHUNK = 8000                               # Размер буфера для чтения микрофона
GRAMMAR = ["закрыть", "выход", "создать", "имя", "страна", "анкета", "сохранить"]  # Разрешённые команды

# ====== ПРОВЕРКА НАЛИЧИЯ МОДЕЛИ ======
if not os.path.isdir(MODEL_PATH):
    print(f"Ошибка: папка модели не найдена по пути: {MODEL_PATH}")
    print("Скачайте и распакуйте модель Vosk и укажите правильный путь в MODEL_PATH.")
    exit(1)

# ====== ИНИЦИАЛИЗАЦИЯ TTS ======
engine = pyttsx3.init()
voices = engine.getProperty('voices')
if voices:
    engine.setProperty('voice', voices[0].id)

def speak(text: str):
    """Озвучить текст и вывести в консоль."""
    print(f"Ассистент: {text}")
    engine.say(text)
    engine.runAndWait()

# ====== ФУНКЦИЯ РАСПОЗНАВАНИЯ С ГРАММАТИКОЙ ======
def recognize_speech() -> str:
    """
    Слушает микрофон и возвращает распознанную команду из списка GRAMMAR.
    """
    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, RATE, json.dumps(GRAMMAR))

    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=RATE,
                     input=True,
                     frames_per_buffer=CHUNK)
    stream.start_stream()
    speak("Слушаю команду...")

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            cmd = result.get("text", "").strip().lower()
            if cmd:
                return cmd

# ====== ПОЛЬЗОВАТЕЛЬСКАЯ ЛОГИКА ======
current_user = None

def fetch_user():
    global current_user
    try:
        resp = requests.get("https://randomuser.me/api/", timeout=10)
        resp.raise_for_status()
        current_user = resp.json()["results"][0]
        speak("Пользователь создан.")
    except Exception as e:
        speak("Ошибка при создании пользователя.")
        print("Request error:", e)


def say_name():
    if not current_user:
        speak("Сначала создайте пользователя.")
        return
    n = current_user["name"]
    speak(f"{n['title']} {n['first']} {n['last']}")


def say_country():
    if not current_user:
        speak("Сначала создайте пользователя.")
        return
    speak(current_user["location"]["country"])


def say_profile():
    if not current_user:
        speak("Сначала создайте пользователя.")
        return
    n = current_user["name"]
    age = current_user["dob"]["age"]
    email = current_user["email"]
    city = current_user["location"]["city"]
    country = current_user["location"]["country"]
    text = f"{n['title']} {n['first']} {n['last']}, {age} лет, email {email}, город {city}, страна {country}"
    speak(text)


def save_picture():
    if not current_user:
        speak("Сначала создайте пользователя.")
        return
    try:
        url = current_user["picture"]["large"]
        ext = os.path.splitext(url)[-1] or ".jpg"
        filename = f"user_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        img = requests.get(url, timeout=10)
        img.raise_for_status()
        with open(filename, "wb") as f:
            f.write(img.content)
        speak("Фотография сохранена.")
        print(f"Сохранено как {filename}")
    except Exception as e:
        speak("Не удалось сохранить фотографию.")
        print("Save error:", e)

# ====== ГЛАВНЫЙ ЦИКЛ ======
def main():
    speak("Голосовой ассистент готов.")
    while True:
        try:
            cmd = recognize_speech()
            print(f"Команда: {cmd}")

            if "закрыть" in cmd or "выход" in cmd:
                speak("До встречи.")
                break
            elif "создать" in cmd:
                fetch_user()
            elif "имя" in cmd:
                say_name()
            elif "страна" in cmd:
                say_country()
            elif "анкета" in cmd:
                say_profile()
            elif "сохранить" in cmd:
                save_picture()
            else:
                speak("Команда не распознана.")
        except Exception as e:
            print("Ошибка в основном цикле:", e)
            speak("Произошла ошибка. Повторите команду.")


if __name__ == "__main__":
    main()
