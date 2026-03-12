"""
MimiControl - Gezichtsdetectie Module
Gebruikt de MediaPipe Tasks API (FaceLandmarker) voor gezichtsdetectie,
meetfuncties en tekenhulpen.
"""

import cv2
import math
import os
import urllib.request

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ---------------------------------------------------------------------------
# Model configuratie
# ---------------------------------------------------------------------------
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)
MODEL_PAD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "face_landmarker.task"
)

# ---------------------------------------------------------------------------
# Landmark indices
# Mondhoeken (links/rechts vanuit perspectief van de persoon)
MONDHOEK_LINKS = 61
MONDHOEK_RECHTS = 291
# Binnenkant lippen (boven/onder)
BOVENLIP_BINNEN = 13
ONDERLIP_BINNEN = 14
# Buitenste ooghoeken (stabiele referentiepunten voor normalisatie)
OOG_LINKS_BUITEN = 33
OOG_RECHTS_BUITEN = 263
# Wenkbrauwen en oogleden (voor multi-trigger modus)
WENKBRAUW_LINKS = 105       # linker wenkbrauw bovenkant (inner)
WENKBRAUW_RECHTS = 334      # rechter wenkbrauw bovenkant (inner)
OOG_LINKS_BOVEN = 159       # linker bovenste ooglid
OOG_RECHTS_BOVEN = 386      # rechter bovenste ooglid
# ---------------------------------------------------------------------------

# Alle beschikbare metingnamen en hun leesbare labels
METING_NAMEN = ["mondbreedte", "liphoogte", "wenkbrauwhoogte"]
METING_LABELS = {
    "mondbreedte": "Mondbreedte (lach)",
    "liphoogte": "Liphoogte (tongbol / mond open)",
    "wenkbrauwhoogte": "Wenkbrauwhoogte (optrekken)",
}
METING_KLEUREN = {
    "mondbreedte": (0, 255, 0),
    "liphoogte": (0, 165, 255),
    "wenkbrauwhoogte": (255, 100, 200),
}

# Connecties voor het tekenen van de face mesh
TESSELATION = vision.FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION
LIPPEN = vision.FaceLandmarksConnections.FACE_LANDMARKS_LIPS


def zorg_voor_model():
    """Download het Face Landmarker model als het nog niet lokaal staat."""
    if not os.path.exists(MODEL_PAD):
        print("  [INFO] Face Landmarker model downloaden...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PAD)
        print("  [OK] Model opgeslagen.")


def maak_face_landmarker(modus="video"):
    """
    Maak een MediaPipe FaceLandmarker aan.
    modus: "video" voor video/webcam, "image" voor losse afbeeldingen.
    """
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
    )
    return vision.FaceLandmarker.create_from_options(options)


def detecteer_gezicht(landmarker, frame_rgb, timestamp_ms):
    """
    Voer face landmark detectie uit op een RGB frame.
    Returns: lijst van landmarks voor het eerste gezicht, of None.
    """
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB, data=frame_rgb
    )
    resultaat = landmarker.detect_for_video(mp_image, timestamp_ms)

    if resultaat.face_landmarks:
        return resultaat.face_landmarks[0]
    return None


def bereken_afstand(punt1, punt2):
    """Euclidische afstand tussen twee genormaliseerde landmarks."""
    return math.sqrt((punt1.x - punt2.x) ** 2 + (punt1.y - punt2.y) ** 2)


def bereken_mond_metingen(landmarks):
    """
    Bereken mondbreedte en liphoogte, genormaliseerd op de afstand
    tussen de buitenste ooghoeken. Dit maakt de meting onafhankelijk
    van de afstand tot de camera.

    Returns:
        (mondbreedte, liphoogte) – beide genormaliseerde floats
    """
    mondhoek_l = landmarks[MONDHOEK_LINKS]
    mondhoek_r = landmarks[MONDHOEK_RECHTS]
    bovenlip = landmarks[BOVENLIP_BINNEN]
    onderlip = landmarks[ONDERLIP_BINNEN]
    oog_l = landmarks[OOG_LINKS_BUITEN]
    oog_r = landmarks[OOG_RECHTS_BUITEN]

    normalisatie = bereken_afstand(oog_l, oog_r)
    if normalisatie == 0:
        return 0.0, 0.0

    mondbreedte = bereken_afstand(mondhoek_l, mondhoek_r) / normalisatie
    liphoogte = bereken_afstand(bovenlip, onderlip) / normalisatie

    return mondbreedte, liphoogte


