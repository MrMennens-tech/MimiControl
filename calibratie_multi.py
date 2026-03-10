"""
MimiMultiControl - Kalibratie voor individuele triggers.

Elke trigger wordt apart gekalibreerd in twee fasen:
  1. Neutraal gezicht opnemen (baseline)
  2. De specifieke uitdrukking opnemen (pieken zoeken)

Metingen die significant toenemen t.o.v. de baseline worden
automatisch als actieve drempelwaarden opgeslagen.
"""

import cv2
import time

from gezichtsdetectie import (
    maak_face_landmarker, detecteer_gezicht, bereken_alle_metingen,
    teken_face_mesh, teken_alle_meetpunten, METING_NAMEN, METING_LABELS
)
from config_multi import laad_multi_config, sla_multi_config_op

NEUTRAAL_DUUR = 3       # seconden neutraal opnemen
EXPRESSIE_DUUR = 4      # seconden expressie opnemen
COUNTDOWN_SEC = 3
SIGNIFICANTIE = 1.25    # meting moet ≥25% boven baseline liggen
MARGE = 0.10            # drempel = piek × (1 − marge)


def calibreer_trigger(trigger_index):
    """
    Kalibreer één trigger via de webcam.
    Returns True als de kalibratie succesvol is afgerond.
    """
    config = laad_multi_config()
    trigger = config["triggers"][trigger_index]
    naam = trigger["naam"]

    print(f"\n  === KALIBRATIE: {naam} ===")
    print("  De webcam opent met een preview.")
    print("  Druk SPATIE als je klaar bent, 'q' om af te breken.\n")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("  [!] Kan de webcam niet openen!")
        return False

    landmarker = maak_face_landmarker(modus="video")
    venster = f"Kalibratie: {naam}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    ts = 0

    # ---- Preview ----
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ts += 33
        lm = detecteer_gezicht(landmarker, rgb, ts)
        if lm:
            teken_face_mesh(frame, lm)
            teken_alle_meetpunten(frame, lm)

        _overlay_tekst(frame, "Positioneer het gezicht — druk SPATIE",
                       (0, 255, 255))
        cv2.imshow(venster, frame)
        k = cv2.waitKey(1) & 0xFF
        if k == ord(' '):
            break
        if k == ord('q'):
            _sluit(cap, landmarker)
            return False

    # ---- Countdown ----
    if not _doe_countdown(cap, landmarker, venster, ts, COUNTDOWN_SEC):
        return False
    ts += COUNTDOWN_SEC * 30 * 33

    # ---- Fase 1: Neutraal ----
    print(f"  [NEUTRAAL] Ontspan je gezicht ({NEUTRAAL_DUUR}s)...")
    baselines = {m: [] for m in METING_NAMEN}
    start = time.time()

    while time.time() - start < NEUTRAAL_DUUR:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ts += 33
        lm = detecteer_gezicht(landmarker, rgb, ts)

        if lm:
            teken_face_mesh(frame, lm)
            teken_alle_meetpunten(frame, lm)
            metingen = bereken_alle_metingen(lm)
            for m in METING_NAMEN:
                baselines[m].append(metingen[m])

        rest = NEUTRAAL_DUUR - (time.time() - start)
        _overlay_tekst(frame, f"Ontspan je gezicht  ({rest:.1f}s)", (255, 255, 255))
        _teken_fase_balk(frame, (time.time() - start) / NEUTRAAL_DUUR,
                         (200, 200, 200))
        cv2.imshow(venster, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            _sluit(cap, landmarker)
            return False

    # Korte "NU!" flash
    _flash(cap, venster, ts)
    ts += 30 * 33

    # ---- Fase 2: Expressie ----
    print(f"  [EXPRESSIE] Maak de uitdrukking ({EXPRESSIE_DUUR}s)!")
    pieken = {m: 0.0 for m in METING_NAMEN}
    frames_ok = 0
    start = time.time()

    while time.time() - start < EXPRESSIE_DUUR:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ts += 33
        lm = detecteer_gezicht(landmarker, rgb, ts)

        if lm:
            frames_ok += 1
            teken_face_mesh(frame, lm)
            teken_alle_meetpunten(frame, lm)
            metingen = bereken_alle_metingen(lm)
            for m in METING_NAMEN:
                if metingen[m] > pieken[m]:
                    pieken[m] = metingen[m]

            # Toon live waarden
            y = 55
            for m in METING_NAMEN:
                cv2.putText(frame,
                            f"{METING_LABELS[m]}: {metingen[m]:.3f}  "
                            f"(piek: {pieken[m]:.3f})",
                            (10, y), font, 0.5, (0, 255, 0), 1)
                y += 22

        rest = EXPRESSIE_DUUR - (time.time() - start)
        _overlay_tekst(frame, f"Maak de uitdrukking!  ({rest:.1f}s)",
                       (0, 255, 255))
        _teken_fase_balk(frame, (time.time() - start) / EXPRESSIE_DUUR,
                         (0, 0, 255))
        # REC indicator
        cv2.circle(frame, (frame.shape[1] - 25, 25), 8, (0, 0, 255), -1)
        cv2.imshow(venster, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            _sluit(cap, landmarker)
            return False

    _sluit(cap, landmarker)

    # ---- Analyse ----
    baseline_gem = {}
    for m in METING_NAMEN:
        vals = baselines[m]
        baseline_gem[m] = sum(vals) / len(vals) if vals else 0.001

    print(f"\n  --- Resultaten {naam} ---")
    drempelwaarden = {}

    for m in METING_NAMEN:
        bl = baseline_gem[m]
        pk = pieken[m]
        ratio = pk / bl if bl > 0 else 0
        significant = ratio >= SIGNIFICANTIE

        symbool = ">>>" if significant else "   "
        print(f"  {symbool} {METING_LABELS[m]:35s}  "
              f"baseline={bl:.4f}  piek={pk:.4f}  ratio={ratio:.2f}")

        if significant:
            drempelwaarden[m] = round(pk * (1 - MARGE), 6)

    if not drempelwaarden:
        print("\n  [!] Geen significante verandering gedetecteerd.")
        print("      Probeer de uitdrukking duidelijker te maken.")
        return False

    print(f"\n  Actieve metingen: {', '.join(drempelwaarden.keys())}")
    for m, d in drempelwaarden.items():
        print(f"    {m}: drempel = {d:.4f}")

    trigger["drempelwaarden"] = drempelwaarden
    trigger["actief"] = True
    config["triggers"][trigger_index] = trigger
    sla_multi_config_op(config)

    print(f"\n  [OK] {naam} gekalibreerd en opgeslagen!\n")
    return True


# ---------------------------------------------------------------------------
# Hulpfuncties voor de kalibratie-UI
# ---------------------------------------------------------------------------

def _overlay_tekst(frame, tekst, kleur):
    """Tekst met donkere achtergrond bovenaan het frame."""
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.putText(frame, tekst, (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, kleur, 2)


def _teken_fase_balk(frame, voortgang, kleur):
    """Voortgangsbalk onderaan het frame."""
    h, w = frame.shape[:2]
    bw = int(w * 0.8)
    bx = int(w * 0.1)
    by = h - 25
    cv2.rectangle(frame, (bx, by), (bx + bw, by + 12), (50, 50, 50), -1)
    cv2.rectangle(frame, (bx, by),
                  (bx + int(bw * min(voortgang, 1.0)), by + 12), kleur, -1)


def _doe_countdown(cap, landmarker, venster, ts_start, seconden):
    """Toon een visuele countdown. Returns False bij 'q'."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    ts = ts_start
    start = time.time()

    while True:
        rest = seconden - (time.time() - start)
        if rest <= 0:
            return True
        ret, frame = cap.read()
        if not ret:
            return True
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ts += 33
        lm = detecteer_gezicht(landmarker, rgb, ts)
        if lm:
            teken_face_mesh(frame, lm)

        h, w = frame.shape[:2]
        cijfer = str(int(rest) + 1)
        sz = cv2.getTextSize(cijfer, font, 4, 6)[0]
        cv2.putText(frame, cijfer,
                    ((w - sz[0]) // 2, (h + sz[1]) // 2),
                    font, 4, (0, 255, 255), 6)
        cv2.imshow(venster, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            _sluit(cap, landmarker)
            return False


def _flash(cap, venster, ts_basis):
    """Korte visuele flash als overgang tussen fasen."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    start = time.time()
    while time.time() - start < 0.8:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        # Gele rand-flash
        cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 255, 255), 8)
        tekst = "NU!"
        sz = cv2.getTextSize(tekst, font, 2.5, 4)[0]
        cv2.putText(frame, tekst,
                    ((w - sz[0]) // 2, (h + sz[1]) // 2),
                    font, 2.5, (0, 255, 255), 4)
        cv2.imshow(venster, frame)
        cv2.waitKey(1)


def _sluit(cap, landmarker):
    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
