"""
MimiExplorer - Live Modus
Controleert alle geconfigureerde triggers gelijktijdig op basis
van blendshape-scores, met anti-spasme filter en cooldown.
Bevat een apart CustomTkinter paneel voor live drempelaanpassingen
en een info-paneel onder het webcambeeld.
"""

import cv2
import time
import threading
import numpy as np
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
# Mennens.Tech kleurenpalet — Hex voor CustomTkinter
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

# ---------------------------------------------------------------------------
# BGR kleuren voor het OpenCV info-paneel
# ---------------------------------------------------------------------------
BGR_DONKER      = (54, 45, 6)       # #062D36
BGR_TEAL        = (190, 184, 77)    # #4DB8BE
BGR_BRAND       = (209, 204, 104)   # #68CCD1
BGR_WIT         = (255, 255, 255)
BGR_GROEN       = (60, 200, 0)
BGR_ROOD        = (70, 70, 220)
BGR_GRIJS       = (140, 140, 140)
BGR_DONKERGRIJS = (60, 60, 60)
BGR_SCHEIDING   = (70, 60, 12)

TRIGGER_KLEUREN_BGR = [
    (190, 184, 77),
    (209, 204, 104),
    (180, 160, 60),
    (160, 200, 80),
    (220, 200, 90),
]


