"""
MimiControl Studio - Toetskeuze
Vertaalt tussen PyAutoGUI-toetsnamen ("space", "left") en Nederlandse
labels ("Spatie", "Pijl links"), en biedt een CustomTkinter-widget
waarmee je een actie kiest uit een lijst of opneemt via een toetsaanslag.
"""

import sys

import customtkinter as ctk

# ---------------------------------------------------------------------------
# Keuzelijst: Nederlands label -> PyAutoGUI-toetsnaam
# ---------------------------------------------------------------------------
TOETS_KEUZES = [
    ("Spatie", "space"),
    ("Enter", "enter"),
    ("Tab", "tab"),
    ("Escape", "esc"),
    ("Backspace", "backspace"),
    ("Delete", "delete"),
    ("Pijl links", "left"),
    ("Pijl rechts", "right"),
    ("Pijl omhoog", "up"),
    ("Pijl omlaag", "down"),
    ("Page Up", "pageup"),
    ("Page Down", "pagedown"),
    ("Home", "home"),
    ("End", "end"),
    ("Cijfer 1", "1"),
    ("Cijfer 2", "2"),
    ("Cijfer 3", "3"),
    ("Cijfer 4", "4"),
    ("Cijfer 5", "5"),
    ("Cijfer 6", "6"),
    ("Cijfer 7", "7"),
    ("Cijfer 8", "8"),
    ("Cijfer 9", "9"),
    ("Cijfer 0", "0"),
]

ANDERS_LABEL = "Anders / combinatie…"

# Extra labels voor weergave van toetsen die niet in de keuzelijst staan
EXTRA_LABELS = {
    "escape": "Escape",
    "return": "Enter",
    "pgup": "Page Up",
    "pgdn": "Page Down",
    "ctrl": "Ctrl",
    "ctrlleft": "Ctrl",
    "ctrlright": "Ctrl",
    "alt": "Alt",
    "shift": "Shift",
    "win": "Windows",
}

# Tkinter keysym -> PyAutoGUI-toetsnaam (voor het opnemen van een toets)
_KEYSYM_MAP = {
    "space": "space",
    "Return": "enter",
    "KP_Enter": "enter",
    "Escape": "esc",
    "BackSpace": "backspace",
    "Delete": "delete",
    "Tab": "tab",
    "Left": "left",
    "Right": "right",
    "Up": "up",
    "Down": "down",
    "Prior": "pageup",
    "Next": "pagedown",
    "Home": "home",
    "End": "end",
    "Insert": "insert",
}

FONT = "Segoe UI" if sys.platform == "win32" else "Helvetica"

_LABEL_PER_TOETS = {toets: label for label, toets in TOETS_KEUZES}
_TOETS_PER_LABEL = {label: toets for label, toets in TOETS_KEUZES}


def toets_label(toets):
    """Geef het Nederlandse label voor één PyAutoGUI-toetsnaam."""
    toets = toets.strip().lower()
    if toets in _LABEL_PER_TOETS:
        return _LABEL_PER_TOETS[toets]
    if toets in EXTRA_LABELS:
        return EXTRA_LABELS[toets]
    if len(toets) == 1:
        return toets.upper()
    if toets.startswith("f") and toets[1:].isdigit():
        return toets.upper()
    return toets.capitalize()


def label_voor_toetsen(toetsen):
    """Geef een leesbaar label voor een lijst toetsen, bijv. 'Ctrl + C'."""
    if not toetsen:
        return ""
    return " + ".join(toets_label(t) for t in toetsen)


def parse_toetsen(invoer):
    """Zet vrije invoer ('ctrl+c', 'space') om naar een lijst toetsnamen."""
    invoer = invoer.strip().lower()
    return [t.strip() for t in invoer.replace(" + ", "+").split("+") if t.strip()]


def keysym_naar_toets(event):
    """Zet een Tkinter key-event om naar een PyAutoGUI-toetsnaam."""
    keysym = event.keysym
    if keysym in _KEYSYM_MAP:
        return _KEYSYM_MAP[keysym]
    if keysym.startswith("F") and keysym[1:].isdigit():
        return keysym.lower()
    if keysym.startswith("KP_") and keysym[3:].isdigit():
        return keysym[3:]
    if len(keysym) == 1:
        return keysym.lower()
    if event.char and len(event.char) == 1 and event.char.isprintable():
        return event.char.lower()
    return None


