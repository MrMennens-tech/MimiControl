"""
MimiExplorer - Explorer Modus
OpenCV-venster dat live alle blendshape-scores toont als balkjes.
De gebruiker kan een piek-opname doen en de resultaten doorsturen
naar de trigger-editor. Opname heeft geen vaste duur; de gebruiker
stopt zelf met SPATIE of ESC.
"""

import cv2
import time
import numpy as np

from blendshape_detectie import (
    maak_blendshape_landmarker, detecteer_blendshapes,
    teken_face_mesh_simpel, teken_blendshape_bars, nl_label
)

TOP_N = 5  # standaard aantal pieken dat gehighlight wordt

# ---------------------------------------------------------------------------
# Alle 52 ARKit blendshapes gegroepeerd (Nederlandse groepsnamen)
# ---------------------------------------------------------------------------
BLENDSHAPE_GROEPEN = [
    ("Mond", [
        "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
        "mouthPucker", "mouthLeft", "mouthRight",
        "mouthShrugUpper", "mouthShrugLower", "mouthClose", "mouthFunnel",
        "mouthDimpleLeft", "mouthDimpleRight", "mouthStretchLeft", "mouthStretchRight",
        "mouthRollUpper", "mouthRollLower", "mouthPressLeft", "mouthPressRight",
        "mouthUpperUpLeft", "mouthUpperUpRight", "mouthLowerDownLeft", "mouthLowerDownRight",
    ]),
    ("Ogen", [
        "eyeBlinkLeft", "eyeBlinkRight", "eyeWideLeft", "eyeWideRight",
        "eyeSquintLeft", "eyeSquintRight", "eyeLookUpLeft", "eyeLookUpRight",
        "eyeLookDownLeft", "eyeLookDownRight", "eyeLookInLeft", "eyeLookInRight",
        "eyeLookOutLeft", "eyeLookOutRight",
    ]),
    ("Wenkbrauwen", [
        "browDownLeft", "browDownRight", "browInnerUp",
        "browOuterUpLeft", "browOuterUpRight",
    ]),
    ("Kaak", ["jawOpen", "jawForward", "jawLeft", "jawRight"]),
    ("Tong", ["tongueOut"]),
    ("Wang", ["cheekPuff", "cheekSquintLeft", "cheekSquintRight"]),
    ("Neus", ["noseSneerLeft", "noseSneerRight"]),
]

STANDAARD_SELECTIE = {
    "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
    "mouthPucker", "mouthFunnel", "mouthClose",
    "eyeBlinkLeft", "eyeBlinkRight", "eyeWideLeft", "eyeWideRight",
    "eyeSquintLeft", "eyeSquintRight",
    "browDownLeft", "browDownRight", "browInnerUp",
    "browOuterUpLeft", "browOuterUpRight",
    "jawOpen", "tongueOut",
    "cheekPuff",
    "noseSneerLeft", "noseSneerRight",
}


