"""
MimiControl - Grafische Gebruikersinterface
Een toegankelijke, overzichtelijke GUI zodat ook niet-technische
collega's de applicatie eenvoudig kunnen bedienen.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont

from config_beheer import laad_config, sla_config_op
from calibratie import kalibratie_via_video, kalibratie_via_webcam
from live_modus import start_live_modus

# ---------------------------------------------------------------------------
# Kleurenpalet
# ---------------------------------------------------------------------------
PRIMAIR = "#00897B"
PRIMAIR_DONKER = "#00695C"
INDIGO = "#5C6BC0"
GROEN = "#43A047"
ORANJE = "#FF9800"
ROOD = "#E53935"

ACHTERGROND = "#ECEFF1"
KAART = "#FFFFFF"
RAND = "#CFD8DC"
TEKST = "#37474F"
TEKST_LICHT = "#78909C"
WIT = "#FFFFFF"


def _donkerder(hex_kleur, factor=0.82):
    """Maak een hex-kleur donkerder (voor hover-effecten)."""
    r = int(int(hex_kleur[1:3], 16) * factor)
    g = int(int(hex_kleur[3:5], 16) * factor)
    b = int(int(hex_kleur[5:7], 16) * factor)
    return f"#{min(r,255):02x}{min(g,255):02x}{min(b,255):02x}"


# ---------------------------------------------------------------------------
# Hoofdvenster
# ---------------------------------------------------------------------------
class MimiControlApp:
    """Het hoofdvenster van MimiControl."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MimiControl")
        self.root.configure(bg=ACHTERGROND)
        self.root.resizable(False, False)

        # DPI-awareness op Windows zodat het venster scherp is
        if sys.platform == "win32":
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

        # Venster centreren — ruim genoeg voor alle inhoud
        breedte, hoogte = 500, 700
        self.root.update_idletasks()
        sx = (self.root.winfo_screenwidth() - breedte) // 2
        sy = (self.root.winfo_screenheight() - hoogte) // 2
        self.root.geometry(f"{breedte}x{hoogte}+{sx}+{sy}")

        # Fonts
        systeemfont = "Segoe UI" if sys.platform == "win32" else "Helvetica"
        self.f_titel = tkfont.Font(family=systeemfont, size=20, weight="bold")
        self.f_sub = tkfont.Font(family=systeemfont, size=10)
        self.f_knop = tkfont.Font(family=systeemfont, size=13, weight="bold")
        self.f_knop_desc = tkfont.Font(family=systeemfont, size=9)
        self.f_label = tkfont.Font(family=systeemfont, size=10)
        self.f_waarde = tkfont.Font(family=systeemfont, size=10, weight="bold")
        self.f_sectie = tkfont.Font(family=systeemfont, size=11, weight="bold")

        self._bouw_interface()
        self._update_status()

    # ---- Layout ----

    def _bouw_interface(self):
        # --- Header ---
        header = tk.Frame(self.root, bg=PRIMAIR, height=100)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="MimiControl",
                 font=self.f_titel, bg=PRIMAIR, fg=WIT).pack(pady=(20, 0))
        tk.Label(header, text="Gezichtsbesturing op maat",
                 font=self.f_sub, bg=PRIMAIR, fg="#B2DFDB").pack(pady=(2, 0))

        # --- Knoppen ---
        knoppen = tk.Frame(self.root, bg=ACHTERGROND)
        knoppen.pack(fill="x", padx=24, pady=(18, 0))

        self._maak_knop(knoppen, "Kalibreren",
                        "Analyseer een video of neem direct op via de webcam",
                        PRIMAIR, self._lanceer_kalibratie)

        self._maak_knop(knoppen, "Actie instellen",
                        "Kies welke toets of combinatie getriggerd wordt",
                        INDIGO, self._open_actie_dialog)

        self._maak_knop(knoppen, "Live besturing starten",
                        "Start de webcam en voer toetsacties uit",
                        GROEN, self._lanceer_live)

        # --- Scheidingslijn ---
        ttk.Separator(self.root, orient="horizontal").pack(
            fill="x", padx=24, pady=(18, 8))

        # --- Status ---
        tk.Label(self.root, text="Huidige instellingen",
                 font=self.f_sectie, bg=ACHTERGROND, fg=TEKST
                 ).pack(anchor="w", padx=26)

        self.status_kaart = tk.Frame(
            self.root, bg=KAART,
            highlightbackground=RAND, highlightthickness=1)
        self.status_kaart.pack(fill="x", padx=24, pady=(4, 16))

        self.lbl_breedte = self._status_rij("Drempel breedte")
        self.lbl_hoogte = self._status_rij("Drempel hoogte")
        self.lbl_toets = self._status_rij("Toets")
        self.lbl_cooldown = self._status_rij("Cooldown")
        self.lbl_vasthoud = self._status_rij("Vasthoudtijd")

        # Onderste padding in de kaart
        tk.Frame(self.status_kaart, bg=KAART, height=6).pack()

    # ---- Widget-helpers ----

    def _maak_knop(self, parent, tekst, beschrijving, kleur, commando):
        """Gekleurde kaart-knop met titel en beschrijving."""
        frame = tk.Frame(parent, bg=kleur, cursor="hand2")
        frame.pack(fill="x", pady=4, ipady=6)

        lbl_t = tk.Label(frame, text=tekst, font=self.f_knop,
                         bg=kleur, fg=WIT, cursor="hand2")
        lbl_t.pack(anchor="w", padx=16, pady=(6, 0))

        lbl_d = tk.Label(frame, text=beschrijving, font=self.f_knop_desc,
                         bg=kleur, fg="#E0E0E0", cursor="hand2")
        lbl_d.pack(anchor="w", padx=16, pady=(0, 6))

        hover = _donkerder(kleur)
        for w in (frame, lbl_t, lbl_d):
            w.bind("<Enter>", lambda _e, f=frame, a=lbl_t, b=lbl_d, h=hover:
                   (f.config(bg=h), a.config(bg=h), b.config(bg=h)))
            w.bind("<Leave>", lambda _e, f=frame, a=lbl_t, b=lbl_d, k=kleur:
                   (f.config(bg=k), a.config(bg=k), b.config(bg=k)))
            w.bind("<Button-1>", lambda _e, c=commando: c())

    def _status_rij(self, label_tekst):
        rij = tk.Frame(self.status_kaart, bg=KAART)
        rij.pack(fill="x", padx=16, pady=4)
        tk.Label(rij, text=label_tekst, font=self.f_label,
                 bg=KAART, fg=TEKST_LICHT, width=20, anchor="w").pack(side="left")
        waarde = tk.Label(rij, text="—", font=self.f_waarde,
                          bg=KAART, fg=TEKST, anchor="w")
        waarde.pack(side="left", fill="x")
        return waarde

    # ---- Status ----

    def _update_status(self):
        config = laad_config()
        b = config["drempelwaarde_breedte"]
        h = config["drempelwaarde_hoogte"]

        if b == 0 and h == 0:
            self.lbl_breedte.config(text="Niet gekalibreerd", fg=ROOD)
            self.lbl_hoogte.config(text="Niet gekalibreerd", fg=ROOD)
        else:
            self.lbl_breedte.config(text=f"{b:.4f}", fg=GROEN)
            self.lbl_hoogte.config(text=f"{h:.4f}", fg=GROEN)

        self.lbl_toets.config(
            text=" + ".join(config["toetsen"]).upper(), fg=TEKST)
        self.lbl_cooldown.config(text=f"{config['cooldown']}s", fg=TEKST)
        self.lbl_vasthoud.config(text=f"{config['vasthoud_tijd']}s", fg=TEKST)

    # ---- Acties ----

    def _lanceer_kalibratie(self):
        KalibratieKeuze(self.root, self._na_kalibratie)

    def _na_kalibratie(self):
        self._update_status()
        self.root.deiconify()

    def _lanceer_live(self):
        config = laad_config()
        if config["drempelwaarde_breedte"] == 0:
            messagebox.showwarning(
                "Niet gekalibreerd",
                "Voer eerst een kalibratie uit voordat je\n"
                "de live besturing kunt starten.",
                parent=self.root)
            return
        self.root.withdraw()
        self.root.update()
        start_live_modus()
        self._update_status()
        self.root.deiconify()

    def _open_actie_dialog(self):
        ActieDialog(self.root, self._update_status)

    # ---- Start ----

    def start(self):
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Kalibratiemethode-keuze
# ---------------------------------------------------------------------------
class KalibratieKeuze:
    """Klein dialoogvenster: 'Video importeren' of 'Direct opnemen'."""

    def __init__(self, parent, callback):
        self.parent = parent
        self.callback = callback

        self.venster = tk.Toplevel(parent)
        self.venster.title("Kalibratiemethode")
        self.venster.configure(bg=ACHTERGROND)
        self.venster.resizable(False, False)
        self.venster.grab_set()
        self.venster.transient(parent)

        breedte, hoogte = 380, 260
        sx = parent.winfo_x() + (parent.winfo_width() - breedte) // 2
        sy = parent.winfo_y() + (parent.winfo_height() - hoogte) // 2
        self.venster.geometry(f"{breedte}x{hoogte}+{sx}+{sy}")

        font_s = "Segoe UI" if sys.platform == "win32" else "Helvetica"
        f_titel = tkfont.Font(family=font_s, size=14, weight="bold")
        f_knop = tkfont.Font(family=font_s, size=12, weight="bold")
        f_desc = tkfont.Font(family=font_s, size=9)

        # Header
        header = tk.Frame(self.venster, bg=PRIMAIR, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Kies een methode",
                 font=f_titel, bg=PRIMAIR, fg=WIT).pack(pady=12)

        body = tk.Frame(self.venster, bg=ACHTERGROND)
        body.pack(fill="both", expand=True, padx=20, pady=15)

        # Knop: Video importeren
        btn_video = tk.Frame(body, bg="#1565C0", cursor="hand2")
        btn_video.pack(fill="x", pady=4, ipady=6)
        lbl_vt = tk.Label(btn_video, text="Video importeren",
                          font=f_knop, bg="#1565C0", fg=WIT, cursor="hand2")
        lbl_vt.pack(anchor="w", padx=14, pady=(4, 0))
        lbl_vd = tk.Label(btn_video, text="Analyseer een bestaand videobestand",
                          font=f_desc, bg="#1565C0", fg="#BBDEFB", cursor="hand2")
        lbl_vd.pack(anchor="w", padx=14, pady=(0, 4))
        for w in (btn_video, lbl_vt, lbl_vd):
            w.bind("<Button-1>", lambda _: self._kies("video"))

        # Knop: Direct opnemen
        btn_webcam = tk.Frame(body, bg=ORANJE, cursor="hand2")
        btn_webcam.pack(fill="x", pady=4, ipady=6)
        lbl_wt = tk.Label(btn_webcam, text="Direct opnemen",
                          font=f_knop, bg=ORANJE, fg=WIT, cursor="hand2")
        lbl_wt.pack(anchor="w", padx=14, pady=(4, 0))
        lbl_wd = tk.Label(btn_webcam, text="Neem direct op via de webcam",
                          font=f_desc, bg=ORANJE, fg="#FFF3E0", cursor="hand2")
        lbl_wd.pack(anchor="w", padx=14, pady=(0, 4))
        for w in (btn_webcam, lbl_wt, lbl_wd):
            w.bind("<Button-1>", lambda _: self._kies("webcam"))

    def _kies(self, methode):
        self.venster.destroy()
        self.parent.withdraw()
        self.parent.update()

        if methode == "video":
            kalibratie_via_video()
        else:
            kalibratie_via_webcam()

        self.callback()


