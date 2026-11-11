"""Verdikte und Texte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Werte, nicht Seeds. Dazu die erwartete Verdikt-Zeile je Voreinstellung (Schnellstart)."""

import pytest

import wmg_algorithm as A
import wmg_constants as C
import wmg_evaluation as ev

NBSP = " "


def test_number_format_is_german():
    assert ev.zahl(1040) == f"1{NBSP}040" and ev.zahl(26678.5, 1) == f"26{NBSP}678,5" and ev.zahl(12.0) == "12"
    assert ev.zahl(-57.3, 2) == "-57,30" and ev.prozent(88.44) == "88,4 %" and ev.zahl(4.5, 1) == "4,5"


def test_grenze_violated_names_both_paths_and_the_extra_cost():
    kind, text = ev.verdict_grenze(10, (7, 15, (0, 1, 4, 6)), (12, 9, (0, 2, 5, 6)), 8)
    assert kind == "warning"
    assert "0-1-4-6 kostet 7" in text and "Zeit 15 > T = 10" in text and "0-2-5-6 mit Kosten 12 und Zeit 9" in text and "kostet 5 Kosteneinheiten" in text


def test_grenze_does_not_bind_when_the_cheapest_path_fits_inclusive():
    kind, text = ev.verdict_grenze(15, (7, 15, (0, 1, 4, 6)), (7, 15, (0, 1, 4, 6)), 8)      # Zeit genau T
    assert kind == "success" and "Die Grenze bindet nicht" in text and "Zeit 15 ≤ T = 15" in text
    assert ev.verdict_grenze(14, (7, 15, (0, 1, 4, 6)), (8, 12, (0, 2, 4, 6)), 8)[0] == "warning"   # eine Einheit darunter


def test_grenze_without_a_feasible_path():
    kind, text = ev.verdict_grenze(7, (7, 15, (0, 1, 4, 6)), None, 8)
    assert kind == "warning" and "Kein zulässiger Weg" in text and "Zeit 8" in text and "T = 7" in text


def test_steps_verdict_counts(hand_netz):
    kind, text = ev.verdict_schritte(10, A.label_setting(hand_netz, 10))
    assert kind == "info"
    assert "erzeugt das Verfahren 15 Labels" in text and "davon 3 durch Dominanz" in text and "5 Verlängerungen" in text and "(12, 9), (16, 8)" in text
    assert "keine" in ev.verdict_schritte(7, A.label_setting(hand_netz, 7))[1]


def test_staircase_verdict_counts_steps_and_the_binding_range():
    zeilen = [{"T": 7, "kosten": None}, {"T": 8, "kosten": 16}, {"T": 9, "kosten": 12}, {"T": 10, "kosten": 12}, {"T": 11, "kosten": 8}, {"T": 12, "kosten": 7}]
    kind, text = ev.verdict_treppe(zeilen, 12)
    assert kind == "info" and "Von T = 7 bis T = 12" in text
    assert "3-mal ab, von 16 auf 7 (insgesamt 4 Stufen)" in text and "Kleinste zulässige Grenze: T = 8" in text and "Die Grenze bindet für T < 12" in text
    kind2, text2 = ev.verdict_treppe([{"T": 9, "kosten": 5}, {"T": 10, "kosten": 5}], 8)       # billigster Weg braucht Zeit 8 < alle T
    assert "bindet in diesem Bereich nirgends" in text2
    assert ev.verdict_treppe([{"T": 5, "kosten": None}], 8)[0] == "warning"


def _erg(erzeugt, dominiert, bester=None, abgebrochen=False, erreichbar=9):
    return A.PraemienErgebnis(erzeugt, dominiert, abgebrochen, erreichbar, bester)


def test_gross_verdict_branches():
    kind, text = ev.verdict_gross(100, 12, 5, _erg(22, 1, (-57.3, (12, 3, 4), 93.3)), True)
    assert kind == "success" and "3 Kunden, Kosten -57,30" in text and "Gesamtzeit 93,3 ≤ T = 100" in text
    assert "22 Labels, davon 4,5 %" in text and "9 von 12 Kunden" in text and "mehrfach" not in text
    kind, text = ev.verdict_gross(100, 12, 1, _erg(40, 10, (-5.0, (1, 2, 1), 80.0)), False)
    assert kind == "success" and "besucht einen Kunden mehrfach: bei k = 1" in text
    kind, text = ev.verdict_gross(60, 12, 5, _erg(8, 0, None, erreichbar=3), None)
    assert kind == "info" and "Keine Tour mit negativen Kosten" in text and "8 Labels, davon 0,0 %" in text and "3 von 12" in text
    kind, text = ev.verdict_gross(300, 20, 8, _erg(400_001, 300_000, None, abgebrochen=True), None)
    assert kind == "warning" and "Abgebrochen" in text and f"400{NBSP}001" in text and f"400{NBSP}000" in text


