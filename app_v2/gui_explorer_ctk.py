"""
MimiControl Studio v2 - CustomTkinter GUI (Mennens.Tech branding)
Gemaximaliseerd HD-hoofdscherm: triggergrid 2–3 kolommen, rechterrail
voor camera/profiel/acties/timing. Geen nested mini-scrollvak.
"""

import sys
import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image

import customtkinter as ctk

from config_explorer import (
    laad_explorer_config, sla_explorer_config_op, verwijder_trigger,
    lijst_profielen, actief_profiel, wissel_profiel,
    sla_profiel_op, verwijder_profiel,
    normaliseer_overlay_grootte, overlay_grootte_label,
    overlay_hoek_label, overlay_hoek_van_label, OVERLAY_HOEK_MENU,
)
from paths import resource_path, log_startup_timing
from blendshape_labels import nl_label, TRIGGER_KLEUREN_HEX, TRIGGER_KLEUR_NAMEN

# ---------------------------------------------------------------------------
# Appearance
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ---------------------------------------------------------------------------
# Mennens.Tech kleurenpalet
# ---------------------------------------------------------------------------
BG          = "#F2F2F7"
KAART       = "#FFFFFF"
TEKST       = "#1C1C1E"
TEKST_LICHT = "#5A5A5E"
DONKER      = "#062D36"
DONKER_HOVER = "#0A4050"
TEAL_BRAND  = "#68CCD1"
TEAL_BTN    = "#4DB8BE"
TEAL_HOVER  = "#3A9DA3"
ROOD        = "#E05A50"
ROOD_HOVER  = "#C44840"
RAND        = "#E5E5EA"

FONT = "Segoe UI" if sys.platform == "win32" else "Helvetica"

LOGO_PAD = resource_path("assets", "logo_mennens.png")
ICON_PAD = resource_path("assets", "mimicontrol.ico")

TRIGGER_ACCENTEN = TRIGGER_KLEUREN_HEX
RAIL_BREEDTE = 360


# ---------------------------------------------------------------------------
# Camera-detectie
# ---------------------------------------------------------------------------
def _haal_wmi_camera_namen():
    """Haal camera-namen op via PowerShell/WMI (alleen Windows)."""
    if sys.platform != "win32":
        return []
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             'Get-CimInstance Win32_PnPEntity | '
             'Where-Object {$_.PNPClass -eq "Camera" -or $_.PNPClass -eq "Image"} | '
             'Select-Object -ExpandProperty Name'],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode == 0 and result.stdout.strip():
            return [n.strip() for n in result.stdout.strip().split("\n") if n.strip()]
    except Exception:
        pass
    return []


def detecteer_cameras(max_cameras=5):
    """Detecteer beschikbare camera's via OpenCV, verrijkt met WMI-namen."""
    import cv2

    try:
        wmi_namen = _haal_wmi_camera_namen()

        cameras = []
        wmi_idx = 0
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cap.release()
                if wmi_idx < len(wmi_namen):
                    label = f"{wmi_namen[wmi_idx]} (Camera {i})"
                    wmi_idx += 1
                else:
                    label = f"Camera {i}"
                cameras.append((i, label))
        return cameras
    except Exception:
        return []


def _maximaliseer(venster):
    """Start schermvullend (gemaximaliseerd), met fallback op een HD-formaat."""
    try:
        venster.state("zoomed")
        return
    except Exception:
        pass
    try:
        venster.attributes("-zoomed", True)
        return
    except Exception:
        pass
    sw = venster.winfo_screenwidth()
    sh = venster.winfo_screenheight()
    venster.geometry(f"{max(1280, sw - 40)}x{max(720, sh - 80)}+0+0")


