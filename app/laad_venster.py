"""
MimiControl Studio - Laadvenster
Klein venster dat zichtbaar blijft terwijl camera en gezichtsmodel laden,
zodat de gebruiker ziet dat de app bezig is en niet is vastgelopen.
"""

import sys

import customtkinter as ctk

BG          = "#F2F2F7"
DONKER      = "#062D36"
TEKST_LICHT = "#5A5A5E"
TEAL_BTN    = "#4DB8BE"
RAND        = "#E5E5EA"

FONT = "Segoe UI" if sys.platform == "win32" else "Helvetica"


class LaadVenster:
    """Toont een voortgangsvenster tijdens het starten van camera/model."""

    BREEDTE = 380
    HOOGTE = 170

    def __init__(self, parent, titel="Bezig met starten", tekst="Een moment…"):
        self.parent = parent
        self.venster = ctk.CTkToplevel(parent)
        self.venster.title(titel)
        self.venster.configure(fg_color=BG)
        self.venster.resizable(False, False)
        self.venster.transient(parent)
        self.venster.attributes("-topmost", True)
        self.venster.protocol("WM_DELETE_WINDOW", lambda: None)
        self._plaats_venster()

        ctk.CTkLabel(
            self.venster, text=titel,
            font=(FONT, 16, "bold"), text_color=DONKER,
        ).pack(pady=(30, 8))

        self.status_label = ctk.CTkLabel(
            self.venster, text=tekst,
            font=(FONT, 13), text_color=TEKST_LICHT,
        )
        self.status_label.pack(pady=(0, 18))

        self.balk = ctk.CTkProgressBar(
            self.venster, width=280, height=8,
            progress_color=TEAL_BTN, fg_color=RAND,
        )
        self.balk.pack()
        self.balk.set(0.15)

        self._verversen()

    def _plaats_venster(self):
        try:
            self.parent.update_idletasks()
            x = self.parent.winfo_x() + max(
                0, (self.parent.winfo_width() - self.BREEDTE) // 2)
            y = self.parent.winfo_y() + max(
                0, (self.parent.winfo_height() - self.HOOGTE) // 2)
            self.venster.geometry(f"{self.BREEDTE}x{self.HOOGTE}+{x}+{y}")
        except Exception:
            self.venster.geometry(f"{self.BREEDTE}x{self.HOOGTE}")

    def status(self, tekst, voortgang=None):
        """Werk de statustekst bij en forceer een herteken-actie."""
        try:
            self.status_label.configure(text=tekst)
            if voortgang is not None:
                self.balk.set(voortgang)
            self._verversen()
        except Exception:
            pass

    def sluit(self):
        try:
            if self.venster.winfo_exists():
                self.venster.grab_release()
                self.venster.destroy()
        except Exception:
            pass

    def _verversen(self):
        """Teken direct opnieuw; de GUI-thread blokkeert straks tijdens het laden."""
        try:
            self.venster.lift()
            self.venster.update_idletasks()
            self.venster.update()
        except Exception:
            pass
