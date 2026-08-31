"""
Nederlandse labels voor ARKit blendshapes.
Lichtgewicht module zonder MediaPipe/OpenCV — veilig bij GUI-startup.
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
    "mouthFunnel": "Mond trechter (tongbol)",
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

NIET_ONDERSTEUND = {
    "tongueOut",
}


def nl_label(naam):
    """Geef het Nederlandse label voor een blendshape, of de originele naam."""
    return NL_LABELS.get(naam, naam)
