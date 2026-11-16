
"""
PixelBuddy Desktop Companion

Live activity monitoring and resumption notifications.
"""

import threading
import tkinter as tk
from tkinter import messagebox

from app.intelligence.task_ranker import TaskRanker
from app.monitor.activity_monitor import monitor_activity
from app.storage.database import initialize_database
from app.ui.event_bridge import read_event, clear_event


class PixelBuddyWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("PixelBuddy - Adaptive Edge AI Companion")
        self.root.geometry("700x680")
        self.root.minsize(580, 520)

        self.background = "#141821"
        self.surface = "#202633"
        self.text_color = "#F4F6FA"
        self.muted_color = "#AAB5C5"
        self.accent = "#8B9CFF"

        self.root.configure(bg=self.background)

        self.ranker = TaskRanker()
        self.stop_event = None
        self.monitor_thread = None
        self.last_event_timestamp = None

        clear_event()

        self.build_interface()
        self.refresh_recommendations()
        self.check_events()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_interface(self):
        header = tk.Frame(self.root, bg=self.background)
        header.pack(fill="x", padx=24, pady=(24, 12))

        tk.Label(
            header,
            text="PixelBuddy",
            font=("Segoe UI", 26, "bold"),
            fg=self.text_color,
            bg=self.background
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Your Adaptive Edge AI Desktop Companion",
            font=("Segoe UI", 11),
            fg=self.muted_color,
            bg=self.background
        ).pack(anchor="w", pady=(4, 0))

        self.status_label = tk.Label(
            self.root,
            text="● Monitoring stopped",
            font=("Segoe UI", 11, "bold"),
            fg="#F59E9E",
            bg=self.background
        )
        self.status_label.pack(anchor="w", padx=24, pady=12)

        controls = tk.Frame(self.root, bg=self.background)
        controls.pack(fill="x", padx=24, pady=(0, 16))

        self.monitor_button = tk.Button(
            controls,
            text="Start Monitoring",
            command=self.toggle_monitor,
            bg=self.accent,
            fg="#10131A",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=10
        )
        self.monitor_button.pack(side="left")

        tk.Button(
            controls,
            text="Refresh Recommendations",
            command=self.refresh_recommendations,
            bg=self.surface,
            fg=self.text_color,
            relief="flat",
            font=("Segoe UI", 10),
            padx=12,
            pady=10
        ).pack(side="left", padx=10)

        self.alert_frame = tk.Frame(
            self.root,
            bg="#29354A",
            padx=16,
            pady=14
        )

        self.alert_title = tk.Label(
            self.alert_frame,
            text="Welcome back!",
            font=("Segoe UI", 15, "bold"),
            fg=self.text_color,
            bg="#29354A"
        )
        self.alert_title.pack(anchor="w")

        self.alert_message = tk.Label(
            self.alert_frame,
            text="",
            font=("Segoe UI", 10),
            fg=self.muted_color,
            bg="#29354A",
            wraplength=580,
            justify="left"
        )
        self.alert_message.pack(anchor="w", pady=8)

        tk.Button(
            self.alert_frame,
            text="Dismiss",
            command=self.dismiss_alert,
            bg=self.accent,
            fg="#10131A",
            relief="flat",
            padx=12,
            pady=6
        ).pack(anchor="w")

        tk.Label(
            self.root,
            text="Suggested Tasks",
            font=("Segoe UI", 16, "bold"),
            fg=self.text_color,
            bg=self.background
        ).pack(anchor="w", padx=24, pady=(10, 8))

        self.recommendation_frame = tk.Frame(
            self.root,
            bg=self.background
        )
        self.recommendation_frame.pack(
            fill="both",
            expand=True,
            padx=24,
            pady=(0, 12)
        )

        tk.Label(
            self.root,
            text="All recommendations are generated locally.",
            font=("Segoe UI", 9),
            fg=self.muted_color,
            bg=self.background
        ).pack(anchor="w", padx=24, pady=(0, 20))

    def refresh_recommendations(self):
        try:
            recommendations = self.ranker.rank_tasks(limit=3)
            self.render_recommendations(recommendations)
        except Exception as error:
            messagebox.showerror("PixelBuddy", str(error))

    def render_recommendations(self, recommendations):
        for widget in self.recommendation_frame.winfo_children():
            widget.destroy()

        if not recommendations:
            tk.Label(
                self.recommendation_frame,
                text="No recorded tasks available yet.",
                fg=self.muted_color,
                bg=self.background
            ).pack(anchor="w", pady=12)
            return

        for index, task in enumerate(recommendations, start=1):
            card = tk.Frame(
                self.recommendation_frame,
                bg=self.surface,
                padx=14,
                pady=12
            )
            card.pack(fill="x", pady=5)

            tk.Label(
                card,
                text=f"{index}. {task['window']}",
                font=("Segoe UI", 11, "bold"),
                fg=self.text_color,
                bg=self.surface,
                anchor="w",
                wraplength=570,
                justify="left"
            ).pack(fill="x")

            tk.Label(
                card,
                text=f"{task['application']} | {task['task_type']}",
                font=("Segoe UI", 9),
                fg=self.muted_color,
                bg=self.surface,
                anchor="w"
            ).pack(fill="x", pady=(5, 2))

            tk.Label(
                card,
                text=f"Score: {task['score']:.4f}",
                font=("Segoe UI", 9),
                fg=self.accent,
                bg=self.surface,
                anchor="w"
            ).pack(fill="x")

    def toggle_monitor(self):
        if self.monitor_thread is not None:
            if self.monitor_thread.is_alive():
                self.stop_monitor()
                return

        self.start_monitor()

    def start_monitor(self):
        clear_event()
        self.last_event_timestamp = None
        self.stop_event = threading.Event()

        self.monitor_thread = threading.Thread(
            target=monitor_activity,
            kwargs={"stop_event": self.stop_event},
            daemon=True
        )
        self.monitor_thread.start()

        self.update_status(True)

    def stop_monitor(self):
        if self.stop_event is not None:
            self.stop_event.set()

        self.update_status(False)

    def update_status(self, running):
        if running:
            self.status_label.config(
                text="● Monitoring active",
                fg="#8FE3AD"
            )
            self.monitor_button.config(text="Stop Monitoring")
        else:
            self.status_label.config(
                text="● Monitoring stopped",
                fg="#F59E9E"
            )
            self.monitor_button.config(text="Start Monitoring")

    def check_events(self):
        event = read_event()

        if event:
            timestamp = event.get("timestamp")

            if timestamp != self.last_event_timestamp:
                self.last_event_timestamp = timestamp

                if event.get("event_type") == "resumption":
                    payload = event.get("payload", {})
                    recommendations = payload.get(
                        "recommendations",
                        []
                    )

                    self.show_resumption_alert(
                        payload.get("application"),
                        recommendations
                    )

        if self.monitor_thread is not None:
            if not self.monitor_thread.is_alive():
                self.update_status(False)

        self.root.after(1000, self.check_events)

    def show_resumption_alert(self, application, recommendations):
        if recommendations:
            task = recommendations[0]
            message = (
                f"You returned to {application}.\n"
                f"Suggested task: {task['window']}\n"
                f"Score: {task['score']:.4f}"
            )
        else:
            message = f"You returned to {application}."

        self.alert_message.config(text=message)
        self.alert_frame.pack(
            fill="x",
            padx=24,
            pady=(0, 12),
            before=self.recommendation_frame
        )

        self.render_recommendations(recommendations)

        self.root.lift()

    def dismiss_alert(self):
        self.alert_frame.pack_forget()

    def on_close(self):
        if self.stop_event is not None:
            self.stop_event.set()

        self.root.destroy()


def main():
    initialize_database()

    root = tk.Tk()
    PixelBuddyWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
