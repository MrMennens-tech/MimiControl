"""
MimiControl Studio - CustomTkinter versie
Start de grafische interface met Mennens.Tech branding.
"""

import traceback

from paths import (
    install_crash_handlers, log_message, is_frozen,
    bundle_dir, user_data_dir, model_path,
)


def _start():
    from gui_explorer_ctk import start_gui_explorer_ctk

    log_message(
        "MimiControl Studio gestart\n"
        f"frozen={is_frozen()}\n"
        f"bundle={bundle_dir()}\n"
        f"data={user_data_dir()}\n"
        f"model={model_path()} (exists={__import__('os').path.exists(model_path())})"
    )
    start_gui_explorer_ctk()


if __name__ == "__main__":
    install_crash_handlers()
    try:
        _start()
    except Exception:
        log_message(f"Startup crash:\n{traceback.format_exc()}")
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "MimiControl Studio — fout",
                "De applicatie kon niet starten.\n\n"
                f"Details staan in:\n{user_data_dir()}\\crash.log",
            )
            root.destroy()
        except Exception:
            pass
        raise
