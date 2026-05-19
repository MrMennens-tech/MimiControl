"""
MimiControl - Live Modus
Gebruikt de webcam om de gezichtsuitdrukking te detecteren
en toetsacties uit te voeren op basis van kalibratiedata.
"""

import cv2
import time
import pyautogui

from config_beheer import laad_config, toon_config
from gezichtsdetectie import (
    maak_face_landmarker, detecteer_gezicht, bereken_mond_metingen,
    teken_face_mesh, teken_meetpunten
)
from toets_actie import voer_toetsen_uit

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


def teken_overlay(frame, mondbreedte, liphoogte, drempel_b, drempel_h,
                  trigger_start, nu, vasthoud_tijd, laatste_actie,
                  cooldown, actie_flash, toetsen, gezicht_ok):
    """Teken een informatief heads-up overlay bovenaan het videoframe."""
    h, w, _ = frame.shape

    # Semi-transparante achtergrond
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 155), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    wit = (255, 255, 255)
    groen = (0, 255, 0)
    rood = (0, 0, 255)
    oranje = (0, 165, 255)
    geel = (0, 255, 255)
    font = cv2.FONT_HERSHEY_SIMPLEX

    if not gezicht_ok:
        cv2.putText(frame, "Geen gezicht gedetecteerd",
                    (10, 35), font, 0.7, rood, 2)
        return

    # --- Breedte indicator + progress bar ---
    b_ok = mondbreedte > drempel_b
    cv2.putText(frame,
                f"Breedte: {mondbreedte:.3f} / {drempel_b:.3f}",
                (10, 30), font, 0.6, groen if b_ok else wit, 2)

    ratio_b = min(mondbreedte / drempel_b, 1.5) if drempel_b > 0 else 0
    bar_b = int(200 * min(ratio_b, 1.0))
    cv2.rectangle(frame, (300, 15), (500, 35), (50, 50, 50), -1)
    cv2.rectangle(frame, (300, 15), (300 + bar_b, 35),
                  groen if b_ok else oranje, -1)

    # --- Hoogte indicator + progress bar ---
    h_ok = liphoogte > drempel_h
    cv2.putText(frame,
                f"Hoogte:  {liphoogte:.3f} / {drempel_h:.3f}",
                (10, 60), font, 0.6, groen if h_ok else wit, 2)

    ratio_h = min(liphoogte / drempel_h, 1.5) if drempel_h > 0 else 0
    bar_h = int(200 * min(ratio_h, 1.0))
    cv2.rectangle(frame, (300, 45), (500, 65), (50, 50, 50), -1)
    cv2.rectangle(frame, (300, 45), (300 + bar_h, 65),
                  groen if h_ok else oranje, -1)

    # --- Status tekst ---
    in_cooldown = (nu - laatste_actie) < cooldown
    actie_recent = (nu - actie_flash) < 1.0

    if actie_recent:
        cv2.putText(frame, f"ACTIE: {' + '.join(toetsen)}",
                    (10, 100), font, 0.9, geel, 2)
        dikte = max(4, int(12 * (1 - (nu - actie_flash))))
        cv2.rectangle(frame, (0, 0), (w - 1, h - 1), geel, dikte)

    elif in_cooldown:
        rest = cooldown - (nu - laatste_actie)
        cv2.putText(frame, f"Cooldown: {rest:.1f}s",
                    (10, 100), font, 0.7, oranje, 2)

    elif trigger_start is not None:
        duur = nu - trigger_start
        cv2.putText(frame,
                    f"Vasthouden: {duur:.1f}s / {vasthoud_tijd:.1f}s",
                    (10, 100), font, 0.7, geel, 2)
        vr = min(duur / vasthoud_tijd, 1.0)
        bar_v = int(200 * vr)
        cv2.rectangle(frame, (300, 85), (500, 105), (50, 50, 50), -1)
        cv2.rectangle(frame, (300, 85), (300 + bar_v, 105), geel, -1)

    elif b_ok or h_ok:
        cv2.putText(frame, "Gedeeltelijke trigger...",
                    (10, 100), font, 0.6, oranje, 2)
    else:
        cv2.putText(frame, "Wachten op trigger...",
                    (10, 100), font, 0.6, wit, 2)

    cv2.putText(frame,
                f"Actie: {' + '.join(toetsen)}  |  Druk 'q' om te stoppen",
                (10, 140), font, 0.5, (180, 180, 180), 1)


def start_live_modus():
    """Start de live gezichtsbesturing via de webcam."""
    config = laad_config()

    drempel_b = config["drempelwaarde_breedte"]
    drempel_h = config["drempelwaarde_hoogte"]
    toetsen = config["toetsen"]
    cooldown = config["cooldown"]
    vasthoud_tijd = config["vasthoud_tijd"]
    toets_duur_ms = config.get("toets_duur_ms", 100)

    if drempel_b == 0 or drempel_h == 0:
        print("\n  [!] Geen kalibratiedata gevonden in config.json!")
        print("      Voer eerst Optie 1 (Kalibreren via Video) uit.\n")
        return

    print("\n" + "=" * 50)
    print("  LIVE MODUS - Gezichtsbesturing actief")
    print("=" * 50)
    toon_config()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("  [!] Kan de webcam niet openen!")
        print("      Controleer of de webcam is aangesloten.")
        return

    landmarker = maak_face_landmarker(modus="video")

    # State voor de trigger-logica
    trigger_start = None
    laatste_actie = 0.0
    actie_flash = 0.0
    ts_teller = 0

    print("  [INFO] Webcam geopend. Live besturing gestart.")
    print("  [INFO] Druk op 'q' in het videovenster om te stoppen.\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("  [!] Kan geen frame lezen van de webcam.")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        ts_teller += 33
        landmarks = detecteer_gezicht(landmarker, rgb, ts_teller)

        nu = time.time()
        mondbreedte = 0.0
        liphoogte = 0.0
        gezicht_ok = False

        if landmarks:
            gezicht_ok = True
            teken_face_mesh(frame, landmarks)
            teken_meetpunten(frame, landmarks)
            mondbreedte, liphoogte = bereken_mond_metingen(landmarks)

        # ---- Trigger detectie met anti-spasme filter ----
        trigger_nu = (
            gezicht_ok
            and mondbreedte > drempel_b
            and liphoogte > drempel_h
        )
        in_cooldown = (nu - laatste_actie) < cooldown

        if trigger_nu and not in_cooldown:
            if trigger_start is None:
                trigger_start = nu

            if (nu - trigger_start) >= vasthoud_tijd:
                voer_toetsen_uit(toetsen, duur_ms=toets_duur_ms)

                laatste_actie = nu
                actie_flash = nu
                trigger_start = None
                print(f"  >>> ACTIE UITGEVOERD: {' + '.join(toetsen)}")
        else:
            trigger_start = None

        teken_overlay(
            frame, mondbreedte, liphoogte, drempel_b, drempel_h,
            trigger_start, nu, vasthoud_tijd, laatste_actie,
            cooldown, actie_flash, toetsen, gezicht_ok
        )

        cv2.imshow("MimiControl - Live Modus (druk 'q' om te stoppen)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
    print("\n  [OK] Live modus gestopt.\n")
