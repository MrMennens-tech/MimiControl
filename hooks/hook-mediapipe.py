"""PyInstaller hook: bundel mediapipe native libs (libmediapipe.dll) en tasks-submodules."""

from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all("mediapipe")

hiddenimports += collect_submodules("mediapipe.tasks.python")
hiddenimports += [
    "mediapipe.tasks.c",
    "mediapipe.tasks.python.core.mediapipe_c_bindings",
    "mediapipe.tasks.python.vision",
]
