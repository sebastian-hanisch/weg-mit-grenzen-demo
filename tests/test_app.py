"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: lädt app.py mit den Standardeinstellungen, klickt jeden Knopf, fährt jeden Regler an seine
Grenzen (einzeln sowie alle Minima und alle Maxima zugleich), prüft jede Voreinstellung mit ihrer erwarteten Verdikt-Zeile und den Permalink.
Expander werden nie per Index oder als feste Titelliste angesprochen (DEMO-PLAYBOOK §2)."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import wmg_constants as C

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
SLIDER_KEYS = ["t_hand", "n_slider", "t_slider", "k_slider"]


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at) -> str:
    return " ".join(x.value for kind in (at.success, at.warning, at.info, at.error) for x in kind)


def test_app_loads_without_exception():
    at = _fresh_app()
    assert not at.error


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


@pytest.mark.parametrize("edge", ["min", "max"])
def test_all_sliders_at_their_minimum_or_maximum_together(edge):
    at = _fresh_app()
    for key in SLIDER_KEYS:
        s = at.sidebar.slider(key=key)
        s.set_value(int(s.min if edge == "min" else s.max))
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert not at.error


def test_seed_extremes_do_not_raise():
    for seed in (0, C.SEED_MAX):
        at = _fresh_app()
        at.sidebar.number_input(key="seed_input").set_value(seed).run(timeout=TIMEOUT)
        assert not at.exception, (seed, [str(e) for e in at.exception])


# --- Voreinstellungen: erwartete Verdikt-Zeile -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name, erwartet", [
    ("Handnetz, Grenze T = 10", ["Der billigste Weg verletzt die Grenze", "0-2-5-6 mit Kosten 12 und Zeit 9", "Bei T = 10 erzeugt das Verfahren 15 Labels"]),
    ("Handnetz, Grenze bindet nicht (T = 15)", ["Die Grenze bindet nicht", "Zeit 15 ≤ T = 15"]),
    ("Handnetz, kein zulässiger Weg (T = 7)", ["Kein zulässiger Weg", "die Grenze ist T = 7", "Bei T = 7 erzeugt das Verfahren 10 Labels"]),
    ("20 Kunden, Grenze 150", ["Beste Tour", "von 20 Kunden einzeln erreichbar"]),
    ("20 Kunden, Grenze 250", ["Beste Tour", "≤ T = 250", "20 von 20 Kunden einzeln erreichbar"]),
])
def test_each_preset_runs_and_shows_its_expected_verdict(name, erwartet):
    at = _fresh_app()
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    text = _texts(at).replace(" ", " ")
    for stueck in erwartet:
        assert stueck in text, (name, stueck)


def test_preset_sets_every_regler_value():
    at = _fresh_app()
    name = "20 Kunden, Grenze 250"
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    p = C.PRESETS[name]
    assert [at.sidebar.slider(key=k).value for k in SLIDER_KEYS] == [p["t_hand"], p["n"], p["t"], p["k"]]
    assert at.sidebar.number_input(key="seed_input").value == p["seed"]


# --- Permalink ---------------------------------------------------------------------------------------------------------------------------

def test_permalink_sets_the_regler_and_clamps_to_the_bounds():
    at = AppTest.from_file(APP_PATH)
    at.query_params["th"] = "12"
    at.query_params["n"] = "999"          # über dem Maximum
    at.query_params["t"] = "157"          # nicht auf dem Raster
    at.query_params["k"] = "0"            # unter dem Minimum
    at.query_params["seed"] = "42"
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.sidebar.slider(key="t_hand").value == 12
    assert at.sidebar.slider(key="n_slider").value == C.N_MAX
    assert at.sidebar.slider(key="t_slider").value == 160
    assert at.sidebar.slider(key="k_slider").value == C.K_MIN
    assert at.sidebar.number_input(key="seed_input").value == 42


def test_permalink_ignores_garbage_values():
    at = AppTest.from_file(APP_PATH)
    at.query_params["th"] = "abc"
    at.query_params["seed"] = ""
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.sidebar.slider(key="t_hand").value == C.DEFAULT_T_HAND


# --- Schritt-für-Schritt-Ansicht -------------------------------------------------------------------------------------------------------------

def test_step_view_starts_at_the_end_and_the_buttons_move_one_step():
    at = _fresh_app()
    letzter = at.slider(key="schritt").max
    assert at.slider(key="schritt").value == letzter and "Fertig" in _texts(at)
    at.button(key="btn_zurueck").click().run(timeout=TIMEOUT)
    assert at.slider(key="schritt").value == letzter - 1
    at.button(key="btn_weiter").click().run(timeout=TIMEOUT)
    assert at.slider(key="schritt").value == letzter
    at.button(key="btn_weiter").click().run(timeout=TIMEOUT)          # am Ende bleibt es am Ende
    assert at.slider(key="schritt").value == letzter and not at.exception


def test_step_slider_at_zero_shows_the_start_and_a_new_limit_resets_to_the_end():
    at = _fresh_app()
    at.slider(key="schritt").set_value(0).run(timeout=TIMEOUT)
    assert "Schritt 0 von" in _texts(at) and "Start: L0" in _texts(at)
    at.sidebar.slider(key="t_hand").set_value(8).run(timeout=TIMEOUT)
    assert not at.exception
    assert at.slider(key="schritt").value == at.slider(key="schritt").max


def test_step_count_follows_the_events_of_the_run():
    import wmg_evaluation as ev

    at = _fresh_app()
    assert at.slider(key="schritt").max == len(ev.analyse_hand(C.DEFAULT_T_HAND).ergebnis.ereignisse) - 1


# --- Aufbau ------------------------------------------------------------------------------------------------------------------------------

def test_expanders_are_found_by_their_titles_and_the_first_is_the_how_it_works_one():
    at = _fresh_app()
    titel = {e.label for e in at.expander}
    assert {"So funktioniert das Label-Setting mit Zeitgrenze", "📐 Mathematische Formulierung", "⚠️ Annahmen, Grenzen und bekannte Probleme"} <= titel
    assert next(e for e in at.expander if e.label == "So funktioniert das Label-Setting mit Zeitgrenze").proto.expanded


def test_five_experiments_and_the_section_of_the_assumptions_exist():
    at = _fresh_app()
    koepfe = [s.value for s in at.subheader]
    assert [k for k in koepfe if k.startswith("🔬 Experiment")] and len([k for k in koepfe if k.startswith("🔬 Experiment")]) == 5
    assert "🚧 Wo die Annahmen enden" in koepfe


def test_no_dead_file_links_in_the_markdown():
    at = _fresh_app()
    import re

    for m in at.markdown:
        for ziel in re.findall(r"\]\(([^)]+)\)", m.value):
            assert ziel.startswith("http"), ziel
