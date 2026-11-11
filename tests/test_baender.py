"""Feste Messreihen (data/*.json): Zusammenfassungen stimmen mit den Einzelwerten, jede Zeile nennt ihre Quelle, und die neu rechenbare Reihe wird in Stichproben nachgerechnet.

Reihe über die Zeitgrenze (n = 20, k = 5, Zufalls-Seeds 0 bis 11): erzeugt von `tools/messreihe_baender.py zeitgrenze` mit demselben Kern wie die App.
Reihe über die Fensterbreite: Rohzeilen einer früheren Messreihe (Spaltenerzeugung bis zur Konvergenz), hier nur zusammengefasst; sie lässt sich mit diesem Kern
nicht nachrechnen (Fenster, Kapazität und Master fehlen), die Zusammenfassung wird aus den Einzelwerten der Datei geprüft."""

import statistics

import pytest

import wmg_algorithm as A
import wmg_constants as C
import wmg_evaluation as ev
import wmg_scenario as S


def _zeilen(name):
    return ev.lade_baender(name)["zeilen"]


def test_zeitgrenze_rows_cover_the_band_grid_and_name_their_source():
    zeilen = _zeilen("zeitgrenze")
    assert [z["T"] for z in zeilen] == list(C.BAND_T)
    for z in zeilen:
        assert z["instanzen"] == len(z["labels_je_instanz"]) == len(C.SWEEP_SEEDS) == 12
        assert "messreihe_baender.py" in z["quelle"] and f"T = {z['T']}" in z["quelle"] and "n = 20" in z["quelle"] and "k = 5" in z["quelle"]


def test_zeitgrenze_summaries_follow_from_the_single_values():
    for z in _zeilen("zeitgrenze"):
        labels = z["labels_je_instanz"]
        assert z["labels_median"] == statistics.median(labels)
        assert z["labels_mittel"] == pytest.approx(statistics.mean(labels), abs=0.05)
        assert z["labels_max"] == max(labels)
        assert 0 <= z["instanzen_mit_route"] <= z["instanzen"]
        assert 0 <= z["dominiert_mittel_prozent"] <= 100 and 0 <= z["erreichbar_median"] <= 20


@pytest.mark.parametrize("T", [60, 80, 100, 150, 200])
def test_zeitgrenze_row_is_reproduced_for_all_twelve_instances(T):
    """Neu gerechnet (Zufalls-Seeds 0 bis 11): jede Einzelzahl der Zeile stimmt, ebenso Zahl der Instanzen mit Tour und erreichbare Kunden."""
    z = next(z for z in _zeilen("zeitgrenze") if z["T"] == T)
    labels, erreichbar, mit_tour = [], [], 0
    for seed in C.SWEEP_SEEDS:
        inst = S.instanz_aus_seed(C.BAND_N, seed)
        r = A.praemienweg(inst, S.praemien_erste_runde(inst), T, C.BAND_K)
        labels.append(r.erzeugt)
        erreichbar.append(r.erreichbar)
        mit_tour += r.bester is not None
    assert labels == z["labels_je_instanz"]
    assert statistics.median(erreichbar) == z["erreichbar_median"] and mit_tour == z["instanzen_mit_route"]


@pytest.mark.parametrize("T", [250, 300])
def test_zeitgrenze_large_rows_are_reproduced_on_a_sample(T):
    """Die großen Zeilen (Sekunden je Instanz) in einer Stichprobe von zwei Instanzen; die volle Zeile erzeugt tools/messreihe_baender.py."""
    z = next(z for z in _zeilen("zeitgrenze") if z["T"] == T)
    for seed in (0, 5):
        inst = S.instanz_aus_seed(C.BAND_N, seed)
        assert A.praemienweg(inst, S.praemien_erste_runde(inst), T, C.BAND_K).erzeugt == z["labels_je_instanz"][seed]


def test_fensterbreite_rows_are_k1_and_k5_for_three_widths_with_six_instances():
    zeilen = _zeilen("fensterbreite")
    assert sorted((z["breite"], z["k"]) for z in zeilen) == [(40, 1), (40, 5), (100, 1), (100, 5), (200, 1), (200, 5)]
    for z in zeilen:
        assert z["instanzen"] == len(z["labels_je_instanz"]) == 6
        assert "out_v1_n30.txt" in z["quelle"] and f"Fensterbreite {z['breite']}" in z["quelle"] and f"k = {z['k']}" in z["quelle"]
        labels = z["labels_je_instanz"]
        assert z["labels_median"] == statistics.median(labels) and z["labels_max"] == max(labels)
        assert z["labels_mittel"] == pytest.approx(statistics.mean(labels), abs=0.05)


def test_fensterbreite_medians_equal_the_published_table_of_the_earlier_measurement():
    """Median der Labels je Zelle laut Auswertung der früheren Messreihe (auf ganze Zahlen gerundet; die Medians aus sechs Werten liegen auf x,5)."""
    erwartet = {(40, 1): 16938, (100, 1): 57330, (200, 1): 160456, (40, 5): 20904, (100, 5): 92038, (200, 5): 348904}
    for z in _zeilen("fensterbreite"):
        assert round(z["labels_median"]) == erwartet[(z["breite"], z["k"])] and z["labels_median"] % 1 == 0.5


def test_loader_returns_a_description_with_the_conditions():
    assert "12 Instanzen" in ev.lade_baender("zeitgrenze")["beschreibung"] and "6 Instanzen" in ev.lade_baender("fensterbreite")["beschreibung"]