# ---------------------------------------------------------------------------
# Hoofdvenster
# ---------------------------------------------------------------------------
class MimiControlStudioApp:

    def __init__(self, startup_t0=None):
        self._startup_t0 = startup_t0
        self._loading_val = 0.0
        self._loading_overlay = None
        self._loading_progress = None
        self._trigger_kaarten = []
        self._laatste_kolommen = 0
        self._resize_after = None
        self._save_after = None
        self._config_cache = None
        self._switches_laden = False

        self.app = ctk.CTk()
        self.app.title("MimiControl Studio v2")
        self.app.configure(fg_color=BG)
        if os.path.exists(ICON_PAD):
            try:
                self.app.iconbitmap(ICON_PAD)
            except Exception:
                pass
        self.app.resizable(True, True)
        self.app.minsize(1024, 640)

        sw = self.app.winfo_screenwidth()
        sh = self.app.winfo_screenheight()
        self.app.geometry(f"{min(1920, sw)}x{min(1080, sh)}+0+0")
        self.app.after(40, lambda: _maximaliseer(self.app))

        self._cameras = []
        self._loading_overlay = self._maak_laad_overlay()
        self.app.update_idletasks()
        self.app.update()

        if self._startup_t0 is not None:
            log_startup_timing("splash_visible", self._startup_t0)

        threading.Thread(target=self._achtergrond_init, daemon=True).start()

    def _maak_laad_overlay(self):
        """Toon direct een laadscherm terwijl zware modules op de achtergrond laden."""
        overlay = ctk.CTkFrame(self.app, fg_color=BG, corner_radius=0)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        center = ctk.CTkFrame(overlay, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            center,
            text="MimiControl Studio v2",
            font=(FONT, 22, "bold"),
            text_color=DONKER,
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            center,
            text="Mimiek omzetten naar toetsen  ·  Mennens.Tech",
            font=(FONT, 13),
            text_color=TEAL_HOVER,
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            center,
            text="Wordt geladen…",
            font=(FONT, 14),
            text_color=TEKST_LICHT,
        ).pack(pady=(0, 16))

        self._loading_progress = ctk.CTkProgressBar(
            center, width=280, height=8,
            progress_color=TEAL_BTN,
            fg_color=RAND,
        )
        self._loading_progress.pack()
        self._loading_progress.set(0)
        self._animeer_laad_balk()

        return overlay

    def _animeer_laad_balk(self):
        if self._loading_overlay is None or not self._loading_overlay.winfo_exists():
            return
        self._loading_val = (self._loading_val + 0.04) % 1.0
        if self._loading_progress is not None:
            self._loading_progress.set(self._loading_val)
        self.app.after(80, self._animeer_laad_balk)

    def _achtergrond_init(self):
        """Laad OpenCV en detecteer camera's buiten de GUI-thread."""
        t0 = time.perf_counter()
        import cv2  # noqa: F401 — warm-up voor latere preview/explorer

        if self._startup_t0 is not None:
            log_startup_timing("cv2_imported", self._startup_t0)

        cameras = detecteer_cameras()

        if self._startup_t0 is not None:
            log_startup_timing(
                f"cameras_detected ({len(cameras)}, thread {time.perf_counter() - t0:.2f}s)",
                self._startup_t0,
            )

        self.app.after(0, lambda: self._rond_init_af(cameras))

    def _rond_init_af(self, cameras):
        self._cameras = cameras
        if self._loading_overlay is not None and self._loading_overlay.winfo_exists():
            self._loading_overlay.destroy()
        self._loading_overlay = None
        self._loading_progress = None
        self._bouw_interface()
        self._ververs_triggers()
        _maximaliseer(self.app)

        if self._startup_t0 is not None:
            log_startup_timing("gui_ready", self._startup_t0)

    # ---- Layout ----

    def _bouw_interface(self):
        self._bouw_header()

        body = ctk.CTkFrame(self.app, fg_color=BG, corner_radius=0)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, minsize=RAIL_BREEDTE, weight=0)
        body.grid_rowconfigure(0, weight=1)

        links = ctk.CTkFrame(body, fg_color="transparent")
        links.grid(row=0, column=0, sticky="nsew", padx=(20, 8), pady=(10, 16))
        links.grid_rowconfigure(1, weight=1)
        links.grid_columnconfigure(0, weight=1)

        trigger_header = ctk.CTkFrame(links, fg_color="transparent")
        trigger_header.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        ctk.CTkLabel(trigger_header, text="\u2022",
                     font=(FONT, 22, "bold"), text_color=TEAL_BTN
                     ).pack(side="left", padx=(4, 6))
        ctk.CTkLabel(trigger_header, text="Geconfigureerde triggers",
                     font=(FONT, 17, "bold"), text_color=TEKST
                     ).pack(side="left")

        # Groot inhoudsvak (geen mini-reststrook). Bij veel kaarten scrollt
        # alleen dit vak; de rechterrail blijft staan.
        self.trigger_scroll = ctk.CTkScrollableFrame(
            links, fg_color="transparent", corner_radius=0
        )
        self.trigger_scroll.grid(row=1, column=0, sticky="nsew")

        self.trigger_grid = ctk.CTkFrame(self.trigger_scroll, fg_color="transparent")
        self.trigger_grid.pack(fill="both", expand=True)

        self.rail = ctk.CTkScrollableFrame(
            body, fg_color="transparent", width=RAIL_BREEDTE
        )
        self.rail.grid(row=0, column=1, sticky="nsew", padx=(8, 20), pady=(10, 16))

        self._bouw_status(self.rail)
        self._bouw_camera_selectie(self.rail)
        self._bouw_profiel_selector(self.rail)
        self._bouw_actieknoppen(self.rail)
        self._bouw_live_weergave(self.rail)
        self._bouw_timing(self.rail)

        self.app.bind("<Configure>", self._on_venster_resize)

    def _bouw_header(self):
        header = ctk.CTkFrame(self.app, fg_color=DONKER, corner_radius=0, height=76)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=24)

        self.logo_img = None
        if os.path.exists(LOGO_PAD):
            try:
                pil_img = Image.open(LOGO_PAD).convert("RGBA")
                try:
                    import numpy as np
                    arr = np.array(pil_img)
                    rgb_som = arr[:, :, 0].astype("int16") + arr[:, :, 1] + arr[:, :, 2]
                    masker = (arr[:, :, 3] > 30) & (rgb_som < 400)
                    arr[masker, 0] = 255
                    arr[masker, 1] = 255
                    arr[masker, 2] = 255
                    pil_img = Image.fromarray(arr)
                except Exception:
                    pass
                self.logo_img = ctk.CTkImage(light_image=pil_img, size=(86, 56))
                ctk.CTkLabel(header_inner, image=self.logo_img, text=""
                             ).pack(side="left", padx=(0, 14), pady=8)
            except Exception:
                pass

        tekst_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        tekst_frame.pack(side="left")
        ctk.CTkLabel(tekst_frame, text="MimiControl Studio v2",
                     font=(FONT, 22, "bold"), text_color=KAART
                     ).pack(anchor="w", pady=(10, 0))
        ctk.CTkLabel(
            tekst_frame,
            text="Mimiek omzetten naar toetsen  ·  Mennens.Tech",
            font=(FONT, 12), text_color=TEAL_BRAND
        ).pack(anchor="w", pady=(0, 8))

    def _bouw_status(self, parent):
        """Laat direct zien of Studio klaar is voor Communicator 5."""
        try:
            from toets_actie import studio_draait_als_admin
            admin = studio_draait_als_admin()
        except Exception:
            admin = False

        kaart = ctk.CTkFrame(parent, fg_color=KAART, corner_radius=12,
                             border_width=1, border_color=RAND)
        kaart.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(kaart, text="Communicator 5",
                     font=(FONT, 13, "bold"), text_color=TEKST
                     ).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(
            kaart,
            text="✓  Beheerder: ja" if admin else "✗  Beheerder: nee",
            font=(FONT, 12, "bold"),
            text_color="#2E9E5B" if admin else "#C2410C",
        ).pack(anchor="w", padx=16)
        uitleg = (
            "Toetsen kunnen in Communicator 5 aankomen. Zet Communicator 5 "
            "op Vensterweergave. Je toetsen gaan altijd naar het actieve "
            "venster: klik dus op Communicator 5 voordat je begint."
            if admin else
            "Zonder beheerdersrechten blokkeert Windows de toetsen naar "
            "Communicator 5. Sluit Studio en start hem opnieuw als beheerder."
        )
        ctk.CTkLabel(kaart, text=uitleg, font=(FONT, 11),
                     text_color=TEKST_LICHT, wraplength=300,
                     anchor="w", justify="left"
                     ).pack(fill="x", padx=16, pady=(2, 12))

    def _bouw_actieknoppen(self, parent):
        knoppen = ctk.CTkFrame(parent, fg_color=KAART, corner_radius=12,
                               border_width=1, border_color=RAND)
        knoppen.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(knoppen, text="Acties",
                     font=(FONT, 13, "bold"), text_color=TEKST
                     ).pack(anchor="w", padx=16, pady=(12, 6))

        ctk.CTkButton(
            knoppen, text="Mimiek verkennen",
            font=(FONT, 13, "bold"), height=40,
            fg_color=TEAL_BTN, hover_color=TEAL_HOVER,
            corner_radius=12, cursor="hand2",
            command=self._lanceer_explorer
        ).pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(knoppen,
                     text="Neem een gezichtsbeweging op en maak er een trigger van",
                     font=(FONT, 11), text_color=TEKST_LICHT, wraplength=300,
                     anchor="w", justify="left"
                     ).pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkButton(
            knoppen, text="Live modus starten",
            font=(FONT, 13, "bold"), height=40,
            fg_color=DONKER, hover_color=DONKER_HOVER,
            corner_radius=12, cursor="hand2",
            command=self._lanceer_live
        ).pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(knoppen,
                     text="Je mimiek stuurt toetsen naar het actieve venster (waar je "
                          "het laatst op klikte). Stoppen: de X rechtsboven in het "
                          "camerabeeld (twee keer klikken), 'Stop live' of Q.",
                     font=(FONT, 11), text_color=TEKST_LICHT, wraplength=300,
                     anchor="w", justify="left"
                     ).pack(fill="x", padx=16, pady=(0, 14))

    def _bouw_camera_selectie(self, parent):
        """Camera-selectie dropdown met preview in de rechterrail."""
        self.cam_frame = ctk.CTkFrame(parent, fg_color=KAART,
                                       corner_radius=12, border_width=1,
                                       border_color=RAND)
        self.cam_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.cam_frame, text="Camera",
                     font=(FONT, 13, "bold"), text_color=TEKST
                     ).pack(anchor="w", padx=16, pady=(12, 6))

        rij = ctk.CTkFrame(self.cam_frame, fg_color="transparent")
        rij.pack(fill="x", padx=16, pady=(0, 8))

        config = laad_explorer_config()
        huidige_index = config.get("camera_index", 0)

        if self._cameras:
            cam_namen = [naam for _, naam in self._cameras]
            huidige_naam = next(
                (naam for idx, naam in self._cameras if idx == huidige_index),
                cam_namen[0],
            )
        else:
            cam_namen = ["Geen camera gevonden"]
            huidige_naam = cam_namen[0]

        self.camera_dropdown = ctk.CTkOptionMenu(
            rij, values=cam_namen,
            font=(FONT, 12), dropdown_font=(FONT, 12),
            fg_color=TEAL_BTN, button_color=TEAL_HOVER,
            button_hover_color=TEAL_HOVER,
            corner_radius=10, height=34, width=250,
            command=self._on_camera_change
        )
        self.camera_dropdown.set(huidige_naam)
        self.camera_dropdown.pack(side="left", fill="x", expand=True)

        self.camera_ververs_btn = ctk.CTkButton(
            rij, text="\u21BB", font=(FONT, 16),
            fg_color="transparent", hover_color=RAND,
            text_color=TEKST_LICHT,
            corner_radius=8, height=34, width=34,
            command=self._ververs_cameras
        )
        self.camera_ververs_btn.pack(side="left", padx=(8, 0))

        preview_rij = ctk.CTkFrame(self.cam_frame, fg_color="transparent")
        preview_rij.pack(fill="x", padx=16, pady=(0, 12))

        self._preview_ctk_img = None
        self.preview_btn = ctk.CTkButton(
            preview_rij, text="Camera preview",
            font=(FONT, 12), height=30,
            fg_color=DONKER, hover_color=DONKER_HOVER,
            corner_radius=8, cursor="hand2",
            command=self._toon_camera_preview
        )
        self.preview_btn.pack(fill="x")

        self.preview_label = ctk.CTkLabel(
            self.cam_frame, text="", fg_color=BG,
            corner_radius=8, width=180, height=120,
        )

    def _on_camera_change(self, keuze):
        """Callback wanneer de gebruiker een andere camera kiest."""
        for idx, naam in self._cameras:
            if naam == keuze:
                config = laad_explorer_config()
                config["camera_index"] = idx
                sla_explorer_config_op(config)
                self._config_cache = config
                break
        self._toon_camera_preview()

    def _ververs_cameras(self):
        """Herdetecteer beschikbare camera's."""
        self._cameras = detecteer_cameras()
        if self._cameras:
            cam_namen = [naam for _, naam in self._cameras]
        else:
            cam_namen = ["Geen camera gevonden"]
        self.camera_dropdown.configure(values=cam_namen)
        if cam_namen:
            self.camera_dropdown.set(cam_namen[0])
            if self._cameras:
                self._on_camera_change(cam_namen[0])

    # ---- Camera preview ----

    def _toon_camera_preview(self):
        """Pak één frame van de geselecteerde camera en toon als preview."""
        cam_idx = self._get_camera_index()
        self.preview_btn.configure(state="disabled", text="Laden...")
        self.preview_label.configure(image=None, text="")
        self.preview_label.pack(padx=16, pady=(0, 12))

        def _grab():
            import cv2

            frame = None
            try:
                cap = cv2.VideoCapture(cam_idx)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    for _ in range(5):
                        cap.read()
                    ret, frame = cap.read()
                    cap.release()
                    if not ret:
                        frame = None
            except Exception:
                frame = None
            self.app.after(0, lambda: self._update_preview(frame))

        threading.Thread(target=_grab, daemon=True).start()

    def _update_preview(self, frame):
        """Update het preview-label met het opgehaalde frame."""
        import cv2

        self.preview_btn.configure(state="normal", text="Camera preview")

        if frame is None:
            self.preview_label.configure(
                image=None,
                text="Geen beeld beschikbaar",
                font=(FONT, 11),
                text_color=TEKST_LICHT,
            )
            self.preview_label.pack(padx=16, pady=(0, 12))
            return

        from blendshape_detectie import naar_contiguous_beeld
        frame = naar_contiguous_beeld(frame)
        if frame is None:
            self.preview_label.configure(
                image=None,
                text="Geen beeld beschikbaar",
                font=(FONT, 11),
                text_color=TEKST_LICHT,
            )
            self.preview_label.pack(padx=16, pady=(0, 12))
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = frame_rgb.shape[:2]
        if w <= 0 or h <= 0:
            self.preview_label.configure(
                image=None,
                text="Geen beeld beschikbaar",
                font=(FONT, 11),
                text_color=TEKST_LICHT,
            )
            self.preview_label.pack(padx=16, pady=(0, 12))
            return
        max_w, max_h = 180, 120
        schaal = min(max_w / w, max_h / h)
        nieuw_w = max(1, int(w * schaal))
        nieuw_h = max(1, int(h * schaal))
        frame_klein = cv2.resize(frame_rgb, (nieuw_w, nieuw_h),
                                 interpolation=cv2.INTER_AREA)

        pil_img = Image.fromarray(frame_klein)
        self._preview_ctk_img = ctk.CTkImage(
            light_image=pil_img, size=(nieuw_w, nieuw_h)
        )
        self.preview_label.configure(
            image=self._preview_ctk_img,
            text="",
            width=nieuw_w,
            height=nieuw_h,
        )
        self.preview_label.pack(padx=16, pady=(0, 12))

    # ---- Profiel ----

    def _bouw_profiel_selector(self, parent):
        """Profiel-selector met dropdown, nieuw-knop en verwijder-knop."""
        self.profiel_frame = ctk.CTkFrame(parent, fg_color=KAART,
                                           corner_radius=12, border_width=1,
                                           border_color=RAND)
        self.profiel_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.profiel_frame, text="Profiel",
                     font=(FONT, 13, "bold"), text_color=TEKST
                     ).pack(anchor="w", padx=16, pady=(12, 6))

        rij = ctk.CTkFrame(self.profiel_frame, fg_color="transparent")
        rij.pack(fill="x", padx=16, pady=(0, 12))

        profielen = lijst_profielen()
        huidig = actief_profiel()

        self.profiel_dropdown = ctk.CTkOptionMenu(
            rij, values=profielen if profielen else ["Standaard"],
            font=(FONT, 12), dropdown_font=(FONT, 12),
            fg_color=TEAL_BTN, button_color=TEAL_HOVER,
            button_hover_color=TEAL_HOVER,
            corner_radius=10, height=34, width=180,
            command=self._on_profiel_wissel
        )
        self.profiel_dropdown.set(huidig)
        self.profiel_dropdown.pack(side="left", fill="x", expand=True)

        self.profiel_nieuw_btn = ctk.CTkButton(
            rij, text="+", font=(FONT, 16, "bold"),
            fg_color=TEAL_BTN, hover_color=TEAL_HOVER,
            corner_radius=8, height=34, width=34, cursor="hand2",
            command=self._nieuw_profiel
        )
        self.profiel_nieuw_btn.pack(side="left", padx=(8, 0))

        self.profiel_verwijder_btn = ctk.CTkButton(
            rij, text="✕", font=(FONT, 14, "bold"),
            fg_color=ROOD, hover_color=ROOD_HOVER,
            corner_radius=8, height=34, width=34, cursor="hand2",
            command=self._verwijder_huidig_profiel
        )
        self.profiel_verwijder_btn.pack(side="left", padx=(6, 0))
        self._update_verwijder_knop()

    def _update_verwijder_knop(self):
        """Verberg de verwijderknop als er maar één profiel is."""
        if len(lijst_profielen()) <= 1:
            self.profiel_verwijder_btn.configure(state="disabled",
                                                 fg_color=RAND)
        else:
            self.profiel_verwijder_btn.configure(state="normal",
                                                 fg_color=ROOD)

    def _on_profiel_wissel(self, naam):
        """Wissel naar een ander profiel en herlaad de interface."""
        wissel_profiel(naam)
        self._config_cache = None
        self._ververs_triggers()
        self._update_verwijder_knop()

    def _nieuw_profiel(self):
        """Open een dialoog om een nieuw profiel aan te maken."""
        dialoog = ctk.CTkInputDialog(
            text="Voer een naam in voor het nieuwe profiel:",
            title="Nieuw profiel",
            font=(FONT, 13)
        )
        naam = dialoog.get_input()
        if not naam or not naam.strip():
            return
        naam = naam.strip()
        if naam in lijst_profielen():
            messagebox.showwarning(
                "Profiel bestaat al",
                f'Er bestaat al een profiel met de naam "{naam}".',
                parent=self.app)
            return
        from config_explorer import STANDAARD_CONFIG
        import copy
        sla_profiel_op(naam, copy.deepcopy(STANDAARD_CONFIG))
        wissel_profiel(naam)
        self._config_cache = None
        self._ververs_profiel_dropdown()
        self._ververs_triggers()

    def _verwijder_huidig_profiel(self):
        """Verwijder het huidige profiel na bevestiging."""
        naam = actief_profiel()
        ok = messagebox.askyesno(
            "Profiel verwijderen",
            f'Wil je profiel "{naam}" echt verwijderen?\n'
            f'Alle triggers in dit profiel gaan verloren.',
            parent=self.app)
        if not ok:
            return
        verwijder_profiel(naam)
        self._config_cache = None
        self._ververs_profiel_dropdown()
        self._ververs_triggers()

    def _ververs_profiel_dropdown(self):
        """Werk de dropdown bij met de actuele profiellijst."""
        profielen = lijst_profielen()
        huidig = actief_profiel()
        self.profiel_dropdown.configure(values=profielen)
        self.profiel_dropdown.set(huidig)
        self._update_verwijder_knop()

    def _bouw_live_weergave(self, parent):
        """Overlay-opties — blijven bewaard in het profiel."""
        kaart = ctk.CTkFrame(parent, fg_color=KAART,
                             corner_radius=12, border_width=1,
                             border_color=RAND)
        kaart.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(kaart, text="Live-weergave",
                     font=(FONT, 13, "bold"), text_color=TEKST
                     ).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(
            kaart,
            text="Het kleine camerabeeld blijft boven Communicator 5 staan. "
                 "Volledig scherm kan het beeld laten "
                 "stokken: gebruik Vensterweergave.",
            font=(FONT, 11), text_color=TEKST_LICHT, wraplength=300,
            anchor="w", justify="left"
        ).pack(fill="x", padx=16, pady=(0, 8))

        self._sneltoetsen_open = False
        sneltoetsen_knop = ctk.CTkButton(
            kaart, text="Sneltoetsen tonen", height=26, width=150,
            font=(FONT, 11), fg_color="#E5E5EA", hover_color="#D1D1D6",
            text_color=TEKST, corner_radius=8, cursor="hand2",
        )
        sneltoetsen_knop.pack(anchor="w", padx=16, pady=(0, 6))
        sneltoetsen_box = ctk.CTkFrame(kaart, fg_color="transparent", height=1)
        sneltoetsen_box.pack(fill="x", padx=16)
        sneltoetsen_lbl = ctk.CTkLabel(
            sneltoetsen_box,
            text="Klik eerst op het camerabeeld, dan:\n"
                 "Q stoppen · P pauze · 1/2/3 grootte\n"
                 "T triggerbalken · S toetsen sturen · K melding · A bovenop\n"
                 "M gezichtsnet · F spiegelen · O hoek · C alleen camera",
            font=(FONT, 11), text_color=TEKST_LICHT, anchor="w", justify="left",
        )

        def _toggle_sneltoetsen():
            self._sneltoetsen_open = not self._sneltoetsen_open
            if self._sneltoetsen_open:
                sneltoetsen_lbl.pack(fill="x", pady=(0, 6))
                sneltoetsen_knop.configure(text="Sneltoetsen verbergen")
            else:
                sneltoetsen_lbl.pack_forget()
                sneltoetsen_knop.configure(text="Sneltoetsen tonen")

        sneltoetsen_knop.configure(command=_toggle_sneltoetsen)

        self.overlay_var = ctk.BooleanVar(value=True)
        self.overlay_hud_var = ctk.BooleanVar(value=True)
        self.overlay_camera_var = ctk.BooleanVar(value=False)
        self.toetsen_var = ctk.BooleanVar(value=True)
        self.toets_melding_var = ctk.BooleanVar(value=True)
        self.topmost_var = ctk.BooleanVar(value=True)
        self.spiegel_var = ctk.BooleanVar(value=True)
        self.mesh_var = ctk.BooleanVar(value=False)

        def _switch(parent_w, tekst, var, sleutel):
            w = ctk.CTkSwitch(
                parent_w, text=tekst,
                font=(FONT, 12), text_color=TEKST,
                variable=var, onvalue=True, offvalue=False,
                progress_color=TEAL_BTN, button_color=KAART,
                button_hover_color=RAND, fg_color="#C8C8CC",
                command=lambda: self._on_live_switch(sleutel, var)
            )
            w.pack(anchor="w", padx=16, pady=2)
            return w

        self.overlay_switch = _switch(
            kaart, "Camerabeeld tonen", self.overlay_var, "overlay_aan"
        )

        grootte_rij = ctk.CTkFrame(kaart, fg_color="transparent")
        grootte_rij.pack(fill="x", padx=16, pady=(6, 2))
        ctk.CTkLabel(
            grootte_rij, text="Grootte (1/2/3):",
            font=(FONT, 12), text_color=TEKST, width=110, anchor="w"
        ).pack(side="left")
        self.overlay_grootte_lbl = ctk.CTkLabel(
            grootte_rij, text=overlay_grootte_label(2),
            font=(FONT, 11, "bold"), text_color=TEKST, width=150, anchor="e"
        )
        self.overlay_grootte_lbl.pack(side="right")
        self.overlay_grootte_slider = ctk.CTkSlider(
            kaart, from_=1, to=3, number_of_steps=2,
            button_color=TEAL_BTN, button_hover_color=TEAL_HOVER,
            progress_color=TEAL_BTN,
            command=self._on_overlay_grootte
        )
        self.overlay_grootte_slider.set(2)
        self.overlay_grootte_slider.pack(fill="x", padx=16, pady=(0, 2))
        ctk.CTkLabel(
            kaart,
            text="1 minimaal 320×180 · 2 480×270 · 3 dubbel 640×360",
            font=(FONT, 10), text_color=TEKST_LICHT, wraplength=300,
            anchor="w", justify="left"
        ).pack(fill="x", padx=16, pady=(0, 6))

        hoek_rij = ctk.CTkFrame(kaart, fg_color="transparent")
        hoek_rij.pack(fill="x", padx=16, pady=(2, 6))
        ctk.CTkLabel(
            hoek_rij, text="Hoek (O):",
            font=(FONT, 12), text_color=TEKST, width=110, anchor="w"
        ).pack(side="left")
        self.overlay_hoek_menu = ctk.CTkOptionMenu(
            hoek_rij, values=list(OVERLAY_HOEK_MENU),
            font=(FONT, 12), fg_color=DONKER, button_color=TEAL_BTN,
            button_hover_color=TEAL_HOVER, width=150,
            command=self._on_overlay_hoek
        )
        self.overlay_hoek_menu.set("Rechtsboven")
        self.overlay_hoek_menu.pack(side="right")

        self.overlay_hud_switch = _switch(
            kaart, "Triggerbalken tonen (T)",
            self.overlay_hud_var, "overlay_hud_aan"
        )
        self.overlay_camera_switch = _switch(
            kaart, "Alleen camerabeeld (C)",
            self.overlay_camera_var, "overlay_alleen_camera"
        )
        self.toetsen_switch = _switch(
            kaart, "Toetsen sturen (S)",
            self.toetsen_var, "overlay_toetsen_sturen"
        )
        self.toets_melding_switch = _switch(
            kaart, "Toets-melding tonen (K)",
            self.toets_melding_var, "overlay_toets_melding"
        )
        self.topmost_switch = _switch(
            kaart, "Altijd bovenop (A)",
            self.topmost_var, "overlay_topmost"
        )
        self.spiegel_switch = _switch(
            kaart, "Spiegelbeeld camera (F)",
            self.spiegel_var, "overlay_spiegel"
        )
        self.mesh_switch = _switch(
            kaart, "Gezichtsnet volledig tekenen (M)",
            self.mesh_var, "mesh_volledig"
        )

        kleuren = " · ".join(
            f"{i + 1} {naam}" for i, naam in enumerate(TRIGGER_KLEUR_NAMEN[:6])
        )
        ctk.CTkLabel(
            kaart,
            text=f"Triggerkleuren: {kleuren}",
            font=(FONT, 10), text_color=TEKST_LICHT, wraplength=300,
            anchor="w", justify="left"
        ).pack(fill="x", padx=16, pady=(4, 12))

    # ---- Timing ----

    def _bouw_timing(self, parent):
        timing = ctk.CTkFrame(parent, fg_color=KAART,
                               corner_radius=14, border_width=1,
                               border_color=RAND)
        timing.pack(fill="x")

        ctk.CTkLabel(timing, text="Timing-instellingen",
                     font=(FONT, 13, "bold"), text_color=TEKST
                     ).pack(anchor="w", padx=16, pady=(14, 8))

        rij1 = ctk.CTkFrame(timing, fg_color="transparent")
        rij1.pack(fill="x", padx=16, pady=4)

        ctk.CTkLabel(rij1, text="Cooldown:", font=(FONT, 12),
                     text_color=TEKST_LICHT, width=90, anchor="w"
                     ).pack(side="left")

        self.cd_lbl = ctk.CTkLabel(rij1, text="—", font=(FONT, 12, "bold"),
                                    text_color=TEKST, width=48, anchor="e")
        self.cd_lbl.pack(side="right")

        self.cd_slider = ctk.CTkSlider(
            rij1, from_=0.5, to=10.0,
            button_color=TEAL_BTN, button_hover_color=TEAL_HOVER,
            progress_color=TEAL_BTN,
            command=self._on_cd_change
        )
        self.cd_slider.pack(side="left", fill="x", expand=True, padx=(6, 6))
        ctk.CTkLabel(timing, text="Wachttijd na een toets, voordat dezelfde trigger opnieuw mag.",
                     font=(FONT, 10), text_color=TEKST_LICHT, wraplength=300,
                     anchor="w", justify="left"
                     ).pack(fill="x", padx=16, pady=(0, 2))

        rij2 = ctk.CTkFrame(timing, fg_color="transparent")
        rij2.pack(fill="x", padx=16, pady=4)

        ctk.CTkLabel(rij2, text="Vasthoudtijd:", font=(FONT, 12),
                     text_color=TEKST_LICHT, width=90, anchor="w"
                     ).pack(side="left")

        self.vh_lbl = ctk.CTkLabel(rij2, text="—", font=(FONT, 12, "bold"),
                                    text_color=TEKST, width=48, anchor="e")
        self.vh_lbl.pack(side="right")

        self.vh_slider = ctk.CTkSlider(
            rij2, from_=0.1, to=3.0,
            button_color=TEAL_BTN, button_hover_color=TEAL_HOVER,
            progress_color=TEAL_BTN,
            command=self._on_vh_change
        )
        self.vh_slider.pack(side="left", fill="x", expand=True, padx=(6, 6))
        ctk.CTkLabel(timing, text="Zo lang moet je de beweging vasthouden voordat de toets wordt gestuurd.",
                     font=(FONT, 10), text_color=TEKST_LICHT, wraplength=300,
                     anchor="w", justify="left"
                     ).pack(fill="x", padx=16, pady=(0, 2))

        rij3 = ctk.CTkFrame(timing, fg_color="transparent")
        rij3.pack(fill="x", padx=16, pady=(4, 0))

        ctk.CTkLabel(rij3, text="Toetsduur:", font=(FONT, 12),
                     text_color=TEKST_LICHT, width=90, anchor="w"
                     ).pack(side="left")

        self.td_lbl = ctk.CTkLabel(rij3, text="—", font=(FONT, 12, "bold"),
                                    text_color=TEKST, width=48, anchor="e")
        self.td_lbl.pack(side="right")

        self.td_slider = ctk.CTkSlider(
            rij3, from_=20, to=500,
            button_color=TEAL_BTN, button_hover_color=TEAL_HOVER,
            progress_color=TEAL_BTN,
            command=self._on_td_change
        )
        self.td_slider.pack(side="left", fill="x", expand=True, padx=(6, 6))
        ctk.CTkLabel(timing, text="Zo lang blijft de toets ingedrukt (in milliseconden).",
                     font=(FONT, 10), text_color=TEKST_LICHT, wraplength=300,
                     anchor="w", justify="left"
                     ).pack(fill="x", padx=16, pady=(0, 14))

    # ---- Triggers ----

    def _kolom_aantal(self):
        try:
            w = self.trigger_scroll.winfo_width()
        except Exception:
            w = 900
        if w >= 1320:
            return 3
        if w >= 820:
            return 2
        return 1

    def _on_venster_resize(self, event):
        if event.widget is not self.app:
            return
        if self._resize_after is not None:
            try:
                self.app.after_cancel(self._resize_after)
            except Exception:
                pass
        self._resize_after = self.app.after(140, self._plaats_trigger_kaarten)

    def _plaats_trigger_kaarten(self):
        self._resize_after = None
        if not hasattr(self, "trigger_grid"):
            return
        cols = self._kolom_aantal()
        widgets = list(self.trigger_grid.winfo_children())
        if not widgets:
            self._laatste_kolommen = cols
            return
        if cols == self._laatste_kolommen and self._laatste_kolommen != 0:
            return
        for c in range(max(cols, 3)):
            self.trigger_grid.grid_columnconfigure(c, weight=1 if c < cols else 0)

        if len(widgets) == 1 and not self._trigger_kaarten:
            widgets[0].grid(row=0, column=0, columnspan=cols, sticky="ew",
                            padx=4, pady=8)
        else:
            for i, kaart in enumerate(widgets):
                kaart.grid(row=i // cols, column=i % cols, sticky="nsew",
                           padx=6, pady=6)
        self._laatste_kolommen = cols

    def _ververs_triggers(self):
        for w in self.trigger_grid.winfo_children():
            w.destroy()
        self._trigger_kaarten = []
        self._laatste_kolommen = 0

        config = laad_explorer_config()
        self._config_cache = config
        triggers = config.get("triggers", [])

        self.cd_slider.set(config["cooldown"])
        self.cd_lbl.configure(text=f"{config['cooldown']:.1f}s")
        self.vh_slider.set(config["vasthoud_tijd"])
        self.vh_lbl.configure(text=f"{config['vasthoud_tijd']:.1f}s")
        td = config.get("toets_duur_ms", 100)
        self.td_slider.set(td)
        self.td_lbl.configure(text=f"{int(td)}ms")
        self._zet_live_switches(config)

        if not triggers:
            self._toon_welkomstbericht()
        else:
            for i, t in enumerate(triggers):
                self._maak_trigger_kaart(i, t)
        self.app.after(30, self._plaats_trigger_kaarten)

    def _toon_welkomstbericht(self):
        """Toon een stap-voor-stap welkomstbericht als er nog geen triggers zijn."""
        welkom = ctk.CTkFrame(self.trigger_grid, fg_color=KAART,
                               corner_radius=14, border_width=1,
                               border_color=RAND)

        inner = ctk.CTkFrame(welkom, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=24)

        ctk.CTkLabel(inner, text="Welkom bij MimiControl Studio v2!",
                     font=(FONT, 16, "bold"), text_color=TEKST
                     ).pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(inner,
                     text="Je hebt nog geen triggers ingesteld. Volg deze stappen:",
                     font=(FONT, 13), text_color=TEKST_LICHT
                     ).pack(anchor="w", pady=(0, 14))

        stappen = [
            ("1", "Klik op \"Mimiek verkennen\" in de balk rechts"),
            ("2", "Maak het gebaar dat je wilt gebruiken voor de webcam"),
            ("3", "Stel de trigger in met de gewenste toets"),
            ("4", "Klik op \"Live modus starten\" om te beginnen"),
        ]

        for nr, tekst in stappen:
            stap_rij = ctk.CTkFrame(inner, fg_color="transparent")
            stap_rij.pack(fill="x", pady=4)

            ctk.CTkLabel(stap_rij, text=nr,
                         font=(FONT, 13, "bold"), text_color=KAART,
                         fg_color=TEAL_BTN, corner_radius=12,
                         width=26, height=26
                         ).pack(side="left", padx=(0, 12))

            ctk.CTkLabel(stap_rij, text=tekst,
                         font=(FONT, 13), text_color=TEKST
                         ).pack(side="left")

    def _maak_trigger_kaart(self, index, trigger):
        accent = TRIGGER_ACCENTEN[index % len(TRIGGER_ACCENTEN)]

        kaart = ctk.CTkFrame(self.trigger_grid, fg_color=KAART,
                              corner_radius=14, border_width=1,
                              border_color=RAND)
        self._trigger_kaarten.append(kaart)

        accent_bar = ctk.CTkFrame(kaart, fg_color=accent, height=4,
                                   corner_radius=0)
        accent_bar.pack(fill="x", padx=14, pady=(12, 0))

        inhoud = ctk.CTkFrame(kaart, fg_color="transparent")
        inhoud.pack(fill="x", padx=16, pady=(10, 14))

        rij_top = ctk.CTkFrame(inhoud, fg_color="transparent")
        rij_top.pack(fill="x")

        from toets_keuze import label_voor_toetsen
        toets = label_voor_toetsen(trigger["toetsen"])
        ctk.CTkLabel(rij_top, text=f"{index+1}. {trigger['naam']}",
                     font=(FONT, 14, "bold"), text_color=TEKST
                     ).pack(side="left")

        ctk.CTkButton(rij_top, text=toets, font=(FONT, 11, "bold"),
                      fg_color=accent, hover_color=accent,
                      corner_radius=10, height=28,
                      width=max(72, 11 * len(toets)),
                      state="disabled", text_color_disabled=KAART
                      ).pack(side="right")

        bs = trigger.get("blendshapes", {})
        if bs:
            bs_frame = ctk.CTkFrame(inhoud, fg_color=BG, corner_radius=8)
            bs_frame.pack(fill="x", pady=(8, 8))

            bs_inner = ctk.CTkFrame(bs_frame, fg_color="transparent")
            bs_inner.pack(fill="x", padx=10, pady=6)

            for naam, drempel in bs.items():
                bs_rij = ctk.CTkFrame(bs_inner, fg_color="transparent")
                bs_rij.pack(fill="x", pady=1)
                ctk.CTkLabel(bs_rij, text=f"\u25B8 {nl_label(naam)}",
                             font=(FONT, 11), text_color=TEKST,
                             anchor="w"
                             ).pack(side="left")
                ctk.CTkLabel(bs_rij, text=f"> {drempel:.2f}",
                             font=(FONT, 11, "bold"), text_color=TEKST_LICHT,
                             anchor="e"
                             ).pack(side="right")

        btn_rij = ctk.CTkFrame(inhoud, fg_color="transparent")
        btn_rij.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(
            btn_rij, text="Bewerken", font=(FONT, 11),
            fg_color=TEAL_BTN, hover_color=TEAL_HOVER,
            corner_radius=16, height=30, width=96, cursor="hand2",
            command=lambda idx=index: self._bewerk_trigger(idx)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_rij, text="Verwijderen", font=(FONT, 11),
            fg_color=ROOD, hover_color=ROOD_HOVER,
            corner_radius=16, height=30, width=104, cursor="hand2",
            command=lambda idx=index: self._verwijder_trigger(idx)
        ).pack(side="left")

    # ---- Timing callbacks ----

    def _plan_config_opslag(self):
        if self._save_after is not None:
            try:
                self.app.after_cancel(self._save_after)
            except Exception:
                pass
        self._save_after = self.app.after(280, self._sla_timing_nu_op)

    def _sla_timing_nu_op(self):
        self._save_after = None
        if self._config_cache is None:
            self._config_cache = laad_explorer_config()
        sla_explorer_config_op(self._config_cache)

    def _on_cd_change(self, value):
        val = round(value, 1)
        self.cd_lbl.configure(text=f"{val:.1f}s")
        if self._config_cache is None:
            self._config_cache = laad_explorer_config()
        self._config_cache["cooldown"] = val
        self._plan_config_opslag()

    def _on_vh_change(self, value):
        val = round(value, 1)
        self.vh_lbl.configure(text=f"{val:.1f}s")
        if self._config_cache is None:
            self._config_cache = laad_explorer_config()
        self._config_cache["vasthoud_tijd"] = val
        self._plan_config_opslag()

    def _on_td_change(self, value):
        val = int(round(value))
        self.td_lbl.configure(text=f"{val}ms")
        if self._config_cache is None:
            self._config_cache = laad_explorer_config()
        self._config_cache["toets_duur_ms"] = val
        self._plan_config_opslag()

    def _zet_live_switches(self, config):
        if not hasattr(self, "overlay_var"):
            return
        self._switches_laden = True
        try:
            self.overlay_var.set(bool(config.get("overlay_aan", True)))
            self.overlay_hud_var.set(bool(config.get("overlay_hud_aan", True)))
            self.overlay_camera_var.set(bool(config.get("overlay_alleen_camera", False)))
            self.toetsen_var.set(bool(config.get("overlay_toetsen_sturen", True)))
            self.toets_melding_var.set(bool(config.get("overlay_toets_melding", True)))
            self.topmost_var.set(bool(config.get("overlay_topmost", True)))
            self.spiegel_var.set(bool(config.get("overlay_spiegel", True)))
            self.mesh_var.set(bool(config.get("mesh_volledig", False)))
            stap = normaliseer_overlay_grootte(config.get("overlay_grootte", 2))
            if hasattr(self, "overlay_grootte_slider"):
                self.overlay_grootte_slider.set(stap)
                self.overlay_grootte_lbl.configure(text=overlay_grootte_label(stap))
            if hasattr(self, "overlay_hoek_menu"):
                self.overlay_hoek_menu.set(
                    overlay_hoek_label(config.get("overlay_hoek", "rechtsboven"))
                )
        finally:
            self._switches_laden = False

    def _on_live_switch(self, sleutel, var):
        if self._switches_laden:
            return
        if self._config_cache is None:
            self._config_cache = laad_explorer_config()
        self._config_cache[sleutel] = bool(var.get())
        sla_explorer_config_op(self._config_cache)

    def _on_overlay_grootte(self, value):
        if self._switches_laden:
            return
        stap = normaliseer_overlay_grootte(value)
        self.overlay_grootte_lbl.configure(text=overlay_grootte_label(stap))
        if self._config_cache is None:
            return
        self._config_cache["overlay_grootte"] = stap
        sla_explorer_config_op(self._config_cache)

    def _on_overlay_hoek(self, label):
        if self._switches_laden or self._config_cache is None:
            return
        self._config_cache["overlay_hoek"] = overlay_hoek_van_label(label)
        sla_explorer_config_op(self._config_cache)

    # ---- Acties ----

    def _get_camera_index(self):
        """Geef de huidig geselecteerde camera-index."""
        config = self._config_cache or laad_explorer_config()
        return config.get("camera_index", 0)

    def _maak_laad_venster(self, titel):
        """Toon een laadvenster; None als het niet gemaakt kan worden."""
        try:
            from laad_venster import LaadVenster
            return LaadVenster(self.app, titel=titel,
                               tekst="Even geduld, de camera start op…")
        except Exception:
            return None

    def _lanceer_explorer(self):
        from explorer import start_explorer
        from trigger_editor_ctk import open_trigger_editor

        pieken = None
        laad_ui = None
        try:
            laad_ui = self._maak_laad_venster("Mimiek verkennen wordt gestart")
            pieken = start_explorer(
                camera_index=self._get_camera_index(),
                parent=self.app,
                laad_ui=laad_ui,
                on_gereed=self._verberg_hoofdvenster,
            )
        finally:
            if laad_ui is not None:
                laad_ui.sluit()
            try:
                self.app.deiconify()
                _maximaliseer(self.app)
                self.app.lift()
            except Exception:
                pass

        if pieken:
            open_trigger_editor(
                self.app, pieken,
                callback=self._ververs_triggers
            )

    def _lanceer_live(self):
        from live_modus_explorer import start_live_explorer

        config = laad_explorer_config()
        self._config_cache = config
        if not config["triggers"]:
            messagebox.showwarning(
                "Geen triggers",
                "Maak eerst minstens één trigger aan via 'Mimiek verkennen'.",
                parent=self.app)
            return

        laad_ui = None
        try:
            laad_ui = self._maak_laad_venster("Live modus wordt gestart")
            start_live_explorer(
                camera_index=self._get_camera_index(),
                laad_ui=laad_ui,
                on_gereed=self._verberg_hoofdvenster,
            )
        finally:
            if laad_ui is not None:
                laad_ui.sluit()
            try:
                self.app.deiconify()
                _maximaliseer(self.app)
                self.app.lift()
            except Exception:
                pass

    def _verberg_hoofdvenster(self):
        """Verberg het dashboard zodra het webcamvenster opent."""
        try:
            self.app.withdraw()
            self.app.update_idletasks()
        except Exception:
            pass

    def _bewerk_trigger(self, index):
        from trigger_editor_ctk import open_trigger_editor

        config = laad_explorer_config()
        trigger = config["triggers"][index]
        pieken = {naam: min(drempel / 0.7, 1.0)
                  for naam, drempel in trigger["blendshapes"].items()}
        open_trigger_editor(
            self.app, pieken,
            callback=self._ververs_triggers,
            bewerk_index=index,
            bewerk_data=trigger
        )

    def _verwijder_trigger(self, index):
        config = laad_explorer_config()
        naam = config["triggers"][index]["naam"]
        ok = messagebox.askyesno(
            "Trigger verwijderen",
            f'Wil je trigger "{naam}" echt verwijderen?',
            parent=self.app)
        if ok:
            verwijder_trigger(index)
            self._config_cache = None
            self._ververs_triggers()

    def start(self):
        self.app.mainloop()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def start_gui_explorer_ctk(startup_t0=None):
    app = MimiControlStudioApp(startup_t0=startup_t0)
    app.start()


if __name__ == "__main__":
    start_gui_explorer_ctk()
