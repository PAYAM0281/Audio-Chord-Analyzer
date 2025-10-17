import asyncio
import librosa
import numpy as np
from pathlib import Path
from . import chord_recognition


async def run_full_analysis(file_path: Path) -> dict:
    """Run full analysis (beats, key, chords) on an audio file."""
    loop = asyncio.get_running_loop()
    y, sr = await loop.run_in_executor(None, librosa.load, file_path, sr=22050)
    tempo, beat_frames = await loop.run_in_executor(
        None, librosa.beat.beat_track, y, sr
    )
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    chroma = await loop.run_in_executor(None, librosa.feature.chroma_cqt, y, sr)
    key = await loop.run_in_executor(None, chord_recognition.detect_key, chroma)
    chords = await loop.run_in_executor(
        None, chord_recognition.recognize_chords, chroma, beat_times, sr
    )
    return {
        "tempo": tempo,
        "beats": beat_times.tolist(),
        "key": key,
        "chords": chords,
        "duration": librosa.get_duration(y=y, sr=sr),
    }