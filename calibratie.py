"""
MimiControl - Kalibratie Module
Analyseert een video (bestand of live webcam-opname) om piekwaarden
van de gezichtsuitdrukking te vinden.
De drempelwaarden worden automatisch opgeslagen in config.json.
"""

import cv2
import time
import os
import tkinter as tk
from tkinter import filedialog

from gezichtsdetectie import (
    maak_face_landmarker, detecteer_gezicht, bereken_mond_metingen,
    teken_face_mesh, teken_meetpunten
)
from config_beheer import laad_config, sla_config_op

# Piekwaarden worden met deze marge verlaagd zodat de trigger
# niet exact op het maximum hoeft te zitten.
MARGE = 0.10

# Standaard opnameduur voor webcam-kalibratie (in seconden)
OPNAME_DUUR = 5
COUNTDOWN_SECONDEN = 3


def selecteer_video():
    """Open een bestandsdialoog om een videobestand te selecteren."""
    root = tk.Tk()
    root.withdraw()
    pad = filedialog.askopenfilename(
        title="Selecteer een kalibratievideo",
        filetypes=[
            ("MP4 Video", "*.mp4"),
            ("Alle videobestanden", "*.avi *.mov *.mkv *.mp4"),
        ]
    )
    root.destroy()
    return pad


def verwerk_resultaten(piek_breedte, piek_hoogte, frame_nr, frames_met_gezicht):
    """
    Verwerk de kalibratie-resultaten: bereken drempelwaarden en sla op.
    Gedeelde logica voor zowel video- als webcam-kalibratie.
    Returns True als de kalibratie succesvol was.
    """
    print("\n" + "=" * 50)
    print("  KALIBRATIE RESULTATEN")
    print("=" * 50)
    print(f"  Frames geanalyseerd   : {frame_nr}")
    print(f"  Frames met gezicht    : {frames_met_gezicht}")
    print(f"  Piek mondbreedte      : {piek_breedte:.4f}")
    print(f"  Piek liphoogte        : {piek_hoogte:.4f}")

    if piek_breedte == 0 or piek_hoogte == 0:
        print("\n  [!] Geen bruikbare data gevonden. Probeer opnieuw.")
        return False

    drempel_breedte = piek_breedte * (1 - MARGE)
    drempel_hoogte = piek_hoogte * (1 - MARGE)

    print(f"\n  Drempel breedte (piek - {int(MARGE*100)}%) : {drempel_breedte:.4f}")
    print(f"  Drempel hoogte  (piek - {int(MARGE*100)}%) : {drempel_hoogte:.4f}")
    print("=" * 50)

    config = laad_config()
    config["drempelwaarde_breedte"] = round(drempel_breedte, 6)
    config["drempelwaarde_hoogte"] = round(drempel_hoogte, 6)
    sla_config_op(config)

    print("\n  [OK] Kalibratie voltooid! Drempelwaarden opgeslagen.\n")
    return True


