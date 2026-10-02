"""
MimiControl - Actie Instellen Module
Laat de gebruiker een toets of toetscombinatie kiezen en sla deze op.
"""

from config_beheer import laad_config, sla_config_op

BEKENDE_TOETSEN = [
    "space", "enter", "tab", "escape", "backspace", "delete",
    "up", "down", "left", "right",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9",
    "f10", "f11", "f12",
    "ctrl", "alt", "shift", "win",
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
]


def start_actie_instellen():
    """Interactief menu om de toets(en) en timings in te stellen."""
    print("\n" + "=" * 50)
    print("  ACTIE INSTELLEN - Toets(en) kiezen")
    print("=" * 50)

    config = laad_config()
    huidige = " + ".join(config.get("toetsen", ["space"]))
    print(f"\n  Huidige instelling: {huidige}")

    print("\n  Voorbeelden van invoer:")
    print("    Enkele toets  :  space")
    print("    Enkele toets  :  enter")
    print("    Combinatie     :  ctrl+c")
    print("    Combinatie     :  alt+tab")
    print("    Combinatie     :  ctrl+shift+s")
    print(f"\n  Bekende toetsen: {', '.join(BEKENDE_TOETSEN[:20])} ...")

    while True:
        invoer = input("\n  Voer toets(en) in (gescheiden door '+'): ").strip().lower()
        if not invoer:
            print("  [!] Lege invoer. Probeer opnieuw.")
            continue

        toetsen = [t.strip() for t in invoer.split("+") if t.strip()]
        if not toetsen:
            print("  [!] Geen geldige toetsen herkend. Probeer opnieuw.")
            continue

        onbekend = [t for t in toetsen if t not in BEKENDE_TOETSEN]
        if onbekend:
            print(f"  [!] Onbekende toets(en): {', '.join(onbekend)}")
            antwoord = input("  Toch opslaan? (j/n): ").strip().lower()
            if antwoord != 'j':
                continue

        print(f"\n  Gekozen actie: {' + '.join(toetsen)}")
        bevestig = input("  Opslaan? (j/n): ").strip().lower()
        if bevestig == 'j':
            config["toetsen"] = toetsen
            sla_config_op(config)
            print(f"  [OK] Actie '{' + '.join(toetsen)}' opgeslagen!")
            break
        print("  Probeer opnieuw...")

    # Optioneel: cooldown en vasthoudtijd aanpassen
    print(f"\n  Huidige cooldown     : {config['cooldown']}s")
    print(f"  Huidige vasthoudtijd : {config['vasthoud_tijd']}s")
    wijzig = input("\n  Wil je cooldown/vasthoudtijd wijzigen? (j/n): ").strip().lower()

    if wijzig == 'j':
        try:
            cd = input(f"  Nieuwe cooldown in seconden [{config['cooldown']}]: ").strip()
            if cd:
                config["cooldown"] = max(0.1, float(cd))

            vt = input(
                f"  Nieuwe vasthoudtijd in seconden [{config['vasthoud_tijd']}]: "
            ).strip()
            if vt:
                config["vasthoud_tijd"] = max(0.1, float(vt))

            sla_config_op(config)
            print(f"  [OK] Cooldown: {config['cooldown']}s, "
                  f"Vasthoudtijd: {config['vasthoud_tijd']}s")
        except ValueError:
            print("  [!] Ongeldige waarde. Instellingen niet gewijzigd.")
