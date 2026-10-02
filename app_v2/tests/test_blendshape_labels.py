"""Tests voor de pure filterlogica in blendshape_labels (geen Tk/cv2 nodig)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blendshape_labels import (
    groepen_voor_ui, pas_zichtbaar_filter_toe, pieken_voor_editor,
    pieken_voor_trigger_menu, suggestie_namen, is_ondersteund,
)

KAAK = ["jawOpen", "jawLeft", "jawRight", "jawForward"]


def test_tong_is_niet_ondersteund():
    assert not is_ondersteund("tongueOut")
    alle = [n for _, namen in groepen_voor_ui() for n in namen]
    assert "tongueOut" not in alle


def test_filter_houdt_alleen_zichtbare_shapes():
    pieken = {"jawOpen": 0.8, "eyeBlinkLeft": 0.9, "tongueOut": 0.5}
    uit = pas_zichtbaar_filter_toe(pieken, set(KAAK))
    assert uit == {"jawOpen": 0.8}


def test_pieken_voor_editor_vult_ontbrekende_met_nul():
    uit = pieken_voor_editor({"jawOpen": 0.8, "eyeBlinkLeft": 0.9}, set(KAAK))
    assert set(uit) == set(KAAK)
    assert uit["jawOpen"] == 0.8
    assert uit["jawLeft"] == 0.0


def test_trigger_menu_alleen_filter_toont_geen_ogen():
    menu = pieken_voor_trigger_menu({n: 0.1 for n in KAAK}, alleen_filter=True)
    assert set(menu) == set(KAAK)


def test_trigger_menu_zonder_filter_toont_alles():
    menu = pieken_voor_trigger_menu({"jawOpen": 0.5})
    alle = {n for _, namen in groepen_voor_ui() for n in namen}
    assert set(menu) == alle


def test_suggesties_komen_alleen_uit_gegeven_pieken():
    pieken = pieken_voor_editor({"jawOpen": 0.9, "jawLeft": 0.2}, set(KAAK))
    assert set(suggestie_namen(pieken)) <= set(KAAK)
