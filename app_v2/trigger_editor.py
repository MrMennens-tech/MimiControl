"""
MimiExplorer - Trigger Editor
Tkinter dialoog voor het samenstellen van blendshape-triggers
met checkboxes, sliders en toetsinvoer.
Mennens.Tech huisstijl.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont

from blendshape_labels import (
    nl_label, is_ondersteund, groepen_voor_ui, namen_in_groepsvolgorde,
    suggestie_namen, MODEL_BEPERKING_TEKST, pieken_voor_trigger_menu,
)
from config_explorer import (
    laad_explorer_config, sla_explorer_config_op, voeg_trigger_toe
)

# ---------------------------------------------------------------------------
# Mennens.Tech Huisstijl
# ---------------------------------------------------------------------------
DONKER = "#062D36"
TEAL = "#68CCD1"
TEAL_MID = "#2C6479"
GROEN = "#3BAF6A"
ROOD = "#D94040"

BG = "#F4F6F7"
KAART = "#FFFFFF"
RAND = "#D5DDE0"
TEKST = "#062D36"
TEKST_LICHT = "#5F7A83"
WIT = "#FFFFFF"

FONT_FALLBACK = "Segoe UI" if sys.platform == "win32" else "Helvetica"


def open_trigger_editor(parent, pieken, callback=None,
                        bewerk_index=None, bewerk_data=None):
    TriggerEditorDialog(parent, pieken, callback,
                        bewerk_index, bewerk_data)


class TriggerEditorDialog:
    def __init__(self, parent, pieken, callback=None,
                 bewerk_index=None, bewerk_data=None):
        self.callback = callback
        self.bewerk_index = bewerk_index
        # Nieuwe trigger: alleen de shapes uit het explorer-filter.
        # Bewerken: alle shapes, zodat je er een kunt toevoegen.
        self.pieken = pieken_voor_trigger_menu(
            pieken, alleen_filter=bewerk_index is None)
        self.groepen = groepen_voor_ui()
        if bewerk_index is None and pieken:
            # Nieuwe trigger: alleen groepen/shapes uit het filter tonen
            self.groepen = [
                (g, [n for n in namen if n in self.pieken])
                for g, namen in self.groepen
            ]
            self.groepen = [(g, n) for g, n in self.groepen if n]
        self.voorgesteld = (
            set() if bewerk_data
            else suggestie_namen(self.pieken)
        )

        self.v = tk.Toplevel(parent)
        self.v.title("Trigger samenstellen")
        self.v.configure(bg=BG)
        self.v.resizable(True, True)
        self.v.grab_set()
        self.v.transient(parent)

        # Font
        beschikbaar = tkfont.families(parent)
        sf = "Work Sans" if "Work Sans" in beschikbaar else FONT_FALLBACK

        self.f_titel = tkfont.Font(family=sf, size=16, weight="bold")
        self.f_label = tkfont.Font(family=sf, size=11)
        self.f_waarde = tkfont.Font(family=sf, size=11, weight="bold")
        self.f_knop = tkfont.Font(family=sf, size=13, weight="bold")
        self.f_entry = tkfont.Font(family=sf, size=13)
        self.f_bs_naam = tkfont.Font(family=sf, size=11)
        self.f_bs_piek = tkfont.Font(family=sf, size=10)
        self.f_bs_val = tkfont.Font(family=sf, size=12, weight="bold")
        self.f_sectie = tkfont.Font(family=sf, size=11)

        # Venstergrootte: scrollbaar, zodat alle bruikbare shapes passen
        n_rijen = sum(len(namen) for _, namen in self.groepen) + len(self.groepen)
        breedte = 720
        hoogte = min(820, 300 + max(n_rijen, 1) * 54)
        self.v.update_idletasks()
        sx = parent.winfo_x() + max(0, (parent.winfo_width() - breedte) // 2)
        sy = parent.winfo_y() + max(0, (parent.winfo_height() - hoogte) // 2)
        self.v.geometry(f"{breedte}x{hoogte}+{sx}+{sy}")

        # Header
        header = tk.Frame(self.v, bg=DONKER, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        titel = "Trigger bewerken" if bewerk_index is not None else "Nieuwe trigger"
        tk.Label(header, text=titel, font=self.f_titel,
                 bg=DONKER, fg=WIT).pack(pady=20)

        body = tk.Frame(self.v, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=16)

        # --- Naam + toets ---
        rij_boven = tk.Frame(body, bg=BG)
        rij_boven.pack(fill="x", pady=(0, 14))

        tk.Label(rij_boven, text="Naam:", font=self.f_label,
                 bg=BG, fg=TEKST).pack(side="left")
        self.naam_var = tk.StringVar(
            value=bewerk_data["naam"] if bewerk_data else
            f"Trigger {len(laad_explorer_config()['triggers']) + 1}")
        ttk.Entry(rij_boven, textvariable=self.naam_var,
                  font=self.f_entry, width=20).pack(side="left", padx=(8, 28))

        tk.Label(rij_boven, text="Toets:", font=self.f_label,
                 bg=BG, fg=TEKST).pack(side="left")
        self.toets_var = tk.StringVar(
            value=" + ".join(bewerk_data["toetsen"]) if bewerk_data
            else "space")
        ttk.Entry(rij_boven, textvariable=self.toets_var,
                  font=self.f_entry, width=18).pack(side="left", padx=(8, 0))

        # --- Instructie ---
        tk.Label(body,
                 text="Selecteer blendshapes en stel drempels in:",
                 font=self.f_sectie, bg=BG, fg=TEKST_LICHT
                 ).pack(anchor="w", pady=(4, 2))
        tk.Label(body,
                 text=MODEL_BEPERKING_TEKST,
                 font=self.f_sectie, bg=BG, fg="#8A5A2A",
                 wraplength=640, justify="left",
                 ).pack(anchor="w", pady=(0, 8))

        # --- Kolomkoppen ---
        kop_rij = tk.Frame(body, bg=BG)
        kop_rij.pack(fill="x", padx=4)
        tk.Label(kop_rij, text="", bg=BG, width=3).pack(side="left")
        tk.Label(kop_rij, text="Blendshape", font=self.f_bs_piek,
                 bg=BG, fg=TEKST_LICHT, width=22, anchor="w"
                 ).pack(side="left")
        tk.Label(kop_rij, text="Piek", font=self.f_bs_piek,
                 bg=BG, fg=TEKST_LICHT, width=8).pack(side="left")
        tk.Label(kop_rij, text="Drempel", font=self.f_bs_piek,
                 bg=BG, fg=TEKST_LICHT).pack(side="left", fill="x", expand=True)
        tk.Label(kop_rij, text="Waarde", font=self.f_bs_piek,
                 bg=BG, fg=TEKST_LICHT, width=7).pack(side="right")

        # --- Blendshape rijen (scrollbaar, groepsvolgorde) ---
        self.rijen = []
        bewerk_bs = bewerk_data["blendshapes"] if bewerk_data else {}

        canvas_host = tk.Frame(body, bg=BG)
        canvas_host.pack(fill="both", expand=True)
        canvas = tk.Canvas(canvas_host, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_host, orient="vertical",
                                  command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _sync_breedte(event):
            canvas.itemconfigure(inner_id, width=event.width)

        canvas.bind("<Configure>", _sync_breedte)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for groep_naam, namen in self.groepen:
            tk.Label(
                inner, text=groep_naam, font=self.f_sectie, bg=BG,
                fg=DONKER, anchor="w"
            ).pack(fill="x", pady=(8, 2), padx=4)
            for naam in namen:
                piek = self.pieken.get(naam, 0.0)
                standaard_aan = (
                    naam in bewerk_bs if bewerk_data
                    else naam in self.voorgesteld
                )
                standaard_drempel = (
                    bewerk_bs.get(naam, piek * 0.7) if bewerk_data
                    else (piek * 0.7 if piek > 0 else 0.15)
                )
                rij = self._maak_blendshape_rij(
                    inner, naam, piek, standaard_aan, standaard_drempel, 0
                )
                self.rijen.append(rij)

        # --- Knoppen ---
        btn_frame = tk.Frame(body, bg=BG)
        btn_frame.pack(fill="x", pady=(18, 0))

        tk.Button(btn_frame, text="Annuleren", font=self.f_knop,
                  bg=RAND, fg=TEKST, relief="flat", padx=20, pady=8,
                  cursor="hand2", activebackground="#B0BEC5",
                  command=self.v.destroy).pack(side="right", padx=(10, 0))

        tk.Button(btn_frame, text="Opslaan", font=self.f_knop,
                  bg=GROEN, fg=WIT, relief="flat", padx=20, pady=8,
                  cursor="hand2", activebackground="#2E8B57",
                  activeforeground=WIT,
                  command=self._opslaan).pack(side="right")

    def _maak_blendshape_rij(self, parent, naam, piek,
                              standaard_aan, standaard_drempel, index):
        rij = tk.Frame(parent, bg=KAART, highlightbackground=RAND,
                       highlightthickness=1)
        rij.pack(fill="x", pady=3, ipady=6)

        # Checkbox
        var_aan = tk.BooleanVar(value=standaard_aan)
        cb = tk.Checkbutton(rij, variable=var_aan, bg=KAART,
                            activebackground=KAART, selectcolor=KAART)
        cb.pack(side="left", padx=(10, 6))

        # Naam
        label = nl_label(naam)
        if len(label) > 24:
            label = label[:22] + ".."
        tk.Label(rij, text=label, font=self.f_bs_naam, bg=KAART,
                 fg=TEKST, width=22, anchor="w").pack(side="left")

        # Piek
        tk.Label(rij, text=f"piek {piek:.2f}", font=self.f_bs_piek,
                 bg=KAART, fg=TEKST_LICHT, width=8).pack(side="left", padx=(0, 6))

        # Drempel waarde (RECHTS, vaste breedte, EERST toevoegen)
        var_drempel = tk.DoubleVar(value=round(standaard_drempel, 2))
        drempel_lbl = tk.Label(rij, text=f"{var_drempel.get():.2f}",
                               font=self.f_bs_val, bg=KAART, fg=DONKER,
                               width=6, anchor="e")
        drempel_lbl.pack(side="right", padx=(6, 14))

        # Slider (vult de rest)
        slider = ttk.Scale(rij, from_=0.05, to=1.0,
                           variable=var_drempel, orient="horizontal")
        slider.pack(side="right", fill="x", expand=True, padx=(6, 6))

        var_drempel.trace_add(
            "write",
            lambda *_: self._sync_label(var_drempel, drempel_lbl)
        )

        return {"naam": naam, "aan": var_aan, "drempel": var_drempel}

    def _sync_label(self, var, lbl):
        try:
            lbl.config(text=f"{var.get():.2f}")
        except tk.TclError:
            pass

    def _opslaan(self):
        naam = self.naam_var.get().strip()
        if not naam:
            messagebox.showwarning("Lege naam", "Geef de trigger een naam.",
                                   parent=self.v)
            return

        toets_invoer = self.toets_var.get().strip().lower()
        toetsen = [t.strip() for t in toets_invoer.replace(" + ", "+").split("+")
                   if t.strip()]
        if not toetsen:
            messagebox.showwarning("Geen toets", "Voer een toets in.",
                                   parent=self.v)
            return

        blendshapes = {}
        for rij in self.rijen:
            if rij["aan"].get() and is_ondersteund(rij["naam"]):
                blendshapes[rij["naam"]] = round(rij["drempel"].get(), 3)

        if not blendshapes:
            messagebox.showwarning(
                "Geen selectie",
                "Vink minstens één blendshape aan.",
                parent=self.v)
            return

        if self.bewerk_index is not None:
            config = laad_explorer_config()
            config["triggers"][self.bewerk_index] = {
                "naam": naam,
                "toetsen": toetsen,
                "blendshapes": blendshapes
            }
            sla_explorer_config_op(config)
        else:
            voeg_trigger_toe(naam, toetsen, blendshapes)

        if self.callback:
            self.callback()
        self.v.destroy()
