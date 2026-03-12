"""
MimiExplorer - Grafische Gebruikersinterface
Hoofdvenster met triggerlijst, Explorer-knop, Live-knop en
timing-instellingen. Branding: Mennens.Tech huisstijl.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
from PIL import Image, ImageTk

from config_explorer import (
    laad_explorer_config, sla_explorer_config_op, verwijder_trigger
)
from blendshape_detectie import nl_label
from explorer import start_explorer
from trigger_editor import open_trigger_editor
from live_modus_explorer import start_live_explorer

# ---------------------------------------------------------------------------
# Mennens.Tech Huisstijl
# ---------------------------------------------------------------------------
DONKER = "#062D36"
TEAL = "#68CCD1"
TEAL_MID = "#2C6479"
GROEN = "#3BAF6A"
ROOD = "#D94040"
ORANJE = "#E88D2A"

BG = "#F4F6F7"
KAART = "#FFFFFF"
RAND = "#D5DDE0"
TEKST = "#062D36"
TEKST_LICHT = "#5F7A83"
WIT = "#FFFFFF"

LOGO_PAD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "assets", "logo_mennens.png"
)
FONT_FALLBACK = "Segoe UI" if sys.platform == "win32" else "Helvetica"


def _donkerder(hex_kleur, factor=0.82):
    r = int(int(hex_kleur[1:3], 16) * factor)
    g = int(int(hex_kleur[3:5], 16) * factor)
    b = int(int(hex_kleur[5:7], 16) * factor)
    return f"#{min(r,255):02x}{min(g,255):02x}{min(b,255):02x}"


# ---------------------------------------------------------------------------
# Hoofdvenster
# ---------------------------------------------------------------------------
class MimiExplorerApp:

    def __init__(self):
        # DPI-awareness VOOR de root aanmaken
        if sys.platform == "win32":
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

        self.root = tk.Tk()
        self.root.title("MimiExplorer — Mennens.Tech")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # Font: check of Work Sans beschikbaar is
        beschikbaar = tkfont.families(self.root)
        self.sf = "Work Sans" if "Work Sans" in beschikbaar else FONT_FALLBACK

        # Venstergrootte
        breedte, hoogte = 680, 900
        self.root.update_idletasks()
        sx = (self.root.winfo_screenwidth() - breedte) // 2
        sy = max(10, (self.root.winfo_screenheight() - hoogte) // 2)
        self.root.geometry(f"{breedte}x{hoogte}+{sx}+{sy}")

        # Fonts
        self.f_titel = tkfont.Font(family=self.sf, size=24, weight="bold")
        self.f_sub = tkfont.Font(family=self.sf, size=12)
        self.f_knop = tkfont.Font(family=self.sf, size=15, weight="bold")
        self.f_knop_desc = tkfont.Font(family=self.sf, size=11)
        self.f_label = tkfont.Font(family=self.sf, size=11)
        self.f_waarde = tkfont.Font(family=self.sf, size=11, weight="bold")
        self.f_sectie = tkfont.Font(family=self.sf, size=14, weight="bold")
        self.f_small = tkfont.Font(family=self.sf, size=10)
        self.f_card_naam = tkfont.Font(family=self.sf, size=13, weight="bold")
        self.f_card_label = tkfont.Font(family=self.sf, size=10)

        self._bouw_interface()
        self._ververs_triggers()

    # ---- Layout ----

    def _bouw_interface(self):
        # --- Header ---
        header = tk.Frame(self.root, bg=DONKER, height=140)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_inner = tk.Frame(header, bg=DONKER)
        header_inner.place(relx=0.5, rely=0.5, anchor="center")

        # Logo laden (PNG met palette mode -> RGBA)
        self.logo_img = None
        if os.path.exists(LOGO_PAD):
            try:
                img = Image.open(LOGO_PAD).convert("RGBA")
                img = img.resize((56, 56), Image.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                tk.Label(header_inner, image=self.logo_img, bg=DONKER
                         ).pack(side="left", padx=(0, 16))
            except Exception:
                pass

        tekst_frame = tk.Frame(header_inner, bg=DONKER)
        tekst_frame.pack(side="left")
        tk.Label(tekst_frame, text="MimiExplorer",
                 font=self.f_titel, bg=DONKER, fg=WIT).pack(anchor="w")
        tk.Label(tekst_frame, text="Blendshape Trigger Builder  —  Mennens.Tech",
                 font=self.f_sub, bg=DONKER, fg=TEAL).pack(anchor="w", pady=(2, 0))

        # --- Actieknoppen ---
        knoppen = tk.Frame(self.root, bg=BG)
        knoppen.pack(fill="x", padx=32, pady=(22, 0))

        self._maak_knop(knoppen, "Explorer openen",
                        "Ontdek welke blendshapes uitslaan bij een gebaar",
                        TEAL_MID, self._lanceer_explorer)

        self._maak_knop(knoppen, "Live besturing starten",
                        "Start de webcam en voer toetsacties uit",
                        GROEN, self._lanceer_live)

        # --- Triggers ---
        sep = tk.Frame(self.root, bg=RAND, height=1)
        sep.pack(fill="x", padx=32, pady=(20, 12))

        trigger_header = tk.Frame(self.root, bg=BG)
        trigger_header.pack(fill="x", padx=34)
        tk.Label(trigger_header, text="Geconfigureerde triggers",
                 font=self.f_sectie, bg=BG, fg=TEKST
                 ).pack(side="left")

        # Scroll-container
        self.trigger_container = tk.Frame(self.root, bg=BG)
        self.trigger_container.pack(fill="both", expand=True,
                                    padx=32, pady=(8, 8))

        # --- Timing ---
        sep2 = tk.Frame(self.root, bg=RAND, height=1)
        sep2.pack(fill="x", padx=32, pady=(8, 8))
        self._bouw_timing()

    def _bouw_timing(self):
        timing = tk.Frame(self.root, bg=KAART,
                          highlightbackground=RAND, highlightthickness=1)
        timing.pack(fill="x", padx=32, pady=(0, 22))

        tk.Label(timing, text="Timing-instellingen", font=self.f_waarde,
                 bg=KAART, fg=TEKST).pack(anchor="w", padx=18, pady=(14, 6))

        # Cooldown
        rij1 = tk.Frame(timing, bg=KAART)
        rij1.pack(fill="x", padx=18, pady=4)
        tk.Label(rij1, text="Cooldown:", font=self.f_label,
                 bg=KAART, fg=TEKST_LICHT, width=14, anchor="w"
                 ).pack(side="left")
        self.cd_var = tk.DoubleVar()
        style = ttk.Style()
        style.configure("Teal.Horizontal.TScale", background=KAART)
        ttk.Scale(rij1, from_=0.5, to=10.0,
                  variable=self.cd_var, orient="horizontal",
                  style="Teal.Horizontal.TScale"
                  ).pack(side="left", fill="x", expand=True, padx=8)
        self.cd_lbl = tk.Label(rij1, text="—", font=self.f_waarde,
                               bg=KAART, fg=DONKER, width=6)
        self.cd_lbl.pack(side="right", padx=(0, 4))
        self.cd_var.trace_add("write", self._sync_cd)

        # Vasthoudtijd
        rij2 = tk.Frame(timing, bg=KAART)
        rij2.pack(fill="x", padx=18, pady=(4, 14))
        tk.Label(rij2, text="Vasthoudtijd:", font=self.f_label,
                 bg=KAART, fg=TEKST_LICHT, width=14, anchor="w"
                 ).pack(side="left")
        self.vh_var = tk.DoubleVar()
        ttk.Scale(rij2, from_=0.1, to=3.0,
                  variable=self.vh_var, orient="horizontal",
                  style="Teal.Horizontal.TScale"
                  ).pack(side="left", fill="x", expand=True, padx=8)
        self.vh_lbl = tk.Label(rij2, text="—", font=self.f_waarde,
                               bg=KAART, fg=DONKER, width=6)
        self.vh_lbl.pack(side="right", padx=(0, 4))
        self.vh_var.trace_add("write", self._sync_vh)

    # ---- Knop-helper ----

    def _maak_knop(self, parent, tekst, beschrijving, kleur, commando):
        frame = tk.Frame(parent, bg=kleur, cursor="hand2")
        frame.pack(fill="x", pady=5, ipady=10)

        lbl_t = tk.Label(frame, text=tekst, font=self.f_knop,
                         bg=kleur, fg=WIT, cursor="hand2")
        lbl_t.pack(anchor="w", padx=24, pady=(10, 0))

        lbl_d = tk.Label(frame, text=beschrijving, font=self.f_knop_desc,
                         bg=kleur, fg="#D5EFF1", cursor="hand2")
        lbl_d.pack(anchor="w", padx=24, pady=(2, 10))

        hover = _donkerder(kleur)
        for w in (frame, lbl_t, lbl_d):
            w.bind("<Enter>", lambda _e, f=frame, a=lbl_t, b=lbl_d, h=hover:
                   (f.config(bg=h), a.config(bg=h), b.config(bg=h)))
            w.bind("<Leave>", lambda _e, f=frame, a=lbl_t, b=lbl_d, k=kleur:
                   (f.config(bg=k), a.config(bg=k), b.config(bg=k)))
            w.bind("<Button-1>", lambda _e, c=commando: c())

    # ---- Triggers ----

    def _ververs_triggers(self):
        for w in self.trigger_container.winfo_children():
            w.destroy()

        config = laad_explorer_config()
        triggers = config.get("triggers", [])
        self.cd_var.set(config["cooldown"])
        self.vh_var.set(config["vasthoud_tijd"])

        if not triggers:
            lbl = tk.Label(self.trigger_container,
                           text="Nog geen triggers.\n"
                                "Open de Explorer om je eerste trigger aan te maken.",
                           font=self.f_label, bg=BG, fg=TEKST_LICHT,
                           justify="center")
            lbl.pack(pady=36)
        else:
            for i, t in enumerate(triggers):
                self._maak_trigger_kaart(i, t)

    def _maak_trigger_kaart(self, index, trigger):
        kleur_accent = [TEAL_MID, ORANJE, GROEN, ROOD, DONKER]
        accent = kleur_accent[index % len(kleur_accent)]

        kaart = tk.Frame(self.trigger_container, bg=KAART,
                         highlightbackground=RAND, highlightthickness=1)
        kaart.pack(fill="x", pady=5)

        # Gekleurde zijbalk
        zijbalk = tk.Frame(kaart, bg=accent, width=6)
        zijbalk.pack(side="left", fill="y")
        zijbalk.pack_propagate(False)

        inhoud = tk.Frame(kaart, bg=KAART)
        inhoud.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        # Bovenste rij
        rij_top = tk.Frame(inhoud, bg=KAART)
        rij_top.pack(fill="x")

        toets = " + ".join(trigger["toetsen"]).upper()
        tk.Label(rij_top, text=f"{index+1}. {trigger['naam']}",
                 font=self.f_card_naam, bg=KAART, fg=TEKST
                 ).pack(side="left")

        toets_badge = tk.Label(rij_top, text=f"  {toets}  ",
                               font=self.f_waarde, bg=accent, fg=WIT)
        toets_badge.pack(side="right")

        # Blendshapes
        bs = trigger.get("blendshapes", {})
        if bs:
            bs_tekst = "  |  ".join(
                f"{nl_label(n)} > {d:.2f}" for n, d in bs.items()
            )
            tk.Label(inhoud, text=bs_tekst, font=self.f_card_label,
                     bg=KAART, fg=TEKST_LICHT, wraplength=560, justify="left"
                     ).pack(anchor="w", pady=(6, 6))

        # Knoppen
        btn_rij = tk.Frame(inhoud, bg=KAART)
        btn_rij.pack(fill="x", pady=(4, 0))

        tk.Button(btn_rij, text="Bewerken", font=self.f_small,
                  bg=DONKER, fg=WIT, relief="flat", padx=14, pady=4,
                  cursor="hand2", activebackground=TEAL_MID,
                  activeforeground=WIT,
                  command=lambda idx=index: self._bewerk_trigger(idx)
                  ).pack(side="left", padx=(0, 8))

        tk.Button(btn_rij, text="Verwijderen", font=self.f_small,
                  bg=ROOD, fg=WIT, relief="flat", padx=14, pady=4,
                  cursor="hand2", activebackground=_donkerder(ROOD),
                  activeforeground=WIT,
                  command=lambda idx=index: self._verwijder_trigger(idx)
                  ).pack(side="left")

    # ---- Timing sync ----

    def _sync_cd(self, *_):
        try:
            val = self.cd_var.get()
            self.cd_lbl.config(text=f"{val:.1f}s")
            config = laad_explorer_config()
            config["cooldown"] = round(val, 1)
            sla_explorer_config_op(config)
        except tk.TclError:
            pass

    def _sync_vh(self, *_):
        try:
            val = self.vh_var.get()
            self.vh_lbl.config(text=f"{val:.1f}s")
            config = laad_explorer_config()
            config["vasthoud_tijd"] = round(val, 1)
            sla_explorer_config_op(config)
        except tk.TclError:
            pass

    # ---- Acties ----

    def _lanceer_explorer(self):
        self.root.withdraw()
        self.root.update()
        pieken = start_explorer()
        self.root.deiconify()

        if pieken:
            open_trigger_editor(
                self.root, pieken,
                callback=self._ververs_triggers
            )

    def _lanceer_live(self):
        config = laad_explorer_config()
        if not config["triggers"]:
            messagebox.showwarning(
                "Geen triggers",
                "Maak eerst minstens één trigger aan via de Explorer.",
                parent=self.root)
            return
        self.root.withdraw()
        self.root.update()
        start_live_explorer()
        self.root.deiconify()

    def _bewerk_trigger(self, index):
        config = laad_explorer_config()
        trigger = config["triggers"][index]
        pieken = {naam: min(drempel / 0.7, 1.0)
                  for naam, drempel in trigger["blendshapes"].items()}
        open_trigger_editor(
            self.root, pieken,
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
            parent=self.root)
        if ok:
            verwijder_trigger(index)
            self._ververs_triggers()

    def start(self):
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def start_gui_explorer():
    app = MimiExplorerApp()
    app.start()


if __name__ == "__main__":
    start_gui_explorer()
