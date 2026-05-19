"""
MimiExplorer - Live Modus
Controleert alle geconfigureerde triggers gelijktijdig op basis
van blendshape-scores, met anti-spasme filter en cooldown.
Bevat een apart CustomTkinter paneel voor live drempelaanpassingen.
"""

import cv2
import time
import threading
import pyautogui

import customtkinter as ctk

from config_explorer import laad_explorer_config, sla_explorer_config_op
from blendshape_detectie import (
    maak_blendshape_landmarker, detecteer_blendshapes,
    teken_face_mesh_simpel, nl_label
)
from toets_actie import voer_toetsen_uit

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

# ---------------------------------------------------------------------------
# Mennens.Tech kleurenpalet
# ---------------------------------------------------------------------------
DONKER      = "#062D36"
TEAL_BTN    = "#4DB8BE"
TEAL_HOVER  = "#3A9DA3"
BG          = "#F2F2F7"
KAART       = "#FFFFFF"
TEKST       = "#1C1C1E"
TEKST_LICHT = "#5A5A5E"
RAND        = "#E5E5EA"
TEAL_BRAND  = "#68CCD1"
FONT        = "Segoe UI"

# Kleuren voor triggers in het OpenCV-venster (BGR)
TRIGGER_KLEUREN = [
    (0, 220, 0),
    (220, 160, 0),
    (0, 120, 255),
    (180, 0, 220),
    (0, 220, 220),
]


