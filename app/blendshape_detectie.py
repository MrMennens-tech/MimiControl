"""
MimiExplorer - Blendshape Detectie Module
FaceLandmarker wrapper met blendshape-output, score-functies
en OpenCV tekenhulpen voor live balkjes.
"""

import cv2
import os
import urllib.request

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from paths import model_path
from blendshape_labels import NL_LABELS, NIET_ONDERSTEUND, nl_label

# ---------------------------------------------------------------------------
# Model (hergebruik van gezichtsdetectie.py)
# ---------------------------------------------------------------------------
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)


def zorg_voor_model():
    pad = model_path()
    if not os.path.exists(pad):
        print("  [INFO] Face Landmarker model downloaden...")
        os.makedirs(os.path.dirname(pad), exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, pad)
        print("  [OK] Model opgeslagen.")


# Face mesh connecties voor tekenen
TESSELATION = vision.FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION
LIPPEN = vision.FaceLandmarksConnections.FACE_LANDMARKS_LIPS


# ---------------------------------------------------------------------------
# FaceLandmarker met blendshapes
# ---------------------------------------------------------------------------

def maak_blendshape_landmarker(modus="video"):
    """Maak een FaceLandmarker aan met blendshape-output ingeschakeld."""
    zorg_voor_model()
    running_mode = (
        vision.RunningMode.VIDEO if modus == "video"
        else vision.RunningMode.IMAGE
    )
    options = vision.FaceLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=model_path()),
        running_mode=running_mode,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_face_blendshapes=True,
    )
    return vision.FaceLandmarker.create_from_options(options)


_blendshape_namen_gelogd = False


def detecteer_blendshapes(landmarker, frame_rgb, timestamp_ms):
    """
    Voer detectie uit en retourneer (landmarks, blendshape_dict).
    blendshape_dict: {naam: score} voor alle beschikbare blendshapes.
    landmarks: lijst van landmarks voor het eerste gezicht, of None.
    """
    global _blendshape_namen_gelogd

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
    resultaat = landmarker.detect_for_video(mp_image, timestamp_ms)

    landmarks = None
    scores = {}

    if resultaat.face_landmarks:
        landmarks = resultaat.face_landmarks[0]

    if resultaat.face_blendshapes:
        for cat in resultaat.face_blendshapes[0]:
            if cat.category_name != "_neutral":
                scores[cat.category_name] = cat.score

        if not _blendshape_namen_gelogd and scores:
            _blendshape_namen_gelogd = True
            namen = sorted(scores.keys())
            print(f"  [DEBUG] MediaPipe blendshapes ({len(namen)}): "
                  f"{', '.join(namen)}")
            ontbrekend = set(NL_LABELS.keys()) - set(namen)
            if ontbrekend:
                print(f"  [DEBUG] Niet geleverd door model: "
                      f"{', '.join(sorted(ontbrekend))}")

    return landmarks, scores


# ---------------------------------------------------------------------------
# OpenCV tekenfuncties
# ---------------------------------------------------------------------------

def teken_face_mesh_simpel(frame, landmarks):
    """Teken een lichte face mesh + lipcontour."""
    h, w, _ = frame.shape
    for conn in TESSELATION:
        pt1, pt2 = landmarks[conn.start], landmarks[conn.end]
        cv2.line(frame,
                 (int(pt1.x * w), int(pt1.y * h)),
                 (int(pt2.x * w), int(pt2.y * h)),
                 (160, 160, 160), 1)
    for conn in LIPPEN:
        pt1, pt2 = landmarks[conn.start], landmarks[conn.end]
        cv2.line(frame,
                 (int(pt1.x * w), int(pt1.y * h)),
                 (int(pt2.x * w), int(pt2.y * h)),
                 (0, 230, 120), 2)


def teken_blendshape_bars(frame, scores, x_start, y_start,
                          bar_breedte=180, bar_hoogte=16, max_items=20,
                          pieken=None, top_n_namen=None):
    """
    Teken gesorteerde blendshape-balkjes op het frame.
    pieken: dict met piekwaarden (optioneel, voor highlight)
    top_n_namen: set van namen die gehighlight worden
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    gesorteerd = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

    y = y_start
    for i, (naam, score) in enumerate(gesorteerd[:max_items]):
        is_top = top_n_namen and naam in top_n_namen
        is_piek = pieken and naam in pieken

        # Kleur: geel voor top-N, groen voor actief, grijs voor laag
        if is_top:
            bar_kleur = (0, 255, 255)
            tekst_kleur = (0, 255, 255)
        elif score > 0.3:
            bar_kleur = (0, 200, 0)
            tekst_kleur = (0, 230, 0)
        elif score > 0.1:
            bar_kleur = (0, 140, 0)
            tekst_kleur = (180, 180, 180)
        else:
            bar_kleur = (60, 60, 60)
            tekst_kleur = (120, 120, 120)

        # Label
        label = nl_label(naam)
        if len(label) > 22:
            label = label[:20] + ".."
        cv2.putText(frame, label, (x_start, y + bar_hoogte - 3),
                    font, 0.35, tekst_kleur, 1)

        # Bar achtergrond + vulling
        bx = x_start + 145
        cv2.rectangle(frame, (bx, y), (bx + bar_breedte, y + bar_hoogte),
                      (40, 40, 40), -1)
        vulling = int(bar_breedte * min(score, 1.0))
        if vulling > 0:
            cv2.rectangle(frame, (bx, y), (bx + vulling, y + bar_hoogte),
                          bar_kleur, -1)

        # Score tekst
        score_tekst = f"{score:.2f}"
        cv2.putText(frame, score_tekst,
                    (bx + bar_breedte + 5, y + bar_hoogte - 3),
                    font, 0.35, tekst_kleur, 1)

        # Piek-marker
        if is_piek and pieken:
            piek_x = bx + int(bar_breedte * min(pieken[naam], 1.0))
            cv2.line(frame, (piek_x, y), (piek_x, y + bar_hoogte),
                     (0, 180, 255), 2)

        y += bar_hoogte + 4

    return y
