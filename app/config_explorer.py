"""
MimiExplorer - Configuratiebeheer
Laadt en bewaart triggers met blendshape-drempelwaarden in config_explorer.json.
"""

import json
import os
import copy

CONFIG_PAD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "config_explorer.json"
)

STANDAARD_CONFIG = {
    "triggers": [],
    "cooldown": 2.0,
    "vasthoud_tijd": 0.5,
    "toets_duur_ms": 100,
    "camera_index": 0
}


def laad_explorer_config():
    """Laad de explorer-configuratie, of geef standaardwaarden."""
    if os.path.exists(CONFIG_PAD):
        with open(CONFIG_PAD, 'r', encoding='utf-8') as f:
            config = json.load(f)
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
    return copy.deepcopy(STANDAARD_CONFIG)


def sla_explorer_config_op(config):
    """Sla de explorer-configuratie op."""
    with open(CONFIG_PAD, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


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
