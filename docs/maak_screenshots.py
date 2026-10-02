"""
Maakt de afbeeldingen voor de handleiding van MimiControl Studio v2.

Gebruik (in de repo-root):   python docs\\maak_screenshots.py
Resultaat: docs\\afbeeldingen\\*.png

- Echte schermen (dashboard, keuzescherm, filter, trigger-editor) worden
  automatisch gefotografeerd. Er wordt met demo-gegevens gewerkt en er wordt
  niets in je eigen profiel opgeslagen.
- Het explorer-venster en het live-camerabeeld worden getekend met een
  neutraal silhouet, zodat er geen echt gezicht in de handleiding staat.

Opnieuw draaien na een wijziging in de schermen = actuele handleiding.
Niet aanraken tijdens het draaien: het script zet vensters op de voorgrond.
"""

import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
APP = os.path.abspath(os.path.join(HIER, "..", "app_v2"))
UIT = os.path.join(HIER, "afbeeldingen")
sys.path.insert(0, APP)
os.makedirs(UIT, exist_ok=True)

import numpy as np
import cv2
from PIL import ImageGrab

import toets_actie
toets_actie.studio_draait_als_admin = lambda: True  # toon "Beheerder: ja"

import config_explorer as ce
import gui_explorer_ctk as gui
import customtkinter as ctk

DEMO_TRIGGERS = [
    {"naam": "Spatie met kaak", "toetsen": ["space"],
     "blendshapes": {"jawOpen": 0.45}},
    {"naam": "Volgende met lach", "toetsen": ["enter"],
     "blendshapes": {"mouthSmileLeft": 0.40, "mouthSmileRight": 0.40}},
]


# ---------------------------------------------------------------------------
# Demo-config: de GUI leest en schrijft niets in het echte profiel
# ---------------------------------------------------------------------------
_orig_laad = ce.laad_explorer_config


def _demo_config():
    c = _orig_laad()
    c["triggers"] = [dict(t) for t in DEMO_TRIGGERS]
    c["cooldown"] = 1.5
    c["vasthoud_tijd"] = 0.4
    c["toets_duur_ms"] = 100
    return c


gui.laad_explorer_config = _demo_config
gui.sla_explorer_config_op = lambda c: None


# ---------------------------------------------------------------------------
# Echte schermen
# ---------------------------------------------------------------------------
def grijp(widget, naam, pauze=300):
    widget.lift()
    widget.update()
    widget.after(pauze)
    widget.update()
    x, y = widget.winfo_rootx(), widget.winfo_rooty()
    w, h = widget.winfo_width(), widget.winfo_height()
    ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True).save(
        os.path.join(UIT, naam))
    print("  ->", naam)


def laatste_dialoog(hoofd):
    kandidaten = [w for w in hoofd.winfo_children()
                  if isinstance(w, ctk.CTkToplevel) and w.winfo_viewable()]
    return kandidaten[-1] if kandidaten else None


def maak_echte_schermen():
    studio = gui.MimiControlStudioApp()
    app = studio.app
    stappen = []

    def dashboard():
        # kleiner venster, zodat de tekst in de handleiding leesbaar blijft
        app.state("normal")
        app.geometry("1400x860+40+20")
        app.update()
        grijp(app, "01-dashboard.png", pauze=1200)

    def dialoog(opener, naam, wacht=1800):
        def run():
            def foto():
                d = laatste_dialoog(app)
                if d is not None:
                    grijp(d, naam)
                    try:
                        d.grab_release()
                    except Exception:
                        pass
                    d.destroy()
            app.after(wacht, foto)
            opener()
        return run

    import explorer
    import trigger_editor_ctk as te

    scores = {"jawOpen": 0.62, "jawLeft": 0.05, "jawRight": 0.04,
              "mouthFunnel": 0.30, "mouthSmileLeft": 0.10,
              "eyeBlinkLeft": 0.20}

    stappen.append(dashboard)
    stappen.append(dialoog(
        lambda: explorer._toon_blendshape_selectie_vooraf(app),
        "02-kies-bewegingen.png"))
    stappen.append(dialoog(
        lambda: explorer._toon_filter_dialoog(
            scores, {"jawOpen", "jawLeft", "jawRight"},
            {"jawOpen", "jawLeft", "jawRight"}, parent=app),
        "04-beweging-kiezen.png"))
    stappen.append(dialoog(
        lambda: te.open_trigger_editor(
            app, {"jawOpen": 0.62, "jawLeft": 0.05, "jawRight": 0.04,
                  "jawForward": 0.0}),
        "05-trigger-editor.png"))

    def volgende():
        if stappen:
            stappen.pop(0)()
            app.after(2600, volgende)
        else:
            app.after(300, app.destroy)

    # wacht tot het opstartscherm weg is (camera-detectie duurt een paar sec.)
    app.after(11000, volgende)
    studio.start()