# ---------------------------------------------------------------------------
# Actie-instellingen dialoog
# ---------------------------------------------------------------------------
class ActieDialog:
    """Popup voor het instellen van de toets, cooldown en vasthoudtijd."""

    SNELKEUZES = [
        "space", "enter", "tab", "escape", "backspace",
        "up", "down", "left", "right",
        "f1", "f2", "f3", "f4", "f5",
        "a", "b", "c", "d", "e",
    ]

    def __init__(self, parent, callback):
        self.callback = callback
        self.config = laad_config()

        self.venster = tk.Toplevel(parent)
        self.venster.title("Actie instellen")
        self.venster.configure(bg=ACHTERGROND)
        self.venster.resizable(False, False)
        self.venster.grab_set()
        self.venster.transient(parent)

        breedte, hoogte = 440, 400
        sx = parent.winfo_x() + (parent.winfo_width() - breedte) // 2
        sy = parent.winfo_y() + (parent.winfo_height() - hoogte) // 2
        self.venster.geometry(f"{breedte}x{hoogte}+{sx}+{sy}")

        font_s = "Segoe UI" if sys.platform == "win32" else "Helvetica"
        f_titel = tkfont.Font(family=font_s, size=14, weight="bold")
        f_label = tkfont.Font(family=font_s, size=10)
        f_input = tkfont.Font(family=font_s, size=11)
        f_knop = tkfont.Font(family=font_s, size=11, weight="bold")

        # Header
        header = tk.Frame(self.venster, bg=INDIGO, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Actie instellen",
                 font=f_titel, bg=INDIGO, fg=WIT).pack(pady=12)

        body = tk.Frame(self.venster, bg=ACHTERGROND)
        body.pack(fill="both", expand=True, padx=24, pady=15)

        # --- Toets ---
        tk.Label(body, text="Sneltoets  (bijv. space  of  ctrl+c)",
                 font=f_label, bg=ACHTERGROND, fg=TEKST).pack(anchor="w")

        toets_rij = tk.Frame(body, bg=ACHTERGROND)
        toets_rij.pack(fill="x", pady=(2, 12))

        self.toets_var = tk.StringVar(
            value=" + ".join(self.config.get("toetsen", ["space"])))
        self.toets_entry = ttk.Entry(
            toets_rij, textvariable=self.toets_var, font=f_input)
        self.toets_entry.pack(side="left", fill="x", expand=True)

        self.combo = ttk.Combobox(
            toets_rij, values=self.SNELKEUZES,
            font=f_input, width=12, state="readonly")
        self.combo.set("Snel kiezen")
        self.combo.pack(side="right", padx=(6, 0))
        self.combo.bind("<<ComboboxSelected>>", self._snelkeuze)

        # --- Cooldown ---
        tk.Label(body, text="Cooldown (seconden na een actie)",
                 font=f_label, bg=ACHTERGROND, fg=TEKST).pack(anchor="w")

        cd_rij = tk.Frame(body, bg=ACHTERGROND)
        cd_rij.pack(fill="x", pady=(2, 12))

        self.cd_var = tk.DoubleVar(value=self.config["cooldown"])
        ttk.Scale(cd_rij, from_=0.5, to=10.0,
                  variable=self.cd_var, orient="horizontal"
                  ).pack(side="left", fill="x", expand=True)
        self.cd_lbl = tk.Label(cd_rij, text=f"{self.cd_var.get():.1f}s",
                               font=f_input, bg=ACHTERGROND, fg=TEKST, width=5)
        self.cd_lbl.pack(side="right")
        self.cd_var.trace_add("write", self._sync_cd)

        # --- Vasthoudtijd ---
        tk.Label(body, text="Vasthoudtijd (trigger moet zolang worden vastgehouden)",
                 font=f_label, bg=ACHTERGROND, fg=TEKST).pack(anchor="w")

        vh_rij = tk.Frame(body, bg=ACHTERGROND)
        vh_rij.pack(fill="x", pady=(2, 12))

        self.vh_var = tk.DoubleVar(value=self.config["vasthoud_tijd"])
        ttk.Scale(vh_rij, from_=0.1, to=3.0,
                  variable=self.vh_var, orient="horizontal"
                  ).pack(side="left", fill="x", expand=True)
        self.vh_lbl = tk.Label(vh_rij, text=f"{self.vh_var.get():.1f}s",
                               font=f_input, bg=ACHTERGROND, fg=TEKST, width=5)
        self.vh_lbl.pack(side="right")
        self.vh_var.trace_add("write", self._sync_vh)

        # --- Knoppen ---
        btn_rij = tk.Frame(body, bg=ACHTERGROND)
        btn_rij.pack(fill="x", pady=(8, 0))

        tk.Button(btn_rij, text="Annuleren", font=f_knop,
                  bg=RAND, fg=TEKST, activebackground="#B0BEC5",
                  relief="flat", padx=18, pady=6, cursor="hand2",
                  command=self.venster.destroy).pack(side="right", padx=(6, 0))

        tk.Button(btn_rij, text="Opslaan", font=f_knop,
                  bg=GROEN, fg=WIT, activebackground="#2E7D32",
                  relief="flat", padx=18, pady=6, cursor="hand2",
                  command=self._opslaan).pack(side="right")

    # ---- Helpers ----

    def _snelkeuze(self, _event):
        gekozen = self.combo.get()
        if gekozen and gekozen != "Snel kiezen":
            self.toets_var.set(gekozen)

    def _sync_cd(self, *_):
        try:
            self.cd_lbl.config(text=f"{self.cd_var.get():.1f}s")
        except tk.TclError:
            pass

    def _sync_vh(self, *_):
        try:
            self.vh_lbl.config(text=f"{self.vh_var.get():.1f}s")
        except tk.TclError:
            pass

    def _opslaan(self):
        invoer = self.toets_var.get().strip().lower()
        if not invoer:
            messagebox.showwarning(
                "Lege invoer", "Voer een toets of combinatie in.",
                parent=self.venster)
            return

        toetsen = [t.strip() for t in invoer.replace(" + ", "+").split("+")
                   if t.strip()]
        if not toetsen:
            messagebox.showwarning(
                "Ongeldige invoer", "Geen geldige toetsen herkend.",
                parent=self.venster)
            return

        self.config["toetsen"] = toetsen
        self.config["cooldown"] = round(self.cd_var.get(), 1)
        self.config["vasthoud_tijd"] = round(self.vh_var.get(), 1)
        sla_config_op(self.config)

        self.callback()
        self.venster.destroy()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def start_gui():
    app = MimiControlApp()
    app.start()


if __name__ == "__main__":
    start_gui()
