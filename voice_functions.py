from faster_whisper import WhisperModel, BatchedInferencePipeline
import sounddevice as sd
from scipy.io.wavfile import write
import tkinter as tk
import uuid
import numpy as np

model = WhisperModel("small", device="cpu", compute_type="int8")
pipeline = BatchedInferencePipeline(model=model)


def get_text(speech: str):
    segments, info = pipeline.transcribe(
        speech,
        batch_size=8,
        vad_filter=True
    )

    text = " ".join(segment.text.strip() for segment in segments).strip()

    if not text or not info or not info.language:
        print("No voice input")
        return None

    print(text)
    return text


def get_speech():
    root = tk.Tk()
    root.geometry("200x180")
    root.resizable(False, False)

    tk.Label(root, text="Recording is ON", foreground="green").pack()
    root.update()

    audio = sd.rec(
        int(10 * 16000),
        samplerate=16000,
        channels=1,
        dtype="int16"
    )
    sd.wait()
    root.destroy()

    # Ignore recordings that are effectively silent.
    if np.max(np.abs(audio)) < 500:
        print("No voice detected")
        return None

    name = f"{uuid.uuid4().hex}_recording.wav"
    write(name, 16000, audio)
    return name


def getall():
    speech = get_speech()

    if speech is None:
        return None

    return get_text(speech)
