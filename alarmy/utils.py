import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import json
import platform
import random
import string
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime

import pygame
from appdirs import user_data_dir

import alarmy.constants as c

root_dir = os.path.dirname(os.path.dirname(__file__))
appdata_dir = user_data_dir(c.APP_NAME)
alarms_file = os.path.join(appdata_dir, "alarms.json")


# --- common helpers ---


def generate_id() -> str:
    return "".join(random.choices(string.ascii_letters, k=12))


def log_error(text: str):
    with open(
        os.path.join(appdata_dir, "error.log"), "a", encoding="utf-8"
    ) as f:
        f.write(text + "\n\n")


def init():
    if platform.system() != "Linux":
        print(f"{c.APP_NAME} is only compatible with Linux systems")
        sys.exit(1)

    os.makedirs(appdata_dir, exist_ok=True)
    if not os.path.isfile(alarms_file):
        with open(alarms_file, "w") as f:
            f.write("[]")


# --- store helpers ---


def read_alarms() -> list[dict]:
    with open(alarms_file, encoding="utf-8") as f:
        alarms = json.load(f)
        for alarm in alarms:
            alarm[c.FIELD_SCHEDULE] = datetime.fromisoformat(
                alarm[c.FIELD_SCHEDULE]
            )
        return alarms


def write_alarms(alarms: list[dict]):
    serializable = [
        {**a, c.FIELD_SCHEDULE: a[c.FIELD_SCHEDULE].isoformat()}
        for a in alarms
    ]
    serializable.sort(key=lambda a: a[c.FIELD_SCHEDULE])
    with open(alarms_file, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)


def schedule_alarm(alarm_id: str, schedule: datetime):
    subprocess.run(
        [
            "systemd-run",
            "--user",
            f"--on-calendar={schedule.strftime('%Y-%m-%d %H:%M')}",
            f"--unit=alarmy-{alarm_id}",
            f"--working-directory={root_dir}",
            "--timer-property=AccuracySec=1s",
            sys.executable,
            "-m",
            c.APP_NAME.lower(),
            c.CMD_FIRE,
            alarm_id,
        ],
        check=True,
        capture_output=True,
    )


def cancel_alarm(ids: set[str]):
    for alarm_id in ids:
        subprocess.run(
            ["systemctl", "--user", "stop", f"alarmy-{alarm_id}.timer"],
            capture_output=True,
        )


def add_alarm(title: str, schedule: datetime):
    alarm_id = generate_id()
    schedule = schedule.replace(second=0, microsecond=0)
    alarms = read_alarms()
    alarms.append(
        {
            c.FIELD_ID: alarm_id,
            c.FIELD_TITLE: title,
            c.FIELD_SCHEDULE: schedule,
        }
    )
    write_alarms(alarms)
    schedule_alarm(alarm_id, schedule)


def remove_alarms(ids: set[str]):
    cancel_alarm(ids)
    alarms = read_alarms()
    alarms = [a for a in alarms if a[c.FIELD_ID] not in ids]
    write_alarms(alarms)


# --- sound helpers ---


def play_beeper():
    pygame.mixer.init()
    wav_file = os.path.join(root_dir, "assets/alarm.mp3")
    pygame.mixer.music.load(wav_file)
    pygame.mixer.music.play(-1)


def pause_beeper():
    pygame.mixer.music.stop()


# --- UI helpers ---


def launch_alarms(alarms: list[dict]):
    if not alarms:
        return

    root = tk.Tk()
    root.withdraw()

    remaining = {"count": len(alarms)}

    def make_window(alarm: dict):
        win = tk.Toplevel(root)
        win.title("Alarmy")
        win.geometry("512x256")
        win.configure(bg="#111")

        frame = tk.Frame(win, bg="#111")
        frame.pack(expand=True)

        tk.Label(
            frame,
            text=alarm[c.FIELD_TITLE],
            font=("Arial", 22, "bold"),
            fg="white",
            bg="#111",
        ).pack(pady=20)

        def stop():
            remaining["count"] -= 1
            if remaining["count"] == 0:
                pause_beeper()
            win.destroy()
            if remaining["count"] == 0:
                root.destroy()

        # stops the audio (and the tkinter loop) when user closes window
        win.protocol("WM_DELETE_WINDOW", stop)

        tk.Button(
            frame,
            text="Stop",
            font=("Arial", 14),
            width=10,
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            relief="flat",
            command=stop,
        ).pack(pady=10)

    for alarm in alarms:
        make_window(alarm)

    threading.Thread(target=play_beeper, daemon=True).start()
    root.mainloop()
