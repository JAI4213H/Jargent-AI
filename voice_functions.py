from faster_whisper import WhisperModel, BatchedInferencePipeline
import sounddevice as sd
from scipy.io.wavfile import write
import uuid
import numpy as np
import re
import wave
from pathlib import Path
from piper import PiperVoice

model = WhisperModel("small", device="cpu", compute_type="int8")
pipeline = BatchedInferencePipeline(model=model)


def get_text(speech: str):
    segments, info = pipeline.transcribe(
        speech,
        batch_size=8,
        vad_filter=True,
        language="en",
        task="transcribe"
    )

    text = " ".join(segment.text.strip() for segment in segments).strip()

    if not text or not info or not info.language:
        print("No voice input")
        return None

    print(text)
    return text


def wait_for_wake_word():
    print("Waiting for 'Jargent'...")
    sample_rate = 16000
    chunk_size = sample_rate

    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
        blocksize=chunk_size
    ) as stream:
        while True:
            chunk, _ = stream.read(chunk_size)
            audio = chunk[:, 0].astype(np.float32) / 32768
            segments, _ = pipeline.transcribe(
                audio,
                language="en",
                beam_size=1,
                vad_filter=True
            )
            text = " ".join(segment.text for segment in segments).lower()

            if "jargent" in text:
                return


def get_speech():
    sample_rate = 16000
    chunk_size = int(sample_rate * 0.1)
    silence_limit = 0.8
    max_duration = 15
    frames = []
    speaking = False
    silent_time = 0

    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
        blocksize=chunk_size
    ) as stream:
        for _ in range(int(max_duration / 0.1)):
            chunk, _ = stream.read(chunk_size)
            frames.append(chunk.copy())

            if np.max(np.abs(chunk)) >= 500:
                speaking = True
                silent_time = 0
            elif speaking:
                silent_time += 0.1
                if silent_time >= silence_limit:
                    break

    if not speaking:
        print("No voice detected")
        return None

    audio = np.concatenate(frames)
    folder = Path("voice_notes")
    folder.mkdir(exist_ok=True)
    name = folder / f"{uuid.uuid4().hex}_recording.wav"
    write(name, sample_rate, audio)
    return str(name)


def getall():
    speech = get_speech()

    if speech is None:
        return None

    return get_text(speech)



def clean_for_speech(text: str):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(
        r"[A-Za-z]:\\(?:[^\\\n]+\\)*([^\\\n]+)",
        r"\1",
        text
    )
    text = re.sub(
        r"\b[\w.-]+\.(xlsx|xlsm|csv|pdf|docx|pptx)\b",
        "",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(r"[*_#\"“”]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def tovoice(output: str):
    voice = PiperVoice.load("en_US-lessac-medium.onnx")
    output = clean_for_speech(output)

    name = f"{uuid.uuid4().hex}.wav"
    with wave.open(name, "wb") as wav_file:
        voice.synthesize_wav(output, wav_file)

    with wave.open(name,"rb") as audio_file:
        frames = audio_file.getnframes()
        sample_rate = audio_file.getframerate()
        audio = np.frombuffer(
            audio_file.readframes(frames),
            dtype=np.int16
        )
    print("[+]Speech generated!")
    sd.play(audio, sample_rate)
    sd.wait()
    
    return name
    