# ---------------------------------------------------------------------------
# CustomTkinter slider-paneel voor live drempelaanpassingen
# ---------------------------------------------------------------------------
class DrempelPaneel:
    """
    Apart CTk-venster dat naast het webcam-venster verschijnt.
    Toont per trigger de blendshapes met sliders, zodat de
    gebruiker drempels real-time kan bijstellen.
    """

    def __init__(self, triggers):
        self._triggers = triggers
        self._gesloten = False
        self._slider_refs = {}    # {(trigger_idx, bs_naam): slider}
        self._waarde_refs = {}    # {(trigger_idx, bs_naam): label}
        self._status_refs = {}    # {trigger_idx: status_label}
        self._lock = threading.Lock()

        self.venster = ctk.CTkToplevel()
        self.venster.title("Drempel Aanpassingen — MimiControl")
        self.venster.configure(fg_color=BG)
        self.venster.geometry("420x640+50+50")
        self.venster.minsize(380, 400)
        self.venster.resizable(True, True)
        self.venster.protocol("WM_DELETE_WINDOW", self._sluit)

        try:
            self.venster.attributes("-topmost", True)
        except Exception:
            pass

        self._bouw_ui()

    def _bouw_ui(self):
        # Header
        header = ctk.CTkFrame(self.venster, fg_color=DONKER, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="Live Drempels Aanpassen",
            font=(FONT, 16, "bold"), text_color=KAART
        ).pack(pady=14)

        # Scrollbaar trigger-overzicht
        scroll = ctk.CTkScrollableFrame(self.venster, fg_color=BG, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        for t_idx, trigger in enumerate(self._triggers):
            if not trigger.get("blendshapes"):
                continue

            accent = ["#4DB8BE", "#3D8FA5", "#68CCD1", "#2E7A8A", "#89D4D8"][
                t_idx % 5
            ]

            # Trigger-kaart
            kaart = ctk.CTkFrame(scroll, fg_color=KAART, corner_radius=12,
                                 border_width=1, border_color=RAND)
            kaart.pack(fill="x", padx=12, pady=6)

            # Accent-balk
            ctk.CTkFrame(kaart, fg_color=accent, height=3, corner_radius=0
                         ).pack(fill="x", padx=10, pady=(8, 0))

            # Titel-rij met naam, toets en live status
            titel_rij = ctk.CTkFrame(kaart, fg_color="transparent")
            titel_rij.pack(fill="x", padx=12, pady=(6, 2))

            toets = " + ".join(trigger["toetsen"]).upper()
            ctk.CTkLabel(
                titel_rij, text=f"{trigger['naam']}",
                font=(FONT, 13, "bold"), text_color=TEKST
            ).pack(side="left")

            ctk.CTkLabel(
                titel_rij, text=toets, font=(FONT, 11, "bold"),
                text_color=KAART, fg_color=accent, corner_radius=8,
                width=60, height=24
            ).pack(side="right", padx=(4, 0))

            status_lbl = ctk.CTkLabel(
                titel_rij, text="—", font=(FONT, 11),
                text_color=TEKST_LICHT
            )
            status_lbl.pack(side="right", padx=(0, 8))
            self._status_refs[t_idx] = status_lbl

            # Sliders per blendshape
            for bs_naam, drempel in trigger["blendshapes"].items():
                rij = ctk.CTkFrame(kaart, fg_color="transparent")
                rij.pack(fill="x", padx=14, pady=2)

                ctk.CTkLabel(
                    rij, text=nl_label(bs_naam),
                    font=(FONT, 11), text_color=TEKST_LICHT,
                    width=140, anchor="w"
                ).pack(side="left")

                waarde_lbl = ctk.CTkLabel(
                    rij, text=f"{drempel:.2f}", font=(FONT, 11, "bold"),
                    text_color=TEKST, width=44, anchor="e"
                )
                waarde_lbl.pack(side="right", padx=(4, 2))
                self._waarde_refs[(t_idx, bs_naam)] = waarde_lbl

                slider = ctk.CTkSlider(
                    rij, from_=0.0, to=1.0,
                    button_color=TEAL_BTN, button_hover_color=TEAL_HOVER,
                    progress_color=TEAL_BTN,
                    command=lambda val, ti=t_idx, bn=bs_naam: self._on_slider(ti, bn, val)
                )
                slider.set(drempel)
                slider.pack(side="left", fill="x", expand=True, padx=(4, 4))
                self._slider_refs[(t_idx, bs_naam)] = slider

            # Ruimte onderaan kaart
            ctk.CTkFrame(kaart, fg_color="transparent", height=6).pack()

        # Opslaan-knop onderaan
        btn_frame = ctk.CTkFrame(self.venster, fg_color=BG, height=56)
        btn_frame.pack(fill="x")
        btn_frame.pack_propagate(False)
        ctk.CTkButton(
            btn_frame, text="Opslaan & Sluiten", font=(FONT, 13, "bold"),
            fg_color=TEAL_BTN, hover_color=TEAL_HOVER,
            corner_radius=12, height=38, command=self._sluit
        ).pack(pady=10)

    def _on_slider(self, trigger_idx, bs_naam, waarde):
        """Real-time drempel aanpassen bij slider-beweging."""
        val = round(waarde, 3)
        with self._lock:
            self._triggers[trigger_idx]["blendshapes"][bs_naam] = val
        lbl = self._waarde_refs.get((trigger_idx, bs_naam))
        if lbl:
            lbl.configure(text=f"{val:.2f}")

    def update_status(self, trigger_idx, actief, score_tekst=""):
        """Wordt aangeroepen vanuit de webcam-loop om de status bij te werken."""
        lbl = self._status_refs.get(trigger_idx)
        if lbl and not self._gesloten:
            try:
                if actief:
                    lbl.configure(text="ACTIEF", text_color="#22AA44")
                else:
                    lbl.configure(text=score_tekst if score_tekst else "inactief",
                                  text_color=TEKST_LICHT)
            except Exception:
                pass

    def haal_drempel(self, trigger_idx, bs_naam):
        """Thread-safe drempel ophalen."""
        with self._lock:
            return self._triggers[trigger_idx]["blendshapes"].get(bs_naam, 0)

    def _sluit(self):
        """Config opslaan en venster sluiten."""
        self._gesloten = True
        config = laad_explorer_config()
        for i, trigger in enumerate(self._triggers):
            if i < len(config["triggers"]):
                config["triggers"][i]["blendshapes"] = trigger["blendshapes"]
        sla_explorer_config_op(config)
        self.venster.destroy()

    @property
    def is_open(self):
        return not self._gesloten


# ---------------------------------------------------------------------------
# Verbeterde overlay met grotere tekst en kleurcodering
# ---------------------------------------------------------------------------
def teken_live_overlay(frame, scores, triggers, trigger_states,
                       nu, vasthoud_tijd, laatste_actie, cooldown,
                       actie_flash, actie_idx, gezicht_ok):
    """Teken overlay met trigger-statussen en actieve blendshapes."""
    h, w, _ = frame.shape
    font = cv2.FONT_HERSHEY_SIMPLEX

    actieve_triggers = [t for t in triggers if t.get("blendshapes")]

    # Bereken overlay hoogte: titel + triggers + blendshape details
    regels = 2 + len(actieve_triggers) * 3
    overlay_h = max(80, 32 + regels * 22)
    overlay_h = min(overlay_h, h - 40)

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, overlay_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    if not gezicht_ok:
        cv2.putText(frame, "GEEN GEZICHT GEDETECTEERD",
                    (10, 32), font, 0.7, (0, 0, 255), 2)
        return []

    y = 28
    in_cooldown = (nu - laatste_actie) < cooldown
    actie_recent = (nu - actie_flash) < 1.0
    trigger_actief_lijst = []

    for i, trigger in enumerate(actieve_triggers):
        kleur = TRIGGER_KLEUREN[i % len(TRIGGER_KLEUREN)]
        toets = " + ".join(trigger["toetsen"]).upper()

        # Check welke blendshapes matchen
        bs_matches = {}
        alle_match = True
        for bs_naam, drempel in trigger["blendshapes"].items():
            huidige_score = scores.get(bs_naam, 0)
            bs_matches[bs_naam] = (huidige_score, drempel, huidige_score > drempel)
            if huidige_score <= drempel:
                alle_match = False

        state = trigger_states[i]
        trigger_actief_lijst.append(alle_match)

        # Trigger-naam en status (grotere tekst)
        if actie_recent and actie_idx == i:
            label = f"[{i+1}] {trigger['naam']}  [{toets}]"
            cv2.putText(frame, label,
                        (10, y), font, 0.6, (0, 255, 255), 2)
            cv2.putText(frame, ">>> ACTIE UITGEVOERD! <<<",
                        (w - 310, y), font, 0.55, (0, 255, 255), 2)
        elif in_cooldown:
            rest = cooldown - (nu - laatste_actie)
            label = f"[{i+1}] {trigger['naam']}  [{toets}]"
            cv2.putText(frame, label,
                        (10, y), font, 0.55, (100, 100, 100), 1)
            cv2.putText(frame, f"cooldown {rest:.1f}s",
                        (w - 180, y), font, 0.5, (100, 100, 100), 1)
        elif alle_match and state["start"] is not None:
            duur = nu - state["start"]
            label = f"[{i+1}] {trigger['naam']}  [{toets}]"
            cv2.putText(frame, label,
                        (10, y), font, 0.6, kleur, 2)
            # Voortgangsbalk voor vasthoudtijd
            bar_x = w - 200
            bar_w = 150
            vr = min(duur / vasthoud_tijd, 1.0)
            cv2.rectangle(frame, (bar_x, y - 12), (bar_x + bar_w, y + 4),
                          (40, 40, 40), -1)
            cv2.rectangle(frame, (bar_x, y - 12),
                          (bar_x + int(bar_w * vr), y + 4),
                          kleur, -1)
            cv2.putText(frame, f"{duur:.1f}s / {vasthoud_tijd:.1f}s",
                        (bar_x + bar_w + 5, y), font, 0.4, kleur, 1)
        elif alle_match:
            label = f"[{i+1}] {trigger['naam']}  [{toets}]  MATCH!"
            cv2.putText(frame, label,
                        (10, y), font, 0.6, kleur, 2)
        else:
            label = f"[{i+1}] {trigger['naam']}  [{toets}]"
            cv2.putText(frame, label,
                        (10, y), font, 0.55, (120, 120, 120), 1)

        y += 24

        # Per blendshape: naam, score, drempel, kleurcodering
        for bs_naam, (score, drempel, match) in bs_matches.items():
            bs_label = nl_label(bs_naam)
            if len(bs_label) > 20:
                bs_label = bs_label[:18] + ".."

            if match:
                bs_kleur = (0, 220, 0)     # groen = boven drempel
                status_tekst = "OK"
            else:
                bs_kleur = (0, 0, 220)     # rood = onder drempel
                status_tekst = "--"

            tekst = f"  {bs_label}: {score:.2f} / {drempel:.2f}  [{status_tekst}]"
            cv2.putText(frame, tekst, (20, y), font, 0.4, bs_kleur, 1)

            # Mini-bar voor score vs drempel
            bar_x = w - 200
            bar_w = 120
            cv2.rectangle(frame, (bar_x, y - 8), (bar_x + bar_w, y + 2),
                          (30, 30, 30), -1)
            score_px = int(bar_w * min(score, 1.0))
            drempel_px = int(bar_w * min(drempel, 1.0))
            if score_px > 0:
                cv2.rectangle(frame, (bar_x, y - 8),
                              (bar_x + score_px, y + 2), bs_kleur, -1)
            # Drempel-marker (witte lijn)
            cv2.line(frame, (bar_x + drempel_px, y - 10),
                     (bar_x + drempel_px, y + 4), (255, 255, 255), 2)

            y += 18

        y += 6

    # Actie-flash rand
    if actie_recent:
        dikte = max(4, int(10 * (1 - (nu - actie_flash))))
        cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 255, 255), dikte)

    cv2.putText(frame, "Q=stoppen  |  Sliders: drempels live aanpassen",
                (10, h - 12), font, 0.4, (160, 160, 160), 1)

    return trigger_actief_lijst


