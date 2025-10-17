import reflex as rx
from app.states.base import State, SUPPORTED_MIME_TYPES, MAX_FILE_SIZE_BYTES


def transport_controls() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("play", size=20),
            on_click=State.toggle_play_pause,
            class_name=rx.cond(
                State.is_playing,
                "hidden",
                "p-3 bg-emerald-500 text-white rounded-full shadow-lg hover:bg-emerald-600 transition-all disabled:opacity-50",
            ),
            disabled=~State.has_active_project_audio,
        ),
        rx.el.button(
            rx.icon("pause", size=20),
            on_click=State.toggle_play_pause,
            class_name=rx.cond(
                State.is_playing,
                "p-3 bg-emerald-500 text-white rounded-full shadow-lg hover:bg-emerald-600 transition-all",
                "hidden",
            ),
        ),
        rx.el.button(
            rx.icon("square", size=20),
            on_click=State.stop_playback,
            class_name="p-3 bg-gray-600 text-white rounded-full shadow-lg hover:bg-gray-700 transition-all disabled:opacity-50",
            disabled=~State.has_active_project_audio,
        ),
        rx.el.div(
            rx.text(
                f"{State.current_time.to_string()}s",
                class_name="text-sm font-mono text-gray-600",
            ),
            class_name="px-4 py-2 bg-white rounded-lg border border-gray-200 shadow-sm",
        ),
        class_name="flex items-center gap-4",
    )


def volume_controls() -> rx.Component:
    """Volume sliders for main audio and chord track."""
    return rx.el.div(
        rx.el.div(
            rx.icon("volume-2", size=18, class_name="text-gray-500"),
            rx.el.input(
                type="range",
                min=0,
                max=1,
                step=0.05,
                key=f"main-volume-{State.active_project_id}",
                default_value=State.main_audio_volume.to_string(),
                on_change=State.set_main_audio_volume.throttle(50),
                class_name="w-24 accent-emerald-500 cursor-pointer",
                disabled=~State.has_active_project_audio,
            ),
            class_name="flex items-center gap-2 p-2 bg-white rounded-lg border border-gray-200",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon(
                    rx.cond(State.chord_track_enabled, "volume-2", "volume-x"),
                    size=18,
                    class_name="text-gray-500",
                ),
                on_click=State.toggle_chord_track,
                disabled=~State.chords_detected,
            ),
            rx.el.input(
                type="range",
                min=0,
                max=1,
                step=0.05,
                key=f"chord-volume-{State.active_project_id}",
                default_value=State.chord_track_volume.to_string(),
                on_change=State.set_chord_track_volume.throttle(50),
                class_name="w-24 accent-emerald-500 cursor-pointer",
                disabled=~State.chords_detected,
            ),
            class_name="flex items-center gap-2 p-2 bg-white rounded-lg border border-gray-200",
        ),
        class_name="flex items-center gap-4",
    )


def beat_grid() -> rx.Component:
    return rx.foreach(
        State.active_project.beats,
        lambda beat_time: rx.el.div(
            style={
                "position": "absolute",
                "left": f"{beat_time / State.active_project.duration * 100}%",
                "top": "0",
                "bottom": "0",
                "width": "1px",
                "background_color": "rgba(0, 0, 0, 0.2)",
            }
        ),
    )


def waveform_display() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.svg(
                rx.foreach(
                    State.active_project.waveform_data,
                    lambda peak, index: rx.el.rect(
                        x=f"{index / 2000 * 100}%",
                        y=f"{(1 - peak) * 50}%",
                        width=f"{1 / 2000 * 100 * 0.8}%",
                        height=f"{peak * 100}%",
                        fill="#34d399",
                    ),
                ),
                view_box="0 0 100 100",
                width="100%",
                height="128px",
                preserve_aspect_ratio="none",
                class_name="bg-gray-100 rounded-lg",
            ),
            rx.cond(State.analysis_complete, beat_grid(), rx.fragment()),
            rx.el.div(
                style={
                    "position": "absolute",
                    "left": f"{State.current_time / State.active_project.duration.to(float) * 100}%",
                    "top": "0",
                    "bottom": "0",
                    "width": "2px",
                    "background_color": "#ef4444",
                    "pointer_events": "none",
                },
                class_name=rx.cond(
                    State.has_active_project_audio
                    & (State.active_project.duration > 0),
                    "block",
                    "hidden",
                ),
            ),
            rx.el.div(
                rx.foreach(State.active_project.chords, chord_chip),
                class_name="absolute top-0 left-0 w-full h-[128px]",
                style={"pointer_events": "none"},
            ),
            style={
                "position": "relative",
                "width": f"{State.timeline_zoom * 100}%",
                "transition": "width 0.2s ease-in-out",
            },
            on_click=lambda e: State.on_scrub(e.target),
            class_name="relative cursor-pointer h-[128px]",
        ),
        class_name="w-full overflow-x-auto border border-gray-200 rounded-lg bg-gray-50",
    )