# ---------------------------------------------------------------------------
# CustomTkinter slider-paneel met filter-checkboxes
# ---------------------------------------------------------------------------
class DrempelPaneel:
    """
    Apart CTk-venster dat naast het webcam-venster verschijnt.
    Toont per trigger de blendshapes met sliders voor drempels
    en checkboxes om zichtbaarheid in het info-paneel te regelen.
    """

    def __init__(self, triggers):
        self._triggers = triggers
        self._gesloten = False
        self._slider_refs = {}
        self._waarde_refs = {}
        self._status_refs = {}
        self._filter_vars = {}    # {(trigger_idx, bs_naam): IntVar}
        self._trigger_actief_vars = {}  # {trigger_idx: IntVar} — actief/inactief
        self._actief_labels = {}        # {trigger_idx: CTkLabel}
        self._lock = threading.Lock()

        self.venster = ctk.CTkToplevel()
        self.venster.title("Drempel Aanpassingen — MimiControl")
        self.venster.configure(fg_color=BG)
        self.venster.geometry("480x700+50+50")
        self.venster.minsize(420, 400)
        self.venster.resizable(True, True)
        self.venster.protocol("WM_DELETE_WINDOW", self._sluit)

        try:
            self.venster.attributes("-topmost", True)
        except Exception:
            pass

        self._bouw_ui()

    def _bouw_ui(self):
        header = ctk.CTkFrame(self.venster, fg_color=DONKER, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="Live Drempels & Filter",
            font=(FONT, 16, "bold"), text_color=KAART
        ).pack(pady=14)

        ctk.CTkLabel(
            self.venster,
            text="Toggle = trigger actief/inactief   |   Slider = drempel",
            font=(FONT, 10), text_color=TEKST_LICHT
        ).pack(pady=(6, 2))

        scroll = ctk.CTkScrollableFrame(self.venster, fg_color=BG, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        for t_idx, trigger in enumerate(self._triggers):
            if not trigger.get("blendshapes"):
                continue

            accent = ["#4DB8BE", "#3D8FA5", "#68CCD1", "#2E7A8A", "#89D4D8"][
                t_idx % 5
            ]

            kaart = ctk.CTkFrame(scroll, fg_color=KAART, corner_radius=12,
                                 border_width=1, border_color=RAND)
            kaart.pack(fill="x", padx=12, pady=6)

            ctk.CTkFrame(kaart, fg_color=accent, height=3, corner_radius=0
                         ).pack(fill="x", padx=10, pady=(8, 0))

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

            # Actief/inactief toggle per trigger (sessie-only, niet opgeslagen)
            trigger_var = ctk.IntVar(value=1)
            self._trigger_actief_vars[t_idx] = trigger_var
            master_rij = ctk.CTkFrame(kaart, fg_color="transparent")
            master_rij.pack(fill="x", padx=14, pady=(4, 2))

            actief_lbl = ctk.CTkLabel(
                master_rij, text="ACTIEF", font=(FONT, 12, "bold"),
                text_color="#22AA44", width=90, anchor="w"
            )
            self._actief_labels[t_idx] = actief_lbl

            def _on_toggle(var=trigger_var, lbl=actief_lbl):
                if var.get() == 1:
                    lbl.configure(text="ACTIEF", text_color="#22AA44")
                else:
                    lbl.configure(text="INACTIEF", text_color="#999999")

            ctk.CTkSwitch(
                master_rij, text="",
                variable=trigger_var, onvalue=1, offvalue=0,
                progress_color=accent, button_color=KAART,
                button_hover_color=RAND, fg_color="#999999",
                switch_width=44, switch_height=22,
                command=_on_toggle
            ).pack(side="left")
            actief_lbl.pack(side="left", padx=(8, 0))

            for bs_naam, drempel in trigger["blendshapes"].items():
                rij = ctk.CTkFrame(kaart, fg_color="transparent")
                rij.pack(fill="x", padx=14, pady=2)

                filter_var = ctk.IntVar(value=1)
                self._filter_vars[(t_idx, bs_naam)] = filter_var
                ctk.CTkCheckBox(
                    rij, text="", width=24, height=24,
                    variable=filter_var,
                    fg_color=TEAL_BTN, hover_color=TEAL_HOVER,
                    checkbox_width=18, checkbox_height=18
                ).pack(side="left", padx=(0, 4))

                ctk.CTkLabel(
                    rij, text=nl_label(bs_naam),
                    font=(FONT, 11), text_color=TEKST_LICHT,
                    width=130, anchor="w"
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

            ctk.CTkFrame(kaart, fg_color="transparent", height=6).pack()

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

    def is_zichtbaar(self, trigger_idx, bs_naam):
        """Check of een blendshape zichtbaar moet zijn in het info-paneel."""
        if self._gesloten:
            return True
        var = self._filter_vars.get((trigger_idx, bs_naam))
        if var is None:
            return True
        try:
            return var.get() == 1
        except Exception:
            return True

    def is_trigger_actief(self, trigger_idx):
        """Check of een trigger actief is (voert acties uit en toont normaal)."""
        if self._gesloten:
            return True
        var = self._trigger_actief_vars.get(trigger_idx)
        if var is None:
            return True
        try:
            return var.get() == 1
        except Exception:
            return True

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
# Robuuste webcam-opening met retry en DirectShow fallback
# ---------------------------------------------------------------------------
def _open_webcam_robuust(camera_index, max_pogingen=3, wachttijd=1.5):
    """
    Probeer de webcam te openen met retry-logica.
    Retourneert (cap, foutmelding) — cap is None bij falen.
    """
    for poging in range(1, max_pogingen + 1):
        try:
            print(f"  [INFO] Webcam openen (poging {poging}/{max_pogingen})...")
            if poging > 1:
                cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(camera_index)
        except Exception as e:
            print(f"  [!] Fout bij openen webcam: {e}")
            if poging < max_pogingen:
                time.sleep(wachttijd)
            continue

        if not cap.isOpened():
            print(f"  [!] Webcam niet beschikbaar (poging {poging})")
            try:
                cap.release()
            except Exception:
                pass
            if poging < max_pogingen:
                time.sleep(wachttijd)
            continue

        frame_ok = False
        for leespoging in range(5):
            try:
                ret, frame = cap.read()
                if ret and frame is not None:
                    frame_ok = True
                    break
            except Exception:
                pass
            time.sleep(0.3)

        if frame_ok:
            print(f"  [OK] Webcam geopend op poging {poging}")
            return cap, None

        print(f"  [!] Kan geen frame lezen van webcam (poging {poging})")
        try:
            cap.release()
        except Exception:
            pass
        if poging < max_pogingen:
            time.sleep(wachttijd)

    fout = (
        f"Kan webcam {camera_index} niet openen na {max_pogingen} pogingen.\n\n"
        "Mogelijke oorzaken:\n"
        "- Webcam is in gebruik door een ander programma\n"
        "- Webcam is niet aangesloten\n"
        "- Webcam wordt niet ondersteund\n\n"
        "Probeer een andere camera-index in de instellingen."
    )
    return None, fout


# ---------------------------------------------------------------------------
# Info-paneel onder het webcambeeld (donkere Mennens.Tech stijl)
# Alle triggers worden altijd volledig uitgeklapt getoond.
# Uitgeschakelde triggers verschijnen gedempt.
# Ondersteunt scrolling via pijltjestoetsen.
# ---------------------------------------------------------------------------
def _maak_info_paneel(breedte, trigger_data, trigger_states,
                      nu, vasthoud_tijd, laatste_actie, cooldown,
                      actie_flash, actie_idx, gezicht_ok, paneel=None,
                      scroll_offset=0, max_hoogte=500, gepauzeerd=False):
    """
    Bouw een donker info-paneel als numpy-array.
    Alle triggers altijd volledig uitgeklapt.
    Uitgeschakelde triggers worden gedempt weergegeven.
    Retourneert (panel_array, inhoud_hoogte).
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    MAX_CANVAS = 2000

    info = np.full((MAX_CANVAS, breedte, 3), BGR_DONKER, dtype=np.uint8)
    cv2.rectangle(info, (0, 0), (breedte, 3), BGR_TEAL, -1)

    y = 30

    if not gezicht_ok and not gepauzeerd:
        cv2.putText(info, "GEEN GEZICHT GEDETECTEERD",
                    (15, y), font, 0.65, BGR_ROOD, 2)
        panel = info[:max(y + 25, 60), :, :]
        return panel, panel.shape[0]

    if gepauzeerd:
        cv2.putText(info, "GEPAUZEERD - druk P om te hervatten",
                    (15, y), font, 0.55, BGR_TEAL, 2)
        y += 30

    in_cooldown = (nu - laatste_actie) < cooldown
    actie_recent = (nu - actie_flash) < 1.0

    # Alle triggers tonen (altijd uitgeklapt, geen compact modus)
    zichtbaar_idxs = list(range(len(trigger_data)))

    for i in zichtbaar_idxs:
        td = trigger_data[i]
        trigger = td["trigger"]
        bs_matches = td["bs_matches"]
        alle_match = td["alle_match"]
        state = trigger_states[i]

        trigger_actief = True
        if paneel and hasattr(paneel, 'is_trigger_actief'):
            trigger_actief = paneel.is_trigger_actief(i)

        kleur = TRIGGER_KLEUREN_BGR[i % len(TRIGGER_KLEUREN_BGR)]
        if not trigger_actief:
            kleur = BGR_DONKERGRIJS
        toets = " + ".join(trigger["toetsen"]).upper()

        # Status bepalen
        if not trigger_actief:
            status_tekst = "UITGESCHAKELD"
            status_kleur = BGR_DONKERGRIJS
            naam_kleur = BGR_GRIJS
            dikte = 1
        elif actie_recent and actie_idx == i:
            status_tekst = "ACTIE UITGEVOERD!"
            status_kleur = (0, 255, 255)
            naam_kleur = (0, 255, 255)
            dikte = 2
        elif in_cooldown:
            rest = cooldown - (nu - laatste_actie)
            status_tekst = f"cooldown {rest:.1f}s"
            status_kleur = BGR_GRIJS
            naam_kleur = BGR_GRIJS
            dikte = 1
        elif alle_match and state["start"] is not None:
            duur = nu - state["start"]
            status_tekst = f"ACTIEF  {duur:.1f}s / {vasthoud_tijd:.1f}s"
            status_kleur = BGR_GROEN
            naam_kleur = BGR_WIT
            dikte = 2
        elif alle_match:
            status_tekst = "ACTIEF"
            status_kleur = BGR_GROEN
            naam_kleur = BGR_WIT
            dikte = 2
        else:
            status_tekst = "inactief"
            status_kleur = BGR_DONKERGRIJS
            naam_kleur = (200, 200, 200)
            dikte = 1

        # Accentlijn links van de trigger
        cv2.rectangle(info, (8, y - 16), (12, y + 4), kleur, -1)

        # Trigger naam + toets
        cv2.putText(info, trigger["naam"], (18, y), font, 0.6, naam_kleur, 2)
        naam_breedte = cv2.getTextSize(trigger["naam"], font, 0.6, 2)[0][0]
        toets_kleur = BGR_TEAL if trigger_actief else BGR_DONKERGRIJS
        cv2.putText(info, f"[{toets}]", (22 + naam_breedte, y),
                    font, 0.45, toets_kleur, 1)

        # Status rechts uitgelijnd
        status_breedte = cv2.getTextSize(status_tekst, font, 0.5, 1)[0][0]
        cv2.putText(info, status_tekst,
                    (breedte - status_breedte - 15, y),
                    font, 0.5, status_kleur, dikte)

        # Voortgangsbalk bij vasthouden (alleen actieve triggers)
        if trigger_actief and alle_match and state["start"] is not None and not in_cooldown:
            duur = nu - state["start"]
            vr = min(duur / vasthoud_tijd, 1.0)
            bar_y = y + 5
            bar_x = breedte - 240
            bar_w = 220
            cv2.rectangle(info, (bar_x, bar_y), (bar_x + bar_w, bar_y + 7),
                          BGR_DONKERGRIJS, -1)
            cv2.rectangle(info, (bar_x, bar_y),
                          (bar_x + int(bar_w * vr), bar_y + 7),
                          BGR_GROEN, -1)
            y += 14

        y += 28

        # Blendshapes per trigger (altijd getoond)
        for bs_naam, (score, drempel, match) in bs_matches.items():
            if paneel and not paneel.is_zichtbaar(i, bs_naam):
                continue

            bs_label = nl_label(bs_naam)
            if len(bs_label) > 24:
                bs_label = bs_label[:22] + ".."

            if not trigger_actief:
                tekst_kleur = BGR_GRIJS
            else:
                tekst_kleur = BGR_WIT if match else (170, 170, 170)
            cv2.putText(info, bs_label, (30, y), font, 0.48, tekst_kleur, 1)

            waarde_tekst = f"{score:.2f} / {drempel:.2f}"
            if not trigger_actief:
                waarde_kleur = BGR_GRIJS
            else:
                waarde_kleur = BGR_GROEN if match else BGR_ROOD
            cv2.putText(info, waarde_tekst, (220, y), font, 0.42,
                        waarde_kleur, 1)

            # Score-balk
            bar_x = breedte - 240
            bar_w = 220
            bar_h = 15
            bar_y_top = y - 12

            cv2.rectangle(info, (bar_x, bar_y_top),
                          (bar_x + bar_w, bar_y_top + bar_h),
                          (30, 30, 30), -1)

            score_px = int(bar_w * min(score, 1.0))
            if not trigger_actief:
                bar_kleur = BGR_DONKERGRIJS
            else:
                bar_kleur = BGR_GROEN if match else BGR_ROOD
            if score_px > 0:
                cv2.rectangle(info, (bar_x, bar_y_top),
                              (bar_x + score_px, bar_y_top + bar_h),
                              bar_kleur, -1)

            drempel_px = int(bar_w * min(drempel, 1.0))
            lijn_kleur = BGR_WIT if trigger_actief else BGR_GRIJS
            cv2.line(info, (bar_x + drempel_px, bar_y_top - 2),
                     (bar_x + drempel_px, bar_y_top + bar_h + 2),
                     lijn_kleur, 2)

            y += 26

        # Scheiding tussen triggers
        y += 4
        cv2.line(info, (15, y), (breedte - 15, y), BGR_SCHEIDING, 1)
        y += 10

    # Footer
    footer = "Q=stop  P=pauze  Pijltjes=scroll  |  Sliders: drempels"
    cv2.putText(info, footer, (15, y + 4), font, 0.38, BGR_GRIJS, 1)
    y += 22

    inhoud_hoogte = max(y, 60)
    info = info[:inhoud_hoogte, :, :]

    # Scroll en max hoogte toepassen
    if inhoud_hoogte > max_hoogte:
        max_offset = inhoud_hoogte - max_hoogte
        offset = max(0, min(scroll_offset, max_offset))
        zichtbaar = info[offset:offset + max_hoogte, :, :].copy()

        # Scroll-indicatoren
        if offset > 0:
            cv2.rectangle(zichtbaar, (0, 0), (breedte, 20), BGR_DONKER, -1)
            cv2.rectangle(zichtbaar, (0, 0), (breedte, 3), BGR_TEAL, -1)
            cv2.putText(zichtbaar, "^^ scroll omhoog ^^",
                        (breedte // 2 - 70, 16), font, 0.4, BGR_TEAL, 1)
        if offset < max_offset:
            h = zichtbaar.shape[0]
            cv2.rectangle(zichtbaar, (0, h - 20), (breedte, h), BGR_DONKER, -1)
            cv2.putText(zichtbaar, "vv scroll omlaag vv",
                        (breedte // 2 - 70, h - 6), font, 0.4, BGR_TEAL, 1)

        return zichtbaar, inhoud_hoogte

    return info, inhoud_hoogte


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
    print("  LIVE MODUS - MimiControl Studio")
    print("=" * 50)
    for i, t in enumerate(actieve):
        toets = " + ".join(t["toetsen"]).upper()
        bs_lijst = ", ".join(t["blendshapes"].keys())
        print(f"  [{i+1}] {t['naam']:16s} -> {toets:10s}  ({bs_lijst})")
    print(f"\n  Cooldown: {cooldown}s  |  Vasthoudtijd: {vasthoud_tijd}s")
    print("  [INFO] Slider-paneel wordt geopend voor live drempelaanpassingen.\n")

    paneel = DrempelPaneel(actieve)

    # Robuust webcam openen met retry
    cap, fout = _open_webcam_robuust(camera_index)
    if cap is None:
        print(f"  [!] {fout}")
        try:
            from tkinter import messagebox as mb
            mb.showerror("Webcam Fout — MimiControl Studio", fout)
        except Exception:
            pass
        if paneel.is_open:
            paneel._sluit()
        return

    landmarker = maak_blendshape_landmarker(modus="video")

    trigger_states = [{"start": None} for _ in actieve]
    laatste_actie = 0.0
    actie_flash = 0.0
    actie_idx = -1
    ts = 0

    # Pauze- en scroll-state
    gepauzeerd = False
    pauze_frame = None
    scroll_offset = 0
    scores = {}
    landmarks = None

    print("  [INFO] Live besturing gestart.")
    print("  Q = stoppen  |  P = pauze/hervat  |  Pijltjes = scroll\n")

    while True:
        # Webcam frame lezen (of bevroren frame gebruiken bij pauze)
        if not gepauzeerd or pauze_frame is None:
            try:
                ret, frame = cap.read()
            except Exception as e:
                print(f"  [!] Fout bij lezen webcam frame: {e}")
                break
            if not ret or frame is None:
                break

            frame = cv2.flip(frame, 1)
            pauze_frame = frame.copy()
            cam_h, cam_w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ts += 33
            landmarks, scores = detecteer_blendshapes(landmarker, rgb, ts)
        else:
            frame = pauze_frame.copy()
            cam_h, cam_w = frame.shape[:2]

        nu = time.time()
        gezicht_ok = landmarks is not None

        if landmarks:
            teken_face_mesh_simpel(frame, landmarks)

        # Subtiele statusrand: groen bij gezicht, rood als geen gezicht
        if gezicht_ok:
            cv2.rectangle(frame, (0, 0), (cam_w - 1, cam_h - 1),
                          (0, 120, 0), 2)
        else:
            cv2.rectangle(frame, (0, 0), (cam_w - 1, cam_h - 1),
                          (0, 0, 160), 2)
            cv2.putText(frame, "Geen gezicht", (10, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 220), 2)

        # Pauze-indicator over het webcambeeld
        if gepauzeerd:
            cv2.rectangle(frame, (0, 0), (cam_w - 1, cam_h - 1), BGR_TEAL, 4)
            pauze_tekst = "GEPAUZEERD"
            pt_grootte = cv2.getTextSize(
                pauze_tekst, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 3)[0]
            pt_x = (cam_w - pt_grootte[0]) // 2
            pt_y = 45
            cv2.rectangle(frame,
                          (pt_x - 12, pt_y - pt_grootte[1] - 10),
                          (pt_x + pt_grootte[0] + 12, pt_y + 10),
                          BGR_DONKER, -1)
            cv2.putText(frame, pauze_tekst, (pt_x, pt_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, BGR_TEAL, 3)

        # ---- Trigger detectie ----
        in_cooldown = (nu - laatste_actie) < cooldown
        gevuurd = False
        trigger_data = []

        for i, trigger in enumerate(actieve):
            if gepauzeerd or not gezicht_ok:
                # Geen detectie bij pauze of geen gezicht
                trigger_states[i]["start"] = None
                bs_matches = {}
                for bs_naam, drempel in trigger["blendshapes"].items():
                    huidige_score = scores.get(bs_naam, 0) if gepauzeerd else 0.0
                    drempel_val = (
                        paneel.haal_drempel(i, bs_naam)
                        if paneel.is_open
                        else drempel
                    )
                    bs_matches[bs_naam] = (huidige_score, drempel_val, False)
                trigger_data.append({
                    "trigger": trigger,
                    "bs_matches": bs_matches,
                    "alle_match": False,
                })
                continue

            bs_matches = {}
            alle_match = True
            for bs_naam in trigger["blendshapes"]:
                drempel = (paneel.haal_drempel(i, bs_naam)
                           if paneel.is_open
                           else trigger["blendshapes"][bs_naam])
                huidige_score = scores.get(bs_naam, 0)
                match = huidige_score > drempel
                bs_matches[bs_naam] = (huidige_score, drempel, match)
                if not match:
                    alle_match = False

            trigger_data.append({
                "trigger": trigger,
                "bs_matches": bs_matches,
                "alle_match": alle_match,
            })

            trigger_actief = not paneel.is_open or paneel.is_trigger_actief(i)

            if alle_match and not in_cooldown and not gevuurd and trigger_actief:
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

        # Actie-flash rand op webcambeeld (niet bij pauze)
        actie_recent = (nu - actie_flash) < 1.0
        if actie_recent and not gepauzeerd:
            dikte = max(3, int(8 * (1 - (nu - actie_flash))))
            cv2.rectangle(frame, (0, 0), (cam_w - 1, cam_h - 1),
                          (0, 255, 255), dikte)

        # Info-paneel genereren (met scroll en compact-modus)
        info, inhoud_hoogte = _maak_info_paneel(
            cam_w, trigger_data, trigger_states,
            nu, vasthoud_tijd, laatste_actie, cooldown,
            actie_flash, actie_idx, gezicht_ok,
            paneel=paneel, scroll_offset=scroll_offset,
            max_hoogte=500, gepauzeerd=gepauzeerd
        )

        # Scroll offset begrenzen
        if inhoud_hoogte > 500:
            scroll_offset = min(scroll_offset, inhoud_hoogte - 500)
        else:
            scroll_offset = 0

        # Combineer webcam + info-paneel verticaal
        canvas = np.vstack([frame, info])

        # DrempelPaneel status bijwerken
        if paneel.is_open:
            for i, td in enumerate(trigger_data):
                paneel.update_status(i, td["alle_match"])

        # CTk event-loop bijhouden (Tkinter vereist dit in de main thread)
        if paneel.is_open:
            try:
                paneel.venster.update()
            except Exception:
                pass

        cv2.imshow("MimiControl Studio - Live (Q=stop, P=pauze)", canvas)

        # Toetsafhandeling via waitKeyEx voor pijltjestoetsen
        key = cv2.waitKeyEx(1)
        if key == ord('q') or key == ord('Q'):
            break
        elif key == ord('p') or key == ord('P'):
            gepauzeerd = not gepauzeerd
            if gepauzeerd:
                print("  [INFO] Beeld gepauzeerd. Druk P om te hervatten.")
            else:
                print("  [INFO] Beeld hervat.")
                scroll_offset = 0
        elif key in (2490368, 65362):       # Pijl omhoog
            scroll_offset = max(0, scroll_offset - 40)
        elif key in (2621440, 65364):       # Pijl omlaag
            scroll_offset += 40
        elif key in (2162688, 65365):       # Page Up
            scroll_offset = max(0, scroll_offset - 150)
        elif key in (2228224, 65366):       # Page Down
            scroll_offset += 150

    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()

    if paneel.is_open:
        paneel._sluit()

    print("\n  [OK] Live modus gestopt.\n")
