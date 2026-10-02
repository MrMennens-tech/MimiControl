"""
MimiMultiControl - Grafische interface voor meerdere triggers.
Elke mimiek heeft een eigen kaart met kalibratie-knop en toets-instelling.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont

from config_multi import laad_multi_config, sla_multi_config_op, aantal_actieve_triggers
from calibratie_multi import calibreer_trigger
from live_modus_multi import start_live_multi

# ---------------------------------------------------------------------------
# Kleurenpalet
# ---------------------------------------------------------------------------
PRIMAIR = "#00897B"
INDIGO = "#5C6BC0"
GROEN = "#43A047"
ORANJE = "#FF9800"
ROOD = "#E53935"
BLAUW = "#1E88E5"

ACHTERGROND = "#ECEFF1"
KAART = "#FFFFFF"
RAND = "#CFD8DC"
TEKST = "#37474F"
TEKST_LICHT = "#78909C"
WIT = "#FFFFFF"

SLOT_KLEUREN = [PRIMAIR, INDIGO, ORANJE]

SNELKEUZES = [
    "space", "enter", "tab", "escape", "backspace",
    "up", "down", "left", "right",
    "f1", "f2", "f3", "f4", "f5",
    "a", "b", "c", "d", "e",
]


def _donkerder(hex_kleur, factor=0.82):
    r = int(int(hex_kleur[1:3], 16) * factor)
    g = int(int(hex_kleur[3:5], 16) * factor)
    b = int(int(hex_kleur[5:7], 16) * factor)
    return f"#{min(r,255):02x}{min(g,255):02x}{min(b,255):02x}"


class MimiMultiApp:
    """Hoofdvenster van MimiMultiControl."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MimiMultiControl")
        self.root.configure(bg=ACHTERGROND)
        self.root.resizable(False, False)

        if sys.platform == "win32":
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

        breedte, hoogte = 520, 760
        self.root.update_idletasks()
        sx = (self.root.winfo_screenwidth() - breedte) // 2
        sy = (self.root.winfo_screenheight() - hoogte) // 2
        self.root.geometry(f"{breedte}x{hoogte}+{sx}+{sy}")

        sf = "Segoe UI" if sys.platform == "win32" else "Helvetica"
        self.f_titel = tkfont.Font(family=sf, size=18, weight="bold")
        self.f_sub = tkfont.Font(family=sf, size=9)
        self.f_kaart_titel = tkfont.Font(family=sf, size=12, weight="bold")
        self.f_label = tkfont.Font(family=sf, size=9)
        self.f_waarde = tkfont.Font(family=sf, size=10, weight="bold")
        self.f_knop = tkfont.Font(family=sf, size=10, weight="bold")
        self.f_groot_knop = tkfont.Font(family=sf, size=13, weight="bold")

        self.trigger_widgets = []
        self._bouw_interface()
        self._ververs()

    # ---- Layout ----

    def _bouw_interface(self):
        # Header
        header = tk.Frame(self.root, bg=PRIMAIR, height=85)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="MimiMultiControl",
                 font=self.f_titel, bg=PRIMAIR, fg=WIT).pack(pady=(16, 0))
        tk.Label(header, text="Meerdere gezichtsuitdrukkingen, meerdere acties",
                 font=self.f_sub, bg=PRIMAIR, fg="#B2DFDB").pack(pady=(2, 0))

        # Trigger-kaarten
        kaarten_frame = tk.Frame(self.root, bg=ACHTERGROND)
        kaarten_frame.pack(fill="x", padx=18, pady=(14, 0))

        config = laad_multi_config()
        for i, trigger in enumerate(config["triggers"]):
            kaart = self._maak_trigger_kaart(kaarten_frame, i, trigger)
            self.trigger_widgets.append(kaart)

        # Instellingen
        ttk.Separator(self.root, orient="horizontal").pack(
            fill="x", padx=18, pady=(14, 6))

        inst_frame = tk.Frame(self.root, bg=ACHTERGROND)
        inst_frame.pack(fill="x", padx=22)

        tk.Label(inst_frame, text="Cooldown:", font=self.f_label,
                 bg=ACHTERGROND, fg=TEKST_LICHT).pack(side="left")
        self.cd_var = tk.StringVar(value=str(config["cooldown"]))
        ttk.Entry(inst_frame, textvariable=self.cd_var,
                  font=self.f_label, width=5).pack(side="left", padx=(2, 10))
        tk.Label(inst_frame, text="s", font=self.f_label,
                 bg=ACHTERGROND, fg=TEKST_LICHT).pack(side="left", padx=(0, 16))

        tk.Label(inst_frame, text="Vasthoudtijd:", font=self.f_label,
                 bg=ACHTERGROND, fg=TEKST_LICHT).pack(side="left")
        self.vh_var = tk.StringVar(value=str(config["vasthoud_tijd"]))
        ttk.Entry(inst_frame, textvariable=self.vh_var,
                  font=self.f_label, width=5).pack(side="left", padx=(2, 10))
        tk.Label(inst_frame, text="s", font=self.f_label,
                 bg=ACHTERGROND, fg=TEKST_LICHT).pack(side="left")

        tk.Button(inst_frame, text="Opslaan", font=self.f_label,
                  bg=RAND, fg=TEKST, relief="flat", padx=8, cursor="hand2",
                  command=self._sla_timing_op).pack(side="right")

        # Live-knop
        live_frame = tk.Frame(self.root, bg=ACHTERGROND)
        live_frame.pack(fill="x", padx=18, pady=(14, 16))

        live_btn = tk.Frame(live_frame, bg=GROEN, cursor="hand2")
        live_btn.pack(fill="x", ipady=10)
        live_lbl = tk.Label(live_btn, text="Live besturing starten",
                            font=self.f_groot_knop, bg=GROEN, fg=WIT,
                            cursor="hand2")
        live_lbl.pack(pady=4)

        hover = _donkerder(GROEN)
        for w in (live_btn, live_lbl):
            w.bind("<Enter>", lambda _e, f=live_btn, l=live_lbl, h=hover:
                   (f.config(bg=h), l.config(bg=h)))
            w.bind("<Leave>", lambda _e, f=live_btn, l=live_lbl, k=GROEN:
                   (f.config(bg=k), l.config(bg=k)))
            w.bind("<Button-1>", lambda _e: self._lanceer_live())

    def _maak_trigger_kaart(self, parent, index, trigger):
        """Maak een witte kaart voor één trigger-slot."""
        kleur = SLOT_KLEUREN[index % len(SLOT_KLEUREN)]
        widgets = {}

        # Buitenframe met gekleurde linkerrand
        outer = tk.Frame(parent, bg=kleur)
        outer.pack(fill="x", pady=5)

        kaart = tk.Frame(outer, bg=KAART,
                         highlightbackground=RAND, highlightthickness=1)
        kaart.pack(fill="x", padx=(4, 0), ipady=6)

        # Titel-rij
        titel_rij = tk.Frame(kaart, bg=KAART)
        titel_rij.pack(fill="x", padx=12, pady=(8, 2))

        widgets["naam"] = tk.Label(
            titel_rij, text=trigger["naam"],
            font=self.f_kaart_titel, bg=KAART, fg=kleur)
        widgets["naam"].pack(side="left")

        widgets["status"] = tk.Label(
            titel_rij, text="", font=self.f_label, bg=KAART)
        widgets["status"].pack(side="right")

        # Info-rij
        info_rij = tk.Frame(kaart, bg=KAART)
        info_rij.pack(fill="x", padx=12, pady=2)

        tk.Label(info_rij, text="Toets:", font=self.f_label,
                 bg=KAART, fg=TEKST_LICHT).pack(side="left")
        widgets["toets"] = tk.Label(
            info_rij, text="", font=self.f_waarde, bg=KAART, fg=TEKST)
        widgets["toets"].pack(side="left", padx=(4, 16))

        widgets["metingen"] = tk.Label(
            info_rij, text="", font=self.f_label, bg=KAART, fg=TEKST_LICHT)
        widgets["metingen"].pack(side="left")

        # Knoppen-rij
        knop_rij = tk.Frame(kaart, bg=KAART)
        knop_rij.pack(fill="x", padx=12, pady=(4, 8))

        tk.Button(knop_rij, text="Kalibreren", font=self.f_knop,
                  bg=kleur, fg=WIT, relief="flat", padx=12, pady=3,
                  cursor="hand2",
                  command=lambda idx=index: self._kalibreer(idx)
                  ).pack(side="left", padx=(0, 6))

        tk.Button(knop_rij, text="Toets wijzigen", font=self.f_knop,
                  bg=RAND, fg=TEKST, relief="flat", padx=12, pady=3,
                  cursor="hand2",
                  command=lambda idx=index: self._wijzig_toets(idx)
                  ).pack(side="left")

        widgets["kaart"] = kaart
        widgets["kleur"] = kleur
        return widgets

    # ---- Data verversing ----

    def _ververs(self):
        """Lees config en update alle kaart-widgets."""
        config = laad_multi_config()
        for i, trigger in enumerate(config["triggers"]):
            w = self.trigger_widgets[i]
            toets = " + ".join(trigger["toetsen"]).upper()
            w["toets"].config(text=toets)

            if trigger["actief"] and trigger["drempelwaarden"]:
                metingen = ", ".join(trigger["drempelwaarden"].keys())
                w["status"].config(text="Gekalibreerd", fg=GROEN)
                w["metingen"].config(text=f"Metingen: {metingen}")
            else:
                w["status"].config(text="Niet gekalibreerd", fg=ROOD)
                w["metingen"].config(text="")

    # ---- Acties ----

    def _kalibreer(self, index):
        self.root.withdraw()
        self.root.update()
        calibreer_trigger(index)
        self._ververs()
        self.root.deiconify()

    def _lanceer_live(self):
        config = laad_multi_config()
        if aantal_actieve_triggers(config) == 0:
            messagebox.showwarning(
                "Geen triggers",
                "Kalibreer eerst minstens één mimiek\n"
                "voordat je de live besturing start.",
                parent=self.root)
            return
        self.root.withdraw()
        self.root.update()
        start_live_multi()
        self.root.deiconify()

    def _wijzig_toets(self, index):
        ToetsDialog(self.root, index, self._ververs)

    def _sla_timing_op(self):
        config = laad_multi_config()
        try:
            config["cooldown"] = max(0.1, round(float(self.cd_var.get()), 1))
            config["vasthoud_tijd"] = max(0.1, round(float(self.vh_var.get()), 1))
        except ValueError:
            messagebox.showwarning("Ongeldige waarde",
                                   "Voer een geldig getal in.",
                                   parent=self.root)
            return
        sla_multi_config_op(config)
        self.cd_var.set(str(config["cooldown"]))
        self.vh_var.set(str(config["vasthoud_tijd"]))

    # ---- Start ----

    def start(self):
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Toets-wijzig dialoog
# ---------------------------------------------------------------------------
class ToetsDialog:
    def __init__(self, parent, trigger_index, callback):
        self.index = trigger_index
        self.callback = callback
        self.config = laad_multi_config()
        trigger = self.config["triggers"][trigger_index]

        self.v = tk.Toplevel(parent)
        self.v.title(f"Toets — {trigger['naam']}")
        self.v.configure(bg=ACHTERGROND)
        self.v.resizable(False, False)
        self.v.grab_set()
        self.v.transient(parent)

        breedte, hoogte = 380, 200
        sx = parent.winfo_x() + (parent.winfo_width() - breedte) // 2
        sy = parent.winfo_y() + (parent.winfo_height() - hoogte) // 2
        self.v.geometry(f"{breedte}x{hoogte}+{sx}+{sy}")

        sf = "Segoe UI" if sys.platform == "win32" else "Helvetica"
        f_label = tkfont.Font(family=sf, size=10)
        f_input = tkfont.Font(family=sf, size=11)
        f_knop = tkfont.Font(family=sf, size=11, weight="bold")

        kleur = SLOT_KLEUREN[trigger_index % len(SLOT_KLEUREN)]
        header = tk.Frame(self.v, bg=kleur, height=45)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"Toets voor {trigger['naam']}",
                 font=tkfont.Font(family=sf, size=12, weight="bold"),
                 bg=kleur, fg=WIT).pack(pady=10)

        body = tk.Frame(self.v, bg=ACHTERGROND)
        body.pack(fill="both", expand=True, padx=20, pady=12)

        tk.Label(body, text="Toets of combinatie (bijv. space of ctrl+c):",
                 font=f_label, bg=ACHTERGROND, fg=TEKST).pack(anchor="w")

        rij = tk.Frame(body, bg=ACHTERGROND)
        rij.pack(fill="x", pady=(4, 12))

        self.toets_var = tk.StringVar(
            value=" + ".join(trigger["toetsen"]))
        ttk.Entry(rij, textvariable=self.toets_var,
                  font=f_input).pack(side="left", fill="x", expand=True)
        combo = ttk.Combobox(rij, values=SNELKEUZES, font=f_input,
                             width=10, state="readonly")
        combo.set("Snel...")
        combo.pack(side="right", padx=(6, 0))
        combo.bind("<<ComboboxSelected>>",
                   lambda _: self.toets_var.set(combo.get()))

        btn_rij = tk.Frame(body, bg=ACHTERGROND)
        btn_rij.pack(fill="x")
        tk.Button(btn_rij, text="Annuleren", font=f_knop,
                  bg=RAND, fg=TEKST, relief="flat", padx=14, pady=4,
                  command=self.v.destroy).pack(side="right", padx=(6, 0))
        tk.Button(btn_rij, text="Opslaan", font=f_knop,
                  bg=GROEN, fg=WIT, relief="flat", padx=14, pady=4,
                  command=self._opslaan).pack(side="right")

    def _opslaan(self):
        invoer = self.toets_var.get().strip().lower()
        if not invoer:
            return
        toetsen = [t.strip() for t in invoer.replace(" + ", "+").split("+")
                   if t.strip()]
        if not toetsen:
            return
        self.config["triggers"][self.index]["toetsen"] = toetsen
        sla_multi_config_op(self.config)
        self.callback()
        self.v.destroy()


# ---------------------------------------------------------------------------
def start_gui_multi():
    app = MimiMultiApp()
    app.start()


if __name__ == "__main__":
    start_gui_multi()
