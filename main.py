import tkinter as tk
from PIL import Image, ImageTk, Image as PILImage
import simpleaudio as sa
import numpy as np
import wave
from pynput import mouse, keyboard
import pystray
import threading
import sys
import functools
import os
import json
import sys
import os
import tempfile

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

IMAGE_PATH = resource_path("question_mark.png")
SOUND_PATH = resource_path("ping.wav")
TRAY_ICON_PATH = resource_path("tray_icon.png")
PING_SIZE = 100
MAX_PINGS = 3

SETTINGS_DIR = os.path.join(os.path.expanduser("~"), "Documents", "timerin", "pingtool")
os.makedirs(SETTINGS_DIR, exist_ok=True)
VOLUME_FILE = os.path.join(SETTINGS_DIR, "ping_volume.json")

def load_volume():
    if os.path.exists(VOLUME_FILE):
        try:
            with open(VOLUME_FILE, "r") as f:
                return json.load(f).get("volume", 0.2)
        except Exception as e:
            print(f"Error loading volume file: {e}")
    return 0.2

def save_volume(volume):
    try:
        with open(VOLUME_FILE, "w") as f:
            json.dump({"volume": volume}, f)
    except Exception as e:
        print(f"Error saving volume file: {e}")

global PING_VOLUME
PING_VOLUME = load_volume()

root = tk.Tk()
root.withdraw()
image = PILImage.open(IMAGE_PATH).resize((PING_SIZE, PING_SIZE))
img_tk = ImageTk.PhotoImage(image)
ping_windows = []
for _ in range(MAX_PINGS):
    win = tk.Toplevel(root)
    win.attributes("-topmost", True, "-transparentcolor", "black")
    win.overrideredirect(True)
    win.configure(bg="black")
    label = tk.Label(win, image=img_tk, bg="black", bd=0)
    label.pack()
    win.withdraw()
    ping_windows.append(win)

ctrl_pressed = False
alt_pressed = False
current_ping = 0

def play_sound():
    try:
        with wave.open(SOUND_PATH, "rb") as wf:
            sample_rate = wf.getframerate()
            sample_width = wf.getsampwidth()
            num_channels = wf.getnchannels()
            audio_data = wf.readframes(wf.getnframes())

        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        audio_array = (audio_array * PING_VOLUME).astype(np.int16)
        adjusted_audio = audio_array.tobytes()
        temp_dir = tempfile.gettempdir()
        temp_wav_path = os.path.join(temp_dir, "temp_ping.wav")

        with wave.open(temp_wav_path, "wb") as temp_wav:
            temp_wav.setnchannels(num_channels)
            temp_wav.setsampwidth(sample_width)
            temp_wav.setframerate(sample_rate)
            temp_wav.writeframes(adjusted_audio)

        sa.WaveObject.from_wave_file(temp_wav_path).play()
    except Exception as e:
        print(f"Error playing sound: {e}")

def show_ping(x, y):
    global current_ping
    ping_window = ping_windows[current_ping]
    current_ping = (current_ping + 1) % MAX_PINGS
    ping_window.geometry(f"{PING_SIZE}x{PING_SIZE}+{x - PING_SIZE//2}+{y - PING_SIZE//2}")
    ping_window.deiconify()
    play_sound()
    root.after(700, ping_window.withdraw)

def on_click(x, y, button, pressed):
    if pressed and button == mouse.Button.left and ctrl_pressed and alt_pressed:
        show_ping(x, y)

def on_press(key):
    global ctrl_pressed, alt_pressed
    if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
        ctrl_pressed = True
    if key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
        alt_pressed = True

def on_release(key):
    global ctrl_pressed, alt_pressed
    if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
        ctrl_pressed = False
    if key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
        alt_pressed = False

def quit_application(icon, item):
    icon.stop()
    root.quit()
    root.destroy()
    mouse_listener.stop()
    keyboard_listener.stop()
    os._exit(0)


def set_volume(volume, *args):
    global PING_VOLUME
    PING_VOLUME = volume
    save_volume(volume)
    print(f"Volume set to: {volume:.2f}")

def setup_tray():
    tray_icon = PILImage.open(TRAY_ICON_PATH)
    info_item = pystray.MenuItem("Ctrl+Alt+Left Click to Ping", lambda: None, default=True)
    volume_levels = [0.0, 0.05, 0.1, 0.15, 0.2]
    volume_menu = pystray.Menu(
        *[pystray.MenuItem(f"{int(v / 0.2 * 100)}%", functools.partial(set_volume, v)) for v in volume_levels]
    )
    volume_item = pystray.MenuItem("Volume", volume_menu)
    exit_item = pystray.MenuItem("Exit", quit_application)
    menu = pystray.Menu(info_item, volume_item, pystray.Menu.SEPARATOR, exit_item)
    icon = pystray.Icon("PingTool", tray_icon, "PingTool", menu=menu)
    icon.run()

threading.Thread(target=setup_tray, daemon=True).start()
mouse_listener = mouse.Listener(on_click=on_click)
keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
mouse_listener.start()
keyboard_listener.start()
root.mainloop()
