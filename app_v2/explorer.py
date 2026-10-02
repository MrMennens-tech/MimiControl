"""
MimiExplorer - Explorer Modus
OpenCV-venster dat live alle blendshape-scores toont als balkjes.
De gebruiker kan een piek-opname doen en de resultaten doorsturen
naar de trigger-editor. Opname heeft geen vaste duur; de gebruiker
stopt zelf met SPATIE of ESC.
"""

import cv2
import time
import traceback
import numpy as np

from paths import log_message
from config_explorer import laad_explorer_config
from blendshape_detectie import (
    maak_blendshape_landmarker, detecteer_blendshapes,
    teken_face_mesh_simpel, teken_blendshape_bars, nl_label,
    is_ondersteund, filter_ondersteund,
    naar_contiguous_beeld, veilig_imshow
)
from blendshape_labels import (
    groepen_voor_ui, namen_in_groepsvolgorde, scores_in_groepsvolgorde,
    pas_zichtbaar_filter_toe, pieken_voor_editor,
    STANDAARD_SELECTIE, PRESET_BOLLE_MOND, PRESET_TONG, PRESET_TONG_UITLEG,
    MODEL_BEPERKING_TEKST,
)

TOP_N = 5  # standaard aantal pieken dat gehighlight wordt


def _toon_fout(parent, titel, bericht):
    """Toon een foutmelding; GUI blijft open als parent gezet is."""
    try:
        from tkinter import messagebox
        messagebox.showerror(titel, bericht, parent=parent)
    except Exception:
        print(f"  [!] {titel}: {bericht}")


