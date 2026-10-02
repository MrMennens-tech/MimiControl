"""
MimiExplorer - Blendshape Detectie Module
FaceLandmarker wrapper met blendshape-output, score-functies
en OpenCV tekenhulpen voor live balkjes.
"""

import cv2
import os
import urllib.request

import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from paths import model_path
from blendshape_labels import (
    NL_LABELS, NIET_ONDERSTEUND, is_ondersteund, filter_ondersteund, nl_label,
    scores_in_groepsvolgorde,
)

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
OVAL = getattr(
    vision.FaceLandmarksConnections,
    "FACE_LANDMARKS_FACE_OVAL",
    LIPPEN,
)

# MediaPipe FaceLandmarker heeft geen 1080p nodig; 640 px is nauwkeurig genoeg
# voor blendshapes en scheelt veel op de CPU.
DETECTIE_MAX_BREEDTE = 640


def frame_is_ok(frame):
    """True als numpy-beeld veilig naar cv::Mat kan (geen 0-maat, geen te kleine stride)."""
    if frame is None or not isinstance(frame, np.ndarray):
        return False
    if frame.ndim < 2 or frame.size == 0:
        return False
    hoogte, breedte = frame.shape[:2]
    if hoogte <= 0 or breedte <= 0:
        return False
    kanalen = 1 if frame.ndim == 2 else int(frame.shape[2])
    if kanalen not in (1, 3, 4):
        return False
    min_step = breedte * kanalen * max(1, frame.dtype.itemsize)
    if frame.strides[0] < min_step:
        return False
    return True


def naar_contiguous_beeld(frame):
    """
    Maak een uint8 HxWx3 C-contiguous kopie, of None als het frame onbruikbaar is.
    Numpy-kopie eerst: OpenCV mag nooit een Mat zien met step 0 of step < minstep.
    """
    if not frame_is_ok(frame):
        return None
    try:
        beeld = np.array(frame, dtype=np.uint8, order="C", copy=True)
    except Exception:
        return None
    if beeld.ndim == 2 or (beeld.ndim == 3 and beeld.shape[2] == 1):
        beeld = cv2.cvtColor(beeld, cv2.COLOR_GRAY2BGR)
    elif beeld.ndim == 3 and beeld.shape[2] == 4:
        beeld = cv2.cvtColor(beeld, cv2.COLOR_BGRA2BGR)
    elif beeld.ndim != 3 or beeld.shape[2] != 3:
        return None
    if not beeld.flags["C_CONTIGUOUS"]:
        beeld = np.ascontiguousarray(beeld)
    if not frame_is_ok(beeld):
        return None
    return beeld


