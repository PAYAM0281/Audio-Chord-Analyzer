import reflex as rx
from app.states.base import State
from app.components.sidebar import sidebar
from app.components.main_content import main_content


def index() -> rx.Component:
    """The main view of the app."""
    return rx.el.main(
        rx.el.div(sidebar(), main_content(), class_name="flex h-screen bg-gray-50"),
        class_name="font-['Montserrat'] bg-white",
        on_mount=[State.load_initial_data, State.add_keyboard_shortcuts],
        on_mouse_up=rx.call_script(
            "() => { window.removeEventListener('mousemove', window.scrub_move); window.scrub_move = null; }"
        ),
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
        rx.el.script(src="/js/audio_player.js"),
    ],
)
app.add_page(index, title="Chord Analyzer")