def _maak_ctk_dialoog(parent, titel, geometry, resizable=True):
    """CTkToplevel gekoppeld aan het hoofdvenster (voorkomt app-exit bij destroy)."""
    import customtkinter as ctk

    if parent is not None:
        venster = ctk.CTkToplevel(parent)
        venster.transient(parent)
    else:
        venster = ctk.CTkToplevel()

    venster.title(titel)
    venster.geometry(geometry)
    venster.resizable(resizable, resizable)
    venster.configure(fg_color="#F2F2F7")
    venster.attributes("-topmost", True)

    if parent is not None:
        try:
            parent.update_idletasks()
            pw, ph = parent.winfo_width(), parent.winfo_height()
            px, py = parent.winfo_x(), parent.winfo_y()
            breedte, rest = geometry.split("x", 1)
            hoogte = rest.split("+")[0]
            sx = px + max(0, (pw - int(breedte)) // 2)
            sy = py + max(0, (ph - int(hoogte)) // 2)
            venster.geometry(f"{breedte}x{hoogte}+{sx}+{sy}")
        except Exception:
            pass

    venster.lift()
    venster.focus_force()
    venster.grab_set()
    return venster


def _dialoog_maat(parent, gewenst_w, gewenst_h, min_w=560, min_h=480):
    """Schaal dialogen mee met het scherm (fase 3)."""
    try:
        sw = parent.winfo_screenwidth() if parent is not None else 1920
        sh = parent.winfo_screenheight() if parent is not None else 1080
    except Exception:
        sw, sh = 1920, 1080
    breedte = max(min_w, min(gewenst_w, int(sw * 0.72)))
    hoogte = max(min_h, min(gewenst_h, int(sh * 0.82)))
    return f"{breedte}x{hoogte}"


def _sluit_dialoog(venster):
    try:
        venster.grab_release()
    except Exception:
        pass
    venster.destroy()


# ---------------------------------------------------------------------------
# Blendshape selectie-dialoog (wordt getoond VOOR de webcam start)
# ---------------------------------------------------------------------------
def _toon_blendshape_selectie_vooraf(parent=None):
    """
    CustomTkinter dialoog VOOR de webcam start.
    Gebruiker kiest welke blendshapes zichtbaar zijn in de Explorer.
    Retourneert een set van blendshape-namen, of None bij annuleren.
    """
    import customtkinter as ctk

    FONT = "Segoe UI"
    resultaat = {"selectie": None}

    venster = _maak_ctk_dialoog(
        parent,
        "Gezichtsbewegingen kiezen \u2014 MimiControl Studio v2",
        _dialoog_maat(parent, 1000, 780, min_w=720, min_h=560),
    )

    header = ctk.CTkFrame(venster, fg_color="#062D36", corner_radius=0, height=56)
    header.pack(fill="x")
    header.pack_propagate(False)
    ctk.CTkLabel(
        header, text="Kies je gezichtsbewegingen",
        font=(FONT, 16, "bold"), text_color="#FFFFFF"
    ).pack(pady=14)

    ctk.CTkLabel(
        venster,
        text="Alleen de bewegingen die je aanvinkt worden getoond, gemeten en voorgesteld voor triggers.",
        font=(FONT, 11), text_color="#5A5A5E"
    ).pack(pady=(8, 2))
    ctk.CTkLabel(
        venster,
        text=MODEL_BEPERKING_TEKST,
        font=(FONT, 11), text_color="#8A5A2A",
        wraplength=720, justify="left",
    ).pack(pady=(0, 6), padx=16)

    scroll = ctk.CTkScrollableFrame(venster, fg_color="#F2F2F7", corner_radius=0)
    scroll.pack(fill="both", expand=True, padx=8, pady=4)

    grid_host = ctk.CTkFrame(scroll, fg_color="transparent")
    grid_host.pack(fill="both", expand=True)
    grid_host.grid_columnconfigure(0, weight=1)
    grid_host.grid_columnconfigure(1, weight=1)

    checks = {}

    for i, (groep_naam, bs_lijst) in enumerate(groepen_voor_ui()):
        groep_frame = ctk.CTkFrame(grid_host, fg_color="#FFFFFF", corner_radius=10,
                                   border_width=1, border_color="#E5E5EA")
        groep_frame.grid(row=i // 2, column=i % 2, sticky="nsew", padx=4, pady=4)

        groep_header = ctk.CTkFrame(groep_frame, fg_color="transparent")
        groep_header.pack(fill="x", padx=10, pady=(6, 2))

        ctk.CTkLabel(
            groep_header, text=groep_naam,
            font=(FONT, 13, "bold"), text_color="#1C1C1E"
        ).pack(side="left")

        groep_check_vars = []

        for bs_naam in bs_lijst:
            var = ctk.IntVar(value=1 if bs_naam in STANDAARD_SELECTIE else 0)
            checks[bs_naam] = var
            groep_check_vars.append(var)

            cb = ctk.CTkCheckBox(
                groep_frame, text=nl_label(bs_naam),
                font=(FONT, 11), variable=var,
                fg_color="#4DB8BE",
                hover_color="#3A9DA3",
                text_color="#1C1C1E",
                checkbox_width=18, checkbox_height=18
            )
            cb.pack(anchor="w", padx=20, pady=1)

        # Alles aan/uit knoppen per groep
        btn_rij = ctk.CTkFrame(groep_header, fg_color="transparent")
        btn_rij.pack(side="right")

        def _alles_aan(vars_=groep_check_vars):
            for v in vars_:
                v.set(1)

        def _alles_uit(vars_=groep_check_vars):
            for v in vars_:
                v.set(0)

        ctk.CTkButton(
            btn_rij, text="Alles", width=50, height=22,
            font=(FONT, 10), fg_color="#4DB8BE", hover_color="#3A9DA3",
            corner_radius=6, command=_alles_aan
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_rij, text="Geen", width=50, height=22,
            font=(FONT, 10), fg_color="#E5E5EA", hover_color="#D0D0D5",
            text_color="#1C1C1E", corner_radius=6, command=_alles_uit
        ).pack(side="left", padx=2)

        ctk.CTkFrame(groep_frame, fg_color="transparent", height=4).pack()

    # Voorinstellingen + uitleg (boven de knoppenbalk)
    preset_rij = ctk.CTkFrame(venster, fg_color="#F2F2F7")
    preset_rij.pack(fill="x", padx=16, pady=(4, 0))
    preset_uitleg = ctk.CTkLabel(
        venster, text="", font=(FONT, 11), text_color="#8A5A2A",
        wraplength=720, justify="left", anchor="w",
    )
    preset_uitleg.pack(fill="x", padx=16, pady=(2, 0))

    # Knoppen onderaan
    btn_frame = ctk.CTkFrame(venster, fg_color="#F2F2F7", height=56)
    btn_frame.pack(fill="x")
    btn_frame.pack_propagate(False)

    btn_inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
    btn_inner.pack(pady=10)

    def _bevestig():
        selectie = {naam for naam, var in checks.items()
                    if var.get() == 1 and is_ondersteund(naam)}
        if not selectie:
            # Niet stilletjes alles kiezen: laat de gebruiker er bewust een kiezen.
            try:
                from tkinter import messagebox
                messagebox.showinfo(
                    "Kies een beweging",
                    "Vink minstens één gezichtsbeweging aan, "
                    "of klik op 'Alles aanvinken'.",
                    parent=venster,
                )
            except Exception:
                pass
            return
        resultaat["selectie"] = selectie
        _sluit_dialoog(venster)

    def _alles_selecteren():
        for var in checks.values():
            var.set(1)

    def _alles_deselecteren():
        for var in checks.values():
            var.set(0)

    def _preset_bolle_mond():
        for naam, var in checks.items():
            var.set(1 if naam in PRESET_BOLLE_MOND else 0)
        preset_uitleg.configure(text="")

    def _preset_tong():
        for naam, var in checks.items():
            var.set(1 if naam in PRESET_TONG else 0)
        preset_uitleg.configure(text=PRESET_TONG_UITLEG)

    def _annuleer():
        resultaat["selectie"] = None
        _sluit_dialoog(venster)

    venster.protocol("WM_DELETE_WINDOW", _annuleer)

    ctk.CTkLabel(
        preset_rij, text="Snelle keuze:", font=(FONT, 11),
        text_color="#5A5A5E"
    ).pack(side="left", padx=(0, 6))
    ctk.CTkButton(
        preset_rij, text="Bolle mond / tuiten", font=(FONT, 11),
        fg_color="#FFE8A3", hover_color="#F5D56A", text_color="#1C1C1E",
        corner_radius=10, height=32, width=160, command=_preset_bolle_mond
    ).pack(side="left", padx=4)
    ctk.CTkButton(
        preset_rij, text="Tong uitsteken (benadering)", font=(FONT, 11),
        fg_color="#FFE8A3", hover_color="#F5D56A", text_color="#1C1C1E",
        corner_radius=10, height=32, width=210, command=_preset_tong
    ).pack(side="left", padx=4)

    ctk.CTkButton(
        btn_inner, text="Alles aanvinken", font=(FONT, 11),
        fg_color="#E5E5EA", hover_color="#D0D0D5", text_color="#1C1C1E",
        corner_radius=10, height=34, width=120, command=_alles_selecteren
    ).pack(side="left", padx=4)

    ctk.CTkButton(
        btn_inner, text="Alles uitvinken", font=(FONT, 11),
        fg_color="#E5E5EA", hover_color="#D0D0D5", text_color="#1C1C1E",
        corner_radius=10, height=34, width=120, command=_alles_deselecteren
    ).pack(side="left", padx=4)

    ctk.CTkButton(
        btn_inner, text="Toepassen", font=(FONT, 13, "bold"),
        fg_color="#4DB8BE", hover_color="#3A9DA3",
        corner_radius=10, height=34, width=120, command=_bevestig
    ).pack(side="left", padx=4)

    ctk.CTkButton(
        btn_inner, text="Annuleren", font=(FONT, 11),
        fg_color="#E05A50", hover_color="#C44840",
        corner_radius=10, height=34, width=100, command=_annuleer
    ).pack(side="left", padx=4)

    venster.wait_window()
    return resultaat["selectie"]


# ---------------------------------------------------------------------------
# Filter-dialoog (na piek-opname of tijdens het verkennen)
# ---------------------------------------------------------------------------
def _toon_filter_dialoog(scores, zichtbare_bs, originele_selectie=None,
                         parent=None):
    """
    CustomTkinter dialoog waarmee de gebruiker kiest welke gezichts-
    bewegingen (blendshapes) zichtbaar zijn. Toont ALLE ondersteunde shapes
    per groep: aanvinken voegt toe, uitvinken haalt weg.

    Args:
        scores: {naam: waarde} (piek of live score) voor de getoonde waarde.
        zichtbare_bs: huidige selectie (vooraf aangevinkt).
        originele_selectie: startselectie voor de knop "Startselectie".

    Retourneert de nieuwe selectie als set, of None bij annuleren
    (ook als niets is aangevinkt: er moet minstens één beweging blijven).
    """
    import customtkinter as ctk

    scores = scores or {}
    zichtbaar = set(zichtbare_bs or [])
    resultaat = {"selectie": None}

    venster = _maak_ctk_dialoog(
        parent, "Gezichtsbewegingen kiezen",
        _dialoog_maat(parent, 640, 760, min_w=520, min_h=520),
        resizable=True,
    )

    FONT = "Segoe UI"

    ctk.CTkLabel(
        venster, text="Welke gezichtsbewegingen wil je gebruiken?",
        font=(FONT, 18, "bold"), text_color="#1C1C1E"
    ).pack(pady=(16, 4))

    ctk.CTkLabel(
        venster,
        text=("Vink een beweging aan om hem toe te voegen, of uit om hem weg te halen. "
              "Staat er 0,000 achter een beweging die je net aanvinkt, "
              "dan is die niet opgenomen: neem dan opnieuw op."),
        font=(FONT, 12), text_color="#5A5A5E", wraplength=560, justify="left",
    ).pack(pady=(0, 8), padx=20)

    checks = {}

    def _zet_alles(waarde):
        for var in checks.values():
            var.set(waarde)

    def _zet_selectie(namen):
        namen = set(namen)
        for naam, var in checks.items():
            var.set(1 if naam in namen else 0)

    snel = ctk.CTkFrame(venster, fg_color="transparent")
    snel.pack(fill="x", padx=20, pady=(0, 6))
    for tekst, cmd in (
        ("Alles aan", lambda: _zet_alles(1)),
        ("Alles uit", lambda: _zet_alles(0)),
    ):
        ctk.CTkButton(
            snel, text=tekst, font=(FONT, 12), height=30, width=110,
            fg_color="#E5E5EA", hover_color="#D1D1D6", text_color="#1C1C1E",
            corner_radius=10, command=cmd
        ).pack(side="left", padx=(0, 8))
    if originele_selectie:
        ctk.CTkButton(
            snel, text="Startselectie", font=(FONT, 12), height=30, width=130,
            fg_color="#E5E5EA", hover_color="#D1D1D6", text_color="#1C1C1E",
            corner_radius=10, command=lambda: _zet_selectie(originele_selectie)
        ).pack(side="left")

    scroll = ctk.CTkScrollableFrame(
        venster, fg_color="#FFFFFF", corner_radius=10
    )
    scroll.pack(fill="both", expand=True, padx=20, pady=(0, 8))

    for groep_naam, namen in groepen_voor_ui():
        ctk.CTkLabel(
            scroll, text=groep_naam, font=(FONT, 12, "bold"),
            text_color="#1C1C1E", anchor="w"
        ).pack(fill="x", padx=8, pady=(10, 2))
        for naam in namen:
            var = ctk.IntVar(value=1 if naam in zichtbaar else 0)
            checks[naam] = var
            score = float(scores.get(naam, 0.0) or 0.0)
            ctk.CTkCheckBox(
                scroll, text=f"{nl_label(naam)}  ({score:.3f})",
                font=(FONT, 11), variable=var,
                fg_color="#4DB8BE", hover_color="#3A9DA3",
                text_color="#1C1C1E"
            ).pack(anchor="w", padx=8, pady=2)

    btn_frame = ctk.CTkFrame(venster, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=(0, 16))

    def _bevestig():
        gekozen = {n for n, v in checks.items() if v.get() == 1}
        resultaat["selectie"] = gekozen if gekozen else None
        _sluit_dialoog(venster)

    def _annuleer():
        resultaat["selectie"] = None
        _sluit_dialoog(venster)

    venster.protocol("WM_DELETE_WINDOW", _annuleer)

    ctk.CTkButton(
        btn_frame, text="Toepassen", font=(FONT, 13, "bold"),
        fg_color="#4DB8BE", hover_color="#3A9DA3",
        corner_radius=12, height=38, command=_bevestig
    ).pack(side="left", padx=(0, 8), expand=True, fill="x")

    ctk.CTkButton(
        btn_frame, text="Annuleren", font=(FONT, 13),
        fg_color="#E05A50", hover_color="#C44840",
        corner_radius=12, height=38, command=_annuleer
    ).pack(side="left", expand=True, fill="x")

    venster.wait_window()
    return resultaat["selectie"]


VENSTER_NAAM = "MimiExplorer (Q=sluiten)"
KNOPPEN_HOOGTE = 64
_KLEUR_TEAL = (190, 184, 77)    # BGR van #4DB8BE
_KLEUR_ROOD = (80, 90, 224)     # BGR van #E05A50
_KLEUR_GRIJS = (110, 108, 105)


def _knoppen_voor_staat(opname_actief, heeft_pieken, breedte, y_top):
    """Knoppen voor de huidige stap: [(actie, label, kleur, (x1,y1,x2,y2))].

    Elke knop heeft dezelfde werking als zijn sneltoets (tussen haakjes).
    """
    if opname_actief:
        defs = [("opname", "Opname stoppen  [spatie]", _KLEUR_ROOD)]
    elif heeft_pieken:
        defs = [
            ("maken", "Trigger maken  [enter]", _KLEUR_TEAL),
            ("opname", "Opnieuw opnemen  [spatie]", _KLEUR_GRIJS),
            ("filter", "Beweging kiezen  [f]", _KLEUR_GRIJS),
            ("sluiten", "Sluiten  [q]", _KLEUR_GRIJS),
        ]
    else:
        defs = [
            ("opname", "Opname starten  [spatie]", _KLEUR_TEAL),
            ("filter", "Beweging kiezen  [f]", _KLEUR_GRIJS),
            ("sluiten", "Sluiten  [q]", _KLEUR_GRIJS),
        ]
    marge = 12
    knop_w = min(430, (breedte - marge * (len(defs) + 1)) // len(defs))
    totaal = len(defs) * knop_w + (len(defs) - 1) * marge
    x = (breedte - totaal) // 2
    y1, y2 = y_top + 12, y_top + KNOPPEN_HOOGTE - 12
    knoppen = []
    for actie, label, kleur in defs:
        knoppen.append((actie, label, kleur, (x, y1, x + knop_w, y2)))
        x += knop_w + marge
    return knoppen


def _teken_knoppen(canvas, knoppen):
    font = cv2.FONT_HERSHEY_SIMPLEX
    for _, label, kleur, (x1, y1, x2, y2) in knoppen:
        cv2.rectangle(canvas, (x1, y1), (x2, y2), kleur, -1)
        tw, th = cv2.getTextSize(label, font, 0.6, 2)[0]
        cv2.putText(canvas, label,
                    (x1 + (x2 - x1 - tw) // 2, y1 + (y2 - y1 + th) // 2),
                    font, 0.6, (255, 255, 255), 2)


def _knop_onder(knoppen, pos):
    x, y = pos
    for actie, _, _, (x1, y1, x2, y2) in knoppen:
        if x1 <= x <= x2 and y1 <= y <= y2:
            return actie
    return None


_cursor_staat = {"hand": None}


def _zet_cursor(hand):
    """Pijl (standaard) of hand voor het OpenCV-venster; het kruisje van
    HighGUI is verwarrend boven knoppen. Alleen op Windows, nooit fataal."""
    if hand == _cursor_staat["hand"]:
        return
    try:
        import ctypes
        user32 = ctypes.windll.user32
        user32.LoadCursorW.restype = ctypes.c_void_p
        user32.SetClassLongPtrW.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
        user32.FindWindowW.restype = ctypes.c_void_p
        user32.FindWindowExW.restype = ctypes.c_void_p
        user32.FindWindowExW.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p]
        cursor = user32.LoadCursorW(None, 32649 if hand else 32512)
        top = user32.FindWindowW(None, VENSTER_NAAM)
        if not top:
            return
        kind = user32.FindWindowExW(top, None, None, None)
        for hwnd in (top, kind):
            if hwnd:
                user32.SetClassLongPtrW(hwnd, -12, cursor)  # GCLP_HCURSOR
        _cursor_staat["hand"] = hand
    except Exception:
        _cursor_staat["hand"] = hand  # niet blijven proberen


def _naar_canvas_coord(pos, canvas_w, canvas_h):
    """Zet muispositie in het (evt. geschaalde) venster om naar canvas-pixels."""
    try:
        _, _, w, h = cv2.getWindowImageRect(VENSTER_NAAM)
        if w > 0 and h > 0:
            return int(pos[0] * canvas_w / w), int(pos[1] * canvas_h / h)
    except Exception:
        pass
    return pos


def start_explorer(top_n=TOP_N, camera_index=0, parent=None,
                   laad_ui=None, on_gereed=None):
    """
    Open de Explorer: webcam + live blendshape-bars.

    Args:
        parent: CTk-hoofdvenster voor modale dialogen (verplicht vanuit GUI).
        laad_ui: optioneel laadvenster met .status(tekst) en .sluit().
        on_gereed: callback zonder argumenten, aangeroepen zodra het
                   webcamvenster opent. De GUI regelt dan zelf het verbergen.

    Returns:
        dict met piekwaarden als de gebruiker ENTER drukt,
        of None als de gebruiker Q drukt.
    """
    # Dialoog tonen terwijl het hoofdvenster nog zichtbaar is (niet withdrawen).
    selectie = _toon_blendshape_selectie_vooraf(parent)
    if selectie is None:
        print("  [INFO] Blendshape selectie geannuleerd.")
        return None

    try:
        mesh_volledig = bool(laad_explorer_config().get("mesh_volledig", False))
    except Exception:
        mesh_volledig = False

    def _status(tekst, voortgang=None):
        if laad_ui is not None:
            try:
                laad_ui.status(tekst, voortgang)
            except Exception:
                pass

    def _sluit_laad_ui():
        if laad_ui is not None:
            try:
                laad_ui.sluit()
            except Exception:
                pass

    withdrawn = False
    if parent is not None and on_gereed is None:
        try:
            parent.withdraw()
            parent.update()
            withdrawn = True
        except Exception:
            pass

    cap = None
    landmarker = None
    resultaat = None

    try:
        from live_modus_explorer import _open_webcam_robuust

        _status("Camera wordt gestart…", 0.35)
        cap, fout = _open_webcam_robuust(camera_index)
        if cap is None:
            melding = fout or "Kan de webcam niet openen. Controleer of geen andere app de camera gebruikt."
            print(f"  [!] {melding}")
            _sluit_laad_ui()
            _toon_fout(parent, "Webcam Fout — MimiControl Studio", melding)
            return None

        try:
            _status("Gezichtsmodel wordt geladen…", 0.7)
            landmarker = maak_blendshape_landmarker(modus="video")
        except Exception as exc:
            log_message(f"Landmarker kon niet starten:\n{traceback.format_exc()}")
            _sluit_laad_ui()
            _toon_fout(
                parent,
                "Model Fout — MimiControl Studio",
                f"Face Landmarker kon niet geladen worden:\n\n{exc}",
            )
            return None

        ts = 0
        font = cv2.FONT_HERSHEY_SIMPLEX

        # State
        pieken_alle = {}   # alle gemeten pieken (ook buiten het filter)
        pieken = {}        # gefilterd zicht op pieken_alle: wat de editor krijgt
        top_namen = set()
        opname_actief = False
        opname_start = 0.0
        heeft_pieken = False
        zichtbare_bs = set(filter_ondersteund(selectie))
        originele_selectie = set(zichtbare_bs)
        klik = {"pos": None}

        def _ververs_pieken():
            """Filter en favorieten opnieuw bepalen uit pieken_alle."""
            nonlocal pieken, top_namen
            pieken = pas_zichtbaar_filter_toe(pieken_alle, zichtbare_bs)
            gesorteerd_ = sorted(pieken.items(),
                                 key=lambda kv: kv[1], reverse=True)
            top_namen = {naam for naam, _ in gesorteerd_[:top_n]}

        def _muis(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONUP:
                klik["pos"] = (x, y)
            elif event == cv2.EVENT_MOUSEMOVE and klik.get("knoppen"):
                cw, ch = klik["afm"]
                pos = _naar_canvas_coord((x, y), cw, ch)
                _zet_cursor(_knop_onder(klik["knoppen"], pos) is not None)

        print("\n  === EXPLORER MODUS ===")
        print("  Knoppen onderin het venster, of sneltoetsen:")
        print("  SPATIE = opname starten/stoppen   ENTER = trigger maken")
        print("  F = beweging kiezen   R = startselectie   Q = sluiten\n")

        _status("Beeld wordt geopend…", 0.95)
        cv2.namedWindow(VENSTER_NAAM, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(VENSTER_NAAM, _muis)

        # Laadvenster sluiten en hoofdvenster verbergen zodra beeld start
        _sluit_laad_ui()
        if on_gereed is not None:
            try:
                on_gereed()
            except Exception:
                pass

        eerste_frame = True
        lege_frames = 0

        while True:
            ret, frame = cap.read()
            frame = naar_contiguous_beeld(frame) if ret else None
            if frame is None:
                lege_frames += 1
                if lege_frames > 45:
                    break
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue
            lege_frames = 0

            frame = cv2.flip(frame, 1)
            frame = naar_contiguous_beeld(frame)
            if frame is None:
                continue
            cam_h, cam_w = frame.shape[:2]
            if cam_h <= 0 or cam_w <= 0:
                continue

            # Breed canvas: webcam links, bars rechts
            bar_panel_w = 420
            canvas = np.zeros(
                (cam_h + KNOPPEN_HOOGTE, cam_w + bar_panel_w, 3), dtype=np.uint8
            )
            canvas[:cam_h, :cam_w] = frame
            # Subtiele achtergrond voor het bar-panel zodat het niet zwart is
            canvas[:cam_h, cam_w:] = (25, 25, 30)
            canvas[cam_h:, :] = (38, 38, 44)

            rgb = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            ts += 33
            landmarks, scores = detecteer_blendshapes(landmarker, rgb, ts)

            if landmarks:
                # Alleen visualisatie; blendshapes komen uit detecteer_blendshapes.
                teken_face_mesh_simpel(
                    frame, landmarks, volledig=mesh_volledig
                )
            canvas[:cam_h, :cam_w] = frame

            # Piek-opname logica (onbeperkte duur, gebruiker stopt zelf)
            if opname_actief:
                verstreken = time.time() - opname_start

                # Verzamel pieken van alle bruikbare shapes (geen dode model-
                # shapes). Het filter bepaalt later wat getoond/voorgesteld
                # wordt; zo kun je met "Beweging kiezen" er ook nog een
                # toevoegen met een echte piekwaarde.
                for naam, score in scores.items():
                    if not is_ondersteund(naam):
                        continue
                    if score > pieken_alle.get(naam, 0):
                        pieken_alle[naam] = score

                # REC indicator op webcam
                cv2.circle(canvas, (cam_w - 30, 30), 10, (0, 0, 255), -1)
                cv2.putText(canvas, f"REC {verstreken:.1f}s",
                            (cam_w - 130, 37), font, 0.6, (0, 0, 255), 2)

                # Hint om te stoppen - goed zichtbaar op webcam
                hint_tekst = "Klik STOP of druk SPATIE"
                tekst_grootte = cv2.getTextSize(hint_tekst, font, 0.7, 2)[0]
                hint_x = (cam_w - tekst_grootte[0]) // 2
                cv2.rectangle(canvas, (hint_x - 8, cam_h - 55),
                              (hint_x + tekst_grootte[0] + 8, cam_h - 25),
                              (0, 0, 0), -1)
                cv2.putText(canvas, hint_tekst,
                            (hint_x, cam_h - 32), font, 0.7, (0, 200, 255), 2)

                # Pulserende balk (geen einddoel want onbeperkte duur)
                puls = abs((verstreken % 2.0) - 1.0)
                bx = int(cam_w * 0.1)
                bw = int(cam_w * 0.8)
                by = cam_h - 18
                cv2.rectangle(canvas, (bx, by), (bx + bw, by + 10),
                              (50, 50, 50), -1)
                puls_breedte = int(bw * 0.3)
                puls_start = int((bw - puls_breedte) * puls)
                cv2.rectangle(canvas, (bx + puls_start, by),
                              (bx + puls_start + puls_breedte, by + 10),
                              (0, 0, 255), -1)

            # Bars tekenen op het rechter panel (nooit dode model-shapes)
            toon_scores = {
                k: v for k, v in (scores or {}).items()
                if k in zichtbare_bs and is_ondersteund(k)
            }
            if toon_scores:
                n_items = len(toon_scores)
                beschikbaar = cam_h - 60
                bh = max(8, min(14, beschikbaar // max(n_items, 1) - 4))
                teken_blendshape_bars(
                    canvas, toon_scores,
                    x_start=cam_w + 10, y_start=50,
                    bar_breedte=160, bar_hoogte=bh, max_items=n_items,
                    pieken=pieken if heeft_pieken else None,
                    top_n_namen=top_namen if heeft_pieken else None
                )
            else:
                # Nog geen bruikbare scores — labels van de selectie
                y_placeholder = 50
                for bs_naam in namen_in_groepsvolgorde(zichtbare_bs):
                    if not is_ondersteund(bs_naam):
                        continue
                    label = nl_label(bs_naam)
                    cv2.putText(canvas, label, (cam_w + 10, y_placeholder + 11),
                                font, 0.35, (80, 80, 80), 1)
                    bx = cam_w + 155
                    cv2.rectangle(canvas, (bx, y_placeholder),
                                  (bx + 160, y_placeholder + 14),
                                  (40, 40, 40), -1)
                    y_placeholder += 18

            # Verticale scheiding webcam / bar-panel
            cv2.line(canvas, (cam_w, 0), (cam_w, cam_h), (60, 60, 60), 2)

            # Instructies bovenaan het bar-panel
            ix = cam_w + 10
            if opname_actief:
                cv2.putText(canvas, "Opname loopt: maak je beweging",
                            (ix, 25), font, 0.5, (0, 0, 255), 2)
            elif heeft_pieken:
                cv2.putText(canvas, "Stap 2: klik Trigger maken",
                            (ix, 25), font, 0.5, (0, 255, 255), 1)
            else:
                cv2.putText(canvas, "Stap 1: klik Opname starten",
                            (ix, 25), font, 0.5, (200, 200, 200), 1)

            knoppen = _knoppen_voor_staat(
                opname_actief, heeft_pieken, canvas.shape[1], cam_h
            )
            _teken_knoppen(canvas, knoppen)
            klik["knoppen"] = knoppen
            klik["afm"] = (canvas.shape[1], canvas.shape[0])

            if not landmarks:
                cv2.putText(canvas, "Geen gezicht",
                            (10, 30), font, 0.65, (0, 0, 255), 2)

            if not veilig_imshow(VENSTER_NAAM, canvas):
                continue

            if eerste_frame:
                vis_h, vis_w = canvas.shape[:2]
                if vis_h > 0 and vis_w > 0:
                    cv2.resizeWindow(VENSTER_NAAM, vis_w, vis_h)
                _cursor_staat["hand"] = None
                _zet_cursor(False)
                eerste_frame = False

            key = cv2.waitKey(1) & 0xFF

            # Knopklik of sneltoets geven dezelfde actie
            actie = None
            if klik["pos"] is not None:
                pos = _naar_canvas_coord(
                    klik["pos"], canvas.shape[1], canvas.shape[0]
                )
                klik["pos"] = None
                actie = _knop_onder(knoppen, pos)
            if actie is None:
                if key == ord(' ') or (key == 27 and opname_actief):
                    actie = "opname"
                elif key == ord('f'):
                    actie = "filter"
                elif key == ord('r'):
                    actie = "reset"
                elif key == 13:
                    actie = "maken"
                elif key == ord('q'):
                    actie = "sluiten"

            if actie == "opname":
                if opname_actief:
                    opname_actief = False
                    heeft_pieken = True
                    _ververs_pieken()
                    gesorteerd = sorted(pieken.items(),
                                        key=lambda kv: kv[1], reverse=True)
                    print(f"  [OK] Piek-opname gestopt! Top {top_n}:")
                    for naam, waarde in gesorteerd[:top_n]:
                        print(f"    {nl_label(naam):30s} {waarde:.3f}")
                else:
                    pieken_alle = {}
                    pieken = {}
                    top_namen = set()
                    heeft_pieken = False
                    opname_actief = True
                    opname_start = time.time()
                    print("  [REC] Piek-opname gestart... Maak de uitdrukking!")

            elif actie == "filter" and not opname_actief:
                cv2.destroyAllWindows()
                bron = pieken_alle if heeft_pieken else (scores or {})
                nieuwe_selectie = _toon_filter_dialoog(
                    bron, zichtbare_bs, originele_selectie, parent=parent
                )
                if nieuwe_selectie is not None:
                    zichtbare_bs = set(filter_ondersteund(nieuwe_selectie))
                    if heeft_pieken:
                        _ververs_pieken()
                    print(f"  [OK] Selectie aangepast: "
                          f"{len(zichtbare_bs)} bewegingen")
                cv2.namedWindow(VENSTER_NAAM, cv2.WINDOW_NORMAL)
                cv2.setMouseCallback(VENSTER_NAAM, _muis)
                _cursor_staat["hand"] = None

            elif actie == "reset":
                zichtbare_bs = set(originele_selectie)
                if heeft_pieken and not opname_actief:
                    _ververs_pieken()
                print("  [OK] Selectie gereset naar startselectie")

            elif actie == "maken" and heeft_pieken and not opname_actief:
                resultaat = pieken_voor_editor(pieken_alle, zichtbare_bs)
                break

            elif actie == "sluiten":
                break

    except Exception as exc:
        log_message(f"Explorer crash:\n{traceback.format_exc()}")
        _sluit_laad_ui()
        _toon_fout(
            parent,
            "Explorer Fout — MimiControl Studio",
            f"De Explorer is onverwacht gestopt:\n\n{exc}",
        )
        return None
    finally:
        _sluit_laad_ui()
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        if landmarker is not None:
            try:
                landmarker.close()
            except Exception:
                pass
        if withdrawn and parent is not None:
            try:
                parent.deiconify()
                parent.lift()
            except Exception:
                pass

    return resultaat
