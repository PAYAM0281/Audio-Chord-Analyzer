import reflex as rx
from typing import TypedDict, Optional, Any
import datetime
import logging
import wave
import contextlib
import random
from pathlib import Path
import json


class ChordSegment(TypedDict):
    start_time: float
    end_time: float
    label: str
    root: str
    quality: str
    inversion: int
    confidence: float
    notes: list[int]


class Project(TypedDict):
    id: int
    name: str
    created_at: str
    audio_file_name: Optional[str]
    waveform_data: list[float]
    duration: float
    tempo: float
    beats: list[float]
    key: Optional[str]
    chords: list[ChordSegment]


class State(rx.State):
    projects: list[Project] = []
    active_project_id: Optional[int] = None
    new_project_name: str = ""
    is_uploading: bool = False
    is_playing: bool = False
    current_time: float = 0.0
    is_analyzing: bool = False
    timeline_zoom: float = 1.0
    main_audio_volume: float = 0.8
    chord_track_enabled: bool = True
    chord_track_volume: float = 0.5

    @rx.var
    def active_project(self) -> Optional[Project]:
        if self.active_project_id is None:
            return None
        for p in self.projects:
            if p["id"] == self.active_project_id:
                return p
        return None

    @rx.var
    def has_active_project_audio(self) -> bool:
        return (
            self.active_project is not None
            and self.active_project["audio_file_name"] is not None
        )

    @rx.var
    def analysis_complete(self) -> bool:
        return self.active_project is not None and bool(self.active_project["beats"])

    @rx.var
    def chords_detected(self) -> bool:
        return self.active_project is not None and bool(self.active_project["chords"])

    @rx.event
    def load_initial_data(self):
        """Called on mount to load initial data."""
        if not self.projects:
            self.projects = []

    @rx.event
    def set_new_project_name(self, name: str):
        self.new_project_name = name

    @rx.event
    def create_project(self):
        if not self.new_project_name.strip():
            return rx.toast("Project name cannot be empty.", duration=3000)
        new_id = len(self.projects) + 1
        new_project: Project = {
            "id": new_id,
            "name": self.new_project_name,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "audio_file_name": None,
            "waveform_data": [],
            "duration": 0.0,
            "tempo": 0.0,
            "beats": [],
            "key": None,
            "chords": [],
        }
        self.projects.append(new_project)
        self.new_project_name = ""
        self.active_project_id = new_id
        return rx.toast(f"Project '{new_project['name']}' created!", duration=3000)

    @rx.event
    def set_active_project(self, project_id: int):
        self.active_project_id = project_id

    @rx.event
    def delete_project(self, project_id: int):
        self.projects = [p for p in self.projects if p["id"] != project_id]
        if self.active_project_id == project_id:
            self.active_project_id = self.projects[0]["id"] if self.projects else None
        return rx.toast("Project deleted.", duration=3000)

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        if self.active_project_id is None:
            yield rx.toast("Please select a project first.", duration=3000)
            return
        file = files[0]
        self.is_uploading = True
        yield
        try:
            upload_data = await file.read()
            upload_dir = rx.get_upload_dir()
            upload_dir.mkdir(parents=True, exist_ok=True)
            unique_name = f"{self.active_project_id}_{file.name}"
            file_path = upload_dir / unique_name
            with file_path.open("wb") as f:
                f.write(upload_data)
            waveform_data, duration = self._generate_waveform(file_path)
            project_index = -1
            for i, p in enumerate(self.projects):
                if p["id"] == self.active_project_id:
                    project_index = i
                    break
            if project_index != -1:
                self.projects[project_index]["audio_file_name"] = unique_name
                self.projects[project_index]["waveform_data"] = waveform_data
                self.projects[project_index]["duration"] = duration
            yield rx.call_script(f"loadAudio('/upload/{unique_name}')")
            yield rx.toast("Audio uploaded and processed.", duration=3000)
        except Exception as e:
            logging.exception(f"Upload failed: {e}")
            yield rx.toast(f"Upload failed: {e}", duration=5000)
        finally:
            self.is_uploading = False

    def _generate_waveform(self, file_path: Path) -> tuple[list[float], float]:
        """Generates a low-resolution waveform preview."""
        try:
            with contextlib.closing(wave.open(file_path, "r")) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                n_channels = f.getnchannels()
                sampwidth = f.getsampwidth()
                audio_data = f.readframes(frames)
                import numpy as np

                dtype_map = {1: np.int8, 2: np.int16, 4: np.int32}
                if sampwidth not in dtype_map:
                    raise ValueError(f"Unsupported sample width: {sampwidth}")
                data = np.frombuffer(audio_data, dtype=dtype_map[sampwidth])
                if n_channels > 1:
                    data = data.reshape(-1, n_channels).mean(axis=1)
                data = data / np.iinfo(dtype_map[sampwidth]).max
                num_samples = 2000
                step = len(data) // num_samples
                if step == 0:
                    step = 1
                peaks = [
                    float(np.max(data[i : i + step])) for i in range(0, len(data), step)
                ]
                return (peaks, duration)
        except wave.Error as e:
            logging.exception(f"Could not read as WAV, returning dummy waveform: {e}")
            return ([random.uniform(0, 0.5) for _ in range(2000)], 180.0)
        except Exception as e:
            logging.exception(f"Waveform generation failed: {e}")
            return ([], 0.0)

    @rx.event
    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        return rx.call_script("togglePlayPause")

    @rx.event
    def stop_playback(self):
        self.is_playing = False
        self.current_time = 0.0
        return rx.call_script("stopPlayback")

    @rx.event
    def set_current_time(self, time: float):
        self.current_time = time

    @rx.event
    def on_scrub(self, e_target: dict):
        timeline_width = e_target["offsetWidth"]
        click_x = e_target["offsetX"]
        if self.active_project and self.active_project["duration"] > 0:
            new_time = click_x / timeline_width * self.active_project["duration"]
            self.current_time = new_time
            return rx.call_script(f"seekAudio({new_time})")

    @rx.event(background=True)
    async def analyze_audio(self):
        if self.active_project_id is None or not self.active_project:
            yield rx.toast("No active project to analyze.", duration=3000)
            return
        async with self:
            self.is_analyzing = True
            project_index = -1
            for i, p in enumerate(self.projects):
                if p["id"] == self.active_project_id:
                    project_index = i
                    break
            if project_index != -1:
                self.projects[project_index]["tempo"] = 0.0
                self.projects[project_index]["beats"] = []
                self.projects[project_index]["key"] = None
                self.projects[project_index]["chords"] = []
            yield
        try:
            from app.services.analysis import run_full_analysis

            upload_dir = rx.get_upload_dir()
            file_path = upload_dir / self.active_project["audio_file_name"]
            analysis_results = await run_full_analysis(file_path)
            async with self:
                if project_index != -1:
                    self.projects[project_index]["tempo"] = analysis_results["tempo"]
                    self.projects[project_index]["beats"] = analysis_results["beats"]
                    self.projects[project_index]["key"] = analysis_results["key"]
                    self.projects[project_index]["chords"] = analysis_results["chords"]
                yield rx.toast(
                    f"Analysis complete! Key: {analysis_results['key']}, Tempo: {analysis_results['tempo']:.1f} BPM",
                    duration=5000,
                )
        except Exception as e:
            logging.exception(f"Analysis failed: {e}")
            yield rx.toast(f"Analysis failed: {e}", duration=5000)
        finally:
            async with self:
                self.is_analyzing = False

    @rx.event
    def zoom_in(self):
        self.timeline_zoom = min(self.timeline_zoom * 1.5, 10)

    @rx.event
    def zoom_out(self):
        self.timeline_zoom = max(self.timeline_zoom / 1.5, 0.1)

    @rx.event
    def reset_zoom(self):
        self.timeline_zoom = 1.0

    @rx.event
    def on_chord_click(self, chord_index: int):
        if not self.active_project or not self.active_project["chords"]:
            return
        chord = self.active_project["chords"][chord_index]
        return rx.call_script(f"playChord({json.dumps(chord['notes'])}, 1.5)")

    @rx.event
    def set_main_audio_volume(self, volume: float):
        self.main_audio_volume = float(volume)
        return rx.call_script(f"setMainVolume({self.main_audio_volume})")

    @rx.event
    def set_chord_track_volume(self, volume: float):
        self.chord_track_volume = float(volume)
        return rx.call_script(f"setChordTrackVolume({self.chord_track_volume})")

    @rx.event
    def toggle_chord_track(self):
        self.chord_track_enabled = not self.chord_track_enabled
        return rx.call_script(
            f"toggleChordTrack({str(self.chord_track_enabled).lower()})"
        )

    @rx.event
    def add_keyboard_shortcuts(self):
        return rx.call_script("""
            document.addEventListener('keydown', (event) => {
                if (event.code === 'Space') {
                    event.preventDefault();
                    window.togglePlayPause();
                } else if (event.code === 'KeyM') {
                    event.preventDefault();
                    const chordTrackEnabled = document.querySelector('input[type=range][class*="accent-emerald-500"]').previousElementSibling.querySelector('i').className.includes('volume-2');
                    window.toggleChordTrack(!chordTrackEnabled);
                }
            });
            """)