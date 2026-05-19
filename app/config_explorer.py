"""
MimiExplorer - Configuratiebeheer
Laadt en bewaart triggers met blendshape-drempelwaarden.
Ondersteunt meerdere profielen (opgeslagen in profielen/ submap).
"""

import json
import os
import copy
import re

_APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PAD = os.path.join(_APP_DIR, "config_explorer.json")
PROFIELEN_MAP = os.path.join(_APP_DIR, "profielen")
ACTIEF_PROFIEL_PAD = os.path.join(PROFIELEN_MAP, "actief_profiel.txt")

STANDAARD_CONFIG = {
    "triggers": [],
    "cooldown": 2.0,
    "vasthoud_tijd": 0.5,
    "toets_duur_ms": 100,
    "camera_index": 0
}


def _zorg_voor_profielen_map():
    """Maak de profielen-map aan als die nog niet bestaat."""
    os.makedirs(PROFIELEN_MAP, exist_ok=True)


def _profiel_pad(naam):
    """Geef het bestandspad voor een profielnaam."""
    veilige_naam = re.sub(r'[^\w\s\-]', '', naam).strip().lower().replace(' ', '_')
    return os.path.join(PROFIELEN_MAP, f"profiel_{veilige_naam}.json")


def _migreer_als_nodig():
    """
    Migratie: als config_explorer.json bestaat maar er nog geen profielen zijn,
    kopieer de huidige config naar profiel_standaard.json en stel dat als actief in.
    """
    _zorg_voor_profielen_map()
    if lijst_profielen():
        return
    if os.path.exists(CONFIG_PAD):
        with open(CONFIG_PAD, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = copy.deepcopy(STANDAARD_CONFIG)
    sla_profiel_op("Standaard", config)
    _schrijf_actief_profiel("Standaard")


def _schrijf_actief_profiel(naam):
    """Schrijf het actieve profiel naar het meta-bestand."""
    _zorg_voor_profielen_map()
    with open(ACTIEF_PROFIEL_PAD, 'w', encoding='utf-8') as f:
        f.write(naam)


# ---------------------------------------------------------------------------
# Profielbeheer - publieke functies
# ---------------------------------------------------------------------------

def lijst_profielen():
    """Geef een lijst van beschikbare profielnamen."""
    _zorg_voor_profielen_map()
    profielen = []
    for bestand in sorted(os.listdir(PROFIELEN_MAP)):
        if bestand.startswith("profiel_") and bestand.endswith(".json"):
            with open(os.path.join(PROFIELEN_MAP, bestand), 'r', encoding='utf-8') as f:
                data = json.load(f)
            profielen.append(data.get("_profiel_naam", bestand[8:-5]))
    return profielen


def laad_profiel(naam):
    """Laad een specifiek profiel op naam. Geeft de config-dict terug."""
    pad = _profiel_pad(naam)
    if not os.path.exists(pad):
        return copy.deepcopy(STANDAARD_CONFIG)
    with open(pad, 'r', encoding='utf-8') as f:
        config = json.load(f)
    config.pop("_profiel_naam", None)
    return _vul_standaardwaarden(config)


def sla_profiel_op(naam, config):
    """Sla een profiel op onder de opgegeven naam."""
    _zorg_voor_profielen_map()
    pad = _profiel_pad(naam)
    opslag = copy.deepcopy(config)
    opslag["_profiel_naam"] = naam
    with open(pad, 'w', encoding='utf-8') as f:
        json.dump(opslag, f, indent=4, ensure_ascii=False)


def verwijder_profiel(naam):
    """Verwijder een profiel. Weigert als het het enige profiel is."""
    if len(lijst_profielen()) <= 1:
        return False
    pad = _profiel_pad(naam)
    if os.path.exists(pad):
        os.remove(pad)
    if actief_profiel() == naam:
        overige = lijst_profielen()
        if overige:
            wissel_profiel(overige[0])
    return True


def actief_profiel():
    """Geef de naam van het actieve profiel."""
    _migreer_als_nodig()
    if os.path.exists(ACTIEF_PROFIEL_PAD):
        with open(ACTIEF_PROFIEL_PAD, 'r', encoding='utf-8') as f:
            naam = f.read().strip()
        if naam and naam in lijst_profielen():
            return naam
    profielen = lijst_profielen()
    if profielen:
        _schrijf_actief_profiel(profielen[0])
        return profielen[0]
    return "Standaard"


def wissel_profiel(naam):
    """Stel het actieve profiel in en geef de config terug."""
    _migreer_als_nodig()
    _schrijf_actief_profiel(naam)
    return laad_profiel(naam)


# ---------------------------------------------------------------------------
# Bestaande interface - werkt nu op het actieve profiel
# ---------------------------------------------------------------------------

def _vul_standaardwaarden(config):
    """Vul ontbrekende standaardwaarden aan in een config-dict."""
    if "cooldown" not in config:
        config["cooldown"] = 2.0
    if "vasthoud_tijd" not in config:
        config["vasthoud_tijd"] = 0.5
    if "toets_duur_ms" not in config:
        config["toets_duur_ms"] = 100
    if "triggers" not in config:
        config["triggers"] = []
    if "camera_index" not in config:
        config["camera_index"] = 0
    return config


def laad_explorer_config():
    """Laad de configuratie van het actieve profiel."""
    _migreer_als_nodig()
    return laad_profiel(actief_profiel())


def sla_explorer_config_op(config):
    """Sla de configuratie op in het actieve profiel."""
    _migreer_als_nodig()
    sla_profiel_op(actief_profiel(), config)


def voeg_trigger_toe(naam, toetsen, blendshapes):
    """
    Voeg een nieuwe trigger toe.
    blendshapes: dict {naam: drempel}
    """
    config = laad_explorer_config()
    config["triggers"].append({
        "naam": naam,
        "toetsen": toetsen,
        "blendshapes": blendshapes
    })
    sla_explorer_config_op(config)
    return len(config["triggers"]) - 1


def verwijder_trigger(index):
    """Verwijder een trigger op basis van index."""
    config = laad_explorer_config()
    if 0 <= index < len(config["triggers"]):
        config["triggers"].pop(index)
        sla_explorer_config_op(config)


def update_trigger(index, naam=None, toetsen=None, blendshapes=None):
    """Werk een bestaande trigger bij."""
    config = laad_explorer_config()
    if 0 <= index < len(config["triggers"]):
        t = config["triggers"][index]
        if naam is not None:
            t["naam"] = naam
        if toetsen is not None:
            t["toetsen"] = toetsen
        if blendshapes is not None:
            t["blendshapes"] = blendshapes
        sla_explorer_config_op(config)