# ---------------------------------------------------------------------------
# Hoofdfunctie live modus
# ---------------------------------------------------------------------------
def start_live_explorer(camera_index=0):
    """Start de live modus met blendshape-triggers en live slider-paneel."""
    config = laad_explorer_config()
    triggers = config["triggers"]
    cooldown = config["cooldown"]
    vasthoud_tijd = config["vasthoud_tijd"]
    toets_duur_ms = config.get("toets_duur_ms", 100)

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
    print(f"\n  Cooldown: {cooldown}s  |  Vasthoudtijd: {vasthoud_tijd}s")
    print("  [INFO] Slider-paneel wordt geopend voor live drempelaanpassingen.\n")

    # Start het CTk slider-paneel in de main thread (Tkinter vereist dit)
    paneel = DrempelPaneel(actieve)

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("  [!] Kan de webcam niet openen!")
        if paneel.is_open:
            paneel.venster.destroy()
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

        # Trigger detectie (met live drempels uit het paneel)
        in_cooldown = (nu - laatste_actie) < cooldown
        gevuurd = False

        for i, trigger in enumerate(actieve):
            if not gezicht_ok:
                trigger_states[i]["start"] = None
                continue

            # Haal drempels op uit het paneel (real-time bijgewerkt via sliders)
            match = True
            for bs_naam in trigger["blendshapes"]:
                drempel = paneel.haal_drempel(i, bs_naam) if paneel.is_open else trigger["blendshapes"][bs_naam]
                if scores.get(bs_naam, 0) <= drempel:
                    match = False
                    break

            if match and not in_cooldown and not gevuurd:
                if trigger_states[i]["start"] is None:
                    trigger_states[i]["start"] = nu

                if (nu - trigger_states[i]["start"]) >= vasthoud_tijd:
                    toetsen = trigger["toetsen"]
                    voer_toetsen_uit(toetsen, duur_ms=toets_duur_ms)

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

        actief_lijst = teken_live_overlay(
            frame, scores, actieve, trigger_states,
            nu, vasthoud_tijd, laatste_actie, cooldown,
            actie_flash, actie_idx, gezicht_ok
        )

        # Update status in het slider-paneel
        if paneel.is_open and actief_lijst:
            for i, is_actief in enumerate(actief_lijst):
                paneel.update_status(i, is_actief)

        # CTk event-loop bijhouden (nodig omdat we in dezelfde thread zitten)
        if paneel.is_open:
            try:
                paneel.venster.update()
            except Exception:
                pass

        cv2.imshow("MimiExplorer - Live (Q=stoppen)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()

    # Paneel netjes sluiten als het nog open is
    if paneel.is_open:
        paneel._sluit()

    print("\n  [OK] Live modus gestopt.\n")