# ---------------------------------------------------------------------------
# Blendshape selectie-dialoog (wordt getoond VOOR de webcam start)
# ---------------------------------------------------------------------------
def _toon_blendshape_selectie_vooraf():
    """
    CustomTkinter dialoog VOOR de webcam start.
    Gebruiker kiest welke blendshapes zichtbaar zijn in de Explorer.
    Retourneert een set van blendshape-namen, of None bij annuleren.
    """
    import customtkinter as ctk

    FONT = "Segoe UI"
    resultaat = {"selectie": None}

    venster = ctk.CTkToplevel()
    venster.title("Blendshape Selectie \u2014 MimiControl Studio")
    venster.geometry("520x650")
    venster.resizable(True, True)
    venster.configure(fg_color="#F2F2F7")
    venster.attributes("-topmost", True)
    venster.grab_set()

    header = ctk.CTkFrame(venster, fg_color="#062D36", corner_radius=0, height=56)
    header.pack(fill="x")
    header.pack_propagate(False)
    ctk.CTkLabel(
        header, text="Kies blendshapes om te tonen",
        font=(FONT, 16, "bold"), text_color="#FFFFFF"
    ).pack(pady=14)

    ctk.CTkLabel(
        venster,
        text="Selecteer welke gezichtsmetingen zichtbaar zijn in de Explorer.",
        font=(FONT, 11), text_color="#5A5A5E"
    ).pack(pady=(8, 4))

    scroll = ctk.CTkScrollableFrame(venster, fg_color="#F2F2F7", corner_radius=0)
    scroll.pack(fill="both", expand=True, padx=8, pady=4)

    checks = {}

    for groep_naam, bs_lijst in BLENDSHAPE_GROEPEN:
        groep_frame = ctk.CTkFrame(scroll, fg_color="#FFFFFF", corner_radius=10,
                                   border_width=1, border_color="#E5E5EA")
        groep_frame.pack(fill="x", padx=4, pady=4)

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

            ctk.CTkCheckBox(
                groep_frame, text=nl_label(bs_naam),
                font=(FONT, 11), variable=var,
                fg_color="#4DB8BE", hover_color="#3A9DA3",
                text_color="#1C1C1E",
                checkbox_width=18, checkbox_height=18
            ).pack(anchor="w", padx=20, pady=1)

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

    # Knoppen onderaan
    btn_frame = ctk.CTkFrame(venster, fg_color="#F2F2F7", height=56)
    btn_frame.pack(fill="x")
    btn_frame.pack_propagate(False)

    btn_inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
    btn_inner.pack(pady=10)

    def _bevestig():
        selectie = {naam for naam, var in checks.items() if var.get() == 1}
        resultaat["selectie"] = selectie if selectie else set(checks.keys())
        venster.destroy()

    def _alles_selecteren():
        for var in checks.values():
            var.set(1)

    def _annuleer():
        venster.destroy()

    ctk.CTkButton(
        btn_inner, text="Alle tonen", font=(FONT, 11),
        fg_color="#E5E5EA", hover_color="#D0D0D5", text_color="#1C1C1E",
        corner_radius=10, height=34, width=110, command=_alles_selecteren
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
# Filter-dialoog na piek-opname (bestaande functionaliteit)
# ---------------------------------------------------------------------------
def _toon_filter_dialoog(pieken, top_n=TOP_N):
    """
    CustomTkinter dialoog waarmee de gebruiker kiest welke blendshapes
    zichtbaar zijn (checkboxen) en hoeveel (top-N slider).
    Retourneert gefilterde pieken dict, of None bij annuleren.
    """
    import customtkinter as ctk

    gesorteerd = sorted(pieken.items(), key=lambda kv: kv[1], reverse=True)
    resultaat = {"pieken": None}

    venster = ctk.CTkToplevel()
    venster.title("Blendshape Filter")
    venster.geometry("480x560")
    venster.resizable(False, True)
    venster.configure(fg_color="#F2F2F7")
    venster.attributes("-topmost", True)
    venster.grab_set()

    FONT = "Segoe UI"

    ctk.CTkLabel(
        venster, text="Filter blendshapes",
        font=(FONT, 18, "bold"), text_color="#1C1C1E"
    ).pack(pady=(16, 4))

    ctk.CTkLabel(
        venster, text="Vink aan welke blendshapes je wilt behouden:",
        font=(FONT, 12), text_color="#5A5A5E"
    ).pack(pady=(0, 8))

    # Top-N slider
    top_frame = ctk.CTkFrame(venster, fg_color="#FFFFFF", corner_radius=10)
    top_frame.pack(fill="x", padx=20, pady=(0, 8))

    top_lbl = ctk.CTkLabel(
        top_frame, text=f"Toon top {top_n} meest actief",
        font=(FONT, 12, "bold"), text_color="#1C1C1E"
    )
    top_lbl.pack(side="left", padx=12, pady=8)

    def _on_top_n(val):
        n = int(val)
        top_lbl.configure(text=f"Toon top {n} meest actief")
        for idx, (naam, _) in enumerate(gesorteerd):
            checks[naam].set(1 if idx < n else 0)

    stappen = max(1, min(len(gesorteerd), 30) - 1)
    top_slider = ctk.CTkSlider(
        top_frame, from_=1, to=min(len(gesorteerd), 30),
        number_of_steps=stappen,
        button_color="#4DB8BE", button_hover_color="#3A9DA3",
        progress_color="#4DB8BE", command=_on_top_n
    )
    top_slider.set(min(top_n, len(gesorteerd)))
    top_slider.pack(side="right", padx=12, pady=8, fill="x", expand=True)

    # Scrollbaar lijst met checkboxen
    scroll = ctk.CTkScrollableFrame(
        venster, fg_color="#FFFFFF", corner_radius=10
    )
    scroll.pack(fill="both", expand=True, padx=20, pady=(0, 8))

    checks = {}
    for i, (naam, score) in enumerate(gesorteerd):
        var = ctk.IntVar(value=1 if i < top_n else 0)
        checks[naam] = var
        ctk.CTkCheckBox(
            scroll, text=f"{nl_label(naam)}  ({score:.3f})",
            font=(FONT, 11), variable=var,
            fg_color="#4DB8BE", hover_color="#3A9DA3",
            text_color="#1C1C1E"
        ).pack(anchor="w", padx=8, pady=2)

    # Knoppen
    btn_frame = ctk.CTkFrame(venster, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=(0, 16))

    def _bevestig():
        gefilterd = {n: s for n, s in pieken.items() if checks[n].get() == 1}
        resultaat["pieken"] = gefilterd if gefilterd else pieken
        venster.destroy()

    def _annuleer():
        venster.destroy()

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
    return resultaat["pieken"]


def start_explorer(top_n=TOP_N, camera_index=0):
    """
    Open de Explorer: webcam + live blendshape-bars.

    Returns:
        dict met piekwaarden als de gebruiker ENTER drukt,
        of None als de gebruiker Q drukt.
    """
    # Blendshape selectie-dialoog VOOR de webcam start
    selectie = _toon_blendshape_selectie_vooraf()
    if selectie is None:
        print("  [INFO] Blendshape selectie geannuleerd.")
        return None

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("  [!] Kan de webcam niet openen!")
        return None

    landmarker = maak_blendshape_landmarker(modus="video")
    ts = 0
    font = cv2.FONT_HERSHEY_SIMPLEX

    # State
    pieken = {}
    top_namen = set()
    opname_actief = False
    opname_start = 0.0
    heeft_pieken = False
    zichtbare_bs = selectie
    originele_selectie = selectie

    print("\n  === EXPLORER MODUS ===")
    print("  SPATIE  = Start piek-opname (onbeperkt)")
    print("  Tijdens opname: SPATIE/ESC = Stoppen")
    print("  ENTER   = Opslaan als trigger")
    print("  F       = Filter blendshapes (altijd beschikbaar)")
    print("  R       = Reset filter naar selectie")
    print("  Q       = Terug zonder opslaan\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        cam_h, cam_w = frame.shape[:2]

        # Breed canvas: webcam links, bars rechts
        bar_panel_w = 420
        canvas = np.zeros((cam_h, cam_w + bar_panel_w, 3), dtype=np.uint8)
        canvas[:, :cam_w] = frame

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ts += 33
        landmarks, scores = detecteer_blendshapes(landmarker, rgb, ts)

        if landmarks:
            teken_face_mesh_simpel(frame, landmarks)
        canvas[:, :cam_w] = frame

        # Piek-opname logica (onbeperkte duur, gebruiker stopt zelf)
        if opname_actief:
            verstreken = time.time() - opname_start

            # Verzamel pieken
            for naam, score in scores.items():
                if score > pieken.get(naam, 0):
                    pieken[naam] = score

            # REC indicator op webcam
            cv2.circle(canvas, (cam_w - 30, 30), 10, (0, 0, 255), -1)
            cv2.putText(canvas, f"REC {verstreken:.1f}s",
                        (cam_w - 130, 37), font, 0.6, (0, 0, 255), 2)

            # Hint om te stoppen - goed zichtbaar op webcam
            hint_tekst = "SPATIE of ESC = STOP"
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

        # Bars tekenen op het rechter panel (gefilterd indien actief)
        if scores:
            toon_scores = scores
            if zichtbare_bs is not None:
                toon_scores = {k: v for k, v in scores.items()
                               if k in zichtbare_bs}
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

        # Instructies bovenaan het bar-panel
        ix = cam_w + 10
        if opname_actief:
            cv2.putText(canvas, "OPNAME LOOPT... (SPATIE=stop)",
                        (ix, 25), font, 0.45, (0, 0, 255), 2)
        elif heeft_pieken:
            cv2.putText(canvas, "ENTER=trigger  SPATIE=opnieuw  F=filter",
                        (ix, 25), font, 0.38, (0, 255, 255), 1)
        else:
            cv2.putText(canvas, "SPATIE = piek-opname starten",
                        (ix, 25), font, 0.45, (200, 200, 200), 1)

        if not landmarks:
            cv2.putText(canvas, "Geen gezicht",
                        (10, 30), font, 0.65, (0, 0, 255), 2)

        cv2.imshow("MimiExplorer (Q=sluiten)", canvas)

        key = cv2.waitKey(1) & 0xFF

        # SPATIE of ESC stopt de opname als die actief is
        if opname_actief and key in (ord(' '), 27):
            opname_actief = False
            heeft_pieken = True
            gesorteerd = sorted(pieken.items(),
                                key=lambda kv: kv[1], reverse=True)
            top_namen = {naam for naam, _ in gesorteerd[:top_n]}
            print(f"  [OK] Piek-opname gestopt! Top {top_n}:")
            for naam, waarde in gesorteerd[:top_n]:
                print(f"    {nl_label(naam):30s} {waarde:.3f}")

        elif key == ord(' ') and not opname_actief:
            pieken = {}
            top_namen = set()
            heeft_pieken = False
            opname_actief = True
            opname_start = time.time()
            print("  [REC] Piek-opname gestart... Maak de uitdrukking! (SPATIE/ESC=stop)")

        elif key == ord('f') and not opname_actief:
            cv2.destroyAllWindows()
            brondata = pieken if heeft_pieken else (scores if scores else None)
            if brondata:
                gefilterd = _toon_filter_dialoog(brondata, top_n)
                if gefilterd is not None:
                    if heeft_pieken:
                        pieken = gefilterd
                        gesorteerd = sorted(pieken.items(),
                                            key=lambda kv: kv[1], reverse=True)
                        top_namen = {naam for naam, _ in gesorteerd[:top_n]}
                    zichtbare_bs = set(gefilterd.keys())
                    print(f"  [OK] Filter toegepast: {len(zichtbare_bs)} blendshapes zichtbaar")

        elif key == ord('r'):
            zichtbare_bs = set(originele_selectie)
            print("  [OK] Filter gereset naar selectie")

        elif key == 13 and heeft_pieken:  # ENTER
            cap.release()
            cv2.destroyAllWindows()
            landmarker.close()
            return pieken

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
    return None
