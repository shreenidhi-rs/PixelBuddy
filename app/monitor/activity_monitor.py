
import time
from datetime import datetime

import psutil
import win32gui
import win32process

from app.storage.database import save_activity
from app.monitor.session_manager import WorkflowSessionManager
from app.monitor.interruption_manager import InterruptionManager
from app.monitor.resumption_manager import WorkflowResumptionManager
from app.context.workflow_context import describe_activity
from app.context.context_history import ContextHistory
from app.context.task_understanding import describe_task
from app.context.workflow_state import WorkflowState
from app.context.transition_classifier import classify_transition
from app.intelligence.task_ranker import TaskRanker
from app.ui.event_bridge import publish_event


def get_active_window():
    try:
        hwnd = win32gui.GetForegroundWindow()

        if not hwnd:
            return None, None, None

        window_title = win32gui.GetWindowText(hwnd)
        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(process_id)

        return process.name(), window_title, process_id

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess
    ):
        return None, None, None


def print_workflow_state(state, current_time=None):
    details = state.to_dict(current_time)

    print(f"    Context: {details['context']}")
    print(f"    Task type: {details['task_type']}")
    print(
        f"    State duration: "
        f"{details['duration_seconds']:.1f} seconds"
    )
    print(f"    State active: {details['is_active']}")


def get_recommendations(ranker, application=None, limit=3):
    recommendations = ranker.rank_tasks(limit=100)

    if application:
        matching = [
            task for task in recommendations
            if task["application"].casefold()
            == application.casefold()
        ]

        if matching:
            recommendations = matching

    return recommendations[:limit]


def show_task_recommendations(ranker, application=None, limit=3):
    try:
        recommendations = get_recommendations(
            ranker,
            application,
            limit
        )

        print("\n" + "=" * 60)
        print("PIXELBUDDY - TASK RESUMPTION SUGGESTIONS")
        print("=" * 60)

        if not recommendations:
            print("No recorded tasks available yet.")

        for index, task in enumerate(recommendations, start=1):
            print(f"\n{index}. {task['window']}")
            print(f"   Application: {task['application']}")
            print(f"   Task type: {task['task_type']}")
            print(f"   Recommendation score: {task['score']:.4f}")

        publish_event(
            "resumption",
            {
                "application": application,
                "recommendations": recommendations
            }
        )

    except Exception as error:
        print(f"Recommendation unavailable: {error}")