class ToetsKiezer:
    """
    Widget om een actie te kiezen: dropdown met Nederlandse namen,
    een opnameknop voor willekeurige toetsen, en een vrij invoerveld
    voor combinaties zoals Ctrl + C.
    """

    def __init__(self, parent, toetsen=None, kleuren=None):
        k = kleuren or {}
        self.kaart = k.get("kaart", "#FFFFFF")
        self.tekst = k.get("tekst", "#1C1C1E")
        self.tekst_licht = k.get("tekst_licht", "#5A5A5E")
        self.accent = k.get("accent", "#4DB8BE")
        self.accent_hover = k.get("accent_hover", "#3A9DA3")
        self.rand = k.get("rand", "#E5E5EA")

        self.frame = ctk.CTkFrame(parent, fg_color="transparent")

        rij = ctk.CTkFrame(self.frame, fg_color="transparent")
        rij.pack(fill="x")

        labels = [label for label, _ in TOETS_KEUZES] + [ANDERS_LABEL]
        self.keuze_var = ctk.StringVar(value=labels[0])

        self.menu = ctk.CTkOptionMenu(
            rij, values=labels, variable=self.keuze_var,
            width=190, height=34, font=(FONT, 13),
            corner_radius=10,
            fg_color=self.kaart, text_color=self.tekst,
            button_color=self.accent, button_hover_color=self.accent_hover,
            dropdown_fg_color=self.kaart, dropdown_text_color=self.tekst,
            dropdown_hover_color=self.rand,
            command=self._op_keuze,
        )
        self.menu.pack(side="left")

        self.opname_btn = ctk.CTkButton(
            rij, text="Toets opnemen", width=130, height=34,
            font=(FONT, 12, "bold"), corner_radius=10, cursor="hand2",
            fg_color=self.accent, hover_color=self.accent_hover,
            command=self._start_opname,
        )
        self.opname_btn.pack(side="left", padx=(8, 0))

        # Vrij invoerveld (alleen zichtbaar bij "Anders / combinatie…")
        self.vrij_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.vrij_entry = ctk.CTkEntry(
            self.vrij_frame, font=(FONT, 13), width=190,
            corner_radius=10, border_width=1, border_color=self.rand,
            placeholder_text="bijv. ctrl+c",
        )
        self.vrij_entry.pack(side="left")
        ctk.CTkLabel(
            self.vrij_frame,
            text="Combineer met +  (ctrl+c, shift+tab)",
            font=(FONT, 11), text_color=self.tekst_licht,
        ).pack(side="left", padx=(8, 0))

        self.zet_toetsen(toetsen or ["space"])

    # ---- Publieke API ----

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
        return self

    def zet_toetsen(self, toetsen):
        """Vul de widget met een bestaande toetsconfiguratie."""
        toetsen = [t.strip().lower() for t in toetsen if t.strip()]
        if len(toetsen) == 1 and toetsen[0] in _LABEL_PER_TOETS:
            self.keuze_var.set(_LABEL_PER_TOETS[toetsen[0]])
            self._toon_vrij_veld(False)
            return

        self.keuze_var.set(ANDERS_LABEL)
        self.vrij_entry.delete(0, "end")
        self.vrij_entry.insert(0, "+".join(toetsen))
        self._toon_vrij_veld(True)

    def haal_toetsen(self):
        """Geef de gekozen toetsen als lijst, of None bij ongeldige invoer."""
        keuze = self.keuze_var.get()
        if keuze == ANDERS_LABEL:
            return parse_toetsen(self.vrij_entry.get()) or None
        toets = _TOETS_PER_LABEL.get(keuze)
        return [toets] if toets else None

    # ---- Intern ----

    def _op_keuze(self, keuze):
        self._toon_vrij_veld(keuze == ANDERS_LABEL)

    def _toon_vrij_veld(self, zichtbaar):
        if zichtbaar:
            self.vrij_frame.pack(fill="x", pady=(8, 0))
        else:
            self.vrij_frame.pack_forget()

    def _start_opname(self):
        """Open een klein venster dat wacht op een toetsaanslag."""
        venster = ctk.CTkToplevel(self.frame)
        venster.title("Toets opnemen")
        venster.configure(fg_color=self.kaart)
        venster.resizable(False, False)
        venster.geometry("340x150")
        venster.transient(self.frame.winfo_toplevel())

        top = self.frame.winfo_toplevel()
        try:
            top.update_idletasks()
            x = top.winfo_x() + max(0, (top.winfo_width() - 340) // 2)
            y = top.winfo_y() + max(0, (top.winfo_height() - 150) // 2)
            venster.geometry(f"+{x}+{y}")
        except Exception:
            pass

        ctk.CTkLabel(
            venster, text="Druk nu op de toets die je wilt gebruiken",
            font=(FONT, 13, "bold"), text_color=self.tekst,
        ).pack(pady=(28, 6))
        ctk.CTkLabel(
            venster, text="Escape sluit dit venster zonder wijziging",
            font=(FONT, 11), text_color=self.tekst_licht,
        ).pack()

        def _op_toets(event):
            if event.keysym == "Escape":
                venster.destroy()
                return
            toets = keysym_naar_toets(event)
            if toets:
                self.zet_toetsen([toets])
            venster.destroy()

        venster.bind("<Key>", _op_toets)
        venster.after(120, lambda: (venster.lift(), venster.focus_force(),
                                    venster.grab_set()))
