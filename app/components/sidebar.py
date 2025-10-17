import reflex as rx
from app.states.base import State


def project_list_item(project: dict) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                project["name"],
                class_name="font-semibold text-sm truncate",
                color=rx.cond(
                    State.active_project_id == project["id"], "emerald-700", "gray-700"
                ),
            ),
            rx.el.p(
                f"Created: {project['created_at']}",
                class_name="text-xs",
                color=rx.cond(
                    State.active_project_id == project["id"], "emerald-600", "gray-500"
                ),
            ),
            class_name="flex-1",
        ),
        rx.el.button(
            rx.icon("trash-2", size=14),
            on_click=[lambda: State.delete_project(project["id"]), rx.stop_propagation],
            class_name="p-2 rounded-md text-gray-400 hover:bg-red-100 hover:text-red-600 transition-colors",
        ),
        on_click=lambda: State.set_active_project(project["id"]),
        class_name=rx.cond(
            State.active_project_id == project["id"],
            "flex items-center p-3 rounded-lg cursor-pointer bg-emerald-100 border-l-4 border-emerald-500",
            "flex items-center p-3 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors",
        ),
    )


def sidebar() -> rx.Component:
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.icon("git-fork", class_name="text-emerald-500", size=24),
                rx.el.h1(
                    "Chord Analyzer", class_name="text-xl font-bold text-gray-800"
                ),
                class_name="flex items-center gap-3 p-4 border-b border-gray-200",
            ),
            rx.el.div(
                rx.el.h2(
                    "Projects",
                    class_name="px-4 pt-4 pb-2 text-sm font-semibold text-gray-600 uppercase tracking-wider",
                ),
                rx.el.div(
                    rx.foreach(State.projects, project_list_item),
                    class_name="space-y-2 p-2",
                ),
                class_name="flex-1 overflow-y-auto",
            ),
            rx.el.div(
                rx.el.input(
                    placeholder="New Project Name...",
                    on_change=State.set_new_project_name,
                    class_name="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-400",
                    default_value=State.new_project_name,
                ),
                rx.el.button(
                    "Create Project",
                    rx.icon("plus", size=16, class_name="mr-2"),
                    on_click=State.create_project,
                    class_name="w-full flex items-center justify-center mt-2 px-4 py-2 bg-emerald-500 text-white font-semibold rounded-lg hover:bg-emerald-600 transition-colors shadow-sm",
                ),
                class_name="p-4 border-t border-gray-200 bg-gray-50",
            ),
            class_name="flex flex-col h-full bg-white border-r border-gray-200",
        ),
        class_name="w-80 flex-shrink-0",
    )