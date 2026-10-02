"""
MimiControl Studio - Trigger Editor (CustomTkinter / Mennens.Tech branding)
Dialoog voor het samenstellen van blendshape-triggers
met checkboxes, sliders en toetsinvoer.
"""

import sys
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from blendshape_labels import (
    nl_label, is_ondersteund, groepen_voor_ui, namen_in_groepsvolgorde,
    suggestie_namen, MODEL_BEPERKING_TEKST, pieken_voor_trigger_menu,
)
from config_explorer import (
    laad_explorer_config, sla_explorer_config_op, voeg_trigger_toe
)
from toets_keuze import ToetsKiezer

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

        # Venster
        self.v = ctk.CTkToplevel(parent)
        self.v.title("Trigger samenstellen — Studio v2")
        self.v.configure(fg_color=BG)
        self.v.resizable(True, True)
        self.v.minsize(760, 520)
        self.v.grab_set()
        self.v.transient(parent)

        try:
            sw = parent.winfo_screenwidth()
            sh = parent.winfo_screenheight()
        except Exception:
            sw, sh = 1920, 1080
        breedte = min(960, max(760, int(sw * 0.5)))
        hoogte = min(820, max(560, int(sh * 0.78)))
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

        # --- Naam ---
        naam_rij = ctk.CTkFrame(body, fg_color="transparent")
        naam_rij.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(naam_rij, text="Naam:", font=(FONT, 12),
                     text_color=TEKST, width=52, anchor="w").pack(side="left")

        self.naam_entry = ctk.CTkEntry(
            naam_rij, font=(FONT, 13), width=280,
            corner_radius=10, border_width=1, border_color=RAND
        )
        self.naam_entry.pack(side="left", padx=(8, 0))
        default_naam = (bewerk_data["naam"] if bewerk_data
                        else f"Trigger {len(laad_explorer_config()['triggers']) + 1}")
        self.naam_entry.insert(0, default_naam)

        # --- Actie (toetskeuze met Nederlandse namen) ---
        actie_rij = ctk.CTkFrame(body, fg_color="transparent")
        actie_rij.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(actie_rij, text="Actie:", font=(FONT, 12),
                     text_color=TEKST, width=52, anchor="nw").pack(
                         side="left", anchor="n", pady=(6, 0))

        self.toets_kiezer = ToetsKiezer(
            actie_rij,
            toetsen=bewerk_data["toetsen"] if bewerk_data else ["space"],
            kleuren={
                "kaart": KAART, "tekst": TEKST, "tekst_licht": TEKST_LICHT,
                "accent": TEAL_BTN, "accent_hover": TEAL_HOVER, "rand": RAND,
            },
        )
        self.toets_kiezer.pack(side="left", fill="x", expand=True, padx=(8, 0))

        # --- Instructie ---
        ctk.CTkLabel(body,
                     text="Kies de gezichtsbewegingen en stel in hoe sterk je ze moet maken (drempel):",
                     font=(FONT, 11), text_color=TEKST_LICHT
                     ).pack(anchor="w", pady=(2, 2))
        ctk.CTkLabel(body,
                     text=MODEL_BEPERKING_TEKST,
                     font=(FONT, 11), text_color="#8A5A2A",
                     wraplength=720, justify="left",
                     ).pack(anchor="w", pady=(0, 8))

        # --- Kolomkoppen ---
        kop = ctk.CTkFrame(body, fg_color="transparent")
        kop.pack(fill="x", padx=6)
        ctk.CTkLabel(kop, text="", width=36).pack(side="left")
        ctk.CTkLabel(kop, text="Beweging", font=(FONT, 10),
                     text_color=TEKST_LICHT, width=180, anchor="w"
                     ).pack(side="left")
        ctk.CTkLabel(kop, text="Gemeten", font=(FONT, 10),
                     text_color=TEKST_LICHT, width=70).pack(side="left")
        ctk.CTkLabel(kop, text="Drempel", font=(FONT, 10),
                     text_color=TEKST_LICHT).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(kop, text="Waarde", font=(FONT, 10),
                     text_color=TEKST_LICHT, width=60).pack(side="right")

        # --- Blendshape rijen ---
        self.rijen = []
        bewerk_bs = bewerk_data["blendshapes"] if bewerk_data else {}
        lijst = ctk.CTkScrollableFrame(body, fg_color="transparent", corner_radius=0)
        lijst.pack(fill="both", expand=True, pady=(4, 0))

        for groep_naam, namen in self.groepen:
            ctk.CTkLabel(
                lijst, text=groep_naam, font=(FONT, 12, "bold"),
                text_color=DONKER, anchor="w"
            ).pack(fill="x", pady=(10, 2), padx=4)
            for naam in namen:
                piek = self.pieken.get(naam, 0.0)
                standaard_aan = (naam in bewerk_bs if bewerk_data
                                 else naam in self.voorgesteld)
                standaard_drempel = (bewerk_bs.get(naam, piek * 0.7) if bewerk_data
                                     else (piek * 0.7 if piek > 0 else 0.15))
                rij = self._maak_blendshape_rij(
                    lijst, naam, piek, standaard_aan, standaard_drempel
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

        toetsen = self.toets_kiezer.haal_toetsen()
        if not toetsen:
            messagebox.showwarning(
                "Geen actie",
                "Kies een actie uit de lijst of neem een toets op.",
                parent=self.v)
            return

        blendshapes = {}
        for rij in self.rijen:
            if rij["aan"].get() and is_ondersteund(rij["naam"]):
                blendshapes[rij["naam"]] = round(rij["slider"].get(), 3)

        if not blendshapes:
            messagebox.showwarning(
                "Geen selectie",
                "Vink minstens één gezichtsbeweging aan.",
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
