"""
MimiControl Studio - Trigger Editor (CustomTkinter / Mennens.Tech branding)
Dialoog voor het samenstellen van blendshape-triggers
met checkboxes, sliders en toetsinvoer.
"""

import sys
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from blendshape_detectie import nl_label
from config_explorer import (
    laad_explorer_config, sla_explorer_config_op, voeg_trigger_toe
)

# ---------------------------------------------------------------------------
# Mennens.Tech kleurenpalet
# ---------------------------------------------------------------------------
BG          = "#F2F2F7"
KAART       = "#FFFFFF"
TEKST       = "#1C1C1E"
TEKST_LICHT = "#5A5A5E"
DONKER      = "#062D36"
TEAL_BTN    = "#4DB8BE"
TEAL_HOVER  = "#3A9DA3"
TEAL_BRAND  = "#68CCD1"
OPSLAAN     = "#4DB8BE"
OPSLAAN_HOVER = "#3A9DA3"
RAND        = "#E5E5EA"

FONT = "Segoe UI" if sys.platform == "win32" else "Helvetica"
TOP_STANDAARD_AAN = 3
MAX_TONEN = 10


def open_trigger_editor(parent, pieken, callback=None,
                        bewerk_index=None, bewerk_data=None):
    TriggerEditorDialog(parent, pieken, callback,
                        bewerk_index, bewerk_data)


