"""
MimiExplorer - Live Modus (Studio v2)
Compacte PiP-overlay in een schermhoek (default rechtsboven, always-on-top).
Getekend via een eigen layered Win32-venster (niet OpenCV HighGUI), zodat
het beeld boven Communicator 5 vensterweergave blijft lopen.
Triggerbalk toont waarde vs drempel. Uitgezette triggers verdwijnen.
Hotkeys: Q P 1 2 3 T S A M F O C
"""

import ctypes
import cv2
import time
import threading
import traceback
import numpy as np
import pyautogui

import customtkinter as ctk

from config_explorer import (
    laad_explorer_config, sla_explorer_config_op,
    normaliseer_overlay_grootte, overlay_cam_maten, overlay_hud_breedte,
    normaliseer_overlay_hoek, volgende_overlay_hoek, overlay_hoek_label,
)
from blendshape_detectie import (
    maak_blendshape_landmarker, detecteer_blendshapes,
    teken_face_mesh_simpel, teken_gezicht_gloed, nl_label,
    frame_is_ok, naar_contiguous_beeld,
)
from blendshape_labels import is_ondersteund, trigger_kleur_bgr, trigger_kleur_hex
from paths import log_message
from toets_actie import (
    voer_toetsen_uit, laatste_toets_status, waarschuwing_integriteit,
)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

# ---------------------------------------------------------------------------
# Mennens.Tech kleurenpalet — Hex voor CustomTkinter
# ---------------------------------------------------------------------------
DONKER      = "#062D36"
TEAL_BTN    = "#4DB8BE"
TEAL_HOVER  = "#3A9DA3"
BG          = "#F2F2F7"
KAART       = "#FFFFFF"
TEKST       = "#1C1C1E"
TEKST_LICHT = "#5A5A5E"
RAND        = "#E5E5EA"
TEAL_BRAND  = "#68CCD1"
FONT        = "Segoe UI"

# ---------------------------------------------------------------------------
# BGR kleuren voor het OpenCV info-paneel
# ---------------------------------------------------------------------------
BGR_DONKER      = (54, 45, 6)       # #062D36
BGR_TEAL        = (190, 184, 77)    # #4DB8BE
BGR_BRAND       = (209, 204, 104)   # #68CCD1
BGR_WIT         = (255, 255, 255)
BGR_GROEN       = (60, 200, 0)
BGR_ROOD        = (70, 70, 220)
BGR_GRIJS       = (140, 140, 140)
BGR_DONKERGRIJS = (60, 60, 60)
BGR_SCHEIDING   = (70, 60, 12)

PANEEL_BREEDTE = 420
CAPTURE_MAX_B = 1280
CAPTURE_MAX_H = 720
HUD_INTERVAL_S = 0.07
CTK_INTERVAL_S = 0.10
OVERLAY_MARGE = 12
TOPMOST_HERHAAL_S = 2.5
LIVE_VENSTER = "MimiControl overlay (Q P 1 2 3 T S A M F O C)"
HOTKEY_HINT = "Q P 1 2 3 T S K A M F O C"
OVERLAY_KLASSE = "MimiControlStudioV2Overlay"
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SPI_GETWORKAREA = 0x0030
GA_ROOT = 2
SW_RESTORE = 9
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
ULW_ALPHA = 0x00000002
AC_SRC_OVER = 0x00
PM_REMOVE = 0x0001
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_KEYDOWN = 0x0100
WM_LBUTTONUP = 0x0202
WM_SYSKEYDOWN = 0x0104
IDC_ARROW = 32512
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001
BI_RGB = 0
DIB_RGB_COLORS = 0
VK_PRIOR = 0x21
VK_NEXT = 0x22
VK_UP = 0x26
VK_DOWN = 0x28
ERROR_CLASS_ALREADY_EXISTS = 1410
LRESULT = ctypes.c_ssize_t
WPARAM = ctypes.c_size_t
LPARAM = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT, ctypes.c_void_p, ctypes.c_uint, WPARAM, LPARAM
)


class _RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class _SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


class _BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_byte),
        ("BlendFlags", ctypes.c_byte),
        ("SourceConstantAlpha", ctypes.c_byte),
        ("AlphaFormat", ctypes.c_byte),
    ]


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.c_uint32),
        ("biWidth", ctypes.c_int32),
        ("biHeight", ctypes.c_int32),
        ("biPlanes", ctypes.c_uint16),
        ("biBitCount", ctypes.c_uint16),
        ("biCompression", ctypes.c_uint32),
        ("biSizeImage", ctypes.c_uint32),
        ("biXPelsPerMeter", ctypes.c_int32),
        ("biYPelsPerMeter", ctypes.c_int32),
        ("biClrUsed", ctypes.c_uint32),
        ("biClrImportant", ctypes.c_uint32),
    ]


class _BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", _BITMAPINFOHEADER),
        ("bmiColors", ctypes.c_uint32 * 3),
    ]


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam", WPARAM),
        ("lParam", LPARAM),
        ("time", ctypes.c_uint),
        ("pt", _POINT),
    ]


class _WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("style", ctypes.c_uint),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", ctypes.c_void_p),
        ("hIcon", ctypes.c_void_p),
        ("hCursor", ctypes.c_void_p),
        ("hbrBackground", ctypes.c_void_p),
        ("lpszMenuName", ctypes.c_wchar_p),
        ("lpszClassName", ctypes.c_wchar_p),
        ("hIconSm", ctypes.c_void_p),
    ]


def _bruikbare_blendshapes(trigger):
    """Blendshapes van een trigger die het Face Landmarker-model kan vullen."""
    return {
        naam: drempel
        for naam, drempel in trigger.get("blendshapes", {}).items()
        if is_ondersteund(naam)
    }


def _scherm_maten():
    """Werkgebied van het primaire scherm (px)."""
    try:
        import ctypes
        return (
            ctypes.windll.user32.GetSystemMetrics(0),
            ctypes.windll.user32.GetSystemMetrics(1),
        )
    except Exception:
        return 1920, 1080


def _begrens_capture(cap, max_w=CAPTURE_MAX_B, max_h=CAPTURE_MAX_H):
    """Vraag een lagere camera-resolutie; detectie blijft nauwkeurig via MediaPipe 640."""
    try:
        # MJPG + 30 fps: minder USB-bandbreedte en lagere latency bij 720p.
        # Wordt de aanvraag genegeerd of geeft de camera geen frame, dan
        # valt _open_webcam_robuust terug op de native resolutie.
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, max_w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, max_h)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass


def _schaal_voor_weergave(frame, max_w, max_h):
    """Schaal het webcambeeld zodat het binnen max_w × max_h blijft."""
    frame = naar_contiguous_beeld(frame)
    if frame is None:
        return None
    h, w = frame.shape[:2]
    if max_w <= 0 or max_h <= 0:
        return frame
    schaal = min(max_w / w, max_h / h, 1.0)
    if schaal >= 0.99:
        return frame
    nieuw_w = max(1, int(w * schaal))
    nieuw_h = max(1, int(h * schaal))
    geschaald = cv2.resize(
        frame, (nieuw_w, nieuw_h), interpolation=cv2.INTER_AREA
    )
    return naar_contiguous_beeld(geschaald)


