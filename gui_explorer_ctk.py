"""
MimiControl Studio - CustomTkinter GUI (Mennens.Tech branding)
Hoofdvenster met triggerlijst, Explorer-knop, Live-knop en
timing-instellingen.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image

import customtkinter as ctk

from config_explorer import (
    laad_explorer_config, sla_explorer_config_op, verwijder_trigger
)
from blendshape_detectie import nl_label
from explorer import start_explorer
from trigger_editor_ctk import open_trigger_editor
from live_modus_explorer import start_live_explorer

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

LOGO_PAD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "assets", "logo_mennens.png"
)
ICON_PAD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "assets", "mimicontrol.ico"
)

TRIGGER_ACCENTEN = ["#4DB8BE", "#3D8FA5", "#68CCD1", "#2E7A8A", "#89D4D8"]


# ---------------------------------------------------------------------------
# Hoofdvenster
# ---------------------------------------------------------------------------
class MimiControlStudioApp:

    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("MimiControl Studio — Mennens.Tech")
        self.app.configure(fg_color=BG)
        if os.path.exists(ICON_PAD):
            self.app.iconbitmap(ICON_PAD)
        self.app.resizable(True, True)
        self.app.minsize(680, 600)

        breedte = 680
        scherm_h = self.app.winfo_screenheight()
        hoogte = min(920, scherm_h - 80)
        sx = (self.app.winfo_screenwidth() - breedte) // 2
        self.app.geometry(f"{breedte}x{hoogte}+{sx}+20")

        self._bouw_interface()
        self._ververs_triggers()

    # ---- Layout ----

    def _bouw_interface(self):
        # --- Header ---
        header = ctk.CTkFrame(self.app, fg_color=DONKER, corner_radius=0, height=130)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.place(relx=0.5, rely=0.5, anchor="center")

        self.logo_img = None
        if os.path.exists(LOGO_PAD):
            try:
                pil_img = Image.open(LOGO_PAD).convert("RGBA")
                # Maak donkere pixels wit zodat het logo zichtbaar is op de donkere header
                pixels = pil_img.load()
                w_img, h_img = pil_img.size
                for y in range(h_img):
                    for x in range(w_img):
                        r, g, b, a = pixels[x, y]
                        if a > 30 and (r + g + b) < 400:
                            pixels[x, y] = (255, 255, 255, a)
                self.logo_img = ctk.CTkImage(light_image=pil_img, size=(120, 78))
                ctk.CTkLabel(header_inner, image=self.logo_img, text=""
                             ).pack(side="left", padx=(0, 16))
            except Exception:
                pass

        tekst_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        tekst_frame.pack(side="left")
        ctk.CTkLabel(tekst_frame, text="MimiControl Studio",
                     font=(FONT, 26, "bold"), text_color=KAART
                     ).pack(anchor="center")
        ctk.CTkLabel(tekst_frame, text="Jouw gezicht, jouw besturing  —  Mennens.Tech",
                     font=(FONT, 13), text_color=TEAL_BRAND
                     ).pack(anchor="center", pady=(2, 0))

        # --- Actieknoppen (compact, naast beschrijving) ---
        knoppen = ctk.CTkFrame(self.app, fg_color="transparent")
        knoppen.pack(fill="x", padx=32, pady=(18, 0))

        rij1 = ctk.CTkFrame(knoppen, fg_color=KAART, corner_radius=12,
                             border_width=1, border_color=RAND)
        rij1.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(
            rij1, text="Mimiek verkennen",
            font=(FONT, 13, "bold"), height=40, width=200,
            fg_color=TEAL_BTN, hover_color=TEAL_HOVER,
            corner_radius=12, cursor="hand2",
            command=self._lanceer_explorer
        ).pack(side="left", padx=6, pady=6)
        ctk.CTkLabel(rij1,
                     text="Herken gezichtsuitdrukkingen en stel triggers in",
                     font=(FONT, 12), text_color=TEKST_LICHT
                     ).pack(side="left", padx=(8, 14))

        rij2 = ctk.CTkFrame(knoppen, fg_color=KAART, corner_radius=12,
                             border_width=1, border_color=RAND)
        rij2.pack(fill="x", pady=(0, 4))
        ctk.CTkButton(
            rij2, text="Live modus starten",
            font=(FONT, 13, "bold"), height=40, width=200,
            fg_color=DONKER, hover_color=DONKER_HOVER,
            corner_radius=12, cursor="hand2",
            command=self._lanceer_live
        ).pack(side="left", padx=6, pady=6)
        ctk.CTkLabel(rij2,
                     text="Start de webcam en voer toetsacties uit",
                     font=(FONT, 12), text_color=TEKST_LICHT
                     ).pack(side="left", padx=(8, 14))

        # --- Separator ---
        ctk.CTkFrame(self.app, fg_color=RAND, height=1, corner_radius=0
                     ).pack(fill="x", padx=32, pady=(14, 10))

        # --- Timing (boven triggers zodat het altijd zichtbaar is) ---
        self._bouw_timing()

        # --- Separator ---
        ctk.CTkFrame(self.app, fg_color=RAND, height=1, corner_radius=0
                     ).pack(fill="x", padx=32, pady=(6, 10))

        # --- Trigger header ---
        ctk.CTkLabel(self.app, text="Geconfigureerde triggers",
                     font=(FONT, 16, "bold"), text_color=TEKST
                     ).pack(anchor="w", padx=36)

        # --- Scrollable trigger container ---
        self.trigger_scroll = ctk.CTkScrollableFrame(
            self.app, fg_color="transparent", corner_radius=0
        )
        self.trigger_scroll.pack(fill="both", expand=True, padx=28, pady=(8, 12))

    def _bouw_timing(self):
        timing = ctk.CTkFrame(self.app, fg_color=KAART,
                               corner_radius=14, border_width=1,
                               border_color=RAND)
        timing.pack(fill="x", padx=32, pady=(0, 4))

        ctk.CTkLabel(timing, text="Timing-instellingen",
                     font=(FONT, 13, "bold"), text_color=TEKST
                     ).pack(anchor="w", padx=20, pady=(16, 8))

        # Cooldown
        rij1 = ctk.CTkFrame(timing, fg_color="transparent")
        rij1.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(rij1, text="Cooldown:", font=(FONT, 12),
                     text_color=TEKST_LICHT, width=120, anchor="w"
                     ).pack(side="left")

        self.cd_lbl = ctk.CTkLabel(rij1, text="—", font=(FONT, 13, "bold"),
                                    text_color=TEKST, width=55, anchor="e")
        self.cd_lbl.pack(side="right", padx=(0, 4))

        self.cd_slider = ctk.CTkSlider(
            rij1, from_=0.5, to=10.0,
            button_color=TEAL_BTN, button_hover_color=TEAL_HOVER,
            progress_color=TEAL_BTN,
            command=self._on_cd_change
        )
        self.cd_slider.pack(side="left", fill="x", expand=True, padx=(8, 8))

        # Vasthoudtijd
        rij2 = ctk.CTkFrame(timing, fg_color="transparent")
        rij2.pack(fill="x", padx=20, pady=(4, 16))

        ctk.CTkLabel(rij2, text="Vasthoudtijd:", font=(FONT, 12),
                     text_color=TEKST_LICHT, width=120, anchor="w"
                     ).pack(side="left")

        self.vh_lbl = ctk.CTkLabel(rij2, text="—", font=(FONT, 13, "bold"),
                                    text_color=TEKST, width=55, anchor="e")
        self.vh_lbl.pack(side="right", padx=(0, 4))

        self.vh_slider = ctk.CTkSlider(
            rij2, from_=0.1, to=3.0,
            button_color=TEAL_BTN, button_hover_color=TEAL_HOVER,
            progress_color=TEAL_BTN,
            command=self._on_vh_change
        )
        self.vh_slider.pack(side="left", fill="x", expand=True, padx=(8, 8))

    # ---- Triggers ----

    def _ververs_triggers(self):
        for w in self.trigger_scroll.winfo_children():
            w.destroy()

        config = laad_explorer_config()
        triggers = config.get("triggers", [])

        self.cd_slider.set(config["cooldown"])
        self.cd_lbl.configure(text=f"{config['cooldown']:.1f}s")
        self.vh_slider.set(config["vasthoud_tijd"])
        self.vh_lbl.configure(text=f"{config['vasthoud_tijd']:.1f}s")

        if not triggers:
            ctk.CTkLabel(
                self.trigger_scroll,
                text="Nog geen triggers.\nOpen de Explorer om je eerste trigger aan te maken.",
                font=(FONT, 12), text_color=TEKST_LICHT, justify="center"
            ).pack(pady=40)
        else:
            for i, t in enumerate(triggers):
                self._maak_trigger_kaart(i, t)

    def _maak_trigger_kaart(self, index, trigger):
        accent = TRIGGER_ACCENTEN[index % len(TRIGGER_ACCENTEN)]

        kaart = ctk.CTkFrame(self.trigger_scroll, fg_color=KAART,
                              corner_radius=14, border_width=1,
                              border_color=RAND)
        kaart.pack(fill="x", pady=5, padx=4)

        # Gekleurde accent-balk bovenaan
        accent_bar = ctk.CTkFrame(kaart, fg_color=accent, height=4,
                                   corner_radius=0)
        accent_bar.pack(fill="x", padx=14, pady=(10, 0))

        # Inhoud
        inhoud = ctk.CTkFrame(kaart, fg_color="transparent")
        inhoud.pack(fill="x", padx=16, pady=(8, 12))

        # Bovenste rij: naam + toets badge
        rij_top = ctk.CTkFrame(inhoud, fg_color="transparent")
        rij_top.pack(fill="x")

        toets = " + ".join(trigger["toetsen"]).upper()
        ctk.CTkLabel(rij_top, text=f"{index+1}. {trigger['naam']}",
                     font=(FONT, 14, "bold"), text_color=TEKST
                     ).pack(side="left")

        ctk.CTkButton(rij_top, text=toets, font=(FONT, 11, "bold"),
                      fg_color=accent, hover_color=accent,
                      corner_radius=10, height=28, width=70,
                      state="disabled", text_color_disabled=KAART
                      ).pack(side="right")

        # Blendshapes detail
        bs = trigger.get("blendshapes", {})
        if bs:
            bs_tekst = "  |  ".join(
                f"{nl_label(n)} > {d:.2f}" for n, d in bs.items()
            )
            ctk.CTkLabel(inhoud, text=bs_tekst, font=(FONT, 10),
                         text_color=TEKST_LICHT, wraplength=540,
                         justify="left").pack(anchor="w", pady=(6, 6))

        # Knoppen
        btn_rij = ctk.CTkFrame(inhoud, fg_color="transparent")
        btn_rij.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(
            btn_rij, text="Bewerken", font=(FONT, 11),
            fg_color=TEAL_BTN, hover_color=TEAL_HOVER,
            corner_radius=16, height=32, width=100, cursor="hand2",
            command=lambda idx=index: self._bewerk_trigger(idx)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_rij, text="Verwijderen", font=(FONT, 11),
            fg_color=ROOD, hover_color=ROOD_HOVER,
            corner_radius=16, height=32, width=110, cursor="hand2",
            command=lambda idx=index: self._verwijder_trigger(idx)
        ).pack(side="left")

    # ---- Timing callbacks ----

    def _on_cd_change(self, value):
        val = round(value, 1)
        self.cd_lbl.configure(text=f"{val:.1f}s")
        config = laad_explorer_config()
        config["cooldown"] = val
        sla_explorer_config_op(config)

    def _on_vh_change(self, value):
        val = round(value, 1)
        self.vh_lbl.configure(text=f"{val:.1f}s")
        config = laad_explorer_config()
        config["vasthoud_tijd"] = val
        sla_explorer_config_op(config)

    # ---- Acties ----

    def _lanceer_explorer(self):
        self.app.withdraw()
        self.app.update()
        pieken = start_explorer()
        self.app.deiconify()

        if pieken:
            open_trigger_editor(
                self.app, pieken,
                callback=self._ververs_triggers
            )

    def _lanceer_live(self):
        config = laad_explorer_config()
        if not config["triggers"]:
            messagebox.showwarning(
                "Geen triggers",
                "Maak eerst minstens één trigger aan via de Explorer.",
                parent=self.app)
            return
        self.app.withdraw()
        self.app.update()
        start_live_explorer()
        self.app.deiconify()

    def _bewerk_trigger(self, index):
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
            self._ververs_triggers()

    def start(self):
        self.app.mainloop()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def start_gui_explorer_ctk():
    app = MimiControlStudioApp()
    app.start()


if __name__ == "__main__":
    start_gui_explorer_ctk()
