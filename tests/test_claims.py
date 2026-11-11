"""Jede Zahl der README an den festen Zufalls-Seeds nachgerechnet (DEMO-PLAYBOOK §4, §11a). Zeiten werden nie festgeschrieben.

Die README-Tabellen werden aus den Messreihen in data/ erzeugt; der Test erzeugt sie noch einmal und sucht sie in der README. Die Zahl-zu-Test-Tabelle
in der README nennt für jede Zahl den Test. Zahlen aus der früheren Messreihe über die Fensterbreite sind Bandwerte aus der Datei, nicht neu gerechnet."""

import random
import re
import statistics
import subprocess
import sys
from pathlib import Path

import pytest

import wmg_algorithm as A
import wmg_constants as C
import wmg_evaluation as ev
import wmg_scenario as S
from wmg_texts import ASSUMPTIONS_MARKDOWN

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")



def _tabelle_zeitgrenze():
    z = ev.lade_baender("zeitgrenze")["zeilen"]
    zeilen = ["| Zeitgrenze T | erreichbare Kunden (Median) | Labels (Median) | Labels (Mittel) | Labels (Maximum) | dominiert (Mittel) | Instanzen mit Gewinn-Tour |", "|---|---|---|---|---|---|---|"]
    for r in z:
        med = ev.zahl(r["labels_median"], 1 if r["labels_median"] % 1 else 0)
        zeilen.append(f"| {r['T']} | {ev.zahl(r['erreichbar_median'], 1)} | {med} | {ev.zahl(r['labels_mittel'], 1)} | {ev.zahl(r['labels_max'])} | "
                      f"{ev.prozent(r['dominiert_mittel_prozent'])} | {r['instanzen_mit_route']} von {r['instanzen']} |")
    return "\n".join(zeilen)


def _tabelle_breite():
    f = ev.lade_baender("fensterbreite")["zeilen"]
    zeilen = ["| Fensterbreite | Gedächtnis k | Labels (Median) | Labels (Mittel) | Labels (Maximum) | dominiert (Mittel) |", "|---|---|---|---|---|---|"]
    for r in f:
        med = ev.zahl(r["labels_median"], 1 if r["labels_median"] % 1 else 0)
        zeilen.append(f"| {r['breite']} | {r['k']} | {med} | {ev.zahl(r['labels_mittel'], 1)} | {ev.zahl(r['labels_max'])} | {ev.prozent(r['dominiert_mittel_prozent'])} |")
    return "\n".join(zeilen)


def test_readme_tables_are_generated_from_the_data():
    assert _tabelle_zeitgrenze() in README
    assert _tabelle_breite() in README


def test_the_assumptions_text_of_the_app_is_in_the_readme_verbatim():
    assert ASSUMPTIONS_MARKDOWN.strip() in README


def test_readme_names_the_same_test_count_as_the_suite():
    p = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "tests", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True, text=True, timeout=300)
    m = re.search(r"(\d+) tests? collected", p.stdout)
    assert m, p.stdout[-300:]
    assert f"{m.group(1)} Tests (`pytest --collect-only -q tests`)" in README


# --- Handnetz -----------------------------------------------------------------------------------------------------------------------------

def test_handnetz_claims(hand_netz, hand_wege):
    assert len(A.alle_wege(hand_netz)) == 11
    (dk, dz, dw), gesetzt = A.dijkstra(hand_netz)
    assert (dk, dz, dw, gesetzt) == (7, 15, (0, 1, 4, 6), 7)
    r = A.label_setting(hand_netz, 10)
    assert r.bester == (12, 9, (0, 2, 5, 6)) and 15 - 12 + 7 == 10 and r.bester[0] - dk == 5
    assert (r.erzeugt, r.dominiert, r.zu_spaet) == (15, 3, 5)
    kosten = [A.label_setting(hand_netz, T).bester for T in range(7, 17)]
    assert [None if b is None else b[0] for b in kosten] == [None, 16, 12, 12, 12, 8, 8, 8, 7, 7]
    assert A.label_setting(hand_netz, float("inf")).ziel_labels == ((7, 15), (8, 12), (12, 9), (16, 8))


