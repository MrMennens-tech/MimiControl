"""
MimiExplorer - Live Modus
Controleert alle geconfigureerde triggers gelijktijdig op basis
van blendshape-scores, met anti-spasme filter en cooldown.
"""

import cv2
import time
import pyautogui

from config_explorer import laad_explorer_config
from blendshape_detectie import (
    maak_blendshape_landmarker, detecteer_blendshapes,
    teken_face_mesh_simpel, nl_label
)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

TRIGGER_KLEUREN = [
    (0, 220, 0),       # groen
    (220, 160, 0),     # cyaan-achtig
    (0, 120, 255),     # oranje
    (180, 0, 220),     # paars
    (0, 220, 220),     # geel
]


def teken_live_overlay(frame, scores, triggers, trigger_states,
                       nu, vasthoud_tijd, laatste_actie, cooldown,
                       actie_flash, actie_idx, gezicht_ok):
    """Teken overlay met trigger-statussen en actieve blendshapes."""
    h, w, _ = frame.shape
    font = cv2.FONT_HERSHEY_SIMPLEX

    actieve_triggers = [t for t in triggers if t.get("blendshapes")]
    regels = 2 + len(actieve_triggers)
    overlay_h = max(60, 28 + regels * 24)

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, overlay_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    if not gezicht_ok:
        cv2.putText(frame, "Geen gezicht gedetecteerd",
                    (10, 28), font, 0.65, (0, 0, 255), 2)
        return

    y = 22
    in_cooldown = (nu - laatste_actie) < cooldown
    actie_recent = (nu - actie_flash) < 1.0

    for i, trigger in enumerate(actieve_triggers):
        kleur = TRIGGER_KLEUREN[i % len(TRIGGER_KLEUREN)]
        toets = " + ".join(trigger["toetsen"]).upper()
        label = f"[{i+1}] {trigger['naam']}  ({toets})"

        # Check match
        match = True
        for bs_naam, drempel in trigger["blendshapes"].items():
            if scores.get(bs_naam, 0) <= drempel:
                match = False
                break

        state = trigger_states[i]

        if actie_recent and actie_idx == i:
            cv2.putText(frame, f"{label}  >>> ACTIE! <<<",
                        (10, y), font, 0.5, (0, 255, 255), 2)
        elif in_cooldown:
            rest = cooldown - (nu - laatste_actie)
            cv2.putText(frame, f"{label}  cooldown {rest:.1f}s",
                        (10, y), font, 0.45, (100, 100, 100), 1)
        elif match and state["start"] is not None:
            duur = nu - state["start"]
            cv2.putText(frame, f"{label}  vasthouden {duur:.1f}s",
                        (10, y), font, 0.45, kleur, 2)
            bar_w = int(min(duur / vasthoud_tijd, 1.0) * 100)
            cv2.rectangle(frame, (380, y - 10), (380 + bar_w, y + 2),
                          kleur, -1)
        elif match:
            cv2.putText(frame, f"{label}  MATCH",
                        (10, y), font, 0.45, kleur, 1)
        else:
            cv2.putText(frame, f"{label}  —",
                        (10, y), font, 0.45, (120, 120, 120), 1)
        y += 24

    if actie_recent:
        dikte = max(4, int(10 * (1 - (nu - actie_flash))))
        cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 255, 255), dikte)

    cv2.putText(frame, "Druk 'q' om te stoppen",
                (10, y + 4), font, 0.38, (140, 140, 140), 1)


def start_live_explorer():
    """Start de live modus met blendshape-triggers."""
    config = laad_explorer_config()
    triggers = config["triggers"]
    cooldown = config["cooldown"]
    vasthoud_tijd = config["vasthoud_tijd"]

    actieve = [t for t in triggers if t.get("blendshapes")]
    if not actieve:
        print("\n  [!] Geen triggers geconfigureerd!")
        print("      Gebruik eerst de Explorer om triggers aan te maken.\n")
        return

    print("\n" + "=" * 50)
    print("  LIVE MODUS - MimiExplorer")
    print("=" * 50)
    for i, t in enumerate(actieve):
        toets = " + ".join(t["toetsen"]).upper()
        bs_lijst = ", ".join(t["blendshapes"].keys())
        print(f"  [{i+1}] {t['naam']:16s} -> {toets:10s}  ({bs_lijst})")
    print(f"\n  Cooldown: {cooldown}s  |  Vasthoudtijd: {vasthoud_tijd}s\n")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("  [!] Kan de webcam niet openen!")
        return

    landmarker = maak_blendshape_landmarker(modus="video")

    trigger_states = [{"start": None} for _ in actieve]
    laatste_actie = 0.0
    actie_flash = 0.0
    actie_idx = -1
    ts = 0

    print("  [INFO] Live besturing gestart. Druk 'q' om te stoppen.\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ts += 33
        landmarks, scores = detecteer_blendshapes(landmarker, rgb, ts)

        nu = time.time()
        gezicht_ok = landmarks is not None

        if landmarks:
            teken_face_mesh_simpel(frame, landmarks)

        # Trigger detectie
        in_cooldown = (nu - laatste_actie) < cooldown
        gevuurd = False

        for i, trigger in enumerate(actieve):
            if not gezicht_ok:
                trigger_states[i]["start"] = None
                continue

            match = all(
                scores.get(bs, 0) > drempel
                for bs, drempel in trigger["blendshapes"].items()
            )

            if match and not in_cooldown and not gevuurd:
                if trigger_states[i]["start"] is None:
                    trigger_states[i]["start"] = nu

                if (nu - trigger_states[i]["start"]) >= vasthoud_tijd:
                    toetsen = trigger["toetsen"]
                    if len(toetsen) == 1:
                        pyautogui.press(toetsen[0])
                    else:
                        pyautogui.hotkey(*toetsen)

                    laatste_actie = nu
                    actie_flash = nu
                    actie_idx = i
                    gevuurd = True
                    for s in trigger_states:
                        s["start"] = None

                    toets_tekst = " + ".join(toetsen).upper()
                    print(f"  >>> [{i+1}] {trigger['naam']}: {toets_tekst}")
            else:
                trigger_states[i]["start"] = None

        teken_live_overlay(
            frame, scores, actieve, trigger_states,
            nu, vasthoud_tijd, laatste_actie, cooldown,
            actie_flash, actie_idx, gezicht_ok
        )

        cv2.imshow("MimiExplorer - Live (druk 'q' om te stoppen)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
    print("\n  [OK] Live modus gestopt.\n")
