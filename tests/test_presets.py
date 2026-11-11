"""Voreinstellungen (Schnellstart): Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Begrenzung."""

import wmg_constants as C
import wmg_evaluation as ev
import wmg_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_on_the_grid():
    for name, p in C.PRESETS.items():
        assert C.T_HAND_MIN <= p["t_hand"] <= C.T_HAND_MAX, name
        assert C.N_MIN <= p["n"] <= C.N_MAX and C.K_MIN <= p["k"] <= C.K_MAX and 0 <= p["seed"] <= C.SEED_MAX, name
        assert C.T_MIN <= p["t"] <= C.T_MAX and (p["t"] - C.T_MIN) % C.T_STEP == 0, name


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**next(iter(C.PRESETS.values()))) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_preset_names_match_their_values():
    """Die Namen der Voreinstellungen nennen Zahlen: sie müssen zu den Werten passen (Klasse „vertauschte Beschriftungen“)."""
    assert C.PRESETS["Handnetz, Grenze T = 10"]["t_hand"] == 10
    assert C.PRESETS["Handnetz, Grenze bindet nicht (T = 15)"]["t_hand"] == 15
    assert C.PRESETS["Handnetz, kein zulässiger Weg (T = 7)"]["t_hand"] == 7
    for name, (n, t) in {"20 Kunden, Grenze 150": (20, 150), "20 Kunden, Grenze 250": (20, 250)}.items():
        assert (C.PRESETS[name]["n"], C.PRESETS[name]["t"]) == (n, t)


def test_bands_use_the_slider_range_of_the_time_limit():
    assert C.T_MIN == min(C.BAND_T) and C.T_MAX == max(C.BAND_T) and all((t - C.T_MIN) % C.T_STEP == 0 for t in C.BAND_T)
    assert C.BAND_N == C.N_MAX and C.BAND_K in range(C.K_MIN, C.K_MAX + 1)


def test_label_cap_is_far_above_the_measured_maximum():
    """Die Obergrenze trifft nur Hänger: die größte Messung der Reihe (n = 20, k = 5, T = 300) liegt weit darunter."""
    zeilen = ev.lade_baender("zeitgrenze")["zeilen"]
    assert max(z["labels_max"] for z in zeilen) * 3 < C.LABEL_CAP