def test_handnetz_label_counts_and_bridge(hand_netz):
    assert [A.label_setting(hand_netz, T).erzeugt for T in range(7, 17)] == [10, 12, 15, 15, 17, 18, 19, 19, 20, 21]
    front = A.label_setting(hand_netz, float("inf"))
    assert front.erzeugt == 21 and sum(len(v) for v in front.lebend.values()) == 15
    assert [len(front.lebend[v]) for v in range(7)] == [1, 1, 2, 1, 3, 3, 4]
    assert ev.aus_front_ablesen(front.ziel_labels, 10) == (12, 9)
    assert A.label_setting(hand_netz, 10).erzeugt == 15


# --- Messreihe über die Zeitgrenze ---------------------------------------------------------------------------------------------------------------

def test_growth_claims_over_the_limit():
    zeilen = ev.lade_baender("zeitgrenze")["zeilen"]
    meds = [z["labels_median"] for z in zeilen]
    f = ev.faktoren(meds)
    assert len(f) == 6 and all(x >= 1.5 for x in f)
    assert round(min(f), 2) == 1.81 and f.index(min(f)) == 5                        # T = 250 auf 300
    assert round(max(f), 2) == 17.14 and f.index(max(f)) == 2                       # T = 100 auf 150
    assert round(meds[-1] / meds[0], 1) == 5928.6                                   # T = 60 auf 300
    assert round(meds[-1] / meds[3], 1) == 30.5                                     # T = 150 auf 300
    assert [z["erreichbar_median"] for z in zeilen[3:]] == [20.0] * 4              # ab T = 150 alle Kunden einzeln erreichbar (Median)
    assert [z["instanzen_mit_route"] for z in zeilen] == [1, 12, 12, 12, 12, 12, 12]
    assert [z["dominiert_mittel_prozent"] for z in zeilen][0] == 0.0 and zeilen[-1]["dominiert_mittel_prozent"] == 90.7
    assert all(a <= b for a, b in zip([z["dominiert_mittel_prozent"] for z in zeilen], [z["dominiert_mittel_prozent"] for z in zeilen][1:]))


def test_window_width_factors():
    zeilen = ev.lade_baender("fensterbreite")["zeilen"]
    for k, (a, b) in {1: (3.38, 2.80), 5: (4.40, 3.79)}.items():
        meds = [z["labels_median"] for z in zeilen if z["k"] == k]
        f = ev.faktoren(meds)
        assert [round(x, 2) for x in f] == [a, b] and all(x >= 1.5 for x in f)
        assert all(m % 1 == 0.5 for m in meds)


def test_memory_claim_at_t200():
    labels = {}
    for k in (1, 2, 3, 5, 8):
        labels[k] = []
        for seed in C.SWEEP_SEEDS:
            inst = S.instanz_aus_seed(C.BAND_N, seed)
            labels[k].append(A.praemienweg(inst, S.praemien_erste_runde(inst), 200, k).erzeugt)
    assert [statistics.median(labels[k]) for k in (1, 2, 3, 5, 8)] == [2436.5, 3071.5, 3766, 5284, 7428.5]
    for i in range(12):
        reihe = [labels[k][i] for k in (1, 2, 3, 5, 8)]
        assert reihe == sorted(reihe), (i, reihe)
    # bei T = 100 gilt „nimmt nicht ab“ nicht in allen 12 Instanzen
    nicht_monoton = 0
    for seed in C.SWEEP_SEEDS:
        inst = S.instanz_aus_seed(C.BAND_N, seed)
        reihe = [A.praemienweg(inst, S.praemien_erste_runde(inst), 100, k).erzeugt for k in (1, 2, 3, 5, 8)]
        nicht_monoton += reihe != sorted(reihe)
    assert nicht_monoton >= 1