def monitor_activity(stop_event=None):
    previous_activity = None
    activity_start_time = None
    current_workflow_state = None

    previous_context = None
    previous_task_type = None
    previous_application = None

    session_manager = WorkflowSessionManager()
    interruption_manager = InterruptionManager(minimum_duration=10)
    resumption_manager = WorkflowResumptionManager(minimum_duration=10)
    context_history = ContextHistory(max_history=10)
    task_ranker = TaskRanker()

    print("=" * 60)
    print("PIXELBUDDY - ADAPTIVE EDGE AI ACTIVITY MONITOR")
    print("=" * 60)
    print("Tracking workflow activity...")
    print("Press Ctrl+C to stop.\n")

    try:
        while stop_event is None or not stop_event.is_set():
            process_name, window_title, process_id = get_active_window()

            if process_name is None:
                time.sleep(1)
                continue

            current_activity = (process_name, window_title, process_id)
            current_time = datetime.now()

            if previous_activity is None:
                context = describe_activity(process_name, window_title)
                task = describe_task(process_name, window_title)

                current_context = context["category"]
                current_task_type = task["task_type"]

                previous_activity = current_activity
                activity_start_time = current_time
                previous_context = current_context
                previous_task_type = current_task_type
                previous_application = process_name

                current_workflow_state = WorkflowState(
                    application=process_name,
                    window_title=window_title,
                    process_id=process_id,
                    context=current_context,
                    task_type=current_task_type,
                    description=context["description"],
                    start_time=current_time
                )

                context_history.add_context(current_context)
                session_manager.start_session(current_time)

                print(
                    f"[{current_time:%Y-%m-%d %H:%M:%S}] "
                    f"Workflow started -> {process_name}"
                )
                print(f"    Window: {window_title}")
                print_workflow_state(current_workflow_state, current_time)

            elif current_activity != previous_activity:
                duration = (
                    current_time - activity_start_time
                ).total_seconds()

                save_activity(
                    activity_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    previous_activity[0],
                    previous_activity[1],
                    previous_activity[2],
                    duration
                )
                session_manager.add_activity()

                context = describe_activity(process_name, window_title)
                task = describe_task(process_name, window_title)

                current_context = context["category"]
                current_task_type = task["task_type"]

                transition = classify_transition(
                    previous_application,
                    previous_context,
                    previous_task_type,
                    process_name,
                    current_context,
                    current_task_type
                )

                print(
                    f"\n[{current_time:%Y-%m-%d %H:%M:%S}] "
                    f"Activity change -> {process_name}"
                )
                print(f"    Window: {window_title}")
                print(f"    Transition type: {transition}")

                if resumption_manager.previous_context is not None:
                    if current_context == resumption_manager.previous_context:
                        resumption_manager.check_resumption(
                            current_context,
                            current_time
                        )
                    else:
                        resumption_manager.add_interruption_context(
                            current_context
                        )

                elif (
                    previous_context is not None
                    and current_context != previous_context
                ):
                    resumption_manager.start_interruption(
                        previous_context,
                        current_time
                    )
                    resumption_manager.add_interruption_context(
                        current_context
                    )

                if process_name != previous_application:
                    original_application = (
                        interruption_manager.previous_workflow[0]
                        if interruption_manager.previous_workflow is not None
                        else None
                    )

                    returning_to_original = (
                        original_application is not None
                        and process_name == original_application
                    )

                    if returning_to_original:
                        resumed = interruption_manager.check_resumption(
                            current_activity,
                            current_time
                        )

                        if resumed:
                            show_task_recommendations(
                                task_ranker,
                                application=process_name,
                                limit=3
                            )

                    elif original_application is None:
                        interruption_manager.start_interruption(
                            previous_activity,
                            current_activity,
                            current_time
                        )

                    else:
                        interruption_manager.add_interruption_activity(
                            current_activity
                        )

                if transition in ("CONTEXT_CHANGE", "TASK_CHANGE"):
                    if current_workflow_state is not None:
                        current_workflow_state.close(current_time)

                        print("    Previous workflow state closed.")
                        print(
                            f"    Final state duration: "
                            f"{current_workflow_state.get_duration():.1f} seconds"
                        )

                    current_workflow_state = WorkflowState(
                        application=process_name,
                        window_title=window_title,
                        process_id=process_id,
                        context=current_context,
                        task_type=current_task_type,
                        description=context["description"],
                        start_time=current_time
                    )

                    print("    New workflow state created.")

                else:
                    print("    Existing workflow state retained.")

                context_history.add_context(current_context)

                if transition == "CONTEXT_CHANGE":
                    print(
                        f"    Context history: "
                        f"{' -> '.join(context_history.get_history())}"
                    )

                previous_activity = current_activity
                activity_start_time = current_time
                previous_context = current_context
                previous_task_type = current_task_type
                previous_application = process_name

                if current_workflow_state is not None:
                    print_workflow_state(
                        current_workflow_state,
                        current_time
                    )

            if stop_event is not None:
                stop_event.wait(1)
            else:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping activity monitor...")

    finally:
        current_time = datetime.now()

        if previous_activity is not None and activity_start_time is not None:
            duration = (
                current_time - activity_start_time
            ).total_seconds()

            save_activity(
                activity_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                previous_activity[0],
                previous_activity[1],
                previous_activity[2],
                duration
            )

            if current_workflow_state is not None:
                current_workflow_state.close(current_time)

                print(
                    f"Final workflow state duration: "
                    f"{current_workflow_state.get_duration():.1f} seconds"
                )

            session_manager.end_session(current_time)

        print("Activity monitor stopped.")


if __name__ == "__main__":
    monitor_activity()
