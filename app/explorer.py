"""
MimiExplorer - Explorer Modus
OpenCV-venster dat live alle blendshape-scores toont als balkjes.
De gebruiker kan een piek-opname doen en de resultaten doorsturen
naar de trigger-editor.
"""

import cv2
import time
import numpy as np

from blendshape_detectie import (
    maak_blendshape_landmarker, detecteer_blendshapes,
    teken_face_mesh_simpel, teken_blendshape_bars, nl_label
)

OPNAME_DUUR = 3  # seconden piek-opname
TOP_N = 5        # aantal pieken dat gehighlight wordt


def start_explorer():
    """
    Open de Explorer: webcam + live blendshape-bars.

    Returns:
        dict met piekwaarden als de gebruiker ENTER drukt,
        of None als de gebruiker Q drukt.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("  [!] Kan de webcam niet openen!")
        return None

    landmarker = maak_blendshape_landmarker(modus="video")
    ts = 0
    font = cv2.FONT_HERSHEY_SIMPLEX

    # State
    pieken = {}
    top_namen = set()
    opname_actief = False
    opname_start = 0.0
    heeft_pieken = False

    print("\n  === EXPLORER MODUS ===")
    print("  SPATIE  = Start piek-opname (3s)")
    print("  ENTER   = Opslaan als trigger")
    print("  Q       = Terug zonder opslaan\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        cam_h, cam_w = frame.shape[:2]

        # Breed canvas: webcam links, bars rechts
        bar_panel_w = 420
        canvas = np.zeros((cam_h, cam_w + bar_panel_w, 3), dtype=np.uint8)
        canvas[:, :cam_w] = frame

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ts += 33
        landmarks, scores = detecteer_blendshapes(landmarker, rgb, ts)

        if landmarks:
            teken_face_mesh_simpel(frame, landmarks)
        canvas[:, :cam_w] = frame

        # Piek-opname logica
        if opname_actief:
            verstreken = time.time() - opname_start
            if verstreken >= OPNAME_DUUR:
                opname_actief = False
                heeft_pieken = True
                # Bepaal top N
                gesorteerd = sorted(pieken.items(),
                                    key=lambda kv: kv[1], reverse=True)
                top_namen = {naam for naam, _ in gesorteerd[:TOP_N]}
                print(f"  [OK] Piek-opname klaar! Top {TOP_N}:")
                for naam, waarde in gesorteerd[:TOP_N]:
                    print(f"    {nl_label(naam):30s} {waarde:.3f}")
            else:
                # Verzamel pieken
                for naam, score in scores.items():
                    if score > pieken.get(naam, 0):
                        pieken[naam] = score

                # REC indicator op webcam
                rest = OPNAME_DUUR - verstreken
                cv2.circle(canvas, (cam_w - 30, 30), 10, (0, 0, 255), -1)
                cv2.putText(canvas, f"REC {rest:.1f}s",
                            (cam_w - 130, 37), font, 0.6, (0, 0, 255), 2)
                # Voortgangsbalk
                vr = verstreken / OPNAME_DUUR
                bx = int(cam_w * 0.1)
                bw = int(cam_w * 0.8)
                by = cam_h - 25
                cv2.rectangle(canvas, (bx, by), (bx + bw, by + 12),
                              (50, 50, 50), -1)
                cv2.rectangle(canvas, (bx, by),
                              (bx + int(bw * vr), by + 12),
                              (0, 0, 255), -1)

        # Bars tekenen op het rechter panel
        if scores:
            teken_blendshape_bars(
                canvas, scores,
                x_start=cam_w + 10, y_start=50,
                bar_breedte=160, bar_hoogte=14, max_items=22,
                pieken=pieken if heeft_pieken else None,
                top_n_namen=top_namen if heeft_pieken else None
            )

        # Instructies bovenaan het bar-panel
        ix = cam_w + 10
        if opname_actief:
            cv2.putText(canvas, "OPNAME LOOPT...",
                        (ix, 25), font, 0.55, (0, 0, 255), 2)
        elif heeft_pieken:
            cv2.putText(canvas, "ENTER=trigger maken  SPATIE=opnieuw",
                        (ix, 25), font, 0.42, (0, 255, 255), 1)
        else:
            cv2.putText(canvas, "SPATIE = piek-opname starten",
                        (ix, 25), font, 0.45, (200, 200, 200), 1)

        if not landmarks:
            cv2.putText(canvas, "Geen gezicht",
                        (10, 30), font, 0.65, (0, 0, 255), 2)

        cv2.imshow("MimiExplorer (Q=sluiten)", canvas)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' ') and not opname_actief:
            pieken = {}
            top_namen = set()
            heeft_pieken = False
            opname_actief = True
            opname_start = time.time()
            print("  [REC] Piek-opname gestart (3s)... Maak de uitdrukking!")

        elif key == 13 and heeft_pieken:  # ENTER
            cap.release()
            cv2.destroyAllWindows()
            landmarker.close()
            return pieken

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
    return None