def veilig_imshow(venster, beeld):
    """cv2.imshow zonder crash op lege of non-contiguous frames."""
    beeld = naar_contiguous_beeld(beeld)
    if beeld is None:
        return False
    cv2.imshow(venster, beeld)
    return True


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

    Detectie gebruikt MediaPipe FaceLandmarker-blendshapes, niet de
    getekende mesh. `teken_face_mesh_simpel` is alleen visualisatie.
    """
    global _blendshape_namen_gelogd

    if not frame_is_ok(frame_rgb):
        return None, {}

    try:
        # Geen kopie nodig: de aanroeper levert een eigen RGB-frame; alleen
        # als het niet uint8/C-contiguous is, maakt asarray er een kopie van.
        frame_rgb = np.asarray(frame_rgb, dtype=np.uint8, order="C")
    except Exception:
        return None, {}
    if frame_rgb.ndim == 2 or (frame_rgb.ndim == 3 and frame_rgb.shape[2] == 1):
        frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_GRAY2RGB)
    elif frame_rgb.ndim == 3 and frame_rgb.shape[2] == 4:
        frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_RGBA2RGB)
    elif frame_rgb.ndim != 3 or frame_rgb.shape[2] != 3:
        return None, {}

    h, w = frame_rgb.shape[:2]
    if w > DETECTIE_MAX_BREEDTE:
        nh = max(1, int(h * DETECTIE_MAX_BREEDTE / w))
        frame_rgb = cv2.resize(
            frame_rgb, (DETECTIE_MAX_BREEDTE, nh), interpolation=cv2.INTER_AREA
        )
        frame_rgb = np.ascontiguousarray(frame_rgb)

    if not frame_is_ok(frame_rgb):
        return None, {}
    if not frame_rgb.flags["C_CONTIGUOUS"]:
        frame_rgb = np.ascontiguousarray(frame_rgb)

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
            dood_in_output = sorted(
                n for n in namen if not is_ondersteund(n)
            )
            if dood_in_output:
                print(f"  [DEBUG] In output maar niet bruikbaar: "
                      f"{', '.join(dood_in_output)}")

        scores = filter_ondersteund(scores)

    return landmarks, scores


# ---------------------------------------------------------------------------
# OpenCV tekenfuncties
# ---------------------------------------------------------------------------

def teken_face_mesh_simpel(frame, landmarks, volledig=False, oval_kleur=None):
    """
    Teken lipcontour + gezichtsovaal (licht) of optioneel de volle tesselatie.

    Alleen visualisatie: blendshape-scores komen uit detecteer_blendshapes
    en veranderen niet door deze tekening.
    """
    if landmarks is None or not frame_is_ok(frame) or frame.ndim != 3:
        return
    h, w, _ = frame.shape
    mesh_kleur = (160, 160, 160)
    lijnen = TESSELATION if volledig else OVAL
    for conn in lijnen:
        pt1, pt2 = landmarks[conn.start], landmarks[conn.end]
        cv2.line(frame,
                 (int(pt1.x * w), int(pt1.y * h)),
                 (int(pt2.x * w), int(pt2.y * h)),
                 mesh_kleur, 1)
    if oval_kleur is not None and not volledig:
        for conn in OVAL:
            pt1, pt2 = landmarks[conn.start], landmarks[conn.end]
            cv2.line(frame,
                     (int(pt1.x * w), int(pt1.y * h)),
                     (int(pt2.x * w), int(pt2.y * h)),
                     oval_kleur, 2)
    for conn in LIPPEN:
        pt1, pt2 = landmarks[conn.start], landmarks[conn.end]
        cv2.line(frame,
                 (int(pt1.x * w), int(pt1.y * h)),
                 (int(pt2.x * w), int(pt2.y * h)),
                 (0, 230, 120), 2)


def teken_gezicht_gloed(frame, landmarks, kleur, dikte=3):
    """Gekleurde ovaal-gloed rond het gezicht — leesbaar op een kleine overlay."""
    if landmarks is None or not frame_is_ok(frame) or frame.ndim != 3:
        return
    h, w, _ = frame.shape
    xs = []
    ys = []
    for conn in OVAL:
        for lm in (landmarks[conn.start], landmarks[conn.end]):
            xs.append(lm.x * w)
            ys.append(lm.y * h)
    if not xs:
        return
    cx = int((min(xs) + max(xs)) / 2)
    cy = int((min(ys) + max(ys)) / 2)
    rx = max(10, int((max(xs) - min(xs)) / 2) + 12)
    ry = max(10, int((max(ys) - min(ys)) / 2) + 12)
    cv2.ellipse(frame, (cx, cy), (rx + 5, ry + 5), 0, 0, 360, kleur, 1)
    cv2.ellipse(frame, (cx, cy), (rx, ry), 0, 0, 360, kleur, max(2, int(dikte)))


def teken_blendshape_bars(frame, scores, x_start, y_start,
                          bar_breedte=180, bar_hoogte=16, max_items=20,
                          pieken=None, top_n_namen=None):
    """
    Teken blendshape-balkjes in groepsvolgorde (tuiten/trechter eerst
    binnen mond), niet gesorteerd op ruwe score.
    pieken: dict met piekwaarden (optioneel, voor highlight)
    top_n_namen: set van namen die gehighlight worden
    """
    if not frame_is_ok(frame):
        return y_start
    scores = filter_ondersteund(scores)
    if not scores:
        return y_start
    font = cv2.FONT_HERSHEY_SIMPLEX
    gesorteerd = scores_in_groepsvolgorde(scores)

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
