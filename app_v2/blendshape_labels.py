"""
Nederlandse labels voor ARKit blendshapes.
Lichtgewicht module zonder MediaPipe/OpenCV — veilig bij GUI-startup.

MediaPipe Face Landmarker (Blendshape V2) levert 52 categorieën:
`_neutral` + 51 ARKit-namen. `tongueOut` zit niet in het model.
`cheekPuff` en `cheekSquintLeft/Right` staan wél in de output-lijst
maar worden niet getraind (blijvend ~0). Zie:
https://github.com/google-ai-edge/mediapipe/issues/4403
https://github.com/google-ai-edge/mediapipe/issues/4436
https://github.com/google-ai-edge/mediapipe/issues/5329
"""

NL_LABELS = {
    "browDownLeft": "Wenkbrauw omlaag L",
    "browDownRight": "Wenkbrauw omlaag R",
    "browInnerUp": "Wenkbrauwen omhoog (binnen)",
    "browOuterUpLeft": "Wenkbrauw omhoog L",
    "browOuterUpRight": "Wenkbrauw omhoog R",
    "cheekPuff": "Wangen bol",
    "cheekSquintLeft": "Wang knijp L",
    "cheekSquintRight": "Wang knijp R",
    "eyeBlinkLeft": "Oogknip L",
    "eyeBlinkRight": "Oogknip R",
    "eyeLookDownLeft": "Blik omlaag L",
    "eyeLookDownRight": "Blik omlaag R",
    "eyeLookInLeft": "Blik naar binnen L",
    "eyeLookInRight": "Blik naar binnen R",
    "eyeLookOutLeft": "Blik naar buiten L",
    "eyeLookOutRight": "Blik naar buiten R",
    "eyeLookUpLeft": "Blik omhoog L",
    "eyeLookUpRight": "Blik omhoog R",
    "eyeSquintLeft": "Oog knijp L",
    "eyeSquintRight": "Oog knijp R",
    "eyeWideLeft": "Oog wijd L",
    "eyeWideRight": "Oog wijd R",
    "jawForward": "Kaak vooruit",
    "jawLeft": "Kaak links",
    "jawOpen": "Kaak open",
    "jawRight": "Kaak rechts",
    "mouthClose": "Mond dicht",
    "mouthDimpleLeft": "Mondkuiltje L",
    "mouthDimpleRight": "Mondkuiltje R",
    "mouthFrownLeft": "Mondhoek omlaag L",
    "mouthFrownRight": "Mondhoek omlaag R",
    "mouthFunnel": "Lip-trechter",
    "mouthLeft": "Mond naar links",
    "mouthLowerDownLeft": "Onderlip omlaag L",
    "mouthLowerDownRight": "Onderlip omlaag R",
    "mouthPressLeft": "Lipdruk L",
    "mouthPressRight": "Lipdruk R",
    "mouthPucker": "Lippen tuiten",
    "mouthRight": "Mond naar rechts",
    "mouthRollLower": "Onderlip rollen",
    "mouthRollUpper": "Bovenlip rollen",
    "mouthShrugLower": "Onderlip omhoog",
    "mouthShrugUpper": "Bovenlip omhoog",
    "mouthSmileLeft": "Lach links",
    "mouthSmileRight": "Lach rechts",
    "mouthStretchLeft": "Mond strekken L",
    "mouthStretchRight": "Mond strekken R",
    "mouthUpperUpLeft": "Bovenlip op L",
    "mouthUpperUpRight": "Bovenlip op R",
    "noseSneerLeft": "Neus optrekken L",
    "noseSneerRight": "Neus optrekken R",
    "tongueOut": "Tong uitsteken",
}

# Niet in de model-output (52 = _neutral + 51; tongueOut ontbreekt).
# Alleen deze namen worden weggelaten: ze zitten niet in de 52-lijst.
NIET_IN_MODEL = {
    "tongueOut",
}

# Wel in de output-lijst, maar BlendShapeV2 vult ze nooit (Google: not enabled).
# Niet stilletjes verbergen: tonen met waarde (vaak 0,00).
NOOIT_GEVULD = {
    "cheekPuff",
    "cheekSquintLeft",
    "cheekSquintRight",
}

# Alleen namen die het model niet levert. Wangen blijven zichtbaar.
NIET_ONDERSTEUND = set(NIET_IN_MODEL)


def is_ondersteund(naam):
    """True als de shape in de model-output kan zitten (niet _neutral / tongueOut)."""
    return naam not in NIET_ONDERSTEUND and naam != "_neutral"


def filter_ondersteund(scores_of_namen):
    """Houd alleen ondersteunde blendshapes over (dict of iterable van namen)."""
    if isinstance(scores_of_namen, dict):
        return {k: v for k, v in scores_of_namen.items() if is_ondersteund(k)}
    return [n for n in scores_of_namen if is_ondersteund(n)]


