"""
Pad-hulpfuncties voor development en PyInstaller frozen builds.

Gebundelde resources (model, assets) zitten in sys._MEIPASS.
Profielen, logs en gedownloade modellen gaan naar een beschrijfbare user-data map.
"""

import os
import sys
import traceback
from datetime import datetime

_APP_DIR = os.path.dirname(os.path.abspath(__file__))


def is_frozen():
    """True wanneer de app als PyInstaller .exe draait."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def bundle_dir():
    """Directory met gebundelde, read-only resources."""
    if is_frozen():
        return sys._MEIPASS
    return _APP_DIR


def user_data_dir():
    """Beschrijfbare map voor profielen, crash.log en gedownloade modellen."""
    if is_frozen():
        if sys.platform == "win32":
            base = os.environ.get("APPDATA", os.path.expanduser("~"))
        else:
            base = os.path.join(os.path.expanduser("~"), ".config")
        path = os.path.join(base, "MimiControl Studio")
    else:
        path = _APP_DIR
    os.makedirs(path, exist_ok=True)
    return path


def resource_path(*parts):
    """Pad naar een gebundeld bestand (assets, iconen, model in bundle)."""
    return os.path.join(bundle_dir(), *parts)


def model_path():
    """
    Pad naar face_landmarker.task.
    Eerst gebundelde kopie (_MEIPASS), anders user-data map (download).
    """
    bundled = resource_path("face_landmarker.task")
    if os.path.exists(bundled):
        return bundled
    return os.path.join(user_data_dir(), "face_landmarker.task")


def crash_log_path():
    return os.path.join(user_data_dir(), "crash.log")


def log_message(msg):
    """Schrijf een regel naar crash.log (ook voor diagnostiek, niet alleen crashes)."""
    try:
        with open(crash_log_path(), "a", encoding="utf-8") as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"{datetime.now().isoformat()}\n")
            f.write(msg)
            if not msg.endswith("\n"):
                f.write("\n")
    except Exception:
        pass


def install_crash_handlers():
    """Vang onafgehandelde excepties af en log naar crash.log."""

    def _excepthook(exc_type, exc_value, exc_tb):
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        log_message(f"Onafgehandelde exceptie:\n{tb}")
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook

    import threading

    if hasattr(threading, "excepthook"):
        def _thread_hook(args):
            tb = "".join(traceback.format_exception(
                args.exc_type, args.exc_value, args.exc_traceback
            ))
            log_message(f"Thread-exceptie ({args.thread.name}):\n{tb}")

        threading.excepthook = _thread_hook