class TriggerEditorDialog:
    def __init__(self, parent, pieken, callback=None,
                 bewerk_index=None, bewerk_data=None):
        self.callback = callback
        self.bewerk_index = bewerk_index
        self.pieken = pieken

        self.gesorteerd = sorted(
            pieken.items(), key=lambda kv: kv[1], reverse=True
        )[:MAX_TONEN]

        # Venster
        self.v = ctk.CTkToplevel(parent)
        self.v.title("Trigger samenstellen")
        self.v.configure(fg_color=BG)
        self.v.resizable(False, False)
        self.v.grab_set()
        self.v.transient(parent)

        breedte = 720
        rij_hoogte = 56
        hoogte = 320 + len(self.gesorteerd) * rij_hoogte
        self.v.geometry(f"{breedte}x{hoogte}")
        sx = parent.winfo_x() + max(0, (parent.winfo_width() - breedte) // 2)
        sy = parent.winfo_y() + max(0, (parent.winfo_height() - hoogte) // 2)
        self.v.geometry(f"+{sx}+{sy}")

        # Header
        header = ctk.CTkFrame(self.v, fg_color=DONKER, corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        titel = "Trigger bewerken" if bewerk_index is not None else "Nieuwe trigger"
        ctk.CTkLabel(header, text=titel, font=(FONT, 18, "bold"),
                     text_color=KAART).pack(expand=True)

        # Body
        body = ctk.CTkFrame(self.v, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        # --- Naam + Toets ---
        invoer_rij = ctk.CTkFrame(body, fg_color="transparent")
        invoer_rij.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(invoer_rij, text="Naam:", font=(FONT, 12),
                     text_color=TEKST).pack(side="left")

        self.naam_entry = ctk.CTkEntry(
            invoer_rij, font=(FONT, 13), width=200,
            corner_radius=10, border_width=1, border_color=RAND
        )
        self.naam_entry.pack(side="left", padx=(8, 24))
        default_naam = (bewerk_data["naam"] if bewerk_data
                        else f"Trigger {len(laad_explorer_config()['triggers']) + 1}")
        self.naam_entry.insert(0, default_naam)

        ctk.CTkLabel(invoer_rij, text="Toets:", font=(FONT, 12),
                     text_color=TEKST).pack(side="left")

        self.toets_entry = ctk.CTkEntry(
            invoer_rij, font=(FONT, 13), width=160,
            corner_radius=10, border_width=1, border_color=RAND
        )
        self.toets_entry.pack(side="left", padx=(8, 0))
        default_toets = (" + ".join(bewerk_data["toetsen"]) if bewerk_data
                         else "space")
        self.toets_entry.insert(0, default_toets)

        # --- Instructie ---
        ctk.CTkLabel(body,
                     text="Selecteer blendshapes en stel drempels in:",
                     font=(FONT, 11), text_color=TEKST_LICHT
                     ).pack(anchor="w", pady=(2, 8))

        # --- Kolomkoppen ---
        kop = ctk.CTkFrame(body, fg_color="transparent")
        kop.pack(fill="x", padx=6)
        ctk.CTkLabel(kop, text="", width=36).pack(side="left")
        ctk.CTkLabel(kop, text="Blendshape", font=(FONT, 10),
                     text_color=TEKST_LICHT, width=180, anchor="w"
                     ).pack(side="left")
        ctk.CTkLabel(kop, text="Piek", font=(FONT, 10),
                     text_color=TEKST_LICHT, width=70).pack(side="left")
        ctk.CTkLabel(kop, text="Drempel", font=(FONT, 10),
                     text_color=TEKST_LICHT).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(kop, text="Waarde", font=(FONT, 10),
                     text_color=TEKST_LICHT, width=60).pack(side="right")

        # --- Blendshape rijen ---
        self.rijen = []
        bewerk_bs = bewerk_data["blendshapes"] if bewerk_data else {}

        for i, (naam, piek) in enumerate(self.gesorteerd):
            standaard_aan = (naam in bewerk_bs if bewerk_data
                             else i < TOP_STANDAARD_AAN)
            standaard_drempel = (bewerk_bs.get(naam, piek * 0.7) if bewerk_data
                                 else piek * 0.7)
            rij = self._maak_blendshape_rij(
                body, naam, piek, standaard_aan, standaard_drempel
            )
            self.rijen.append(rij)

        # --- Knoppen ---
        btn_frame = ctk.CTkFrame(body, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(18, 0))

        ctk.CTkButton(
            btn_frame, text="Annuleren", font=(FONT, 13, "bold"),
            fg_color=RAND, text_color=TEKST, hover_color="#D1D1D6",
            corner_radius=20, height=44, width=130, cursor="hand2",
            command=self.v.destroy
        ).pack(side="right", padx=(10, 0))

        ctk.CTkButton(
            btn_frame, text="Opslaan", font=(FONT, 13, "bold"),
            fg_color=OPSLAAN, hover_color=OPSLAAN_HOVER, text_color=KAART,
            corner_radius=20, height=44, width=130, cursor="hand2",
            command=self._opslaan
        ).pack(side="right")

    def _maak_blendshape_rij(self, parent, naam, piek,
                              standaard_aan, standaard_drempel):
        rij = ctk.CTkFrame(parent, fg_color=KAART, corner_radius=10,
                            border_width=1, border_color=RAND, height=46)
        rij.pack(fill="x", pady=3)

        # Checkbox
        var_aan = tk.BooleanVar(value=standaard_aan)
        cb = ctk.CTkCheckBox(
            rij, text="", variable=var_aan, width=28,
            corner_radius=6, fg_color=TEAL_BTN, hover_color=TEAL_HOVER,
            border_color=RAND, border_width=2
        )
        cb.pack(side="left", padx=(12, 6))

        # Naam
        label = nl_label(naam)
        if len(label) > 24:
            label = label[:22] + ".."
        ctk.CTkLabel(rij, text=label, font=(FONT, 11),
                     text_color=TEKST, width=180, anchor="w"
                     ).pack(side="left")

        # Piek
        ctk.CTkLabel(rij, text=f"piek {piek:.2f}", font=(FONT, 10),
                     text_color=TEKST_LICHT, width=70
                     ).pack(side="left", padx=(0, 4))

        # Drempel waarde label (rechts, eerst toevoegen)
        drempel_lbl = ctk.CTkLabel(rij, text=f"{standaard_drempel:.2f}",
                                    font=(FONT, 13, "bold"),
                                    text_color=DONKER, width=55, anchor="e")
        drempel_lbl.pack(side="right", padx=(4, 14))

        # Slider
        slider = ctk.CTkSlider(
            rij, from_=0.05, to=1.0, width=180,
            button_color=TEAL_BTN, button_hover_color=TEAL_HOVER,
            progress_color=TEAL_BTN,
            command=lambda val, lbl=drempel_lbl: lbl.configure(
                text=f"{val:.2f}")
        )
        slider.set(standaard_drempel)
        slider.pack(side="right", padx=(4, 4))

        return {"naam": naam, "aan": var_aan, "slider": slider}

    def _opslaan(self):
        naam = self.naam_entry.get().strip()
        if not naam:
            messagebox.showwarning("Lege naam", "Geef de trigger een naam.",
                                   parent=self.v)
            return

        toets_invoer = self.toets_entry.get().strip().lower()
        toetsen = [t.strip() for t in toets_invoer.replace(" + ", "+").split("+")
                   if t.strip()]
        if not toetsen:
            messagebox.showwarning("Geen toets", "Voer een toets in.",
                                   parent=self.v)
            return

        blendshapes = {}
        for rij in self.rijen:
            if rij["aan"].get():
                blendshapes[rij["naam"]] = round(rij["slider"].get(), 3)

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