def _plak_in_kader(frame, kader_w, kader_h, vul_kleur=BGR_DONKER):
    """Centreer een frame in een vast pixelkader (letterbox)."""
    frame = naar_contiguous_beeld(frame)
    if frame is None:
        return None
    kader_w = max(1, int(kader_w))
    kader_h = max(1, int(kader_h))
    canvas = np.full((kader_h, kader_w, 3), vul_kleur, dtype=np.uint8)
    h, w = frame.shape[:2]
    x = max(0, (kader_w - w) // 2)
    y = max(0, (kader_h - h) // 2)
    kopie_w = min(w, kader_w)
    kopie_h = min(h, kader_h)
    canvas[y:y + kopie_h, x:x + kopie_w] = frame[:kopie_h, :kopie_w]
    return np.ascontiguousarray(canvas)


def _werkgebied():
    """Herkomst + maat van het primaire werkgebied (zonder taakbalk)."""
    try:
        r = _RECT()
        if ctypes.windll.user32.SystemParametersInfoW(
            SPI_GETWORKAREA, 0, ctypes.byref(r), 0
        ):
            return r.left, r.top, r.right - r.left, r.bottom - r.top
    except Exception:
        pass
    w, h = _scherm_maten()
    return 0, 0, w, h


ACTIE_BADGE_S = 2.0  # zo lang blijft "Verstuurd: <toets>" in beeld


def _toets_tekst(toetsen):
    """Nederlandse naam van de toets(en), bv. 'Spatie' of 'Ctrl + C'."""
    try:
        from toets_keuze import label_voor_toetsen
        tekst = label_voor_toetsen(toetsen)
        if tekst:
            return tekst
    except Exception:
        pass
    return " + ".join(toetsen).upper()


def _teken_actiebadge(frame, cam_h, toets, kleur, verstuurd):
    """Duidelijke melding links onderin het camerabeeld: welke toets is gestuurd."""
    tekst = (f"Verstuurd: {toets}" if verstuurd
             else f"Niet verstuurd: {toets}")
    font = cv2.FONT_HERSHEY_SIMPLEX
    schaal = 0.6
    tw, th = cv2.getTextSize(tekst, font, schaal, 2)[0]
    x1, y2 = 8, cam_h - 34
    x2, y1 = x1 + tw + 20, y2 - th - 16
    if y1 < 0:
        return
    achter = kleur if verstuurd else (90, 90, 90)
    cv2.rectangle(frame, (x1, y1), (x2, y2), achter, -1)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
    b, g, r = achter
    licht = (r * 0.3 + g * 0.59 + b * 0.11) > 150
    cv2.putText(frame, tekst, (x1 + 10, y2 - 8), font, schaal,
                (20, 20, 20) if licht else (255, 255, 255), 2)


STOP_BEVESTIG_S = 3.0  # tweede klik moet binnen zoveel seconden komen


def _stop_knop_rect(cam_w, bevestig):
    """Rechthoek (x1, y1, x2, y2) van de stopknop rechtsboven in het camerabeeld."""
    breedte = 196 if bevestig else 28
    x2 = cam_w - 6
    return (x2 - breedte, 6, x2, 30)


def _teken_stop_knop(canvas, cam_w, bevestig):
    """Kleine X; na één klik 'Stoppen? Klik nogmaals' (dubbele bevestiging)."""
    x1, y1, x2, y2 = _stop_knop_rect(cam_w, bevestig)
    if x1 < 0:
        return
    kleur = (60, 60, 220) if bevestig else (70, 70, 70)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), kleur, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), (255, 255, 255), 1)
    tekst = "Stoppen? Klik nogmaals" if bevestig else "X"
    font = cv2.FONT_HERSHEY_SIMPLEX
    schaal = 0.45 if bevestig else 0.55
    tw, th = cv2.getTextSize(tekst, font, schaal, 1)[0]
    cv2.putText(canvas, tekst,
                (x1 + (x2 - x1 - tw) // 2, y1 + (y2 - y1 + th) // 2),
                font, schaal, (255, 255, 255), 1)


def _overlay_positie(breedte, hoogte, hoek="rechtsboven"):
    """Pixelpositie van de overlay in de gekozen schermhoek."""
    ox, oy, scherm_w, scherm_h = _werkgebied()
    hoek = normaliseer_overlay_hoek(hoek)
    rechts = hoek.startswith("rechts")
    onder = "onder" in hoek
    x = ox + (
        scherm_w - int(breedte) - OVERLAY_MARGE if rechts else OVERLAY_MARGE
    )
    y = oy + (
        scherm_h - int(hoogte) - OVERLAY_MARGE if onder else OVERLAY_MARGE
    )
    return max(ox + OVERLAY_MARGE, x), max(oy + OVERLAY_MARGE, y)


def _venster_hwnd(titel):
    try:
        fw = ctypes.windll.user32.FindWindowW
        fw.restype = ctypes.c_void_p
        fw.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        return fw(None, titel) or 0
    except Exception:
        return 0


def _zet_venster_topmost(titel, aan=True, x=None, y=None, w=None, h=None):
    """Always-on-top aan of uit, zonder het venster elke frame de focus te geven."""
    hwnd = _venster_hwnd(titel)
    if not hwnd:
        return False
    try:
        flags = SWP_NOACTIVATE | SWP_SHOWWINDOW
        laag = HWND_TOPMOST if aan else HWND_NOTOPMOST
        if x is None or y is None or w is None or h is None:
            flags |= SWP_NOMOVE | SWP_NOSIZE
            ctypes.windll.user32.SetWindowPos(
                hwnd, laag, 0, 0, 0, 0, flags
            )
        else:
            ctypes.windll.user32.SetWindowPos(
                hwnd, laag, int(x), int(y), int(w), int(h), flags
            )
        return True
    except Exception:
        return False


def _plaats_overlay(breedte, hoogte, hoek="rechtsboven", topmost=True):
    """Zet overlay-grootte en hoek. Geen focus-diefstal. Geen OpenCV HighGUI."""
    x, y = _overlay_positie(breedte, hoogte, hoek)
    _zet_venster_topmost(LIVE_VENSTER, aan=topmost, x=x, y=y, w=breedte, h=hoogte)


def _plaats_overlay_rechtsboven(breedte, hoogte):
    """Compat: plaats overlay rechtsboven, always-on-top."""
    _plaats_overlay(breedte, hoogte, hoek="rechtsboven", topmost=True)


def _sla_live_voorkeur(config, sleutel, waarde):
    """Schrijf één overlay-voorkeur weg zonder de rest van het profiel te verliezen."""
    if config is None:
        return
    config[sleutel] = waarde
    try:
        sla_explorer_config_op(config)
    except Exception:
        pass


def _plaats_drempelpaneel(paneel):
    """Drempelpaneel links; overlay blijft rechtsboven."""
    if paneel is None or not paneel.is_open:
        return
    _, scherm_h = _scherm_maten()
    y = 40
    paneel_h = min(820, max(520, scherm_h - y - 48))
    try:
        paneel.venster.geometry(f"{PANEEL_BREEDTE}x{int(paneel_h)}+16+{int(y)}")
    except Exception:
        pass


def _hwnd_leeft(hwnd):
    """True als Windows het venster nog kent (niet: of het zichtbaar/in focus is)."""
    try:
        if not hwnd:
            return False
        iw = ctypes.windll.user32.IsWindow
        iw.argtypes = [ctypes.c_void_p]
        iw.restype = ctypes.c_bool
        return bool(iw(hwnd))
    except Exception:
        return False


def _hwnd_norm(hwnd):
    try:
        return int(hwnd) if hwnd else 0
    except Exception:
        return 0


def _voorgrond_hwnd():
    try:
        gfw = ctypes.windll.user32.GetForegroundWindow
        gfw.restype = ctypes.c_void_p
        return gfw() or 0
    except Exception:
        return 0


def _venster_titel(hwnd):
    """Titel van een HWND, of lege string. Geen hooks, geen injectie."""
    if not hwnd:
        return ""
    try:
        n = ctypes.windll.user32.GetWindowTextLengthW(hwnd) + 1
        buf = ctypes.create_unicode_buffer(max(n, 2))
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, n)
        return (buf.value or "").strip()
    except Exception:
        return ""


def _wortel_hwnd(hwnd):
    try:
        ga = ctypes.windll.user32.GetAncestor
        ga.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        ga.restype = ctypes.c_void_p
        wortel = ga(hwnd, GA_ROOT)
        return wortel or hwnd
    except Exception:
        return hwnd


def _hwnd_schermvullend(hwnd):
    """True als het venster (vrijwel) het hele primaire scherm bedekt."""
    if not _hwnd_leeft(hwnd):
        return False
    try:
        r = _RECT()
        if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r)):
            return False
        sw, sh = _scherm_maten()
        return (r.right - r.left) >= sw - 8 and (r.bottom - r.top) >= sh - 8
    except Exception:
        return False


def _overlay_hwnd_leeft(titel=LIVE_VENSTER):
    """HWND van de overlay als het venster nog bestaat; anders 0.

    Niet WND_PROP_VISIBLE: die kan 0 worden als Communicator fullscreen
    ervoor zit, terwijl het overlay-venster nog leeft.
    """
    hwnd = _venster_hwnd(titel)
    return hwnd if _hwnd_leeft(hwnd) else 0


def _overlay_heeft_focus(titel=LIVE_VENSTER):
    hwnd = _overlay_hwnd_leeft(titel)
    return bool(hwnd and _hwnd_norm(_voorgrond_hwnd()) == _hwnd_norm(hwnd))


def _vk_naar_hotkey(vk):
    """Win32 virtuele toets → zelfde codes als de oude waitKeyEx-tak."""
    vk = int(vk) & 0xFF
    if vk in (VK_UP,):
        return 2490368
    if vk in (VK_DOWN,):
        return 2621440
    if vk == VK_PRIOR:
        return 2162688
    if vk == VK_NEXT:
        return 2228224
    if 0x30 <= vk <= 0x39 or 0x41 <= vk <= 0x5A:
        return vk
    return -1


_user32 = ctypes.windll.user32
_gdi32 = ctypes.windll.gdi32
_kernel32 = ctypes.windll.kernel32
_overlay_wndproc_c = None
_overlay_klasse_ok = False
_overlay_pending = None
_OVERLAY_INSTANTIES = {}
_win32_overlay_api_ok = False


def _init_win32_overlay_api():
    """64-bit HWND/HDC niet afkappen: restype c_void_p op alle GDI/User32-handles."""
    global _win32_overlay_api_ok
    if _win32_overlay_api_ok:
        return
    _user32.CreateWindowExW.restype = ctypes.c_void_p
    _user32.CreateWindowExW.argtypes = [
        ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
    ]
    _user32.DestroyWindow.argtypes = [ctypes.c_void_p]
    _user32.DefWindowProcW.restype = LRESULT
    _user32.DefWindowProcW.argtypes = [
        ctypes.c_void_p, ctypes.c_uint, WPARAM, LPARAM,
    ]
    _user32.RegisterClassExW.restype = ctypes.c_ushort
    _user32.GetDC.restype = ctypes.c_void_p
    _user32.GetDC.argtypes = [ctypes.c_void_p]
    _user32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    _user32.UpdateLayeredWindow.restype = ctypes.c_int
    _user32.UpdateLayeredWindow.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint,
    ]
    _user32.PeekMessageW.restype = ctypes.c_int
    _user32.PeekMessageW.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
    ]
    _user32.TranslateMessage.restype = ctypes.c_int
    _user32.TranslateMessage.argtypes = [ctypes.c_void_p]
    _user32.DispatchMessageW.restype = LRESULT
    _user32.DispatchMessageW.argtypes = [ctypes.c_void_p]
    _user32.SetWindowPos.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint,
    ]
    _user32.LoadCursorW.restype = ctypes.c_void_p
    _user32.LoadCursorW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    _user32.SetWindowPos.restype = ctypes.c_int
    _user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
    _gdi32.CreateCompatibleDC.restype = ctypes.c_void_p
    _gdi32.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
    _gdi32.CreateDIBSection.restype = ctypes.c_void_p
    _gdi32.CreateDIBSection.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint,
        ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, ctypes.c_uint,
    ]
    _gdi32.SelectObject.restype = ctypes.c_void_p
    _gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    _gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
    _gdi32.DeleteDC.argtypes = [ctypes.c_void_p]
    _kernel32.GetModuleHandleW.restype = ctypes.c_void_p
    _kernel32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
    _kernel32.GetLastError.restype = ctypes.c_uint
    _win32_overlay_api_ok = True


def _overlay_wndproc(hwnd, msg, wparam, lparam):
    inst = _OVERLAY_INSTANTIES.get(_hwnd_norm(hwnd)) or _overlay_pending
    if inst is not None:
        return inst._handle(hwnd, msg, wparam, lparam)
    return _user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def _registreer_overlay_klasse():
    """Eenmalig WNDCLASS voor de PiP-overlay."""
    global _overlay_wndproc_c, _overlay_klasse_ok
    _init_win32_overlay_api()
    if _overlay_klasse_ok:
        return True
    if _overlay_wndproc_c is None:
        _overlay_wndproc_c = WNDPROC(_overlay_wndproc)
    wc = _WNDCLASSEXW()
    wc.cbSize = ctypes.sizeof(_WNDCLASSEXW)
    wc.style = CS_HREDRAW | CS_VREDRAW
    wc.lpfnWndProc = _overlay_wndproc_c
    wc.hInstance = _kernel32.GetModuleHandleW(None)
    wc.hCursor = _user32.LoadCursorW(None, ctypes.c_void_p(IDC_ARROW))
    wc.lpszClassName = OVERLAY_KLASSE
    atom = _user32.RegisterClassExW(ctypes.byref(wc))
    if atom:
        _overlay_klasse_ok = True
        return True
    if _kernel32.GetLastError() == ERROR_CLASS_ALREADY_EXISTS:
        _overlay_klasse_ok = True
        return True
    return False


