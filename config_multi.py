"""
MimiMultiControl - Configuratiebeheer voor meerdere triggers.
Elke trigger heeft een eigen naam, toets, en drempelwaarden.
"""

import json
import os
import copy

CONFIG_PAD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "config_multi.json"
)

STANDAARD_TRIGGER = {
    "naam": "Mimiek",
    "actief": False,
    "toetsen": ["space"],
    "drempelwaarden": {}
}

STANDAARD_CONFIG = {
    "triggers": [
        {"naam": "Mimiek 1", "actief": False,
         "toetsen": ["space"], "drempelwaarden": {}},
        {"naam": "Mimiek 2", "actief": False,
         "toetsen": ["enter"], "drempelwaarden": {}},
        {"naam": "Mimiek 3", "actief": False,
         "toetsen": ["escape"], "drempelwaarden": {}},
    ],
    "cooldown": 2.0,
    "vasthoud_tijd": 0.5
}


def laad_multi_config():
    """Laad de multi-trigger configuratie uit config_multi.json."""
    if os.path.exists(CONFIG_PAD):
        with open(CONFIG_PAD, 'r', encoding='utf-8') as f:
            config = json.load(f)
        if "cooldown" not in config:
            config["cooldown"] = 2.0
        if "vasthoud_tijd" not in config:
            config["vasthoud_tijd"] = 0.5
        return config
    return copy.deepcopy(STANDAARD_CONFIG)


def sla_multi_config_op(config):
    """Sla de multi-trigger configuratie op."""
    with open(CONFIG_PAD, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    print("  [OK] Multi-trigger configuratie opgeslagen.")


def aantal_actieve_triggers(config):
    """Tel hoeveel triggers gekalibreerd en actief zijn."""
    return sum(1 for t in config["triggers"] if t["actief"])