def nl_label(naam):
    """Geef het Nederlandse label voor een blendshape, of de originele naam."""
    return NL_LABELS.get(naam, naam)


# ---------------------------------------------------------------------------
# Groepen (explorer + trigger-editor delen dezelfde volgorde)
# Tuiten/trechter/druk staan vóór lach, zodat bolling niet achter hoeken verdwijnt.
# ---------------------------------------------------------------------------
BLENDSHAPE_GROEPEN = [
    ("Mond", [
        "mouthPucker", "mouthFunnel",
        "mouthPressLeft", "mouthPressRight",
        "mouthRollUpper", "mouthRollLower",
        "mouthClose",
        "mouthSmileLeft", "mouthSmileRight",
        "mouthFrownLeft", "mouthFrownRight",
        "mouthLeft", "mouthRight",
        "mouthShrugUpper", "mouthShrugLower",
        "mouthDimpleLeft", "mouthDimpleRight",
        "mouthStretchLeft", "mouthStretchRight",
        "mouthUpperUpLeft", "mouthUpperUpRight",
        "mouthLowerDownLeft", "mouthLowerDownRight",
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
    ("Wangen", ["cheekPuff", "cheekSquintLeft", "cheekSquintRight"]),
    ("Neus", ["noseSneerLeft", "noseSneerRight"]),
]

STANDAARD_SELECTIE = {
    "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
    "mouthPucker", "mouthFunnel", "mouthClose",
    "eyeBlinkLeft", "eyeBlinkRight", "eyeWideLeft", "eyeWideRight",
    "eyeSquintLeft", "eyeSquintRight",
    "browDownLeft", "browDownRight", "browInnerUp",
    "browOuterUpLeft", "browOuterUpRight",
    "jawOpen",
    "noseSneerLeft", "noseSneerRight",
}

# Preset voor mondbolling: tuiten/trechter/druk/rollen + kaak.
# Lach, mondhoeken, ogen en wenkbrauwen blijven uit.
PRESET_BOLLE_MOND = {
    "mouthPucker", "mouthFunnel",
    "mouthPressLeft", "mouthPressRight",
    "mouthRollUpper", "mouthRollLower",
    "mouthClose", "jawOpen",
}

# Tong uitsteken: het model meet de tong niet. Benadering = kaak open +
# lip-trechter; de gebruiker moet de drempels van beide zelf goed zetten.
PRESET_TONG = {"jawOpen", "mouthFunnel"}
PRESET_TONG_UITLEG = (
    "Tong uitsteken (benadering): dit is een combinatie van 'Kaak open' en "
    "'Lip-trechter'. Het model meet de tong niet echt, dus neem je beweging "
    "op en stel de drempels van beide goed in. Test het daarna even."
)

# Gereserveerde auto-suggestie als de piek hoog genoeg is (niet wegconcurreren
# door lach/hoeken met ruwe score 0,6–0,9).
BOLLING_NAMEN = (
    "mouthPucker", "mouthFunnel",
    "mouthPressLeft", "mouthPressRight",
    "mouthRollUpper", "mouthRollLower",
)
BOLLING_PIEK_DREMPEL = 0.10
SUGGESTIE_MAX = 3

MODEL_BEPERKING_TEKST = (
    "Tip: de tong kan niet los gemeten worden. Wil je op de tong reageren? "
    "Combineer dan 'Kaak open' met 'Lip-trechter'. "
    "Wangen staan er ook bij, maar geven vaak 0,00."
)


def groepen_voor_ui():
    """Groepen zonder shapes die het model niet levert (tongueOut)."""
    groepen = []
    for groep_naam, bs_lijst in BLENDSHAPE_GROEPEN:
        bruikbaar = filter_ondersteund(bs_lijst)
        if bruikbaar:
            groepen.append((groep_naam, bruikbaar))
    return groepen


def namen_in_groepsvolgorde(namen=None):
    """Namen in dezelfde groepsvolgorde als de explorer (subset of alles)."""
    toegestaan = None if namen is None else set(namen)
    gezien = set()
    resultaat = []
    for _, bs_lijst in groepen_voor_ui():
        for naam in bs_lijst:
            if toegestaan is not None and naam not in toegestaan:
                continue
            if naam not in gezien:
                resultaat.append(naam)
                gezien.add(naam)
    if toegestaan is not None:
        for naam in namen:
            if naam not in gezien and is_ondersteund(naam):
                resultaat.append(naam)
                gezien.add(naam)
    return resultaat


def groepen_voor_namen(namen):
    """[(groep, [namen]), ...] alleen groepen die in de subset voorkomen."""
    namen_set = set(namen or [])
    resultaat = []
    gezien = set()
    for groep_naam, bs_lijst in groepen_voor_ui():
        hit = [n for n in bs_lijst if n in namen_set]
        if hit:
            resultaat.append((groep_naam, hit))
            gezien.update(hit)
    rest = [n for n in namen_in_groepsvolgorde(namen_set) if n not in gezien]
    if rest:
        resultaat.append(("Overig", rest))
    return resultaat


def pas_zichtbaar_filter_toe(scores_of_namen, zichtbare_bs):
    """Houd alleen ondersteunde shapes die in het explorer-filter zitten."""
    if zichtbare_bs is None:
        return filter_ondersteund(scores_of_namen)
    zichtbaar = set(zichtbare_bs)
    if isinstance(scores_of_namen, dict):
        return {
            k: v for k, v in scores_of_namen.items()
            if is_ondersteund(k) and k in zichtbaar
        }
    return [
        n for n in scores_of_namen
        if is_ondersteund(n) and n in zichtbaar
    ]


def pieken_voor_editor(pieken, zichtbare_bs):
    """Filter-subset voor live-balken (kijkhulp); ontbrekende piek wordt 0.

    Niet gebruiken voor het trigger-keuzemenu — dat moet altijd alles tonen.
    """
    pieken = pieken or {}
    zichtbaar = set(filter_ondersteund(zichtbare_bs or []))
    return {
        naam: float(pieken.get(naam, 0.0) or 0.0)
        for naam in namen_in_groepsvolgorde(zichtbaar)
    }


def pieken_voor_trigger_menu(pieken, alleen_filter=False):
    """Blendshapes voor het trigger-menu; ontbrekende piek wordt 0,00.

    alleen_filter=True: alleen de meegegeven (door het explorer-filter
    gekozen) shapes, in groepsvolgorde. Anders alle bruikbare shapes.
    """
    pieken = pieken or {}
    if alleen_filter and pieken:
        return pieken_voor_editor(pieken, pieken.keys())
    return {
        naam: float(pieken.get(naam, 0.0) or 0.0)
        for naam in namen_in_groepsvolgorde()
    }


def scores_in_groepsvolgorde(scores):
    """Lijst (naam, score) in groepsvolgorde, geen score-sort."""
    scores = scores or {}
    return [
        (naam, scores.get(naam, 0.0))
        for naam in namen_in_groepsvolgorde(scores.keys())
    ]


def suggestie_namen(pieken, max_totaal=SUGGESTIE_MAX):
    """Welke shapes standaard aanvinken in de trigger-editor.

    Bolling (tuiten/trechter/druk/rollen) met piek ≥ 0,10 krijgt een
    gereserveerde slot en kan daardoor niet weggedrukt worden door lach.
    Overige slots vullen tot max_totaal op piek, zonder de gereserveerde
    namen te verdringen.
    """
    pieken = pieken or {}
    aan = []
    for naam in BOLLING_NAMEN:
        if pieken.get(naam, 0.0) >= BOLLING_PIEK_DREMPEL:
            aan.append(naam)
    gereserveerd = set(aan)
    if len(aan) < max_totaal:
        overig = sorted(
            ((n, p) for n, p in pieken.items() if n not in gereserveerd),
            key=lambda kv: kv[1],
            reverse=True,
        )
        for naam, piek in overig:
            if len(aan) >= max_totaal:
                break
            if piek > 0:
                aan.append(naam)
    return set(aan)


# Kleuren per trigger (index 0 = trigger 1). Overlay én dashboard gebruiken dezelfde set.
# 1 geel (huidige highlight), 2 roze, 3 oranje, daarna duidelijk onderscheidbaar.
TRIGGER_KLEUREN_HEX = [
    "#FFDC00",  # 1 geel
    "#FF5AB4",  # 2 roze
    "#FF8C1A",  # 3 oranje
    "#32C832",  # 4 groen
    "#1AA8FF",  # 5 blauw
    "#B44AFF",  # 6 paars
    "#FF3B30",  # 7 rood
    "#00C8B4",  # 8 turquoise
]
TRIGGER_KLEUREN_BGR = [
    (0, 220, 255),
    (180, 90, 255),
    (26, 140, 255),
    (50, 200, 50),
    (255, 168, 26),
    (255, 74, 180),
    (48, 59, 255),
    (180, 200, 0),
]
TRIGGER_KLEUR_NAMEN = [
    "geel", "roze", "oranje", "groen", "blauw", "paars", "rood", "turquoise",
]


def trigger_kleur_hex(index):
    return TRIGGER_KLEUREN_HEX[index % len(TRIGGER_KLEUREN_HEX)]


def trigger_kleur_bgr(index):
    return TRIGGER_KLEUREN_BGR[index % len(TRIGGER_KLEUREN_BGR)]