def kalibratie_via_video():
    """Kalibreer op basis van een geimporteerd videobestand."""
    print("\n  Selecteer een video waarin de gebruiker de")
    print("  triggeruitdrukking (lach + tongbol) uitvoert.\n")

    video_pad = selecteer_video()
    if not video_pad:
        print("  [!] Geen video geselecteerd. Kalibratie afgebroken.")
        return

    print(f"  [OK] Video geladen: {video_pad}")

    cap = cv2.VideoCapture(video_pad)
    if not cap.isOpened():
        print("  [!] Kan de video niet openen. Controleer het bestand.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    totaal_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    wachttijd = max(1, int(1000 / fps)) if fps > 0 else 33

    landmarker = maak_face_landmarker(modus="video")

    piek_breedte = 0.0
    piek_hoogte = 0.0
    frame_nr = 0
    frames_met_gezicht = 0

    print(f"  [INFO] Video: {totaal_frames} frames @ {fps:.1f} FPS")
    print("  [INFO] Analyseren... Druk op 'q' in het venster om te stoppen.\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_nr += 1
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Timestamp in ms op basis van framenummer
        timestamp_ms = int((frame_nr / fps) * 1000) if fps > 0 else frame_nr * 33
        landmarks = detecteer_gezicht(landmarker, rgb, timestamp_ms)

        if landmarks:
            frames_met_gezicht += 1
            teken_face_mesh(frame, landmarks)
            teken_meetpunten(frame, landmarks)

            breedte, hoogte = bereken_mond_metingen(landmarks)

            if breedte > piek_breedte:
                piek_breedte = breedte
            if hoogte > piek_hoogte:
                piek_hoogte = hoogte

            cv2.putText(
                frame,
                f"Breedte: {breedte:.4f}  (piek: {piek_breedte:.4f})",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 0), 2
            )
            cv2.putText(
                frame,
                f"Hoogte:  {hoogte:.4f}  (piek: {piek_hoogte:.4f})",
                (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 165, 255), 2
            )
        else:
            cv2.putText(
                frame, "Geen gezicht gedetecteerd",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 0, 255), 2
            )

        voortgang = frame_nr / totaal_frames if totaal_frames > 0 else 0
        balk_w = int(frame.shape[1] * 0.8)
        balk_x = int(frame.shape[1] * 0.1)
        balk_y = frame.shape[0] - 30
        cv2.rectangle(
            frame, (balk_x, balk_y),
            (balk_x + balk_w, balk_y + 15), (50, 50, 50), -1
        )
        cv2.rectangle(
            frame, (balk_x, balk_y),
            (balk_x + int(balk_w * voortgang), balk_y + 15), (0, 200, 0), -1
        )
        cv2.putText(
            frame, f"Frame {frame_nr}/{totaal_frames}",
            (balk_x, balk_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            (255, 255, 255), 1
        )

        cv2.imshow("MimiControl - Kalibratie (druk 'q' om te stoppen)", frame)
        if cv2.waitKey(wachttijd) & 0xFF == ord('q'):
            print("  [INFO] Vroegtijdig gestopt door gebruiker.")
            break

    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()

    verwerk_resultaten(piek_breedte, piek_hoogte, frame_nr, frames_met_gezicht)


def kalibratie_via_webcam():
    """
    Kalibreer door direct op te nemen via de webcam.
    Toont eerst een preview, daarna een countdown, en neemt dan op.
    De opname wordt ook opgeslagen als .mp4 bestand.
    """
    print("\n  De webcam opent nu met een live preview.")
    print("  Positioneer het gezicht voor de camera.")
    print("  Druk op SPATIE om de opname te starten.")
    print("  Druk op 'q' om af te breken.\n")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("  [!] Kan de webcam niet openen!")
        print("      Controleer of de webcam is aangesloten.")
        return

    landmarker = maak_face_landmarker(modus="video")
    venster_naam = "MimiControl - Webcam Kalibratie"
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Monotone timestamp teller (vereist door FaceLandmarker VIDEO modus)
    ts_teller = 0

    # ---- FASE 1: Live preview (wacht op SPATIE) ----
    print("  [INFO] Preview actief. Druk SPATIE als je klaar bent.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        ts_teller += 33
        landmarks = detecteer_gezicht(landmarker, rgb, ts_teller)

        if landmarks:
            teken_face_mesh(frame, landmarks)
            teken_meetpunten(frame, landmarks)

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], 50), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        cv2.putText(frame, "Positioneer gezicht - druk SPATIE om te starten",
                    (10, 35), font, 0.65, (0, 255, 255), 2)

        cv2.imshow(venster_naam, frame)
        toets = cv2.waitKey(1) & 0xFF
        if toets == ord(' '):
            break
        if toets == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            landmarker.close()
            print("  [INFO] Kalibratie afgebroken door gebruiker.")
            return

    # ---- FASE 2: Countdown ----
    print(f"  [INFO] Countdown: {COUNTDOWN_SECONDEN} seconden...")
    countdown_start = time.time()

    while True:
        verstreken = time.time() - countdown_start
        resterend = COUNTDOWN_SECONDEN - verstreken
        if resterend <= 0:
            break

        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        ts_teller += 33
        landmarks = detecteer_gezicht(landmarker, rgb, ts_teller)

        if landmarks:
            teken_face_mesh(frame, landmarks)

        h, w, _ = frame.shape
        tekst = str(int(resterend) + 1)
        tekst_grootte = cv2.getTextSize(tekst, font, 4, 6)[0]
        tx = (w - tekst_grootte[0]) // 2
        ty = (h + tekst_grootte[1]) // 2
        cv2.putText(frame, tekst, (tx, ty), font, 4, (0, 255, 255), 6)
        cv2.putText(frame, "Maak je klaar!",
                    (w // 2 - 120, ty + 60), font, 0.8, (255, 255, 255), 2)

        cv2.imshow(venster_naam, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            landmarker.close()
            print("  [INFO] Kalibratie afgebroken.")
            return

    # ---- FASE 3: Opname + analyse ----
    print(f"  [INFO] OPNAME GESTART - {OPNAME_DUUR} seconden")
    print("  [INFO] Voer nu de triggeruitdrukking uit (lach + tongbol)!")

    fps_webcam = cap.get(cv2.CAP_PROP_FPS)
    if fps_webcam == 0:
        fps_webcam = 30.0
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    opname_pad = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "kalibratie_opname.mp4"
    )
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(opname_pad, fourcc, fps_webcam, (frame_w, frame_h))

    piek_breedte = 0.0
    piek_hoogte = 0.0
    frame_nr = 0
    frames_met_gezicht = 0
    opname_start = time.time()

    while True:
        verstreken = time.time() - opname_start
        if verstreken >= OPNAME_DUUR:
            break

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        writer.write(frame)

        frame_nr += 1
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        ts_teller += 33
        landmarks = detecteer_gezicht(landmarker, rgb, ts_teller)

        if landmarks:
            frames_met_gezicht += 1
            teken_face_mesh(frame, landmarks)
            teken_meetpunten(frame, landmarks)

            breedte, hoogte = bereken_mond_metingen(landmarks)

            if breedte > piek_breedte:
                piek_breedte = breedte
            if hoogte > piek_hoogte:
                piek_hoogte = hoogte

            cv2.putText(
                frame,
                f"Breedte: {breedte:.4f}  (piek: {piek_breedte:.4f})",
                (10, 30), font, 0.7, (0, 255, 0), 2
            )
            cv2.putText(
                frame,
                f"Hoogte:  {hoogte:.4f}  (piek: {piek_hoogte:.4f})",
                (10, 65), font, 0.7, (0, 165, 255), 2
            )
        else:
            cv2.putText(
                frame, "Geen gezicht gedetecteerd",
                (10, 30), font, 0.7, (0, 0, 255), 2
            )

        # Opname-indicator + tijdsbalk
        resterend = OPNAME_DUUR - verstreken
        voortgang = verstreken / OPNAME_DUUR
        balk_w = int(frame.shape[1] * 0.8)
        balk_x = int(frame.shape[1] * 0.1)
        balk_y = frame.shape[0] - 30

        cv2.rectangle(
            frame, (balk_x, balk_y),
            (balk_x + balk_w, balk_y + 15), (50, 50, 50), -1
        )
        cv2.rectangle(
            frame, (balk_x, balk_y),
            (balk_x + int(balk_w * voortgang), balk_y + 15), (0, 0, 255), -1
        )

        cv2.circle(frame, (frame.shape[1] - 30, 30), 10, (0, 0, 255), -1)
        cv2.putText(frame, f"REC {resterend:.1f}s",
                    (frame.shape[1] - 130, 37), font, 0.6, (0, 0, 255), 2)

        cv2.imshow(venster_naam, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("  [INFO] Opname vroegtijdig gestopt.")
            break

    writer.release()
    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()

    print(f"  [INFO] Opname opgeslagen als: {opname_pad}")

    verwerk_resultaten(piek_breedte, piek_hoogte, frame_nr, frames_met_gezicht)


def start_kalibratie():
    """Toon het kalibratie-submenu en start de gekozen methode."""
    print("\n" + "=" * 50)
    print("  KALIBRATIE MODUS")
    print("=" * 50)
    print()
    print("  Kies een methode:")
    print("  [A] Video importeren  (analyseer een bestaand bestand)")
    print("  [B] Direct opnemen    (neem op via de webcam)")
    print("  [0] Terug naar hoofdmenu")

    while True:
        keuze = input("\n  Keuze [A/B/0]: ").strip().lower()
        if keuze == 'a':
            kalibratie_via_video()
            return
        elif keuze == 'b':
            kalibratie_via_webcam()
            return
        elif keuze == '0':
            return
        else:
            print("  [!] Ongeldige keuze. Typ A, B of 0.")
