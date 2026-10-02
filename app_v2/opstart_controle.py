"""
Opstartcontroles voor MimiControl Studio v2 (alleen Windows):

1. Beheerdersrechten: Communicator 5 draait verhoogd, dus Windows (UIPI)
   blokkeert toetsen van een gewone Studio. Is Studio niet verhoogd, dan
   vragen we netjes om opnieuw te starten als beheerder.
2. Eén instantie: een tweede Studio zou de camera stelen of toetsen dubbel
   sturen. De tweede start krijgt een duidelijke melding en sluit.

SendInput/scancodes blijven onaangeroerd; dit raakt alleen het opstarten.
"""

import os
import sys

_IS_WINDOWS = sys.platform == "win32"
_MUTEX_NAAM = "Local\\MimiControlStudioV2"
_ERROR_ALREADY_EXISTS = 183
_ERROR_ACCESS_DENIED = 5
NA_ELEVATIE_ARG = "--na-elevatie"

_mutex_handle = None  # moet leven zolang Studio draait


def _bericht(titel, tekst, ja_nee=False):
    """Eenvoudige Windows-melding zonder Tk. Retourneert True bij 'Ja'/OK."""
    import ctypes
    MB_YESNO, MB_OK = 0x4, 0x0
    MB_ICONQUESTION, MB_ICONINFORMATION = 0x20, 0x40
    MB_TOPMOST = 0x40000
    stijl = (MB_YESNO | MB_ICONQUESTION if ja_nee
             else MB_OK | MB_ICONINFORMATION) | MB_TOPMOST
    antwoord = ctypes.windll.user32.MessageBoxW(None, tekst, titel, stijl)
    return antwoord == 6 if ja_nee else True


def _herstart_als_beheerder():
    """Start dezelfde Studio opnieuw met UAC-vraag. True als dat gelukt is."""
    import ctypes
    if getattr(sys, "frozen", False):
        programma = sys.executable
        argumenten = list(sys.argv[1:])
    else:
        programma = sys.executable
        argumenten = [os.path.abspath(sys.argv[0])] + list(sys.argv[1:])
    argumenten.append(NA_ELEVATIE_ARG)
    parameters = " ".join(f'"{a}"' for a in argumenten)
    # ShellExecuteW geeft een waarde > 32 terug als het gelukt is.
    resultaat = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", programma, parameters, os.getcwd(), 1
    )
    return int(resultaat) > 32


def _is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def controleer_beheerder():
    """Vraag om herstart als beheerder. Retourneert False als dit proces
    moet stoppen omdat er een verhoogde Studio is gestart."""
    if not _IS_WINDOWS or _is_admin() or NA_ELEVATIE_ARG in sys.argv:
        return True
    gekozen = _bericht(
        "MimiControl Studio — beheerdersrechten",
        "Studio werkt met Communicator 5 alleen als het als beheerder draait.\n\n"
        "Nu opnieuw starten als beheerder?\n\n"
        "Kies 'Nee' om toch door te gaan; toetsen komen dan mogelijk niet aan "
        "in Communicator 5.",
        ja_nee=True,
    )
    if not gekozen:
        return True
    if _herstart_als_beheerder():
        return False  # de verhoogde Studio neemt het over
    _bericht(
        "MimiControl Studio",
        "Opnieuw starten als beheerder is niet gelukt of geweigerd.\n"
        "Studio start nu zonder beheerdersrechten.",
    )
    return True


def controleer_enkele_instantie():
    """Retourneert False als er al een Studio draait."""
    global _mutex_handle
    if not _IS_WINDOWS:
        return True
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        handle = kernel32.CreateMutexW(None, False, _MUTEX_NAAM)
        fout = kernel32.GetLastError()
        if fout in (_ERROR_ALREADY_EXISTS, _ERROR_ACCESS_DENIED):
            # ACCESS_DENIED: de bestaande Studio draait verhoogd, wij niet.
            _bericht(
                "MimiControl Studio",
                "MimiControl Studio draait al.\n\n"
                "Sluit de andere Studio eerst af (ook in de taakbalk of "
                "Taakbeheer), anders blijft de camera bezet.",
            )
            return False
        _mutex_handle = handle
    except Exception:
        pass  # liever starten dan onterecht blokkeren
    return True


def controleer_opstart():
    """True = doorgaan met starten, False = dit proces moet afsluiten."""
    if not controleer_beheerder():
        return False
    return controleer_enkele_instantie()
