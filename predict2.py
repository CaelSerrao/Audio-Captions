import time
import numpy as np
import soundfile as sf
import os
from faster_whisper import WhisperModel
import subprocess
import tempfile


MODEL_SIZE = "medium"
DEVICE = "cpu"
COMPUTE = "int8"
CHUNK_SEC = 0.3


print("Loading model...")
model = WhisperModel(
    MODEL_SIZE,
    device=DEVICE,
    compute_type=COMPUTE
)
print("Model ready.\n")



def generate_srt(audio_file, save_srt=True):

    if audio_file.lower().endswith((".mp4", ".mov", ".mkv", ".avi", ".m4a")):
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        subprocess.run([
            "ffmpeg", "-y", "-i", audio_file, "-ar", "16000", "-ac", "1", temp_wav.name
        ])
    audio_file = temp_wav.name

    base = os.path.splitext(audio_file)[0]
    srt_path = base + ".srt"

    print("Starting transcription...\n")

    captions = []
    index = 1


    try:
        segments, _ = model.transcribe(
            audio_file,          
            beam_size=5,         
            vad_filter=True,
            language="en"
        )

        for seg in segments:
            text = seg.text.strip()
            print(f"[{seg.start:6.2f}s → {seg.end:6.2f}s] {text}")

            captions.append((index, seg.start, seg.end, text))
            index += 1

        if save_srt:
            write_srt(captions, srt_path)
            print(f"\nSaved → {srt_path}")
    finally:
        if temp_wav:
            os.remove(temp_wav.name)

    return srt_path

    

def format_time(t):
    hrs, rem = divmod(t, 3600)
    mins, secs = divmod(rem, 60)
    ms = int((t - int(t)) * 1000)
    return f"{int(hrs):02}:{int(mins):02}:{int(secs):02},{ms:03}"



def write_srt(captions, path):
    with open(path, "w") as f:
        for i, start, end, text in captions:
            f.write(f"{i}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(text + "\n\n")

def mux_subtitles(video_path, srt_path):
    base, ext = os.path.splitext(video_path)
    output_path = base + "_subtitled.mp4"

    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", srt_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-c:s", "mov_text",
        output_path
    ])

    
    if os.path.exists(srt_path):
        os.remove(srt_path)
    return output_path