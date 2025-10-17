import numpy as np
from scipy.spatial.distance import cosine
import librosa

PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
KEY_PROFILES = {
    "C Major": [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88],
    "C# Major": [
        2.88,
        6.35,
        2.23,
        3.48,
        2.33,
        4.38,
        4.09,
        2.52,
        5.19,
        2.39,
        3.66,
        2.29,
    ],
    "D Major": [2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66],
    "D# Major": [
        3.66,
        2.29,
        2.88,
        6.35,
        2.23,
        3.48,
        2.33,
        4.38,
        4.09,
        2.52,
        5.19,
        2.39,
    ],
    "E Major": [2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19],
    "F Major": [5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52],
    "F# Major": [
        2.52,
        5.19,
        2.39,
        3.66,
        2.29,
        2.88,
        6.35,
        2.23,
        3.48,
        2.33,
        4.38,
        4.09,
    ],
    "G Major": [4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38],
    "G# Major": [
        4.38,
        4.09,
        2.52,
        5.19,
        2.39,
        3.66,
        2.29,
        2.88,
        6.35,
        2.23,
        3.48,
        2.33,
    ],
    "A Major": [2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48],
    "A# Major": [
        3.48,
        2.33,
        4.38,
        4.09,
        2.52,
        5.19,
        2.39,
        3.66,
        2.29,
        2.88,
        6.35,
        2.23,
    ],
    "B Major": [2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35],
    "C Minor": [6.33, 2.68, 3.52, 5.38, 2.6, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17],
    "C# Minor": [3.17, 6.33, 2.68, 3.52, 5.38, 2.6, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34],
    "D Minor": [3.34, 3.17, 6.33, 2.68, 3.52, 5.38, 2.6, 3.53, 2.54, 4.75, 3.98, 2.69],
    "D# Minor": [2.69, 3.34, 3.17, 6.33, 2.68, 3.52, 5.38, 2.6, 3.53, 2.54, 4.75, 3.98],
    "E Minor": [3.98, 2.69, 3.34, 3.17, 6.33, 2.68, 3.52, 5.38, 2.6, 3.53, 2.54, 4.75],
    "F Minor": [4.75, 3.98, 2.69, 3.34, 3.17, 6.33, 2.68, 3.52, 5.38, 2.6, 3.53, 2.54],
    "F# Minor": [2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.33, 2.68, 3.52, 5.38, 2.6, 3.53],
    "G Minor": [3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.33, 2.68, 3.52, 5.38, 2.6],
    "G# Minor": [2.6, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.33, 2.68, 3.52, 5.38],
    "A Minor": [5.38, 2.6, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.33, 2.68, 3.52],
    "A# Minor": [3.52, 5.38, 2.6, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.33, 2.68],
    "B Minor": [2.68, 3.52, 5.38, 2.6, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.33],
}
CHORD_TEMPLATES = {}
CHORD_MIDI_INTERVALS = {}


def _generate_chord_templates():
    qualities = {
        "maj": [0, 4, 7],
        "min": [0, 3, 7],
        "dim": [0, 3, 6],
        "aug": [0, 4, 8],
        "sus2": [0, 2, 7],
        "sus4": [0, 5, 7],
        "maj7": [0, 4, 7, 11],
        "min7": [0, 3, 7, 10],
        "dom7": [0, 4, 7, 10],
        "dim7": [0, 3, 6, 9],
        "add9": [0, 2, 4, 7],
    }
    for root_idx, root_name in enumerate(PITCH_CLASSES):
        for quality, intervals in qualities.items():
            label = f"{root_name}:{quality}"
            template = np.zeros(12)
            midi_notes = []
            for interval in intervals:
                pitch_class_idx = (root_idx + interval) % 12
                template[pitch_class_idx] = 1
                midi_notes.append(60 + root_idx + interval)
            CHORD_TEMPLATES[label] = template / np.linalg.norm(template)
            CHORD_MIDI_INTERVALS[label] = intervals


_generate_chord_templates()


def detect_key(chroma: np.ndarray) -> str:
    chroma_mean = np.mean(chroma, axis=1)
    best_key = ""
    max_corr = -1
    for key, profile in KEY_PROFILES.items():
        corr = 1 - cosine(chroma_mean, np.array(profile))
        if corr > max_corr:
            max_corr = corr
            best_key = key
    return best_key


def recognize_chords(chroma: np.ndarray, beat_times: np.ndarray, sr: int) -> list[dict]:
    frames_per_beat = (
        len(chroma[0])
        * (beat_times[1] - beat_times[0])
        / (
            len(chroma[0])
            * librosa.frames_to_time(1, sr=sr, n_fft=2048, hop_length=512)
        )
    )
    hop_length = 512
    beat_frames = librosa.time_to_frames(beat_times, sr=sr, hop_length=hop_length)
    beat_frames = np.concatenate(([0], beat_frames, [chroma.shape[1] - 1]))
    chord_labels = list(CHORD_TEMPLATES.keys())
    num_chords = len(chord_labels)
    log_prob = np.zeros((num_chords, len(beat_frames) - 1))
    for i in range(len(beat_frames) - 1):
        start, end = (beat_frames[i], beat_frames[i + 1])
        if start >= end:
            continue
        chroma_segment = np.mean(chroma[:, start:end], axis=1)
        for j, label in enumerate(chord_labels):
            template = CHORD_TEMPLATES[label]
            log_prob[j, i] = -cosine(chroma_segment, template)
    trans_prob = np.full((num_chords, num_chords), -1.0)
    np.fill_diagonal(trans_prob, 0.0)
    path = np.zeros(len(beat_frames) - 1, dtype=int)
    path[0] = np.argmax(log_prob[:, 0])
    for i in range(1, len(beat_frames) - 1):
        path[i] = np.argmax(log_prob[:, i] + trans_prob[path[i - 1], :])
    chords = []
    for i in range(len(path)):
        start_time = beat_times[i] if i < len(beat_times) else beat_times[-1]
        end_time = (
            beat_times[i + 1]
            if i + 1 < len(beat_times)
            else librosa.frames_to_time(chroma.shape[1], sr=sr, hop_length=hop_length)
        )
        if end_time <= start_time:
            continue
        label = chord_labels[path[i]]
        root, quality = label.split(":")
        confidence = 1 + log_prob[path[i], i]
        inversion = 0
        base_midi = 60 + PITCH_CLASSES.index(root)
        notes = [base_midi + interval for interval in CHORD_MIDI_INTERVALS[label]]
        chords.append(
            {
                "start_time": start_time,
                "end_time": end_time,
                "label": label.replace(":", " "),
                "root": root,
                "quality": quality,
                "inversion": inversion,
                "confidence": max(0, min(1, confidence)),
                "notes": notes,
            }
        )
    if not chords:
        return []
    merged_chords = [chords[0]]
    for i in range(1, len(chords)):
        if chords[i]["label"] == merged_chords[-1]["label"]:
            merged_chords[-1]["end_time"] = chords[i]["end_time"]
        else:
            merged_chords.append(chords[i])
    return merged_chords