"""
MimiControl - Centrale toetsmodule
Vervangt pyautogui.press() door een expliciet keyDown/keyUp paar
met configureerbare duur, zodat webapps de toetsinput correct registreren.

Op Windows worden toetsen met hun hardware-scancode verstuurd via SendInput.
Browsers leiden KeyboardEvent.code uit die scancode af; zonder scancode
ontvangt een webapp een lege code en herkent hij de toets niet.

SendInput gaat naar het voorgrondvenster (GetForegroundWindow), niet naar
het proces dat de call doet. Geen hooks, geen injectie in andere programma's.
Studio-focus is niet nodig; dezelfde scancodes blijven globaal vuren.
"""

import os
import sys
import time
import pyautogui

DEFAULT_TOETS_DUUR_MS = 100
_MIN_PAUZE_S = 0.03

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

_LAATSTE_STATUS = ""

if _IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    _INPUT_KEYBOARD = 1
    _KEYEVENTF_EXTENDEDKEY = 0x0001
    _KEYEVENTF_KEYUP = 0x0002
    _KEYEVENTF_SCANCODE = 0x0008
    _MAPVK_VK_TO_VSC = 0
    _TOKEN_QUERY = 0x0008
    _TokenIntegrityLevel = 25
    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    _SECURITY_MANDATORY_MEDIUM_RID = 0x2000
    _SECURITY_MANDATORY_HIGH_RID = 0x3000

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

    class _SID_AND_ATTRIBUTES(ctypes.Structure):
        _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", wintypes.DWORD)]

    class _TOKEN_MANDATORY_LABEL(ctypes.Structure):
        _fields_ = [("Label", _SID_AND_ATTRIBUTES)]

    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    _shell32 = ctypes.WinDLL("shell32", use_last_error=True)

    _user32.SendInput.argtypes = (
        wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int
    )
    _user32.SendInput.restype = wintypes.UINT
    _user32.MapVirtualKeyW.argtypes = (wintypes.UINT, wintypes.UINT)
    _user32.MapVirtualKeyW.restype = wintypes.UINT
    _user32.GetForegroundWindow.restype = ctypes.c_void_p
    _user32.GetWindowThreadProcessId.argtypes = (
        ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)
    )
    _user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    _kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _kernel32.OpenProcess.restype = ctypes.c_void_p
    _kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
    _kernel32.CloseHandle.restype = wintypes.BOOL
    _kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    _kernel32.GetCurrentProcessId.restype = wintypes.DWORD
    _advapi32.OpenProcessToken.argtypes = (
        ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p)
    )
    _advapi32.OpenProcessToken.restype = wintypes.BOOL
    _advapi32.GetTokenInformation.argtypes = (
        ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p,
        wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)
    )
    _advapi32.GetTokenInformation.restype = wintypes.BOOL
    _advapi32.GetSidSubAuthorityCount.argtypes = (ctypes.c_void_p,)
    _advapi32.GetSidSubAuthorityCount.restype = ctypes.c_void_p
    _advapi32.GetSidSubAuthority.argtypes = (ctypes.c_void_p, wintypes.DWORD)
    _advapi32.GetSidSubAuthority.restype = ctypes.c_void_p
    _shell32.IsUserAnAdmin.restype = wintypes.BOOL


def normaliseer_toets(naam):
    """Normaliseer toetsnaam naar lowercase zonder witruimte."""
    return naam.strip().lower()


def laatste_toets_status():
    """Laatste Nederlandse status van SendInput (leeg = ok)."""
    return _LAATSTE_STATUS


def _zet_status(tekst):
    global _LAATSTE_STATUS
    _LAATSTE_STATUS = tekst or ""


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
    return int(_user32.MapVirtualKeyW(int(vk), _MAPVK_VK_TO_VSC))


def _stuur_scancode(naam, omhoog=False):
    """Stuur één toets-event met scancode. Geeft False bij mislukking."""
    vk = _vk_code(naam)
    if not vk:
        _zet_status(f"Onbekende toets: {naam}")
        return False
    scan = _scancode(vk)
    if not scan:
        _zet_status(f"Geen scancode voor toets: {naam}")
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
    verstuurd = _user32.SendInput(
        1, ctypes.byref(invoer), ctypes.sizeof(_INPUT)
    )
    if verstuurd != 1:
        err = ctypes.get_last_error()
        _zet_status(f"SendInput mislukt (Windows-fout {err})")
        return False
    return True


def _stuur_via_scancode(toetsen, pauze):
    """Voer de volledige toetsactie uit via SendInput. False = niet gelukt."""
    if not _IS_WINDOWS:
        return False
    if any(_vk_code(t) is None for t in toetsen):
        return False

    gelukt = True
    for t in toetsen:
        if not _stuur_scancode(t, omhoog=False):
            gelukt = False
            break
    time.sleep(max(float(pauze), _MIN_PAUZE_S))
    for t in reversed(toetsen):
        if not _stuur_scancode(t, omhoog=True):
            time.sleep(0.01)
            _stuur_scancode(t, omhoog=True)
    return gelukt