def upload_placeholder() -> rx.Component:
    return rx.el.div(
        rx.upload.root(
            rx.el.div(
                rx.icon("cloud-upload", size=48, class_name="text-gray-400"),
                rx.el.h3(
                    "Upload Audio File",
                    class_name="mt-4 text-lg font-semibold text-gray-700",
                ),
                rx.el.p(
                    "Drag & drop or click to select a file",
                    class_name="mt-1 text-sm text-gray-500",
                ),
                rx.el.p(
                    "(MP3, WAV, FLAC, OGG)", class_name="mt-1 text-xs text-gray-400"
                ),
                class_name="text-center flex flex-col items-center justify-center w-full h-64",
            ),
            class_name="flex items-center justify-center w-full h-full border-2 border-dashed border-gray-300 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer",
            id="audio-upload",
            on_drop=State.handle_upload(rx.upload_files()),
            multiple=False,
            accept=SUPPORTED_MIME_TYPES,
            max_size=MAX_FILE_SIZE_BYTES,
            disabled=State.is_uploading | State.active_project_id.is_none(),
        ),
        rx.el.div(
            rx.foreach(
                rx.selected_files("audio-upload"),
                lambda file: rx.el.div(
                    rx.icon("music-4", size=16),
                    rx.el.p(file, class_name="text-sm truncate"),
                    class_name="flex items-center gap-2 p-2 bg-emerald-50 rounded-md border border-emerald-200 text-emerald-800",
                ),
            ),
            class_name="mt-4",
        ),
        rx.el.button(
            "Upload and Process",
            on_click=State.trigger_upload("audio-upload"),
            disabled=State.is_uploading,
            class_name="mt-4 w-full px-4 py-3 bg-emerald-500 text-white font-semibold rounded-lg hover:bg-emerald-600 transition-colors shadow-sm disabled:bg-gray-400",
        ),
        class_name="w-full h-96 p-4 flex flex-col items-center justify-center",
    )


def chord_chip(chord: dict, index: int) -> rx.Component:
    """A component to display a single chord chip on the timeline."""
    return rx.tooltip(
        rx.el.div(
            rx.el.span(
                chord["label"],
                class_name="text-xs font-bold text-white whitespace-nowrap truncate",
            ),
            style={
                "position": "absolute",
                "left": f"{chord['start_time'] / State.active_project.duration * 100}%",
                "width": f"{(chord['end_time'] - chord['start_time']) / State.active_project.duration * 100}%",
                "top": "8px",
                "min_width": "40px",
                "z_index": "10",
                "pointer_events": "auto",
            },
            class_name="h-[32px] px-2 py-1 bg-emerald-500 rounded-md shadow-sm flex items-center justify-center overflow-hidden hover:bg-emerald-600 hover:shadow-lg hover:scale-105 transition-all duration-150 cursor-pointer border-l-2 border-emerald-300",
            on_click=lambda: State.on_chord_click(index),
        ),
        f"Confidence: {(chord['confidence'] * 100).to_string()}% | Notes: {chord['notes'].to_string()}",
    )


