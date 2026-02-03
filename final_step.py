import os,sys
import subprocess
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)
def audio_to_video_with_subs(image_path, audio_path, srt_path):
    output = os.path.splitext(audio_path)[0] + "_video.mp4"

    subprocess.run([
    "ffmpeg",
    "-y",
    "-loop", "1",
    "-i", image_path,
    "-i", audio_path,
    "-i", srt_path,
    "-shortest",
    "-vf", "scale=1280:720",   
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-c:s", "mov_text",
    output
    ])


    return output