class _LaagVenster:
    """PiP-overlay via WS_EX_LAYERED + UpdateLayeredWindow (geen OpenCV HighGUI).

    OpenCV imshow/waitKey bevriest boven Communicator 5 (DirectX): GDI-blit
    blokkeert of WindowFromPoint denkt dat C5 de overlay bedekt. Dit venster
    is een eigen topmost HWND; DWM composiet het boven vensterweergave.
    Exclusive fullscreen kan het beeld alsnog onzichtbaar maken.
    """

    def __init__(self, titel=LIVE_VENSTER):
        self.titel = titel
        self.hwnd = 0
        self._gesloten = False
        self._keys = []
        self._klik = None
        self._hdc_mem = None
        self._hbm = None
        self._hbm_prev = None
        self._bits = None
        self._dib_w = 0
        self._dib_h = 0

    @property
    def gesloten(self):
        return self._gesloten

    def heropen(self):
        """Na sluiten opnieuw mogen tekenen (knop Overlay naar voren)."""
        self._gesloten = False
        self._keys.clear()
        if self.hwnd and _hwnd_leeft(self.hwnd):
            try:
                _user32.ShowWindow(self.hwnd, SW_RESTORE)
            except Exception:
                pass
            self.zet_topmost(True)
            try:
                ctypes.windll.user32.SetForegroundWindow(self.hwnd)
            except Exception:
                pass
            return True
        self.hwnd = 0
        return False

    def maak(self, breedte, hoogte, x, y, topmost=True):
        if self.hwnd and _hwnd_leeft(self.hwnd):
            return True
        if not _registreer_overlay_klasse():
            log_message("Overlay-vensterklasse registreren mislukt")
            return False
        self._gesloten = False
        ex = WS_EX_LAYERED | WS_EX_TOOLWINDOW
        if topmost:
            ex |= WS_EX_TOPMOST
        style = WS_POPUP | WS_VISIBLE
        global _overlay_pending
        _overlay_pending = self
        try:
            hwnd = _user32.CreateWindowExW(
                ex, OVERLAY_KLASSE, self.titel, style,
                int(x), int(y), int(breedte), int(hoogte),
                None, None, _kernel32.GetModuleHandleW(None), None,
            )
        finally:
            _overlay_pending = None
        if not hwnd:
            log_message(
                f"CreateWindowEx overlay mislukt, error={_kernel32.GetLastError()}"
            )
            return False
        self.hwnd = hwnd
        _OVERLAY_INSTANTIES[_hwnd_norm(hwnd)] = self
        hdc_scherm = _user32.GetDC(None)
        self._hdc_mem = _gdi32.CreateCompatibleDC(hdc_scherm)
        if hdc_scherm:
            _user32.ReleaseDC(None, hdc_scherm)
        if not self._hdc_mem:
            self.sluit()
            return False
        return True

    def zet_topmost(self, aan=True):
        if not self.hwnd or not _hwnd_leeft(self.hwnd):
            return False
        try:
            _user32.SetWindowPos(
                self.hwnd,
                HWND_TOPMOST if aan else HWND_NOTOPMOST,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
            )
            return True
        except Exception:
            return False

    def heeft_focus(self):
        return bool(
            self.hwnd
            and _hwnd_leeft(self.hwnd)
            and _hwnd_norm(_voorgrond_hwnd()) == _hwnd_norm(self.hwnd)
        )

    def _zorg_dib(self, w, h):
        if self._hbm and self._dib_w == w and self._dib_h == h and self._bits:
            return True
        if not self._hdc_mem:
            return False
        bmi = _BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = int(w)
        bmi.bmiHeader.biHeight = -int(h)
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = BI_RGB
        bits = ctypes.c_void_p()
        hbm = _gdi32.CreateDIBSection(
            self._hdc_mem, ctypes.byref(bmi), DIB_RGB_COLORS,
            ctypes.byref(bits), None, 0,
        )
        if not hbm or not bits:
            return False
        prev = _gdi32.SelectObject(self._hdc_mem, hbm)
        if self._hbm:
            _gdi32.DeleteObject(self._hbm)
        else:
            self._hbm_prev = prev
        self._hbm = hbm
        self._bits = bits
        self._dib_w = int(w)
        self._dib_h = int(h)
        return True

    def toon(self, bgr, x, y, topmost=True):
        """Zet één frame in de overlay. False = deze frame mislukt, retry later."""
        if self._gesloten:
            return False
        bgr = naar_contiguous_beeld(bgr)
        if bgr is None:
            return False
        h, w = bgr.shape[:2]
        if w <= 0 or h <= 0:
            return False
        if not self.hwnd or not _hwnd_leeft(self.hwnd):
            if not self.maak(w, h, x, y, topmost=topmost):
                return False
        if not self._zorg_dib(w, h):
            return False
        try:
            bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
            bgra = np.ascontiguousarray(bgra)
        except Exception:
            return False
        if bgra.nbytes != w * h * 4:
            return False
        try:
            ctypes.memmove(self._bits, int(bgra.ctypes.data), int(bgra.nbytes))
            pt_dst = _POINT(int(x), int(y))
            size = _SIZE(int(w), int(h))
            pt_src = _POINT(0, 0)
            blend = _BLENDFUNCTION(AC_SRC_OVER, 0, 255, 0)
            ok = _user32.UpdateLayeredWindow(
                self.hwnd, None,
                ctypes.byref(pt_dst), ctypes.byref(size),
                self._hdc_mem, ctypes.byref(pt_src),
                0, ctypes.byref(blend), ULW_ALPHA,
            )
            return bool(ok)
        except Exception:
            return False

    def pompen(self):
        """Niet-blokkerende message-pump (alleen dit HWND). Geen waitKey."""
        if not self.hwnd or not _hwnd_leeft(self.hwnd):
            return -1
        msg = _MSG()
        while _user32.PeekMessageW(
            ctypes.byref(msg), self.hwnd, 0, 0, PM_REMOVE
        ):
            _user32.TranslateMessage(ctypes.byref(msg))
            _user32.DispatchMessageW(ctypes.byref(msg))
        if self._keys:
            return self._keys.pop(0)
        return -1

    def neem_klik(self):
        """Laatste muisklik (x, y) in het camerabeeld, of None. Wist de klik."""
        klik, self._klik = self._klik, None
        return klik

    def _handle(self, hwnd, msg, wparam, lparam):
        if msg in (WM_KEYDOWN, WM_SYSKEYDOWN):
            key = _vk_naar_hotkey(wparam)
            if key >= 0:
                self._keys.append(key)
            return 0
        if msg == WM_LBUTTONUP:
            # client-coördinaten (signed 16-bit) = pixels van het camerabeeld
            x = ctypes.c_short(lparam & 0xFFFF).value
            y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
            self._klik = (x, y)
            return 0
        if msg == WM_CLOSE:
            self._gesloten = True
            _user32.DestroyWindow(hwnd)
            return 0
        if msg == WM_DESTROY:
            self._na_destroy(hwnd)
            return 0
        return _user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _na_destroy(self, hwnd):
        _OVERLAY_INSTANTIES.pop(_hwnd_norm(hwnd), None)
        if _hwnd_norm(self.hwnd) == _hwnd_norm(hwnd):
            self.hwnd = 0
        self._gesloten = True
        self._vrij_gdi()

    def _vrij_gdi(self):
        if self._hdc_mem:
            if self._hbm_prev:
                _gdi32.SelectObject(self._hdc_mem, self._hbm_prev)
                self._hbm_prev = None
            if self._hbm:
                _gdi32.DeleteObject(self._hbm)
                self._hbm = None
            _gdi32.DeleteDC(self._hdc_mem)
            self._hdc_mem = None
        self._bits = None
        self._dib_w = 0
        self._dib_h = 0

    def sluit(self):
        self._gesloten = True
        hwnd = self.hwnd
        if hwnd and _hwnd_leeft(hwnd):
            _user32.DestroyWindow(hwnd)
        else:
            self.hwnd = 0
            self._vrij_gdi()
            _OVERLAY_INSTANTIES.pop(_hwnd_norm(hwnd), None)


def _breng_overlay_naar_voren(topmost=True):
    """Zet de overlay vooraan — alleen op gebruikersactie (knop)."""
    hwnd = _overlay_hwnd_leeft()
    if not hwnd:
        return 0
    try:
        ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
    except Exception:
        pass
    _zet_venster_topmost(LIVE_VENSTER, aan=topmost)
    try:
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception:
        pass
    return hwnd


def _voorgrond_doel_tekst(overlay_hwnd=0):
    """Korte Nederlandse status: waar SendInput-toetsen terechtkomen."""
    fg = _voorgrond_hwnd()
    titel = _venster_titel(fg) or "onbekend programma"
    if overlay_hwnd and _hwnd_norm(fg) == _hwnd_norm(overlay_hwnd):
        return (
            "Actief venster: het camerabeeld van Studio\n"
            "Let op: je toetsen komen nu hier terecht. Klik op Communicator 5 "
            "(of je eigen programma) om dat het actieve venster te maken."
        )
    if len(titel) > 48:
        titel = titel[:46] + "…"
    return (
        f"Actief venster: {titel}\n"
        "Je mimiek-toetsen gaan naar dit venster."
    )


def _live_status_banner(
    overlay_hwnd=0, overlay_melding="", toets_fout="", uipi="",
):
    """Drempelpaneel-status: doel van toetsen, overlay, admin/UIPI."""
    regels = [_voorgrond_doel_tekst(overlay_hwnd)]
    fg = _voorgrond_hwnd()
    eigen_fg = bool(
        overlay_hwnd and _hwnd_norm(fg) == _hwnd_norm(overlay_hwnd)
    )
    if uipi:
        regels.append(uipi)
    if overlay_melding:
        regels.append(overlay_melding)
    if toets_fout:
        regels.append(toets_fout)
    return "\n".join(regels)


