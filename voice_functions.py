
from faster_whisper import WhisperModel, BatchedInferencePipeline
import sounddevice as sd
from scipy.io.wavfile import write
import tkinter as tk
import uuid



def get_text(speech:str):
    model = WhisperModel(
        "small",
        device="cpu",
        compute_type="int8"
    )
    pipeline = BatchedInferencePipeline(model=model)
    segments, info = pipeline.transcribe(
        speech,
        batch_size=8,
        vad_filter=True
    )
    for segment in segments:
        a = segment.text
    print(a)
    return a


def get_speech():
    root = tk.Tk()
    root.geometry("200x180")
    root.resizable(False,False)
    
    tk.Label(root,text="Recording is ON", foreground="green").pack()
    root.update()
    audio = sd.rec(
        int(10 * 16000),
        samplerate=16000,
        channels=1,
        dtype="int16"
    )

    sd.wait()
    name = f"{uuid.uuid4().hex}recording.wav"
    write(name, 16000, audio)
    root.destroy()
    return name


get_text(get_speech())
