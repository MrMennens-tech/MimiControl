"""
MimiControl - Configuratiebeheer
Laadt en bewaart alle instellingen in config.json.
"""

import json
import os

CONFIG_PAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

STANDAARD_CONFIG = {
    "drempelwaarde_breedte": 0.0,
    "drempelwaarde_hoogte": 0.0,
    "toetsen": ["space"],
    "cooldown": 2.0,
    "vasthoud_tijd": 0.5
}


def laad_config():
    """Laad configuratie uit config.json, of geef standaardwaarden terug."""
    if os.path.exists(CONFIG_PAD):
        with open(CONFIG_PAD, 'r', encoding='utf-8') as f:
            config = json.load(f)
        for sleutel, waarde in STANDAARD_CONFIG.items():
            if sleutel not in config:
                config[sleutel] = waarde
        return config
    return STANDAARD_CONFIG.copy()


def sla_config_op(config):
    """Sla de huidige configuratie op naar config.json."""
    with open(CONFIG_PAD, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    print(f"  [OK] Configuratie opgeslagen in config.json")


def toon_config():
    """Print de huidige configuratie naar de terminal."""
    config = laad_config()
    print("\n  --- Huidige Configuratie ---")
    print(f"  Drempelwaarde breedte : {config['drempelwaarde_breedte']:.4f}")
    print(f"  Drempelwaarde hoogte  : {config['drempelwaarde_hoogte']:.4f}")
    print(f"  Toets(en)             : {' + '.join(config['toetsen'])}")
    print(f"  Cooldown              : {config['cooldown']}s")
    print(f"  Vasthoudtijd          : {config['vasthoud_tijd']}s")
    print("  -----------------------------\n")
