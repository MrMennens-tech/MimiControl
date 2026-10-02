"""
MimiControl - Hoofdapplicatie
Gezichtsbesturing op maat voor gebruikers met zware spasmen.

Start dit script om de applicatie te openen:
    python mimicontrol.py          (grafische interface)
    python mimicontrol.py --cli    (terminal-interface)
"""

import sys

from config_beheer import toon_config
from calibratie import start_kalibratie
from actie_instellen import start_actie_instellen
from live_modus import start_live_modus
from gui import start_gui

BANNER = r"""
  ╔══════════════════════════════════════════════╗
  ║           M I M I C O N T R O L  v1.0       ║
  ║        Gezichtsbesturing op maat             ║
  ╠══════════════════════════════════════════════╣
  ║                                              ║
  ║   [1]  Kalibreren via Video                  ║
  ║   [2]  Sneltoets / Actie instellen           ║
  ║   [3]  Live Besturing starten                ║
  ║   [4]  Huidige configuratie bekijken         ║
  ║   [0]  Afsluiten                             ║
  ║                                              ║
  ╚══════════════════════════════════════════════╝
"""


def hoofdmenu():
    """Terminal-interface (fallback)."""
    while True:
        print(BANNER)
        keuze = input("  Maak een keuze [0-4]: ").strip()

        if keuze == "1":
            start_kalibratie()
        elif keuze == "2":
            start_actie_instellen()
        elif keuze == "3":
            start_live_modus()
        elif keuze == "4":
            toon_config()
        elif keuze == "0":
            print("\n  Tot ziens!\n")
            sys.exit(0)
        else:
            print("\n  [!] Ongeldige keuze. Probeer opnieuw.")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        hoofdmenu()
    else:
        start_gui()
