"""
MimiControl - Centrale toetsmodule
Vervangt pyautogui.press() door een expliciet keyDown/keyUp paar
met configureerbare duur, zodat webapps de toetsinput correct registreren.

Op Windows worden toetsen met hun hardware-scancode verstuurd via SendInput.
Browsers leiden KeyboardEvent.code uit die scancode af; zonder scancode
ontvangt een webapp een lege code en herkent hij de toets niet.
"""

import sys
import time
import pyautogui

DEFAULT_TOETS_DUUR_MS = 100

# ---------------------------------------------------------------------------
# Windows SendInput met scancode
# ---------------------------------------------------------------------------
_IS_WINDOWS = sys.platform == "win32"

# Toetsen links van het hoofdblok hebben een extended-flag nodig
_EXTENDED = {
    "left", "right", "up", "down", "home", "end", "pageup", "pgup",
    "pagedown", "pgdn", "insert", "delete", "del", "numlock",
    "printscreen", "divide", "altright", "ctrlright",
}

# Virtuele toetscodes voor het geval pyautogui's mapping niet beschikbaar is
_EIGEN_VK = {
    "space": 0x20, "enter": 0x0D, "return": 0x0D, "esc": 0x1B, "escape": 0x1B,
    "tab": 0x09, "backspace": 0x08, "delete": 0x2E, "del": 0x2E,
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "insert": 0x2D, "ctrl": 0x11, "shift": 0x10, "alt": 0x12, "win": 0x5B,
}

if _IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    _INPUT_KEYBOARD = 1
    _KEYEVENTF_EXTENDEDKEY = 0x0001
    _KEYEVENTF_KEYUP = 0x0002
    _KEYEVENTF_SCANCODE = 0x0008
    _MAPVK_VK_TO_VSC = 0

    _ULONG_PTR = (ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8
                  else ctypes.c_ulong)

    class _KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                    ("dwExtraInfo", _ULONG_PTR)]

    class _MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD), ("dwExtraInfo", _ULONG_PTR)]

    class _HARDWAREINPUT(ctypes.Structure):
        _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                    ("wParamH", wintypes.WORD)]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("mi", _MOUSEINPUT), ("ki", _KEYBDINPUT),
                    ("hi", _HARDWAREINPUT)]

    class _INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("union", _INPUTUNION)]


def normaliseer_toets(naam):
    """Normaliseer toetsnaam naar lowercase zonder witruimte."""
    return naam.strip().lower()


def _vk_code(naam):
    """Zoek de virtuele toetscode voor een pyautogui-toetsnaam."""
    mapping = getattr(getattr(pyautogui, "platformModule", None),
                      "keyboardMapping", None)
    if mapping:
        vk = mapping.get(naam)
        if vk:
            return vk
    if naam in _EIGEN_VK:
        return _EIGEN_VK[naam]
    if len(naam) == 1:
        return ord(naam.upper())
    return None


def _scancode(vk):
    """Vertaal een virtuele toetscode naar de hardware-scancode."""
    return ctypes.windll.user32.MapVirtualKeyW(vk, _MAPVK_VK_TO_VSC)


def _stuur_scancode(naam, omhoog=False):
    """Stuur één toets-event met scancode. Geeft False bij mislukking."""
    vk = _vk_code(naam)
    if not vk:
        return False
    scan = _scancode(vk)
    if not scan:
        return False

    flags = _KEYEVENTF_SCANCODE
    if omhoog:
        flags |= _KEYEVENTF_KEYUP
    if naam in _EXTENDED:
        flags |= _KEYEVENTF_EXTENDEDKEY

    invoer = _INPUT(type=_INPUT_KEYBOARD,
                    union=_INPUTUNION(ki=_KEYBDINPUT(
                        wVk=0, wScan=scan, dwFlags=flags,
                        time=0, dwExtraInfo=0)))
    verstuurd = ctypes.windll.user32.SendInput(
        1, ctypes.byref(invoer), ctypes.sizeof(_INPUT))
    return verstuurd == 1


def _stuur_via_scancode(toetsen, pauze):
    """Voer de volledige toetsactie uit via SendInput. False = niet gelukt."""
    if not _IS_WINDOWS:
        return False
    if any(_vk_code(t) is None for t in toetsen):
        return False

    for t in toetsen:
        if not _stuur_scancode(t, omhoog=False):
            return False
    time.sleep(pauze)
    for t in reversed(toetsen):
        _stuur_scancode(t, omhoog=True)
    return True


def voer_toetsen_uit(toetsen, duur_ms=DEFAULT_TOETS_DUUR_MS):
    """
    Voer een toetsactie uit met expliciet keyDown/keyUp paar.

    Bij één toets: keyDown → wacht → keyUp
    Bij meerdere toetsen (combo): alle keyDown → wacht → alle keyUp (omgekeerd)
    """
    toetsen = [normaliseer_toets(t) for t in toetsen]
    pauze = duur_ms / 1000

    if _stuur_via_scancode(toetsen, pauze):
        return

    # Fallback voor niet-Windows of onbekende toetsen
    if len(toetsen) == 1:
        pyautogui.keyDown(toetsen[0])
        time.sleep(pauze)
        pyautogui.keyUp(toetsen[0])
    else:
        for t in toetsen:
            pyautogui.keyDown(t)
        time.sleep(pauze)
        for t in reversed(toetsen):
            pyautogui.keyUp(t)