def _integriteit_rid_van_token(token):
    """Mandatory integrity RID van een geopende token, of None."""
    nodig = wintypes.DWORD(0)
    _advapi32.GetTokenInformation(
        token, _TokenIntegrityLevel, None, 0, ctypes.byref(nodig)
    )
    if nodig.value == 0:
        return None
    buf = ctypes.create_string_buffer(nodig.value)
    if not _advapi32.GetTokenInformation(
        token, _TokenIntegrityLevel, buf, nodig.value,
        ctypes.byref(nodig)
    ):
        return None
    try:
        label = _TOKEN_MANDATORY_LABEL.from_buffer(buf)
        sid = label.Label.Sid
    except Exception:
        return None
    if not sid:
        return None
    aantal_addr = _advapi32.GetSidSubAuthorityCount(sid)
    if not aantal_addr:
        return None
    aantal = ctypes.c_ubyte.from_address(aantal_addr).value
    if aantal < 1:
        return None
    rid_addr = _advapi32.GetSidSubAuthority(sid, aantal - 1)
    if not rid_addr:
        return None
    return int(wintypes.DWORD.from_address(rid_addr).value)


def _integriteit_rid_van_proceshandle(handle):
    token = ctypes.c_void_p()
    if not _advapi32.OpenProcessToken(handle, _TOKEN_QUERY, ctypes.byref(token)):
        return None
    try:
        return _integriteit_rid_van_token(token)
    finally:
        _kernel32.CloseHandle(token)


def _eigen_integriteit_rid():
    try:
        return _integriteit_rid_van_proceshandle(_kernel32.GetCurrentProcess())
    except Exception:
        return None


def _voorgrond_pid():
    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        return 0
    pid = wintypes.DWORD(0)
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return int(pid.value)


def _integriteit_rid_van_pid(pid):
    if not pid:
        return None
    handle = _kernel32.OpenProcess(
        _PROCESS_QUERY_LIMITED_INFORMATION, False, pid
    )
    if not handle:
        return None
    try:
        return _integriteit_rid_van_proceshandle(handle)
    finally:
        _kernel32.CloseHandle(handle)


def studio_draait_als_admin():
    """True als dit proces een verhoogd (administrator) token heeft."""
    if not _IS_WINDOWS:
        return False
    try:
        return bool(_shell32.IsUserAnAdmin())
    except Exception:
        return False


def waarschuwing_integriteit():
    """
    Nederlandse melding als UIPI SendInput naar het voorgrondprogramma
    kan blokkeren. Lege string = geen conflict gedetecteerd.
    """
    if not _IS_WINDOWS:
        return ""
    try:
        eigen = _eigen_integriteit_rid()
        fg_pid = _voorgrond_pid()
        if not fg_pid or fg_pid == os.getpid():
            return ""
        fg = _integriteit_rid_van_pid(fg_pid)
        if eigen is None:
            return ""
        if fg is None:
            # Token van het voorgrondproces niet leesbaar: vaak hoger IL.
            if eigen < _SECURITY_MANDATORY_HIGH_RID:
                return (
                    "Het programma vooraan (bijv. Communicator 5) draait mogelijk "
                    "als administrator, Studio niet. Windows blokkeert dan de toets. "
                    "Start Studio als administrator, of start Communicator níet als administrator."
                )
            return ""
        if fg > eigen:
            return (
                "Communicator (of het programma vooraan) draait als administrator, "
                "Studio niet. Windows blokkeert dan de mimiek-toets. "
                "Start Studio als administrator, of start Communicator níet als administrator."
            )
        if eigen >= _SECURITY_MANDATORY_HIGH_RID and fg <= _SECURITY_MANDATORY_MEDIUM_RID:
            # Wij admin, zij niet: SendInput mag, extra melding is niet nodig.
            return ""
    except Exception:
        return ""
    return ""


def voer_toetsen_uit(toetsen, duur_ms=DEFAULT_TOETS_DUUR_MS):
    """
    Voer een toetsactie uit met expliciet keyDown/keyUp paar.

    Bij één toets: keyDown → wacht → keyUp
    Bij meerdere toetsen (combo): alle keyDown → wacht → alle keyUp (omgekeerd)

    Op Windows: SendInput-scancodes naar het voorgrondvenster. Geen focus
    van MimiControl nodig. Geen hooks, geen injectie.
    Geeft True als de scancodes (of de niet-Windows fallback) verstuurd zijn.
    """
    toetsen = [normaliseer_toets(t) for t in toetsen]
    pauze = duur_ms / 1000
    _zet_status("")

    if _stuur_via_scancode(toetsen, pauze):
        return True

    if _IS_WINDOWS and all(_vk_code(t) is not None for t in toetsen):
        # Bekende toetsen: niet stiekem naar pyautogui (dat is geen scancode).
        if not _LAATSTE_STATUS:
            uipi = waarschuwing_integriteit()
            _zet_status(uipi or "SendInput gaf geen toets af")
        return False

    # Fallback voor niet-Windows of onbekende toetsen
    try:
        if len(toetsen) == 1:
            pyautogui.keyDown(toetsen[0])
            time.sleep(max(pauze, _MIN_PAUZE_S))
            pyautogui.keyUp(toetsen[0])
        else:
            for t in toetsen:
                pyautogui.keyDown(t)
            time.sleep(max(pauze, _MIN_PAUZE_S))
            for t in reversed(toetsen):
                pyautogui.keyUp(t)
        return True
    except Exception as exc:
        _zet_status(f"Toets fallback mislukt: {exc}")
        return False
