import reflex as rx
from typing import TypedDict, Optional
import datetime
import logging
import random
from pathlib import Path
import json
import os
import librosa
import numpy as np

MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
SUPPORTED_MIME_TYPES = {
    "audio/mpeg": [".mp3"],
    "audio/wav": [".wav"],
    "audio/x-wav": [".wav"],
    "audio/flac": [".flac"],
    "audio/ogg": [".ogg"],
}
WAVEFORM_SAMPLES = 2000


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
    upload_progress: int = 0
    upload_message: str = ""

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
            return rx.toast.error("Project name cannot be empty.", duration=3000)
        new_id = len(self.projects) + 1 if self.projects else 1
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
        return rx.toast.success(
            f"Project '{new_project['name']}' created!", duration=3000
        )

    @rx.event
    def set_active_project(self, project_id: int):
        self.stop_playback()
        self.active_project_id = project_id
        if self.active_project and self.active_project["audio_file_name"]:
            audio_file = self.active_project["audio_file_name"]
            return rx.call_script(f"loadAudio(rx.get_upload_url('{audio_file}'))")

    @rx.event
    def delete_project(self, project_id: int):
        project_to_delete = next(
            (p for p in self.projects if p["id"] == project_id), None
        )
        if project_to_delete and project_to_delete["audio_file_name"]:
            self._cleanup_audio_file(project_to_delete["audio_file_name"])
        self.projects = [p for p in self.projects if p["id"] != project_id]
        if self.active_project_id == project_id:
            self.active_project_id = self.projects[0]["id"] if self.projects else None
            if self.active_project_id:
                return State.set_active_project(self.active_project_id)
        return rx.toast.info("Project deleted.", duration=3000)

    def _cleanup_audio_file(self, filename: Optional[str]):
        if not filename:
            return
        try:
            upload_dir = rx.get_upload_dir()
            file_path = upload_dir / filename
            if file_path.exists():
                os.remove(file_path)
                logging.info(f"Cleaned up old audio file: {filename}")
        except Exception:
            logging.exception(f"Error cleaning up file {filename}")

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        if self.active_project_id is None:
            yield rx.toast.warning("Please select a project first.", duration=3000)
            return
        if not files:
            yield rx.toast.error("No file selected for upload.", duration=3000)
            return
        file = files[0]
        if file.size > MAX_FILE_SIZE_BYTES:
            yield rx.toast.error(
                f"File is too large. Maximum size is {MAX_FILE_SIZE_MB}MB.",
                duration=5000,
            )
            return
        if file.content_type not in SUPPORTED_MIME_TYPES:
            yield rx.toast.error(
                f"Unsupported file type: {file.content_type}. Please upload MP3, WAV, FLAC, or OGG.",
                duration=5000,
            )
            return
        self.is_uploading = True
        self.upload_message = "Uploading file..."
        self.upload_progress = 0
        yield
        old_filename = None
        try:
            project_index = -1
            for i, p in enumerate(self.projects):
                if p["id"] == self.active_project_id:
                    project_index = i
                    break
            if project_index == -1:
                raise Exception("Active project not found.")
            old_filename = self.projects[project_index]["audio_file_name"]
            self._cleanup_audio_file(old_filename)
            upload_data = await file.read()
            upload_dir = rx.get_upload_dir()
            upload_dir.mkdir(parents=True, exist_ok=True)
            unique_name = f"{self.active_project_id}_{datetime.datetime.now().timestamp()}_{file.name}"
            file_path = upload_dir / unique_name
            with file_path.open("wb") as f:
                f.write(upload_data)
            self.upload_message = "Generating waveform..."
            self.upload_progress = 50
            yield
            waveform_data, duration = await self._generate_waveform(file_path)
            self.upload_message = "Finalizing..."
            self.upload_progress = 90
            yield
            self.projects[project_index].update(
                {
                    "audio_file_name": unique_name,
                    "waveform_data": waveform_data,
                    "duration": duration,
                    "tempo": 0.0,
                    "beats": [],
                    "key": None,
                    "chords": [],
                }
            )
            self.upload_progress = 100
            audio_file_name = self.projects[project_index]["audio_file_name"]
            yield rx.call_script(f"loadAudio(rx.get_upload_url('{audio_file_name}'))")
            yield rx.toast.success(
                "Audio uploaded and processed successfully.", duration=3000
            )
        except Exception as e:
            logging.exception(f"Upload and processing failed: {e}")
            yield rx.toast.error(f"Upload failed: {e}", duration=5000)
            if (
                "project_index" in locals()
                and project_index != -1
                and (old_filename is not None)
            ):
                self.projects[project_index]["audio_file_name"] = old_filename
                self.projects[project_index]["waveform_data"] = []
                self.projects[project_index]["duration"] = 0.0
        finally:
            self.is_uploading = False
            self.upload_progress = 0
            self.upload_message = ""

    async def _generate_waveform(self, file_path: Path) -> tuple[list[float], float]:
        """Generates a low-resolution waveform preview using librosa."""
        try:
            loop = self.get_event_loop()
            y, sr = await loop.run_in_executor(None, librosa.load, file_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            if y.ndim > 1 or (
                y.ndim == 1 and y.shape[0] > 0 and isinstance(y[0], np.ndarray)
            ):
                y = librosa.to_mono(y)
            if np.max(np.abs(y)) > 0:
                y = y / np.max(np.abs(y))
            num_samples = WAVEFORM_SAMPLES
            step = len(y) // num_samples if num_samples > 0 else 1
            if step == 0:
                step = 1
            peaks = [
                float(np.max(np.abs(y[i : i + step]))) for i in range(0, len(y), step)
            ]
            return (peaks[:num_samples], duration)
        except Exception as e:
            logging.exception(f"Waveform generation failed for {file_path}: {e}")
            try:
                self._cleanup_audio_file(file_path.name)
            except Exception as cleanup_error:
                logging.exception(
                    f"Failed to cleanup file during waveform error: {cleanup_error}"
                )
            raise IOError(
                f"Failed to process audio. The file may be corrupt or in an unsupported format."
            )

    @rx.event
    def trigger_upload(self, upload_id: str):
        return rx.upload_files(upload_id=upload_id)

    @rx.event
    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        return rx.call_script("togglePlayPause()")

    @rx.event
    def stop_playback(self):
        self.is_playing = False
        self.current_time = 0.0
        return rx.call_script("stopPlayback()")

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
        async with self:
            if self.active_project_id is None or not self.active_project:
                yield rx.toast.error("No active project to analyze.", duration=3000)
                return
            if not self.active_project["audio_file_name"]:
                yield rx.toast.error(
                    "No audio file found for this project.", duration=3000
                )
                return
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
        try:
            from app.services.analysis import run_full_analysis

            upload_dir = rx.get_upload_dir()
            file_path = upload_dir / self.active_project["audio_file_name"]
            analysis_results = await run_full_analysis(file_path)
            async with self:
                if project_index != -1:
                    self.projects[project_index].update(analysis_results)
                yield rx.toast.success(
                    f"Analysis complete! Key: {analysis_results['key']}, Tempo: {analysis_results['tempo']:.1f} BPM",
                    duration=5000,
                )
        except Exception as e:
            logging.exception(f"Analysis failed: {e}")
            async with self:
                yield rx.toast.error(f"Analysis failed: {e}", duration=5000)
        finally:
            async with self:
                self.is_analyzing = False

    @rx.event
    def zoom_in(self):
        self.timeline_zoom = min(self.timeline_zoom * 1.5, 10.0)

    @rx.event
    def zoom_out(self):
        self.timeline_zoom = max(self.timeline_zoom / 1.5, 1.0)

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
            window.remove_chord_analyzer_listeners?.();
            const space_handler = (event) => {
                if (event.code === 'Space' && !(event.target instanceof HTMLInputElement)) {
                    event.preventDefault();
                    window.togglePlayPause();
                }
            };
            document.addEventListener('keydown', space_handler);
            window.remove_chord_analyzer_listeners = () => {
                document.removeEventListener('keydown', space_handler);
            };
        """)