# ---------------------------------------------------------------------------
# CustomTkinter slider-paneel met filter-checkboxes
# ---------------------------------------------------------------------------
class DrempelPaneel:
    """
    Apart CTk-venster dat naast het webcam-venster verschijnt.
    Toont per trigger de blendshapes met sliders voor drempels
    en checkboxes om zichtbaarheid in het info-paneel te regelen.
    """

    def __init__(self, triggers):
        self._triggers = triggers
        self._gesloten = False
        self._slider_refs = {}
        self._waarde_refs = {}
        self._status_refs = {}
        self._filter_vars = {}    # {(trigger_idx, bs_naam): IntVar}
        self._trigger_actief_vars = {}  # {trigger_idx: IntVar} — actief/inactief
        self._actief_labels = {}        # {trigger_idx: CTkLabel}
        self._status_cache = {}
        self._banner_cache = None
        self._banner_lbl = None
        self._stop_gevraagd = False
        self._overlay_voor_gevraagd = False
        self._lock = threading.Lock()

        scherm_w, scherm_h = _scherm_maten()
        start_h = min(820, max(520, scherm_h - 80))
        start_x = max(40, scherm_w - PANEEL_BREEDTE - 24)

        self.venster = ctk.CTkToplevel()
        self.venster.title("Drempels — MimiControl Studio v2")
        self.venster.configure(fg_color=BG)
        self.venster.geometry(f"{PANEEL_BREEDTE}x{start_h}+{start_x}+40")
        self.venster.minsize(380, 400)
        self.venster.resizable(True, True)
        self.venster.protocol("WM_DELETE_WINDOW", self._sluit)

        try:
            # Alleen de camera-overlay blijft always-on-top (Communicator 5).
            self.venster.attributes("-topmost", False)
        except Exception:
            pass

        self._bouw_ui()

    def _bouw_ui(self):
        header = ctk.CTkFrame(self.venster, fg_color=DONKER, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="Live Drempels & Filter",
            font=(FONT, 16, "bold"), text_color=KAART
        ).pack(pady=14)

        ctk.CTkLabel(
            self.venster,
            text="Schakelaar: trigger aan/uit   ·   Schuifbalk: hoe sterk de beweging moet zijn",
            font=(FONT, 10), text_color=TEKST_LICHT
        ).pack(pady=(6, 2))

        banner = ctk.CTkFrame(
            self.venster, fg_color="#E8F6F7", corner_radius=8
        )
        banner.pack(fill="x", padx=12, pady=(4, 6))
        self._banner_lbl = ctk.CTkLabel(
            banner,
            text="Actief venster: wordt bepaald…\nJe mimiek-toetsen gaan naar het actieve venster.",
            font=(FONT, 11), text_color=DONKER,
            wraplength=PANEEL_BREEDTE - 48, justify="left", anchor="w",
        )
        self._banner_lbl.pack(fill="x", padx=10, pady=8)

        scroll = ctk.CTkScrollableFrame(self.venster, fg_color=BG, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        for t_idx, trigger in enumerate(self._triggers):
            if not trigger.get("blendshapes"):
                continue

            accent = trigger_kleur_hex(t_idx)

            kaart = ctk.CTkFrame(scroll, fg_color=KAART, corner_radius=12,
                                 border_width=1, border_color=RAND)
            kaart.pack(fill="x", padx=12, pady=6)

            ctk.CTkFrame(kaart, fg_color=accent, height=3, corner_radius=0
                         ).pack(fill="x", padx=10, pady=(8, 0))

            titel_rij = ctk.CTkFrame(kaart, fg_color="transparent")
            titel_rij.pack(fill="x", padx=12, pady=(6, 2))

            toets = _toets_tekst(trigger["toetsen"])
            ctk.CTkLabel(
                titel_rij, text=f"{trigger['naam']}",
                font=(FONT, 13, "bold"), text_color=TEKST
            ).pack(side="left")

            ctk.CTkLabel(
                titel_rij, text=toets, font=(FONT, 11, "bold"),
                text_color=KAART, fg_color=accent, corner_radius=8,
                width=60, height=24
            ).pack(side="right", padx=(4, 0))

            status_lbl = ctk.CTkLabel(
                titel_rij, text="—", font=(FONT, 11),
                text_color=TEKST_LICHT
            )
            status_lbl.pack(side="right", padx=(0, 8))
            self._status_refs[t_idx] = status_lbl

            # Actief/inactief toggle per trigger (sessie-only, niet opgeslagen)
            trigger_var = ctk.IntVar(value=1)
            self._trigger_actief_vars[t_idx] = trigger_var
            master_rij = ctk.CTkFrame(kaart, fg_color="transparent")
            master_rij.pack(fill="x", padx=14, pady=(4, 2))

            actief_lbl = ctk.CTkLabel(
                master_rij, text="ACTIEF", font=(FONT, 12, "bold"),
                text_color="#22AA44", width=90, anchor="w"
            )
            self._actief_labels[t_idx] = actief_lbl

            def _on_toggle(var=trigger_var, lbl=actief_lbl):
                if var.get() == 1:
                    lbl.configure(text="ACTIEF", text_color="#22AA44")
                else:
                    lbl.configure(text="INACTIEF", text_color="#999999")

            ctk.CTkSwitch(
                master_rij, text="",
                variable=trigger_var, onvalue=1, offvalue=0,
                progress_color=accent, button_color=KAART,
                button_hover_color=RAND, fg_color="#999999",
                switch_width=44, switch_height=22,
                command=_on_toggle
            ).pack(side="left")
            actief_lbl.pack(side="left", padx=(8, 0))

            for bs_naam, drempel in _bruikbare_blendshapes(trigger).items():
                rij = ctk.CTkFrame(kaart, fg_color="transparent")
                rij.pack(fill="x", padx=14, pady=2)

                filter_var = ctk.IntVar(value=1)
                self._filter_vars[(t_idx, bs_naam)] = filter_var
                ctk.CTkCheckBox(
                    rij, text="", width=24, height=24,
                    variable=filter_var,
                    fg_color=TEAL_BTN, hover_color=TEAL_HOVER,
                    checkbox_width=18, checkbox_height=18
                ).pack(side="left", padx=(0, 4))

                ctk.CTkLabel(
                    rij, text=nl_label(bs_naam),
                    font=(FONT, 11), text_color=TEKST_LICHT,
                    width=130, anchor="w"
                ).pack(side="left")

                waarde_lbl = ctk.CTkLabel(
                    rij, text=f"{drempel:.2f}", font=(FONT, 11, "bold"),
                    text_color=TEKST, width=44, anchor="e"
                )
                waarde_lbl.pack(side="right", padx=(4, 2))
                self._waarde_refs[(t_idx, bs_naam)] = waarde_lbl

                slider = ctk.CTkSlider(
                    rij, from_=0.0, to=1.0,
                    button_color=TEAL_BTN, button_hover_color=TEAL_HOVER,
                    progress_color=TEAL_BTN,
                    command=lambda val, ti=t_idx, bn=bs_naam: self._on_slider(ti, bn, val)
                )
                slider.set(drempel)
                slider.pack(side="left", fill="x", expand=True, padx=(4, 4))
                self._slider_refs[(t_idx, bs_naam)] = slider

            ctk.CTkFrame(kaart, fg_color="transparent", height=6).pack()

        btn_frame = ctk.CTkFrame(self.venster, fg_color=BG, height=112)
        btn_frame.pack(fill="x")
        btn_frame.pack_propagate(False)
        knop_rij = ctk.CTkFrame(btn_frame, fg_color="transparent")
        knop_rij.pack(fill="x", padx=12, pady=(10, 4))
        knop_rij.grid_columnconfigure((0, 1), weight=1, uniform="knop")
        ctk.CTkButton(
            knop_rij, text="Stop live", font=(FONT, 12, "bold"),
            fg_color="#E05A50", hover_color="#C44840",
            corner_radius=12, height=36,
            command=self._stop_live
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkButton(
            knop_rij, text="Opslaan en sluiten", font=(FONT, 12, "bold"),
            fg_color=TEAL_BTN, hover_color=TEAL_HOVER,
            corner_radius=12, height=36,
            command=self._sluit
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ctk.CTkButton(
            knop_rij, text="Camerabeeld naar voren", font=(FONT, 12, "bold"),
            fg_color=DONKER, hover_color="#0A4050",
            corner_radius=12, height=36,
            command=self._vraag_overlay_voor
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    def _on_slider(self, trigger_idx, bs_naam, waarde):
        """Real-time drempel aanpassen bij slider-beweging."""
        val = round(waarde, 3)
        with self._lock:
            self._triggers[trigger_idx]["blendshapes"][bs_naam] = val
        lbl = self._waarde_refs.get((trigger_idx, bs_naam))
        if lbl:
            lbl.configure(text=f"{val:.2f}")

    def update_status(self, trigger_idx, actief, score_tekst=""):
        """Wordt aangeroepen vanuit de webcam-loop om de status bij te werken."""
        sleutel = (actief, score_tekst)
        if self._status_cache.get(trigger_idx) == sleutel:
            return
        self._status_cache[trigger_idx] = sleutel
        lbl = self._status_refs.get(trigger_idx)
        if lbl and not self._gesloten:
            try:
                if actief:
                    lbl.configure(text="ACTIEF", text_color="#22AA44")
                else:
                    lbl.configure(text=score_tekst if score_tekst else "inactief",
                                  text_color=TEKST_LICHT)
            except Exception:
                pass

    def haal_drempel(self, trigger_idx, bs_naam):
        """Thread-safe drempel ophalen."""
        with self._lock:
            return self._triggers[trigger_idx]["blendshapes"].get(bs_naam, 0)

    def is_zichtbaar(self, trigger_idx, bs_naam):
        """Check of een blendshape zichtbaar moet zijn in het info-paneel."""
        if self._gesloten:
            return True
        var = self._filter_vars.get((trigger_idx, bs_naam))
        if var is None:
            return True
        try:
            return var.get() == 1
        except Exception:
            return True

    def is_trigger_actief(self, trigger_idx):
        """Check of een trigger actief is (voert acties uit en toont normaal)."""
        if self._gesloten:
            return True
        var = self._trigger_actief_vars.get(trigger_idx)
        if var is None:
            return True
        try:
            return var.get() == 1
        except Exception:
            return True

    def update_achtergrond_banner(self, tekst):
        """Werk de achtergrond-statusregel bij (zelfde thread als live-loop)."""
        if self._gesloten or self._banner_lbl is None:
            return
        if self._banner_cache == tekst:
            return
        self._banner_cache = tekst
        try:
            self._banner_lbl.configure(text=tekst)
        except Exception:
            pass

    def _stop_live(self):
        """Live-loop stoppen zonder het paneel meteen te vernietigen."""
        self._stop_gevraagd = True

    def _vraag_overlay_voor(self):
        """Gebruikersactie: overlay zichtbaar maken (mag focus nemen)."""
        self._overlay_voor_gevraagd = True

    def neem_overlay_voor(self):
        """True één keer als de gebruiker Overlay naar voren klikte."""
        if self._overlay_voor_gevraagd:
            self._overlay_voor_gevraagd = False
            return True
        return False

    @property
    def stop_gevraagd(self):
        return self._stop_gevraagd

    def _sluit(self):
        """Config opslaan en venster sluiten."""
        self._gesloten = True
        config = laad_explorer_config()
        for i, trigger in enumerate(self._triggers):
            if i < len(config["triggers"]):
                config["triggers"][i]["blendshapes"] = trigger["blendshapes"]
        sla_explorer_config_op(config)
        self.venster.destroy()

    @property
    def is_open(self):
        return not self._gesloten


def _wacht_op_geldig_frame(cap, pogingen=8, wachttijd=0.25):
    """Lees tot een frame met geldige maat én stride binnenkomt."""
    for _ in range(pogingen):
        try:
            ret, frame = cap.read()
            if ret and naar_contiguous_beeld(frame) is not None:
                return True
        except Exception:
            pass
        time.sleep(wachttijd)
    return False


# ---------------------------------------------------------------------------
# Robuuste webcam-opening met retry en DirectShow fallback
# ---------------------------------------------------------------------------
def _open_webcam_robuust(camera_index, max_pogingen=3, wachttijd=1.5):
    """
    Probeer de webcam te openen met retry-logica.
    Retourneert (cap, foutmelding) — cap is None bij falen.
    """
    for poging in range(1, max_pogingen + 1):
        try:
            print(f"  [INFO] Webcam openen (poging {poging}/{max_pogingen})...")
            if poging > 1:
                cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(camera_index)
        except Exception as e:
            print(f"  [!] Fout bij openen webcam: {e}")
            if poging < max_pogingen:
                time.sleep(wachttijd)
            continue

        if not cap.isOpened():
            print(f"  [!] Webcam niet beschikbaar (poging {poging})")
            try:
                cap.release()
            except Exception:
                pass
            if poging < max_pogingen:
                time.sleep(wachttijd)
            continue

        # Resolutie EERST zetten, daarna pas een geldig frame eisen.
        # Anders levert de camera na CAP_PROP-wijziging frames met stride 0
        # of step < minstep (OpenCV cv::Mat::Mat assertion).
        _begrens_capture(cap)
        frame_ok = _wacht_op_geldig_frame(cap)

        if not frame_ok:
            print(f"  [!] Geen bruikbaar frame na 1280x720 — native resolutie")
            try:
                cap.release()
            except Exception:
                pass
            try:
                if poging > 1:
                    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                else:
                    cap = cv2.VideoCapture(camera_index)
            except Exception as e:
                print(f"  [!] Fout bij heropenen webcam: {e}")
                if poging < max_pogingen:
                    time.sleep(wachttijd)
                continue
            if not cap.isOpened():
                try:
                    cap.release()
                except Exception:
                    pass
                if poging < max_pogingen:
                    time.sleep(wachttijd)
                continue
            frame_ok = _wacht_op_geldig_frame(cap)

        if frame_ok:
            print(f"  [OK] Webcam geopend op poging {poging}")
            return cap, None

        print(f"  [!] Kan geen frame lezen van webcam (poging {poging})")
        try:
            cap.release()
        except Exception:
            pass
        if poging < max_pogingen:
            time.sleep(wachttijd)

    fout = (
        f"Kan webcam {camera_index} niet openen na {max_pogingen} pogingen.\n\n"
        "Mogelijke oorzaken:\n"
        "- Webcam is in gebruik door een ander programma\n"
        "- Webcam is niet aangesloten\n"
        "- Webcam wordt niet ondersteund\n\n"
        "Probeer een andere camera-index in de instellingen."
    )
    return None, fout


# ---------------------------------------------------------------------------
# Info-paneel NAAST het webcambeeld (donkere Mennens.Tech stijl)
# Alleen actieve triggers worden getoond (uitgeschakelde verdwijnen,
# zodat de layout inklapt en onderste triggers zichtbaar blijven).
# Hoogte volgt de webcam; geen vaste 500 px-cap.
# Ondersteunt scrolling via pijltjestoetsen als de inhoud hoger is.
# ---------------------------------------------------------------------------
def _maak_info_paneel(breedte, trigger_data, trigger_states,
                      nu, vasthoud_tijd, laatste_actie, cooldown,
                      actie_flash, actie_idx, gezicht_ok, paneel=None,
                      scroll_offset=0, max_hoogte=720, gepauzeerd=False):
    """
    Bouw een donker info-paneel als numpy-array.
    Alleen actieve triggers; uitgeschakelde worden overgeslagen zodat
    de resterende triggers de verticale ruimte gebruiken.
    Retourneert (panel_array, inhoud_hoogte).
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    MAX_CANVAS = max(400, min(1800, int(max_hoogte) + 800))

    breedte = max(1, int(breedte))
    max_hoogte = max(1, int(max_hoogte))
    info = np.full((MAX_CANVAS, breedte, 3), BGR_DONKER, dtype=np.uint8)
    cv2.rectangle(info, (0, 0), (breedte, 3), BGR_TEAL, -1)

    y = 30

    if not gezicht_ok and not gepauzeerd:
        cv2.putText(info, "GEEN GEZICHT GEDETECTEERD",
                    (15, y), font, 0.65, BGR_ROOD, 2)
        panel = np.ascontiguousarray(info[:max(y + 25, 60), :, :])
        return panel, panel.shape[0]

    if gepauzeerd:
        cv2.putText(info, "GEPAUZEERD - druk P om te hervatten",
                    (15, y), font, 0.55, BGR_TEAL, 2)
        y += 30

    in_cooldown = (nu - laatste_actie) < cooldown
    actie_recent = (nu - actie_flash) < 1.0

    # Alleen actieve triggers tekenen (uitgeschakelde nemen geen ruimte in)
    getekend = 0
    for i in range(len(trigger_data)):
        td = trigger_data[i]
        trigger = td["trigger"]
        bs_matches = td["bs_matches"]
        alle_match = td["alle_match"]
        state = trigger_states[i]

        if paneel and hasattr(paneel, "is_trigger_actief"):
            if not paneel.is_trigger_actief(i):
                continue

        kleur = trigger_kleur_bgr(i)
        toets = " + ".join(trigger["toetsen"]).upper()

        # Status bepalen
        if actie_recent and actie_idx == i:
            status_tekst = "ACTIE UITGEVOERD!"
            status_kleur = (0, 255, 255)
            naam_kleur = (0, 255, 255)
            dikte = 2
        elif in_cooldown:
            rest = cooldown - (nu - laatste_actie)
            status_tekst = f"cooldown {rest:.1f}s"
            status_kleur = BGR_GRIJS
            naam_kleur = BGR_GRIJS
            dikte = 1
        elif alle_match and state["start"] is not None:
            duur = nu - state["start"]
            status_tekst = f"ACTIEF  {duur:.1f}s / {vasthoud_tijd:.1f}s"
            status_kleur = BGR_GROEN
            naam_kleur = BGR_WIT
            dikte = 2
        elif alle_match:
            status_tekst = "ACTIEF"
            status_kleur = BGR_GROEN
            naam_kleur = BGR_WIT
            dikte = 2
        else:
            status_tekst = "inactief"
            status_kleur = BGR_DONKERGRIJS
            naam_kleur = (200, 200, 200)
            dikte = 1

        # Accentlijn links van de trigger
        cv2.rectangle(info, (8, y - 16), (12, y + 4), kleur, -1)

        # Trigger naam + toets
        cv2.putText(info, trigger["naam"], (18, y), font, 0.6, naam_kleur, 2)
        naam_breedte = cv2.getTextSize(trigger["naam"], font, 0.6, 2)[0][0]
        cv2.putText(info, f"[{toets}]", (22 + naam_breedte, y),
                    font, 0.45, BGR_TEAL, 1)

        # Status rechts uitgelijnd
        status_breedte = cv2.getTextSize(status_tekst, font, 0.5, 1)[0][0]
        cv2.putText(info, status_tekst,
                    (breedte - status_breedte - 15, y),
                    font, 0.5, status_kleur, dikte)

        # Voortgangsbalk bij vasthouden
        if alle_match and state["start"] is not None and not in_cooldown:
            duur = nu - state["start"]
            vr = min(duur / vasthoud_tijd, 1.0)
            bar_y = y + 5
            bar_x = breedte - 240
            bar_w = 220
            cv2.rectangle(info, (bar_x, bar_y), (bar_x + bar_w, bar_y + 7),
                          BGR_DONKERGRIJS, -1)
            cv2.rectangle(info, (bar_x, bar_y),
                          (bar_x + int(bar_w * vr), bar_y + 7),
                          BGR_GROEN, -1)
            y += 14

        y += 28

        # Blendshapes per trigger
        for bs_naam, (score, drempel, match) in bs_matches.items():
            if paneel and not paneel.is_zichtbaar(i, bs_naam):
                continue

            bs_label = nl_label(bs_naam)
            if len(bs_label) > 24:
                bs_label = bs_label[:22] + ".."

            tekst_kleur = BGR_WIT if match else (170, 170, 170)
            cv2.putText(info, bs_label, (30, y), font, 0.48, tekst_kleur, 1)

            waarde_tekst = f"{score:.2f} / {drempel:.2f}"
            waarde_kleur = BGR_GROEN if match else BGR_ROOD
            cv2.putText(info, waarde_tekst, (220, y), font, 0.42,
                        waarde_kleur, 1)

            # Score-balk
            bar_x = breedte - 240
            bar_w = 220
            bar_h = 15
            bar_y_top = y - 12

            cv2.rectangle(info, (bar_x, bar_y_top),
                          (bar_x + bar_w, bar_y_top + bar_h),
                          (30, 30, 30), -1)

            score_px = int(bar_w * min(score, 1.0))
            bar_kleur = BGR_GROEN if match else BGR_ROOD
            if score_px > 0:
                cv2.rectangle(info, (bar_x, bar_y_top),
                              (bar_x + score_px, bar_y_top + bar_h),
                              bar_kleur, -1)

            drempel_px = int(bar_w * min(drempel, 1.0))
            cv2.line(info, (bar_x + drempel_px, bar_y_top - 2),
                     (bar_x + drempel_px, bar_y_top + bar_h + 2),
                     BGR_WIT, 2)

            y += 26

        # Scheiding tussen triggers
        y += 4
        cv2.line(info, (15, y), (breedte - 15, y), BGR_SCHEIDING, 1)
        y += 10
        getekend += 1

    if getekend == 0:
        cv2.putText(info, "Geen actieve triggers — zet er een aan in het drempelpaneel",
                    (15, y), font, 0.5, BGR_GRIJS, 1)
        y += 28

    # Footer
    footer = "Q=stop  P=pauze  Pijltjes=scroll  |  Sliders: drempels"
    cv2.putText(info, footer, (15, y + 4), font, 0.38, BGR_GRIJS, 1)
    y += 22

    inhoud_hoogte = max(y, 60)
    info = info[:inhoud_hoogte, :, :]

    # Scroll en max hoogte toepassen
    if inhoud_hoogte > max_hoogte:
        max_offset = inhoud_hoogte - max_hoogte
        offset = max(0, min(scroll_offset, max_offset))
        zichtbaar = info[offset:offset + max_hoogte, :, :].copy()

        # Scroll-indicatoren
        if offset > 0:
            cv2.rectangle(zichtbaar, (0, 0), (breedte, 20), BGR_DONKER, -1)
            cv2.rectangle(zichtbaar, (0, 0), (breedte, 3), BGR_TEAL, -1)
            cv2.putText(zichtbaar, "^^ scroll omhoog ^^",
                        (breedte // 2 - 70, 16), font, 0.4, BGR_TEAL, 1)
        if offset < max_offset:
            h = zichtbaar.shape[0]
            cv2.rectangle(zichtbaar, (0, h - 20), (breedte, h), BGR_DONKER, -1)
            cv2.putText(zichtbaar, "vv scroll omlaag vv",
                        (breedte // 2 - 70, h - 6), font, 0.4, BGR_TEAL, 1)

        return np.ascontiguousarray(zichtbaar), inhoud_hoogte

    return np.ascontiguousarray(info), inhoud_hoogte


def _actieve_trigger_index(trigger_data, actie_recent, actie_idx, paneel=None):
    """Index van de trigger die nu oplicht, of None."""
    if actie_recent and 0 <= actie_idx < len(trigger_data):
        return actie_idx
    for i, td in enumerate(trigger_data):
        if paneel and hasattr(paneel, "is_trigger_actief"):
            if not paneel.is_trigger_actief(i):
                continue
        if td.get("alle_match"):
            return i
    return None


def _beperkende_blendshape(bs_matches):
    """Blendshape die het verst van de drempel is (laagste score/drempel)."""
    if not bs_matches:
        return None
    worst = None
    for naam, (score, drempel, match) in bs_matches.items():
        ratio = float(score) / max(float(drempel), 1e-6)
        item = (ratio, naam, float(score), float(drempel), bool(match))
        if worst is None or ratio < worst[0]:
            worst = item
    return worst


def _maak_compacte_triggerbalk(breedte, hoogte, trigger_data, trigger_states,
                               nu, vasthoud_tijd, laatste_actie, cooldown,
                               actie_flash, actie_idx, gezicht_ok, paneel=None,
                               gepauzeerd=False, overlay_stap=2,
                               toetsen_sturen=True):
    """
    Triggerlijst naast de overlay-camera.
    Alleen actieve triggers: naam, kleur, huidige waarde vs drempel, AAN bij vuren.
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    breedte = max(1, int(breedte))
    hoogte = max(1, int(hoogte))
    overlay_stap = normaliseer_overlay_grootte(overlay_stap)
    info = np.full((hoogte, breedte, 3), BGR_DONKER, dtype=np.uint8)
    cv2.rectangle(info, (0, 0), (4, hoogte), BGR_TEAL, -1)

    y = 18
    footer_h = 16
    if not gezicht_ok and not gepauzeerd:
        cv2.putText(info, "Geen gezicht", (12, y), font, 0.42, BGR_ROOD, 1)
        y += 18

    if gepauzeerd:
        cv2.putText(info, "Gepauzeerd (P)", (12, y), font, 0.42, BGR_TEAL, 1)
        y += 18

    in_cooldown = (nu - laatste_actie) < cooldown
    actie_recent = (nu - actie_flash) < 1.0

    zichtbaar = []
    for i, td in enumerate(trigger_data):
        if paneel and hasattr(paneel, "is_trigger_actief"):
            if not paneel.is_trigger_actief(i):
                continue
        zichtbaar.append(i)

    n = len(zichtbaar)
    beschikbaar = max(20, hoogte - y - footer_h)
    if n == 0:
        cv2.putText(info, "Geen actieve triggers", (12, y + 12),
                    font, 0.40, BGR_GRIJS, 1)
        hint = HOTKEY_HINT if toetsen_sturen else "S=toetsen UIT  " + HOTKEY_HINT
        cv2.putText(info, hint, (8, hoogte - 5),
                    font, 0.30, BGR_GRIJS, 1)
        return np.ascontiguousarray(info)

    # Compact bij veel triggers of klein formaat; details als er ruimte is.
    toon_bs = overlay_stap >= 3 and n <= 5
    extra_bs = 0
    if toon_bs:
        extra_bs = max(
            (len(trigger_data[i].get("bs_matches") or {}) for i in zichtbaar),
            default=0,
        )
        extra_bs = min(extra_bs, 4)
    min_rij = 28 if overlay_stap >= 2 else 24
    gewenst = min_rij + (14 * extra_bs if toon_bs else 0)
    rij_h = max(22, min(gewenst, beschikbaar // n))
    toon_balk = rij_h >= 26
    toon_bs = toon_bs and rij_h >= 40

    for i in zichtbaar:
        if y > hoogte - footer_h - 12:
            break
        td = trigger_data[i]
        trigger = td["trigger"]
        alle_match = td["alle_match"]
        bs_matches = td.get("bs_matches") or {}
        kleur = trigger_kleur_bgr(i)
        naam = trigger.get("naam", f"Trigger {i + 1}")
        max_naam = 10 if breedte < 240 else (14 if breedte < 320 else 18)
        if len(naam) > max_naam:
            naam = naam[: max_naam - 2] + ".."

        beperkend = _beperkende_blendshape(bs_matches)
        if beperkend is not None:
            ratio, _bs_naam, score, drempel, _match = beperkend
        else:
            ratio, score, drempel = 0.0, 0.0, 1.0

        if actie_recent and actie_idx == i:
            status = "AAN"
            status_kleur = kleur
            naam_kleur = BGR_WIT
        elif in_cooldown:
            status = "wacht"
            status_kleur = BGR_GRIJS
            naam_kleur = BGR_GRIJS
        elif alle_match:
            status = "AAN"
            status_kleur = BGR_GROEN
            naam_kleur = BGR_WIT
        else:
            pct = int(max(0.0, min(ratio, 1.0)) * 100)
            status = f"{pct}%"
            status_kleur = BGR_GRIJS
            naam_kleur = (210, 210, 210)

        cv2.rectangle(info, (8, y - 11), (14, y + 3), kleur, -1)
        cv2.putText(info, naam, (18, y), font, 0.40, naam_kleur, 1)
        st_w = cv2.getTextSize(status, font, 0.40, 1)[0][0]
        cv2.putText(info, status, (breedte - st_w - 8, y),
                    font, 0.40, status_kleur, 1)

        balk_y = y + 6
        if toon_balk and balk_y + 8 < hoogte - footer_h:
            bar_x = 18
            bar_w = max(40, breedte - 26)
            bar_h = 8 if overlay_stap >= 2 else 6
            cv2.rectangle(
                info, (bar_x, balk_y), (bar_x + bar_w, balk_y + bar_h),
                (28, 28, 28), -1
            )
            score_px = int(bar_w * min(max(score, 0.0), 1.0))
            bar_kleur = kleur if alle_match else (
                BGR_GROEN if ratio >= 1.0 else BGR_TEAL
            )
            if score_px > 0:
                cv2.rectangle(
                    info, (bar_x, balk_y),
                    (bar_x + score_px, balk_y + bar_h),
                    bar_kleur, -1
                )
            drempel_px = int(bar_w * min(max(drempel, 0.0), 1.0))
            cv2.line(
                info,
                (bar_x + drempel_px, balk_y - 1),
                (bar_x + drempel_px, balk_y + bar_h + 1),
                BGR_WIT, 1
            )
            if overlay_stap >= 2:
                waarde = f"{score:.2f}/{drempel:.2f}"
                cv2.putText(
                    info, waarde, (bar_x, balk_y + bar_h + 11),
                    font, 0.32, BGR_GRIJS, 1
                )

        y += rij_h
        if toon_bs:
            getekend_bs = 0
            for bs_naam, (bs_score, bs_drempel, bs_match) in bs_matches.items():
                if getekend_bs >= extra_bs or y > hoogte - footer_h - 10:
                    break
                if paneel and not paneel.is_zichtbaar(i, bs_naam):
                    continue
                label = nl_label(bs_naam)
                if len(label) > 14:
                    label = label[:12] + ".."
                tekst_kleur = BGR_WIT if bs_match else (160, 160, 160)
                cv2.putText(info, label, (20, y), font, 0.32, tekst_kleur, 1)
                mini_x = max(110, breedte - 88)
                mini_w = max(36, breedte - mini_x - 8)
                mini_y = y - 8
                cv2.rectangle(
                    info, (mini_x, mini_y), (mini_x + mini_w, mini_y + 7),
                    (28, 28, 28), -1
                )
                fill = int(mini_w * min(max(float(bs_score), 0.0), 1.0))
                if fill > 0:
                    cv2.rectangle(
                        info, (mini_x, mini_y),
                        (mini_x + fill, mini_y + 7),
                        BGR_GROEN if bs_match else BGR_ROOD, -1
                    )
                drempel_px = int(mini_w * min(max(float(bs_drempel), 0.0), 1.0))
                cv2.line(
                    info,
                    (mini_x + drempel_px, mini_y - 1),
                    (mini_x + drempel_px, mini_y + 8),
                    BGR_WIT, 1
                )
                y += 14
                getekend_bs += 1

    hint = HOTKEY_HINT
    if not toetsen_sturen:
        hint = "S=toetsen UIT  " + HOTKEY_HINT
    cv2.putText(info, hint, (8, hoogte - 5),
                font, 0.30, BGR_GRIJS, 1)
    return np.ascontiguousarray(info)


def _toon_live_fout(bericht):
    """Foutmelding tonen; Live had eerder geen dialog en viel stil om."""
    print(f"  [!] {bericht}")
    try:
        from tkinter import messagebox as mb
        mb.showerror(
            "Live Fout — MimiControl Studio",
            f"De Live modus is onverwacht gestopt:\n\n{bericht}",
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Hoofdfunctie live modus
# ---------------------------------------------------------------------------
def start_live_explorer(camera_index=0, laad_ui=None, on_gereed=None):
    """
    Start de live modus met blendshape-triggers en live slider-paneel.

    Args:
        laad_ui: optioneel laadvenster met .status(tekst) en .sluit().
        on_gereed: callback zodra het webcambeeld start.
    """
    def _status(tekst, voortgang=None):
        if laad_ui is not None:
            try:
                laad_ui.status(tekst, voortgang)
            except Exception:
                pass

    def _sluit_laad_ui():
        if laad_ui is not None:
            try:
                laad_ui.sluit()
            except Exception:
                pass

    config = laad_explorer_config()
    triggers = config["triggers"]
    cooldown = config["cooldown"]
    vasthoud_tijd = config["vasthoud_tijd"]
    toets_duur_ms = config.get("toets_duur_ms", 100)
    overlay_aan = bool(config.get("overlay_aan", True))
    overlay_hud_aan = bool(config.get("overlay_hud_aan", True))
    overlay_grootte = normaliseer_overlay_grootte(config.get("overlay_grootte", 2))
    toetsen_sturen = bool(config.get("overlay_toetsen_sturen", True))
    overlay_topmost = bool(config.get("overlay_topmost", True))
    overlay_spiegel = bool(config.get("overlay_spiegel", True))
    toets_melding = bool(config.get("overlay_toets_melding", True))
    overlay_hoek = normaliseer_overlay_hoek(config.get("overlay_hoek", "rechtsboven"))
    overlay_alleen_camera = bool(config.get("overlay_alleen_camera", False))
    mesh_volledig = bool(config.get("mesh_volledig", False))

    actieve = [t for t in triggers if t.get("blendshapes")]
    if not actieve:
        print("\n  [!] Geen triggers geconfigureerd!")
        print("      Gebruik eerst de Explorer om triggers aan te maken.\n")
        return

    print("\n" + "=" * 50)
    print("  LIVE MODUS - MimiControl Studio")
    print("=" * 50)
    for i, t in enumerate(actieve):
        toets = " + ".join(t["toetsen"]).upper()
        bruikbaar = _bruikbare_blendshapes(t)
        bs_lijst = ", ".join(bruikbaar.keys()) if bruikbaar else "(geen bruikbare blendshapes)"
        print(f"  [{i+1}] {t['naam']:16s} -> {toets:10s}  ({bs_lijst})")
    print(f"\n  Cooldown: {cooldown}s  |  Vasthoudtijd: {vasthoud_tijd}s")
    cam_px = overlay_cam_maten(overlay_grootte)
    print(f"  Overlay: {'aan' if overlay_aan else 'uit'}  |  "
          f"Triggers: {'aan' if overlay_hud_aan else 'uit'}  |  "
          f"Grootte: {overlay_grootte} ({cam_px[0]}x{cam_px[1]})")
    print(f"  Hoek: {overlay_hoek_label(overlay_hoek)}  |  "
          f"Bovenop: {'aan' if overlay_topmost else 'uit'}  |  "
          f"Toetsen: {'aan' if toetsen_sturen else 'UIT'}  |  "
          f"Spiegel: {'aan' if overlay_spiegel else 'uit'}")
    print(f"  Mesh: {'volledig' if mesh_volledig else 'licht'}  |  "
          f"Alleen camera: {'aan' if overlay_alleen_camera else 'uit'}")
    print("  Q=stop P=pauze 1/2/3=grootte T=triggers S=toetsen")
    print("  A=bovenop M=mesh F=spiegel O=hoek C=alleen-camera")
    print("  [INFO] Slider-paneel wordt geopend voor live drempelaanpassingen.\n")

    _status("Instellingen-paneel wordt geopend…", 0.25)
    paneel = DrempelPaneel(actieve)

    # Robuust webcam openen met retry
    _status("Camera wordt gestart…", 0.5)
    cap, fout = _open_webcam_robuust(camera_index)
    if cap is None:
        print(f"  [!] {fout}")
        _sluit_laad_ui()
        try:
            from tkinter import messagebox as mb
            mb.showerror("Webcam Fout — MimiControl Studio", fout)
        except Exception:
            pass
        if paneel.is_open:
            paneel._sluit()
        return

    landmarker = None
    overlay_laag = None
    try:
        _status("Gezichtsmodel wordt geladen…", 0.8)
        landmarker = maak_blendshape_landmarker(modus="video")

        _status("Beeld wordt geopend…", 0.95)
        _sluit_laad_ui()
        if on_gereed is not None:
            try:
                on_gereed()
            except Exception:
                pass

        trigger_states = [{"start": None} for _ in actieve]
        laatste_actie = 0.0
        actie_flash = 0.0
        actie_idx = -1
        laatste_toets_tekst = ""
        laatste_toets_verstuurd = True
        ts = 0

        # Pauze- en overlay-state
        gepauzeerd = False
        pauze_frame = None
        scroll_offset = 0
        scores = {}
        landmarks = None
        hud_cache = None
        hud_tijd = 0.0
        ctk_tijd = 0.0
        overlay_geplaatst = False
        overlay_moet_plaatsen = False
        paneel_geplaatst = False
        overlay_zichtbaar = overlay_aan
        lege_frames = 0
        topmost_tijd = 0.0
        overlay_melding = ""
        toets_fout_melding = ""
        fg_cache = -1
        uipi_cache = ""
        overlay_laag = _LaagVenster(LIVE_VENSTER)

        print("  [INFO] Live besturing gestart.")
        print("  Mimiek-toetsen gaan naar het programma vooraan (SendInput).")
        print("  Studio-focus is niet nodig; Communicator 5 mag ook op volledig scherm.")
        print("  Studio en Communicator op hetzelfde administrator-niveau houden.")
        print("  Overlay-sneltoetsen (Q/P/…) alleen als de overlay is aangeklikt.")
        if overlay_zichtbaar:
            print(f"  Overlay: {overlay_hoek_label(overlay_hoek)}, "
                  f"{'altijd voorop' if overlay_topmost else 'gewoon venster'}. "
                  "Focus wordt niet gestolen. PiP blijft verversen boven vensterweergave.")
            print("  Overlay sluiten: alleen camera uit; drempelpaneel blijft.\n")
        else:
            print("  Overlay uit — sluit het drempelpaneel om te stoppen.\n")

        stop_arm_tijd = 0.0  # moment van de eerste klik op de stopknop
        while True:
            if paneel.stop_gevraagd:
                print("  [INFO] Live gestopt via drempelpaneel.")
                break
            if paneel.is_open and paneel.neem_overlay_voor():
                overlay_zichtbaar = True
                overlay_topmost = True
                overlay_moet_plaatsen = True
                overlay_melding = ""
                overlay_laag.heropen()
                hwnd = _breng_overlay_naar_voren(topmost=True)
                overlay_geplaatst = bool(hwnd) or bool(overlay_laag.hwnd)
                print("  [INFO] Overlay naar voren gehaald.")

            # Webcam frame lezen (of bevroren frame gebruiken bij pauze)
            if not gepauzeerd or pauze_frame is None:
                try:
                    ret, raw = cap.read()
                except Exception as e:
                    print(f"  [!] Fout bij lezen webcam frame: {e}")
                    break
                raw = naar_contiguous_beeld(raw) if ret else None
                if raw is None:
                    lege_frames += 1
                    if lege_frames > 45:
                        print("  [!] Geen bruikbaar camerabeeld meer.")
                        break
                    if overlay_zichtbaar and overlay_laag is not None:
                        try:
                            key = overlay_laag.pompen()
                        except Exception:
                            key = -1
                        if (key in (ord('q'), ord('Q'))
                                and overlay_laag.heeft_focus()):
                            break
                    elif not paneel.is_open:
                        break
                    continue
                lege_frames = 0

                if overlay_spiegel:
                    raw = cv2.flip(raw, 1)
                raw = naar_contiguous_beeld(raw)
                if raw is None:
                    continue
                pauze_frame = raw
                rgb = np.ascontiguousarray(cv2.cvtColor(raw, cv2.COLOR_BGR2RGB))
                ts += 33
                landmarks, scores = detecteer_blendshapes(landmarker, rgb, ts)
            else:
                raw = pauze_frame

            cam_max_w, cam_max_h = overlay_cam_maten(overlay_grootte)
            hud_w = overlay_hud_breedte(overlay_grootte)
            geschaald = _schaal_voor_weergave(raw, cam_max_w, cam_max_h)
            if geschaald is None:
                continue

            nu = time.time()
            gezicht_ok = landmarks is not None

            toon_hud = overlay_zichtbaar and overlay_hud_aan and not overlay_alleen_camera
            toon_mesh = (not overlay_alleen_camera) and landmarks is not None

            if toon_mesh:
                teken_face_mesh_simpel(
                    geschaald, landmarks, volledig=mesh_volledig
                )

            frame = _plak_in_kader(geschaald, cam_max_w, cam_max_h)
            if frame is None:
                continue
            cam_h, cam_w = frame.shape[:2]
            if cam_h <= 0 or cam_w <= 0:
                continue

            # Statusrand: groen bij gezicht, rood als geen gezicht
            if not overlay_alleen_camera:
                if gezicht_ok:
                    cv2.rectangle(frame, (0, 0), (cam_w - 1, cam_h - 1),
                                  (0, 120, 0), 2)
                else:
                    cv2.rectangle(frame, (0, 0), (cam_w - 1, cam_h - 1),
                                  (0, 0, 160), 2)
                    cv2.putText(frame, "Geen gezicht", (8, 22),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 220), 1)

            if gepauzeerd:
                cv2.rectangle(frame, (0, 0), (cam_w - 1, cam_h - 1), BGR_TEAL, 3)
                if not overlay_alleen_camera:
                    cv2.putText(frame, "PAUZE", (8, 22),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, BGR_TEAL, 1)

            # ---- Trigger detectie ----
            in_cooldown = (nu - laatste_actie) < cooldown
            gevuurd = False
            trigger_data = []

            for i, trigger in enumerate(actieve):
                bruikbaar = _bruikbare_blendshapes(trigger)
                if gepauzeerd or not gezicht_ok:
                    # Geen detectie bij pauze of geen gezicht
                    trigger_states[i]["start"] = None
                    bs_matches = {}
                    for bs_naam, drempel in bruikbaar.items():
                        huidige_score = scores.get(bs_naam, 0) if gepauzeerd else 0.0
                        drempel_val = (
                            paneel.haal_drempel(i, bs_naam)
                            if paneel.is_open
                            else drempel
                        )
                        bs_matches[bs_naam] = (huidige_score, drempel_val, False)
                    trigger_data.append({
                        "trigger": trigger,
                        "bs_matches": bs_matches,
                        "alle_match": False,
                    })
                    continue

                bs_matches = {}
                alle_match = bool(bruikbaar)
                for bs_naam, drempel in bruikbaar.items():
                    drempel = (paneel.haal_drempel(i, bs_naam)
                               if paneel.is_open
                               else drempel)
                    huidige_score = scores.get(bs_naam, 0)
                    match = huidige_score > drempel
                    bs_matches[bs_naam] = (huidige_score, drempel, match)
                    if not match:
                        alle_match = False

                trigger_data.append({
                    "trigger": trigger,
                    "bs_matches": bs_matches,
                    "alle_match": alle_match,
                })

                trigger_actief = not paneel.is_open or paneel.is_trigger_actief(i)

                if alle_match and not in_cooldown and not gevuurd and trigger_actief:
                    if trigger_states[i]["start"] is None:
                        trigger_states[i]["start"] = nu

                    if (nu - trigger_states[i]["start"]) >= vasthoud_tijd:
                        toetsen = trigger["toetsen"]
                        verstuurd_ok = False
                        if toetsen_sturen:
                            ok = voer_toetsen_uit(toetsen, duur_ms=toets_duur_ms)
                            verstuurd_ok = bool(ok)
                            if ok:
                                toets_fout_melding = ""
                            else:
                                toets_fout_melding = (
                                    laatste_toets_status()
                                    or "Toets niet verstuurd"
                                )
                                print(f"  [!] {toets_fout_melding}")
                                log_message(
                                    f"Toets niet verstuurd: {toets_fout_melding}"
                                )

                        laatste_actie = nu
                        actie_flash = nu
                        actie_idx = i
                        laatste_toets_tekst = _toets_tekst(toetsen)
                        laatste_toets_verstuurd = verstuurd_ok
                        gevuurd = True
                        for s in trigger_states:
                            s["start"] = None

                        toets_tekst = " + ".join(toetsen).upper()
                        extra = "" if toetsen_sturen else " (niet verstuurd)"
                        doel = _venster_titel(_voorgrond_hwnd()) or "onbekend programma"
                        print(
                            f"  >>> [{i+1}] {trigger['naam']}: {toets_tekst}{extra}"
                            f"  → {doel}"
                        )
                else:
                    trigger_states[i]["start"] = None

            # Triggerkleur op de overlay (rand + gloed); geen tiny HUD nodig
            actie_recent = (nu - actie_flash) < 1.0
            actief_idx = _actieve_trigger_index(
                trigger_data, actie_recent, actie_idx, paneel
            )
            if actief_idx is not None and not gepauzeerd:
                kleur = trigger_kleur_bgr(actief_idx)
                dikte = 4
                if actie_recent and actie_idx == actief_idx:
                    dikte = max(3, int(8 * (1 - (nu - actie_flash))))
                cv2.rectangle(frame, (0, 0), (cam_w - 1, cam_h - 1), kleur, dikte)
                if landmarks:
                    teken_gezicht_gloed(frame, landmarks, kleur, dikte=3)
                if not toon_hud and not overlay_alleen_camera:
                    naam = trigger_data[actief_idx]["trigger"].get(
                        "naam", f"Trigger {actief_idx + 1}"
                    )
                    if len(naam) > 22:
                        naam = naam[:20] + ".."
                    balk_h = 26
                    cv2.rectangle(
                        frame, (0, cam_h - balk_h), (cam_w, cam_h), kleur, -1
                    )
                    b, g, r = kleur
                    licht = (r * 0.3 + g * 0.59 + b * 0.11) > 150
                    tekst_kleur = (20, 20, 20) if licht else (255, 255, 255)
                    cv2.putText(
                        frame, naam, (8, cam_h - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, tekst_kleur, 1,
                    )
            elif overlay_zichtbaar and not toon_hud and not overlay_alleen_camera:
                cv2.putText(
                    frame, HOTKEY_HINT,
                    (8, cam_h - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, BGR_GRIJS, 1,
                )

            if (toets_melding and laatste_toets_tekst and not gepauzeerd
                    and (nu - actie_flash) < ACTIE_BADGE_S):
                _teken_actiebadge(
                    frame, cam_h, laatste_toets_tekst,
                    trigger_kleur_bgr(actie_idx) if actie_idx >= 0 else BGR_GRIJS,
                    laatste_toets_verstuurd,
                )

            canvas = frame
            if toon_hud:
                hud_verouderd = (
                    (hud_cache is None)
                    or ((nu - hud_tijd) >= HUD_INTERVAL_S)
                    or (hud_cache.shape[0] != cam_h)
                    or (hud_cache.shape[1] != hud_w)
                )
                if hud_verouderd:
                    info = _maak_compacte_triggerbalk(
                        hud_w, cam_h, trigger_data, trigger_states,
                        nu, vasthoud_tijd, laatste_actie, cooldown,
                        actie_flash, actie_idx, gezicht_ok,
                        paneel=paneel, gepauzeerd=gepauzeerd,
                        overlay_stap=overlay_grootte,
                        toetsen_sturen=toetsen_sturen,
                    )
                    info = naar_contiguous_beeld(info)
                    if info is None:
                        info = np.full(
                            (cam_h, hud_w, 3), BGR_DONKER, dtype=np.uint8
                        )
                    if info.shape[0] != cam_h or info.shape[1] != hud_w:
                        info = cv2.resize(
                            info, (hud_w, cam_h),
                            interpolation=cv2.INTER_AREA,
                        )
                    hud_cache = np.ascontiguousarray(info)
                    hud_tijd = nu
                else:
                    info = hud_cache
                if frame_is_ok(frame) and frame_is_ok(info) and frame.shape[0] == info.shape[0]:
                    canvas = np.ascontiguousarray(np.hstack([frame, info]))
                else:
                    canvas = frame

            stop_armed = bool(stop_arm_tijd) and (nu - stop_arm_tijd) <= STOP_BEVESTIG_S
            if not stop_armed:
                stop_arm_tijd = 0.0
            if overlay_zichtbaar and overlay_laag is not None:
                _teken_stop_knop(canvas, cam_w, stop_armed)

            overlay_hwnd = overlay_laag.hwnd if (
                overlay_zichtbaar and overlay_laag is not None
            ) else 0
            if overlay_zichtbaar and overlay_laag is not None and overlay_laag.gesloten:
                overlay_zichtbaar = False
                overlay_geplaatst = False
                overlay_hwnd = 0
                overlay_melding = ""
                print("  [INFO] Overlay-venster bestaat niet meer. "
                      "Live gaat door via het drempelpaneel.")

            fg_nu = _hwnd_norm(_voorgrond_hwnd())
            if fg_nu != fg_cache:
                fg_cache = fg_nu
                uipi_cache = waarschuwing_integriteit()
                if uipi_cache:
                    print(f"  [!] {uipi_cache}")
                    log_message(uipi_cache)

            if paneel.is_open and (nu - ctk_tijd) >= CTK_INTERVAL_S:
                for i, td in enumerate(trigger_data):
                    paneel.update_status(i, td["alle_match"])
                paneel.update_achtergrond_banner(
                    _live_status_banner(
                        overlay_hwnd,
                        overlay_melding=overlay_melding,
                        toets_fout=toets_fout_melding,
                        uipi=uipi_cache,
                    )
                )
                try:
                    paneel.venster.update()
                except Exception:
                    pass
                ctk_tijd = nu
            elif not paneel.is_open and not overlay_zichtbaar:
                break

            if paneel.stop_gevraagd:
                print("  [INFO] Live gestopt via drempelpaneel.")
                break

            # Overlay altijd verversen als hij aan staat — ook boven C5 (PiP).
            # Camera/triggers/SendInput lopen ongeacht tekenfout; geen skip
            # omdat Communicator groot is of eronder zit.
            key = -1
            stop_via_knop = False
            if overlay_zichtbaar and overlay_laag is not None and not overlay_laag.gesloten:
                ox, oy = _overlay_positie(
                    canvas.shape[1], canvas.shape[0], overlay_hoek
                )
                getoond = False
                try:
                    getoond = overlay_laag.toon(
                        canvas, ox, oy, topmost=overlay_topmost
                    )
                except Exception as exc:
                    getoond = False
                    print(f"  [!] Overlay-beeld bijwerken mislukt: {exc}")
                    log_message(f"Overlay UpdateLayeredWindow: {exc}")
                if getoond:
                    eerst = (not overlay_geplaatst) or overlay_moet_plaatsen
                    overlay_geplaatst = True
                    overlay_moet_plaatsen = False
                    overlay_melding = ""
                    if eerst or (
                        overlay_topmost
                        and (nu - topmost_tijd) >= TOPMOST_HERHAAL_S
                    ):
                        overlay_laag.zet_topmost(overlay_topmost)
                        topmost_tijd = nu
                else:
                    overlay_melding = (
                        "Het camerabeeld wordt even niet ververst. Camera en "
                        "toetsen lopen door. Blijft het beeld stil, probeer dan "
                        "Vensterweergave."
                    )
                try:
                    key = overlay_laag.pompen()
                except Exception:
                    key = -1
                if not overlay_laag.heeft_focus():
                    key = -1
                klik = overlay_laag.neem_klik()
                if klik is not None:
                    x1, y1, x2, y2 = _stop_knop_rect(cam_w, stop_armed)
                    if x1 <= klik[0] <= x2 and y1 <= klik[1] <= y2:
                        if stop_armed:
                            print("  [INFO] Live gestopt via stopknop.")
                            stop_via_knop = True
                        else:
                            stop_arm_tijd = nu
            else:
                time.sleep(0.001)
                if not paneel.is_open and not overlay_zichtbaar:
                    break

            if paneel.is_open and not paneel_geplaatst:
                _plaats_drempelpaneel(paneel)
                paneel_geplaatst = True

            if key == ord('q') or key == ord('Q') or stop_via_knop:
                break
            elif key == ord('p') or key == ord('P'):
                gepauzeerd = not gepauzeerd
                if gepauzeerd:
                    print("  [INFO] Beeld gepauzeerd. Druk P om te hervatten.")
                else:
                    print("  [INFO] Beeld hervat.")
                    scroll_offset = 0
            elif key in (ord('1'), ord('2'), ord('3')):
                overlay_grootte = int(chr(key))
                _sla_live_voorkeur(config, "overlay_grootte", overlay_grootte)
                hud_cache = None
                overlay_moet_plaatsen = True
                print(f"  [INFO] Overlay-grootte {overlay_grootte} "
                      f"({overlay_cam_maten(overlay_grootte)[0]}x"
                      f"{overlay_cam_maten(overlay_grootte)[1]}).")
            elif key in (ord('t'), ord('T')):
                if overlay_alleen_camera or not overlay_hud_aan:
                    overlay_hud_aan = True
                    overlay_alleen_camera = False
                    print("  [INFO] Trigger-eigenschappen aan (T).")
                else:
                    overlay_hud_aan = False
                    print("  [INFO] Trigger-eigenschappen uit (T).")
                _sla_live_voorkeur(config, "overlay_hud_aan", overlay_hud_aan)
                _sla_live_voorkeur(config, "overlay_alleen_camera", overlay_alleen_camera)
                hud_cache = None
                overlay_moet_plaatsen = True
            elif key in (ord('c'), ord('C')):
                overlay_alleen_camera = not overlay_alleen_camera
                _sla_live_voorkeur(config, "overlay_alleen_camera", overlay_alleen_camera)
                hud_cache = None
                overlay_moet_plaatsen = True
                print(f"  [INFO] Alleen camera: "
                      f"{'aan' if overlay_alleen_camera else 'uit'}.")
            elif key in (ord('s'), ord('S')):
                toetsen_sturen = not toetsen_sturen
                _sla_live_voorkeur(config, "overlay_toetsen_sturen", toetsen_sturen)
                hud_cache = None
                print(f"  [INFO] Toetsen sturen: "
                      f"{'aan' if toetsen_sturen else 'UIT — overlay blijft'}.")
            elif key in (ord('k'), ord('K')):
                toets_melding = not toets_melding
                _sla_live_voorkeur(config, "overlay_toets_melding", toets_melding)
                print(f"  [INFO] Toets-melding: "
                      f"{'aan' if toets_melding else 'uit'}.")
            elif key in (ord('a'), ord('A')):
                overlay_topmost = not overlay_topmost
                _sla_live_voorkeur(config, "overlay_topmost", overlay_topmost)
                overlay_moet_plaatsen = True
                print(f"  [INFO] Altijd bovenop: "
                      f"{'aan' if overlay_topmost else 'uit'}.")
            elif key in (ord('m'), ord('M')):
                mesh_volledig = not mesh_volledig
                _sla_live_voorkeur(config, "mesh_volledig", mesh_volledig)
                print(f"  [INFO] Mesh: "
                      f"{'volledig' if mesh_volledig else 'licht'}.")
            elif key in (ord('f'), ord('F')):
                overlay_spiegel = not overlay_spiegel
                _sla_live_voorkeur(config, "overlay_spiegel", overlay_spiegel)
                pauze_frame = None
                print(f"  [INFO] Spiegelbeeld: "
                      f"{'aan' if overlay_spiegel else 'uit'}.")
            elif key in (ord('o'), ord('O')):
                overlay_hoek = volgende_overlay_hoek(overlay_hoek)
                _sla_live_voorkeur(config, "overlay_hoek", overlay_hoek)
                overlay_moet_plaatsen = True
                print(f"  [INFO] Overlay-hoek: {overlay_hoek_label(overlay_hoek)}.")
            elif key in (2490368, 65362):       # Pijl omhoog
                scroll_offset = max(0, scroll_offset - 40)
                hud_cache = None
            elif key in (2621440, 65364):       # Pijl omlaag
                scroll_offset += 40
                hud_cache = None
            elif key in (2162688, 65365):       # Page Up
                scroll_offset = max(0, scroll_offset - 150)
                hud_cache = None
            elif key in (2228224, 65366):       # Page Down
                scroll_offset += 150
                hud_cache = None

    except Exception as exc:
        log_message(f"Live crash:\n{traceback.format_exc()}")
        _sluit_laad_ui()
        _toon_live_fout(str(exc))
    finally:
        _sluit_laad_ui()
        if overlay_laag is not None:
            try:
                overlay_laag.sluit()
            except Exception:
                pass
        try:
            cap.release()
        except Exception:
            pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        if landmarker is not None:
            try:
                landmarker.close()
            except Exception:
                pass
        if paneel is not None and paneel.is_open:
            try:
                paneel._sluit()
            except Exception:
                pass

    print("\n  [OK] Live modus gestopt.\n")
