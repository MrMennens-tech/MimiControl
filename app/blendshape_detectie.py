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

# ---------------------------------------------------------------------------
# Model (hergebruik van gezichtsdetectie.py)
# ---------------------------------------------------------------------------
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)
MODEL_PAD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "face_landmarker.task"
)


def zorg_voor_model():
    if not os.path.exists(MODEL_PAD):
        print("  [INFO] Face Landmarker model downloaden...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PAD)
        print("  [OK] Model opgeslagen.")


# ---------------------------------------------------------------------------
# Nederlandse labels voor de meest voorkomende blendshapes
# ---------------------------------------------------------------------------
NL_LABELS = {
    "browDownLeft": "Wenkbrauw omlaag L",
    "browDownRight": "Wenkbrauw omlaag R",
    "browInnerUp": "Wenkbrauwen omhoog (binnen)",
    "browOuterUpLeft": "Wenkbrauw omhoog L",
    "browOuterUpRight": "Wenkbrauw omhoog R",
    "cheekPuff": "Wangen bol",
    "cheekSquintLeft": "Wang knijp L",
    "cheekSquintRight": "Wang knijp R",
    "eyeBlinkLeft": "Oogknip L",
    "eyeBlinkRight": "Oogknip R",
    "eyeLookDownLeft": "Blik omlaag L",
    "eyeLookDownRight": "Blik omlaag R",
    "eyeLookInLeft": "Blik naar binnen L",
    "eyeLookInRight": "Blik naar binnen R",
    "eyeLookOutLeft": "Blik naar buiten L",
    "eyeLookOutRight": "Blik naar buiten R",
    "eyeLookUpLeft": "Blik omhoog L",
    "eyeLookUpRight": "Blik omhoog R",
    "eyeSquintLeft": "Oog knijp L",
    "eyeSquintRight": "Oog knijp R",
    "eyeWideLeft": "Oog wijd L",
    "eyeWideRight": "Oog wijd R",
    "jawForward": "Kaak vooruit",
    "jawLeft": "Kaak links",
    "jawOpen": "Kaak open",
    "jawRight": "Kaak rechts",
    "mouthClose": "Mond dicht",
    "mouthDimpleLeft": "Mondkuiltje L",
    "mouthDimpleRight": "Mondkuiltje R",
    "mouthFrownLeft": "Mondhoek omlaag L",
    "mouthFrownRight": "Mondhoek omlaag R",
    "mouthFunnel": "Mond trechter (tongbol)",
    "mouthLeft": "Mond naar links",
    "mouthLowerDownLeft": "Onderlip omlaag L",
    "mouthLowerDownRight": "Onderlip omlaag R",
    "mouthPressLeft": "Lipdruk L",
    "mouthPressRight": "Lipdruk R",
    "mouthPucker": "Lippen tuiten",
    "mouthRight": "Mond naar rechts",
    "mouthRollLower": "Onderlip rollen",
    "mouthRollUpper": "Bovenlip rollen",
    "mouthShrugLower": "Onderlip omhoog",
    "mouthShrugUpper": "Bovenlip omhoog",
    "mouthSmileLeft": "Lach links",
    "mouthSmileRight": "Lach rechts",
    "mouthStretchLeft": "Mond strekken L",
    "mouthStretchRight": "Mond strekken R",
    "mouthUpperUpLeft": "Bovenlip op L",
    "mouthUpperUpRight": "Bovenlip op R",
    "noseSneerLeft": "Neus optrekken L",
    "noseSneerRight": "Neus optrekken R",
    "tongueOut": "Tong uitsteken",
}

# Face mesh connecties voor tekenen
TESSELATION = vision.FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION
LIPPEN = vision.FaceLandmarksConnections.FACE_LANDMARKS_LIPS


NIET_ONDERSTEUND = {
    "tongueOut",
}

def nl_label(naam):
    """Geef het Nederlandse label voor een blendshape, of de originele naam."""
    return NL_LABELS.get(naam, naam)


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
        base_options=python.BaseOptions(model_asset_path=MODEL_PAD),
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