def test_size_presets_numbers():
    erwartet = {(12, 100): (22, 1, 9, 3, -57.30), (20, 150): (798, 465, 20, 4, -211.48), (20, 250): (12728, 11035, 20, 7, -440.83)}
    for (n, T), (erzeugt, dom, erreichbar, kunden, kosten) in erwartet.items():
        inst = S.instanz_aus_seed(n, C.DEFAULT_SEED)
        r = A.praemienweg(inst, S.praemien_erste_runde(inst), T, 5)
        assert (r.erzeugt, r.dominiert, r.erreichbar, len(r.bester[1])) == (erzeugt, dom, erreichbar, kunden), (n, T)
        assert r.bester[0] == pytest.approx(kosten, abs=0.005)
    # die Zahlen stehen so in der README
    for stueck in ("22 Labels (davon 1 dominiert)", "798 Labels (davon 465 dominiert)", "12 728 Labels (davon 11 035 dominiert)", "Kosten -57,30", "Kosten -440,83"):
        assert stueck in README.replace(" ", " "), stueck


def test_cross_check_with_the_earlier_implementation():
    """Mit Pythons `random.Random(seed)` als Generator liefert der Kern dieselben Mediane wie das frühere Mess-Skript ohne Last (Scratch-Lauf der älteren
    Implementierung `ls_kern.price` mit Bedarf 0; bis T = 100 stimmen sie mit der früheren Rohausgabe der Messreihe überein)."""
    erwartet = {60: 8.0, 80: 21.0, 100: 65.5, 150: 938.5, 200: 5831.0}
    for T, median in erwartet.items():
        labels = []
        for seed in C.SWEEP_SEEDS:
            inst = S.make_instanz(C.BAND_N, random.Random(seed))
            labels.append(A.praemienweg(inst, S.praemien_erste_runde(inst), T, C.BAND_K).erzeugt)
        assert statistics.median(labels) == median, T
    for stueck in ("8, 21 und 65,5", "938,5 und 5 831"):
        assert stueck in README.replace(" ", " ")


# --- App-Texte mit Zahlen ---------------------------------------------------------------------------------------------------------------------

def test_numbers_in_app_texts_match_the_data_and_constants():
    zg, fb = ev.lade_baender("zeitgrenze"), ev.lade_baender("fensterbreite")
    assert "nur 12 Instanzen je Zelle bei der Zeitgrenze (20 Kunden)" in APP and all(z["instanzen"] == 12 for z in zg["zeilen"]) and C.BAND_N == 20
    assert "nur 6 Instanzen je Breite bei der Fensterbreite (30 Kunden)" in APP and all(z["instanzen"] == 6 for z in fb["zeilen"])
    assert "Kapazität 70" in fb["beschreibung"] and "30 Kunden" in fb["beschreibung"]
    assert "fünf Experimente" in APP and APP.count('st.subheader("🔬 Experiment') == 5
    assert "Netz mit 7 Knoten" in APP and S.HANDNETZ.n == 7 and len(S.HANDNETZ.kanten) == 12
    assert "Quadrats von 100 × 100" in APP and C.GRID == 100.0 and "Bedienzeit 10 je Kunde" in ASSUMPTIONS_MARKDOWN and C.SERVICE_TIME == 10.0
    assert "8 bis 20 Kunden" in ASSUMPTIONS_MARKDOWN and (C.N_MIN, C.N_MAX) == (8, 20)
    assert f"Zeitgrenze T im Handnetz" in APP and (C.T_HAND_MIN, C.T_HAND_MAX) == (7, 16)
    assert "von 7 bis 16" in APP


def test_forbidden_words_do_not_appear_in_texts():
    """Wortwahl (DEMO-PLAYBOOK §7): „trägt/tragen“ nicht bildlich, „läuft lokal“ nicht, „Saatwert“ nicht; Begriffe der eigenen Planung nicht in Texten."""
    alle = README + APP + ASSUMPTIONS_MARKDOWN + (ROOT / "wmg_constants.py").read_text(encoding="utf-8") + (ROOT / "wmg_evaluation.py").read_text(encoding="utf-8")
    for wort in ("läuft lokal", "Saatwert", "Phase 0", "geplant", "TODO", "Standardfall"):
        assert wort not in alle, wort
    # „trägt/tragen“ als ganzes Wort (nicht „beträgt“); wörtlich gemeint wäre „Kosten tragen“, das kommt hier nicht vor
    assert not re.search(r"\b(trägt|tragen)\b", alle)
    assert not re.search(r"\bStück\b", alle)