def loading_overlay() -> rx.Component:
    return rx.el.div(
        rx.spinner(class_name="text-emerald-500", size="3"),
        rx.el.p(
            rx.cond(
                State.is_uploading,
                State.upload_message,
                "Analyzing chords, key, & tempo...",
            ),
            class_name="mt-4 text-gray-600 font-medium",
        ),
        rx.cond(
            State.is_uploading,
            rx.el.progress(
                value=State.upload_progress,
                class_name="w-1/2 mt-4 [&::-webkit-progress-bar]:rounded-lg [&::-webkit-progress-value]:rounded-lg [&::-webkit-progress-bar]:bg-slate-300 [&::-webkit-progress-value]:bg-emerald-500 [&::-moz-progress-bar]:bg-emerald-500",
            ),
            rx.fragment(),
        ),
        class_name="absolute inset-0 flex flex-col items-center justify-center bg-gray-50/80 backdrop-blur-sm z-20 rounded-xl",
    )


def main_content() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.match(
                State.active_project_id,
                (
                    None,
                    rx.el.div(
                        rx.icon("folder-search", size=48, class_name="text-gray-400"),
                        rx.el.h2(
                            "No Project Selected",
                            class_name="mt-4 text-2xl font-bold text-gray-700",
                        ),
                        rx.el.p(
                            "Create or select a project from the sidebar to begin.",
                            class_name="mt-2 text-gray-500",
                        ),
                        class_name="flex flex-col items-center justify-center h-full text-center",
                    ),
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.h2(
                            State.active_project.name,
                            class_name="text-2xl font-bold text-gray-800",
                        ),
                        rx.el.div(
                            transport_controls(),
                            volume_controls(),
                            class_name="flex items-center gap-6",
                        ),
                        class_name="flex justify-between items-center mb-6",
                    ),
                    rx.el.div(
                        rx.cond(
                            State.has_active_project_audio,
                            rx.el.div(
                                rx.cond(
                                    State.analysis_complete,
                                    rx.el.div(
                                        rx.el.div(
                                            rx.el.p(
                                                "Tempo",
                                                class_name="text-xs text-gray-500",
                                            ),
                                            rx.el.p(
                                                f"{State.active_project.tempo.to_string()} BPM",
                                                class_name="font-bold text-lg text-emerald-600",
                                            ),
                                            class_name="text-center p-2 bg-white rounded-lg border border-gray-200",
                                        ),
                                        rx.cond(
                                            State.chords_detected,
                                            rx.el.div(
                                                rx.el.p(
                                                    "Key",
                                                    class_name="text-xs text-gray-500",
                                                ),
                                                rx.el.p(
                                                    State.active_project.key,
                                                    class_name="font-bold text-lg text-emerald-600",
                                                ),
                                                class_name="text-center p-2 bg-white rounded-lg border border-gray-200",
                                            ),
                                            rx.fragment(),
                                        ),
                                        rx.el.div(
                                            rx.el.button(
                                                rx.icon("zoom-in"),
                                                on_click=State.zoom_in,
                                                class_name="p-2 bg-gray-200 rounded-md hover:bg-gray-300",
                                            ),
                                            rx.el.button(
                                                rx.icon("zoom-out"),
                                                on_click=State.zoom_out,
                                                class_name="p-2 bg-gray-200 rounded-md hover:bg-gray-300",
                                            ),
                                            rx.el.button(
                                                rx.icon("search"),
                                                on_click=State.reset_zoom,
                                                class_name="p-2 bg-gray-200 rounded-md hover:bg-gray-300",
                                            ),
                                            class_name="flex items-center gap-2",
                                        ),
                                        class_name="flex justify-between items-center mb-4",
                                    ),
                                    rx.el.button(
                                        "Analyze Audio",
                                        rx.icon("bar-chart-2", class_name="mr-2"),
                                        on_click=State.analyze_audio,
                                        class_name="mb-4 w-full flex items-center justify-center px-4 py-3 bg-emerald-500 text-white font-semibold rounded-lg hover:bg-emerald-600 transition-colors shadow-sm",
                                    ),
                                ),
                                waveform_display(),
                                class_name="w-full",
                            ),
                            upload_placeholder(),
                        ),
                        rx.cond(
                            State.is_uploading | State.is_analyzing,
                            loading_overlay(),
                            rx.fragment(),
                        ),
                        class_name="relative",
                    ),
                    class_name="w-full",
                ),
            ),
            class_name="p-8 h-full flex flex-col",
        )
    )