def test_baender_verdict_threshold_is_inclusive_at_factor_1_5():
    zeilen = [{"T": 60, "labels_median": 10}, {"T": 80, "labels_median": 15}, {"T": 100, "labels_median": 24}]
    kind, text = ev.verdict_baender(zeilen, "T", "der Zeitgrenze", "T")             # Faktoren genau 1,5 und 1,6
    assert kind == "info" and text.startswith("Die Label-Zahl wächst mit der Zeitgrenze:")
    assert "bei 2 von 2 Stufenwechseln mindestens um den Faktor 1,5 höher" in text and "kleinster Faktor 1,50, größter 1,60" in text
    assert "Bei T = 60 liegt der Median bei 10, bei T = 100 bei 24 (Faktor 2,4)" in text
    gleich = ev.verdict_baender([{"T": 60, "labels_median": 10}, {"T": 80, "labels_median": 14}], "T", "der Zeitgrenze", "T")[1]     # Faktor 1,4
    assert gleich.startswith("Gleichauf bei der Zeitgrenze:") and "bei 0 von 1 Stufenwechseln" in gleich
    teil = ev.verdict_baender([{"breite": 40, "labels_median": 10}, {"breite": 100, "labels_median": 11}, {"breite": 200, "labels_median": 40}], "breite", "der Fensterbreite", "Breite")[1]
    assert "nur zwischen einem Teil der Stufen" in teil and "bei 1 von 2 Stufenwechseln" in teil and "Bei Breite = 40" in teil


def test_bridge_verdict(hand_netz):
    front = A.label_setting(hand_netz, float("inf"))
    kind, text = ev.verdict_bruecke(10, A.label_setting(hand_netz, 10), front)
    assert kind == "info" and "Aus den 4 Paaren der Front gelesen: für T = 10 Kosten 12 bei Zeit 9" in text and "spart 6 von 21 Labels" in text
    assert "spart hier nichts (21 Labels ohne Grenze, 21 mit Grenze)" in ev.verdict_bruecke(16, A.label_setting(hand_netz, 16), front)[1]
    kind, text = ev.verdict_bruecke(7, A.label_setting(hand_netz, 7), front)
    assert kind == "warning" and "kein Paar ist so schnell" in text and "10 Labels statt 21" in text


def test_reading_from_the_front_equals_the_built_in_limit(hand_netz):
    front = A.label_setting(hand_netz, float("inf"))
    for T in range(7, 17):
        abgelesen = ev.aus_front_ablesen(front.ziel_labels, T)
        eingebaut = A.label_setting(hand_netz, T).bester
        assert (abgelesen is None) == (eingebaut is None)
        if eingebaut:
            assert abgelesen == eingebaut[:2]


@pytest.mark.parametrize("art, erwartet", [
    ("start", "Start: L0 = (Knoten 0, Kosten 0, Zeit 0)."),
])
def test_event_texts_start(hand_netz, art, erwartet):
    r = A.label_setting(hand_netz, 10, ereignisse=True)
    assert ev.ereignis_text(r.ereignisse[0], 10) == erwartet


def test_event_texts_name_reason_and_numbers(hand_netz):
    texte = [ev.ereignis_text(e, 10) for e in A.label_setting(hand_netz, 10, ereignisse=True).ereignisse]
    assert "Kante 2→5: L7 = (Knoten 5, Kosten 9, Zeit 4) dominiert das alte L5 (Kosten 10, Zeit 4); L5 entfällt." in texte
    assert "Kante 4→5: L8 = (Knoten 5, Kosten 15, Zeit 4) wird von L7 dominiert (Kosten 9 ≤ 15, Zeit 4 ≤ 4) und verworfen." in texte
    assert "Kante 4→6 (Kosten 2, Zeit 6): Zeit 12 > T = 10, das Label wird gar nicht erst gebildet." in texte
    assert "L5 (Knoten 5, Kosten 10, Zeit 4) ist inzwischen dominiert und wird übersprungen." in texte
    assert texte[-1] == "Fertig: Das billigste Label am Ziel hat Kosten 12 und Zeit 9."


# --- erwartete Verdikt-Zeile je Voreinstellung ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name, kind, stueck", [
    ("Handnetz, Grenze T = 10", "warning", "verletzt die Grenze"),
    ("Handnetz, Grenze bindet nicht (T = 15)", "success", "Die Grenze bindet nicht"),
    ("Handnetz, kein zulässiger Weg (T = 7)", "warning", "Kein zulässiger Weg"),
])
def test_each_hand_preset_shows_its_expected_verdict(name, kind, stueck):
    p = C.PRESETS[name]
    h = ev.analyse_hand(p["t_hand"])
    k, text = ev.verdict_grenze(p["t_hand"], h.dijkstra, h.ergebnis.bester, h.schnellste)
    assert k == kind and stueck in text and h.fehler is None


def test_the_size_presets_show_what_their_help_says():
    s150 = ev.analyse_gross(ev.Settings(**C.PRESETS["20 Kunden, Grenze 150"]))
    assert s150.ergebnis.erreichbar == 20 and s150.ergebnis.erzeugt < 1000 and s150.fehler is None          # „alle 20 Kunden“, „weniger als 1 000 Labels“
    s250 = ev.analyse_gross(ev.Settings(**C.PRESETS["20 Kunden, Grenze 250"]))
    assert s250.ergebnis.erzeugt > 10_000 and not s250.ergebnis.abgebrochen and s250.fehler is None        # „mehr als 10 000 Labels“
    kind, text = ev.verdict_gross(250, 20, 5, s250.ergebnis, A.ist_elementar(s250.ergebnis.bester[1]))
    assert kind == "success" and "Beste Tour" in text
