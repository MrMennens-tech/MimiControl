"""
MimiControl - Centrale toetsmodule
Vervangt pyautogui.press() door een expliciet keyDown/keyUp paar
met configureerbare duur, zodat webapps de toetsinput correct registreren.
"""

import time
import pyautogui

DEFAULT_TOETS_DUUR_MS = 100


def normaliseer_toets(naam):
    """Normaliseer toetsnaam naar lowercase zonder witruimte."""
    return naam.strip().lower()


def voer_toetsen_uit(toetsen, duur_ms=DEFAULT_TOETS_DUUR_MS):
    """
    Voer een toetsactie uit met expliciet keyDown/keyUp paar.

    Bij één toets: keyDown → wacht → keyUp
    Bij meerdere toetsen (combo): alle keyDown → wacht → alle keyUp (omgekeerd)
    """
    toetsen = [normaliseer_toets(t) for t in toetsen]
    pauze = duur_ms / 1000

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