def teken_face_mesh(frame, landmarks):
    """Teken de face mesh tesselation en lipcontour over het frame."""
    h, w, _ = frame.shape

    # Tesselation: dunne grijze lijnen
    for conn in TESSELATION:
        pt1 = landmarks[conn.start]
        pt2 = landmarks[conn.end]
        x1, y1 = int(pt1.x * w), int(pt1.y * h)
        x2, y2 = int(pt2.x * w), int(pt2.y * h)
        cv2.line(frame, (x1, y1), (x2, y2), (180, 180, 180), 1)

    # Lippen: groene lijnen
    for conn in LIPPEN:
        pt1 = landmarks[conn.start]
        pt2 = landmarks[conn.end]
        x1, y1 = int(pt1.x * w), int(pt1.y * h)
        x2, y2 = int(pt2.x * w), int(pt2.y * h)
        cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 128), 2)


def bereken_wenkbrauw_hoogte(landmarks):
    """
    Gemiddelde afstand van wenkbrauw tot ooglid (links + rechts),
    genormaliseerd op de ooghoekafstand. Neemt toe bij optrekken.
    """
    normalisatie = bereken_afstand(
        landmarks[OOG_LINKS_BUITEN], landmarks[OOG_RECHTS_BUITEN])
    if normalisatie == 0:
        return 0.0

    links = bereken_afstand(
        landmarks[WENKBRAUW_LINKS], landmarks[OOG_LINKS_BOVEN]) / normalisatie
    rechts = bereken_afstand(
        landmarks[WENKBRAUW_RECHTS], landmarks[OOG_RECHTS_BOVEN]) / normalisatie
    return (links + rechts) / 2


def bereken_alle_metingen(landmarks):
    """Bereken alle beschikbare metingen in een dict."""
    mondbreedte, liphoogte = bereken_mond_metingen(landmarks)
    return {
        "mondbreedte": mondbreedte,
        "liphoogte": liphoogte,
        "wenkbrauwhoogte": bereken_wenkbrauw_hoogte(landmarks),
    }


def teken_meetpunten(frame, landmarks):
    """
    Markeer de vier meetpunten (mondhoeken + lippen) met gekleurde cirkels
    zodat de gebruiker kan zien welke punten gevolgd worden.
    """
    h, w, _ = frame.shape

    punten = {
        MONDHOEK_LINKS:  (0, 255, 0),      # groen – mondhoek
        MONDHOEK_RECHTS: (0, 255, 0),       # groen – mondhoek
        BOVENLIP_BINNEN: (0, 165, 255),     # oranje – bovenlip
        ONDERLIP_BINNEN: (0, 165, 255),     # oranje – onderlip
    }

    for idx, kleur in punten.items():
        lm = landmarks[idx]
        x, y = int(lm.x * w), int(lm.y * h)
        cv2.circle(frame, (x, y), 6, kleur, -1)
        cv2.circle(frame, (x, y), 8, (255, 255, 255), 2)


def teken_alle_meetpunten(frame, landmarks):
    """Teken alle meetpunten inclusief wenkbrauwen."""
    teken_meetpunten(frame, landmarks)
    h, w, _ = frame.shape
    kleur = METING_KLEUREN["wenkbrauwhoogte"]

    for idx in (WENKBRAUW_LINKS, WENKBRAUW_RECHTS,
                OOG_LINKS_BOVEN, OOG_RECHTS_BOVEN):
        lm = landmarks[idx]
        x, y = int(lm.x * w), int(lm.y * h)
        cv2.circle(frame, (x, y), 5, kleur, -1)
        cv2.circle(frame, (x, y), 7, (255, 255, 255), 2)