# ---------------------------------------------------------------------------
# Getekende schermen (neutraal silhouet)
# ---------------------------------------------------------------------------
def silhouet(breedte, hoogte):
    beeld = np.full((hoogte, breedte, 3), (70, 66, 60), np.uint8)
    cx, cy = breedte // 2, int(hoogte * 0.52)
    rx, ry = int(hoogte * 0.27), int(hoogte * 0.36)
    cv2.ellipse(beeld, (cx, cy), (rx, ry), 0, 0, 360, (150, 150, 150), -1)
    cv2.ellipse(beeld, (cx, cy), (rx, ry), 0, 0, 360, (210, 210, 210), 2)
    for dx in (-1, 1):
        cv2.ellipse(beeld, (cx + dx * rx // 2, cy - ry // 5),
                    (rx // 6, ry // 14), 0, 0, 360, (60, 60, 60), -1)
    cv2.ellipse(beeld, (cx, cy + ry // 2), (rx // 3, ry // 9),
                0, 0, 360, (60, 60, 60), 2)
    return beeld


def maak_explorer_beeld():
    import explorer
    from blendshape_detectie import teken_blendshape_bars
    cam_w, cam_h, paneel = 640, 360, 420
    canvas = np.zeros((cam_h + explorer.KNOPPEN_HOOGTE, cam_w + paneel, 3),
                      np.uint8)
    canvas[:cam_h, :cam_w] = silhouet(cam_w, cam_h)
    canvas[:cam_h, cam_w:] = (25, 25, 30)
    canvas[cam_h:, :] = (38, 38, 44)
    scores = {"jawOpen": 0.71, "jawLeft": 0.05, "jawRight": 0.04,
              "jawForward": 0.02}
    teken_blendshape_bars(canvas, scores, x_start=cam_w + 10, y_start=50,
                          bar_breedte=160, bar_hoogte=14, max_items=4,
                          pieken={"jawOpen": 0.71},
                          top_n_namen={"jawOpen"})
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(canvas, "Stap 2: klik Trigger maken", (cam_w + 10, 25),
                font, 0.5, (0, 255, 255), 1)
    knoppen = explorer._knoppen_voor_staat(False, True, canvas.shape[1], cam_h)
    explorer._teken_knoppen(canvas, knoppen)
    cv2.imwrite(os.path.join(UIT, "03-verkennen.png"), canvas)
    print("  -> 03-verkennen.png")


def maak_live_beelden():
    import live_modus_explorer as lm
    for naam, melding in (("06-live-camerabeeld.png", None),
                          ("07-live-toets-verstuurd.png", "space"),
                          ("08-live-stoppen.png", "stop")):
        beeld = silhouet(480, 270)
        kleur = (0, 200, 255)
        if melding == "space":
            cv2.rectangle(beeld, (0, 0), (479, 269), kleur, 4)
            lm._teken_actiebadge(beeld, 270, lm._toets_tekst(["space"]),
                                 kleur, True)
        lm._teken_stop_knop(beeld, 480, melding == "stop")
        cv2.imwrite(os.path.join(UIT, naam), beeld)
        print("  ->", naam)


if __name__ == "__main__":
    print("Getekende schermen...")
    maak_explorer_beeld()
    maak_live_beelden()
    print("Echte schermen (even niet aanraken)...")
    maak_echte_schermen()
    print("Klaar:", UIT)
