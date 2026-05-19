"""
MimiMultiControl - Live Modus met meerdere triggers.

Laadt alle actieve triggers uit config_multi.json en controleert
ze per frame. Elke trigger heeft eigen drempelwaarden en toets.
Triggers worden op volgorde gecontroleerd (prioriteit).
"""

import cv2
import time
import pyautogui

from config_multi import laad_multi_config, aantal_actieve_triggers
from gezichtsdetectie import (
    maak_face_landmarker, detecteer_gezicht, bereken_alle_metingen,
    teken_face_mesh, teken_alle_meetpunten, METING_NAMEN
)
from toets_actie import voer_toetsen_uit

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

# Kleuren per trigger-slot (BGR)
TRIGGER_KLEUREN = [
    (0, 200, 0),       # groen  – trigger 1
    (200, 150, 0),     # cyaan  – trigger 2
    (0, 100, 255),     # oranje – trigger 3
]


def teken_multi_overlay(frame, metingen, triggers, trigger_states,
                        nu, vasthoud_tijd, laatste_actie, cooldown,
                        actie_flash, actie_trigger_idx, gezicht_ok):
    """Heads-up overlay met alle metingen en trigger-statussen."""
    h, w, _ = frame.shape
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Achtergrond
    regels = 3 + sum(1 for t in triggers if t["actief"])
    overlay_h = 35 + regels * 24
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, overlay_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    if not gezicht_ok:
        cv2.putText(frame, "Geen gezicht gedetecteerd",
                    (10, 28), font, 0.65, (0, 0, 255), 2)
        return

    # Meetwaarden
    y = 22
    tekst_delen = []
    for m in METING_NAMEN:
        tekst_delen.append(f"{m[:6]}: {metingen.get(m, 0):.3f}")
    cv2.putText(frame, "  |  ".join(tekst_delen),
                (10, y), font, 0.45, (200, 200, 200), 1)
    y += 28

    # Per-trigger status
    in_cooldown = (nu - laatste_actie) < cooldown
    actie_recent = (nu - actie_flash) < 1.0

    for i, trigger in enumerate(triggers):
        if not trigger["actief"]:
            continue

        kleur = TRIGGER_KLEUREN[i % len(TRIGGER_KLEUREN)]
        toets_tekst = " + ".join(trigger["toetsen"]).upper()
        label = f"[{i+1}] {toets_tekst}"

        # Check of alle drempelwaarden overschreden zijn
        match = True
        for m, drempel in trigger["drempelwaarden"].items():
            if metingen.get(m, 0) <= drempel:
                match = False
                break

        state = trigger_states[i]

        if actie_recent and actie_trigger_idx == i:
            cv2.putText(frame, f"{label}  >>> ACTIE! <<<",
                        (10, y), font, 0.55, (0, 255, 255), 2)
        elif in_cooldown:
            rest = cooldown - (nu - laatste_actie)
            cv2.putText(frame, f"{label}  cooldown {rest:.1f}s",
                        (10, y), font, 0.5, (100, 100, 100), 1)
        elif match and state["start"] is not None:
            duur = nu - state["start"]
            breedte = int(min(duur / vasthoud_tijd, 1.0) * 120)
            cv2.putText(frame, f"{label}  vasthouden {duur:.1f}s",
                        (10, y), font, 0.5, kleur, 2)
            cv2.rectangle(frame, (280, y - 12), (280 + breedte, y + 2),
                          kleur, -1)
        elif match:
            cv2.putText(frame, f"{label}  MATCH",
                        (10, y), font, 0.5, kleur, 1)
        else:
            cv2.putText(frame, f"{label}  —",
                        (10, y), font, 0.5, (120, 120, 120), 1)
        y += 24

    # Flash bij actie
    if actie_recent:
        dikte = max(4, int(12 * (1 - (nu - actie_flash))))
        cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 255, 255), dikte)

    # Footer
    cv2.putText(frame, "Druk 'q' om te stoppen",
                (10, y + 6), font, 0.4, (140, 140, 140), 1)


def start_live_multi():
    """Start de live modus met meerdere triggers."""
    config = laad_multi_config()
    triggers = config["triggers"]
    cooldown = config["cooldown"]
    vasthoud_tijd = config["vasthoud_tijd"]
    toets_duur_ms = config.get("toets_duur_ms", 100)

    actieve = aantal_actieve_triggers(config)
    if actieve == 0:
        print("\n  [!] Geen gekalibreerde triggers gevonden!")
        print("      Kalibreer eerst minstens één mimiek.\n")
        return

    print("\n" + "=" * 50)
    print("  LIVE MULTI-MODUS")
    print("=" * 50)
    for i, t in enumerate(triggers):
        if t["actief"]:
            toets = " + ".join(t["toetsen"]).upper()
            metingen = ", ".join(t["drempelwaarden"].keys())
            print(f"  [{i+1}] {t['naam']:12s} → {toets:10s}  ({metingen})")
    print(f"\n  Cooldown: {cooldown}s  |  Vasthoudtijd: {vasthoud_tijd}s")
    print(f"  Actieve triggers: {actieve}\n")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("  [!] Kan de webcam niet openen!")
        return

    landmarker = maak_face_landmarker(modus="video")

    # Per-trigger state
    trigger_states = [{"start": None} for _ in triggers]
    laatste_actie = 0.0
    actie_flash = 0.0
    actie_trigger_idx = -1
    ts = 0

    print("  [INFO] Live besturing gestart. Druk 'q' om te stoppen.\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ts += 33
        landmarks = detecteer_gezicht(landmarker, rgb, ts)

        nu = time.time()
        metingen = {}
        gezicht_ok = False

        if landmarks:
            gezicht_ok = True
            teken_face_mesh(frame, landmarks)
            teken_alle_meetpunten(frame, landmarks)
            metingen = bereken_alle_metingen(landmarks)

        # ---- Multi-trigger detectie ----
        in_cooldown = (nu - laatste_actie) < cooldown
        gevuurd = False

        for i, trigger in enumerate(triggers):
            if not trigger["actief"] or not gezicht_ok:
                trigger_states[i]["start"] = None
                continue

            # Controleer of ALLE drempelwaarden overschreden zijn
            match = True
            for m, drempel in trigger["drempelwaarden"].items():
                if metingen.get(m, 0) <= drempel:
                    match = False
                    break

            if match and not in_cooldown and not gevuurd:
                if trigger_states[i]["start"] is None:
                    trigger_states[i]["start"] = nu

                if (nu - trigger_states[i]["start"]) >= vasthoud_tijd:
                    toetsen = trigger["toetsen"]
                    voer_toetsen_uit(toetsen, duur_ms=toets_duur_ms)

                    laatste_actie = nu
                    actie_flash = nu
                    actie_trigger_idx = i
                    gevuurd = True

                    # Reset alle triggers
                    for s in trigger_states:
                        s["start"] = None

                    toets_tekst = " + ".join(toetsen).upper()
                    print(f"  >>> [{i+1}] {trigger['naam']}: "
                          f"{toets_tekst}")
            else:
                trigger_states[i]["start"] = None

        teken_multi_overlay(
            frame, metingen, triggers, trigger_states,
            nu, vasthoud_tijd, laatste_actie, cooldown,
            actie_flash, actie_trigger_idx, gezicht_ok
        )

        cv2.imshow("MimiMultiControl - Live (druk 'q' om te stoppen)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
    print("\n  [OK] Live multi-modus gestopt.\n")
