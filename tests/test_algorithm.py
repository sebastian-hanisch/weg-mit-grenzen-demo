"""Kern gegen Handrechnung (Handnetz und Mini-Kundeninstanz aus conftest.py) und Einheiten einzeln (DEMO-PLAYBOOK §1b).

Die Erwartungswerte des Handnetzes sind Summen der Kantenwerte (conftest.HAND_WEGE), die Zählungen stehen als Tally der
Handrechnung da. Die Orakel gegen eine unabhängige Aufzählung stehen in test_oracle_weg_mit_grenzen.py."""

import math

import pytest

import wmg_algorithm as A
import wmg_constants as C
import wmg_scenario as S
from conftest import HAND, HAND_WEGE, baue_instanz
from wmg_algorithm import Label


# --- Szenario ---------------------------------------------------------------------------------------------------------------------------

def test_scenario_module_has_the_hand_network_of_the_task(hand_netz):
    assert {(e.von, e.nach): (e.kosten, e.zeit) for e in S.HANDNETZ.kanten} == HAND
    assert (S.HANDNETZ.n, S.HANDNETZ.start, S.HANDNETZ.ziel) == (7, 0, 6)
    assert S.HANDNETZ == hand_netz


def test_network_rejects_negative_values_and_unknown_nodes():
    with pytest.raises(ValueError):
        S.Netz(2, (S.Kante(0, 1, -1, 1),), 0, 1)
    with pytest.raises(ValueError):
        S.Netz(2, (S.Kante(0, 1, 1, -1),), 0, 1)
    with pytest.raises(ValueError):
        S.Netz(2, (S.Kante(0, 2, 1, 1),), 0, 1)
    with pytest.raises(ValueError):
        S.Netz(2, (S.Kante(0, 1, 1, 1),), 0, 5)


# --- Einheiten --------------------------------------------------------------------------------------------------------------------------

def test_dominates_rule_cost_time_and_memory():
    a = Label(1, 9, 4)
    assert A.dominiert(a, Label(1, 10, 4))          # billiger bei gleicher Zeit
    assert A.dominiert(a, Label(1, 9, 5))           # gleich teuer, langsamer
    assert A.dominiert(a, Label(1, 9, 4))           # gleiche Werte dominieren sich gegenseitig
    assert not A.dominiert(a, Label(1, 8, 9))       # billiger, aber langsamer: kein Dominieren
    assert not A.dominiert(a, Label(1, 12, 3))      # schneller, aber teurer
    mit_gedaechtnis = Label(1, 5, 5, mem=0b0110)
    assert A.dominiert(mit_gedaechtnis, Label(1, 6, 5, mem=0b0111))        # Gedächtnis {1, 2} ist Teilmenge von {0, 1, 2}
    assert not A.dominiert(mit_gedaechtnis, Label(1, 6, 5, mem=0b0100))    # Gedächtnis enthält Kunde 1 zusätzlich


def test_insert_reports_the_dominator_or_the_displaced_labels():
    labels = [Label(5, 10, 4), Label(5, 7, 8), Label(5, 9, 4)]
    # neues Label 2 = (9, 4) dominiert Label 0 = (10, 4), nicht Label 1 = (7, 8)
    assert A.einfuegen(labels, [0, 1], 2) == (None, [0])
    # ein Label (15, 4) wird von Label 2 = (9, 4) dominiert
    labels.append(Label(5, 15, 4))
    assert A.einfuegen(labels, [1, 2], 3) == (2, [])
    # gleiche Werte: das früher eingefügte Label bleibt
    labels.append(Label(5, 9, 4))
    assert A.einfuegen(labels, [2], 4) == (2, [])


def test_extension_is_inclusive_at_the_limit():
    lab = Label(0, 3, 6)
    assert A.verlaengere(lab, 2, 4, 10) == (5, 10)       # Zeit genau T ist zulässig
    assert A.verlaengere(lab, 2, 5, 10) is None          # Zeit 11 > 10


def test_path_from_labels_follows_the_parents():
    labels = [Label(0, 0, 0), Label(2, 4, 2, eltern=0), Label(5, 9, 4, eltern=1)]
    assert A.weg_von(labels, 2) == (0, 2, 5)


# --- Handnetz ---------------------------------------------------------------------------------------------------------------------------

def test_enumeration_finds_the_eleven_paths_with_hand_sums(hand_netz, hand_wege):
    wege = A.alle_wege(hand_netz)
    assert len(wege) == len(hand_wege) == 11
    assert {w: (c, t) for c, t, w in wege} == hand_wege


def test_dijkstra_takes_the_cheapest_path_and_ignores_time(hand_netz):
    (kosten, zeit, weg), gesetzt = A.dijkstra(hand_netz)
    assert weg == (0, 1, 4, 6) and (kosten, zeit) == (2 + 3 + 2, 4 + 5 + 6)
    assert gesetzt == 7                                    # ein Wert je Knoten
    assert zeit > 10                                       # bei T = 10 unzulässig


def test_label_setting_at_t10_finds_the_cheapest_feasible_path(hand_netz):
    r = A.label_setting(hand_netz, 10)
    assert r.bester == (4 + 5 + 3, 2 + 2 + 5, (0, 2, 5, 6))
    assert r.ziel_labels == ((12, 9), (16, 8))              # (12, 9) und (8 + 6 + 2, 1 + 1 + 6)
    # Handrechnung der Zählung: Start 1 Label; verlängert werden der Reihe nach L0 (3 Kanten), L3 (2), L2 (2), L4 (2), L1 (2), L7 (1), L6 (1), L10 (1)
    assert r.erzeugt == 1 + (3 + 2 + 2 + 2 + 2 + 1 + 1 + 1)
    # wegen Zeit > 10 nicht gebildet: L6 über 4->6 (6 + 6), L10 über 2->4 (7 + 4), L13 über 5->6 (8 + 5), L11 über 4->5 (9 + 2) und 4->6 (9 + 6)
    assert r.zu_spaet == 1 + 1 + 1 + 2
    # dominiert: L5 (von L7 verdrängt), L8 (von L7 verworfen), L14 (von L13 verworfen)
    assert r.dominiert == 3
    assert r.lebend[4] == ((5, 9), (6, 6), (14, 2))


def test_events_show_the_dominance_decisions_of_the_hand_calculation(hand_netz):
    r = A.label_setting(hand_netz, 10, ereignisse=True)
    arten = [e.art for e in r.ereignisse]
    assert arten[0] == "start" and arten[-1] == "ende"
    # L7 entsteht aus L2 = (4, 2) über 2->5 (5, 2): (9, 4); das alte L5 = L3 (8, 1) + 3->5 (2, 3) = (10, 4) entfällt
    verdraengt = [e for e in r.ereignisse if e.art == "verdraengt"]
    assert len(verdraengt) == 1
    assert (verdraengt[0].label, verdraengt[0].werte) == (7, (4 + 5, 2 + 2))
    assert (verdraengt[0].anderes, verdraengt[0].anderes_werte) == (5, (8 + 2, 1 + 3))
    # L8 = L4 (14, 2) + 4->5 (1, 2) = (15, 4) wird von L7 dominiert
    verworfen = [e for e in r.ereignisse if e.art == "verworfen"]
    assert [(e.label, e.werte, e.anderes) for e in verworfen][0] == (8, (14 + 1, 2 + 2), 7)
    # L6 = (6, 6) über 4->6 (2, 6): Zeit 12 > 10, nicht gebildet
    spaet = [e for e in r.ereignisse if e.art == "zu_spaet" and e.kante == (4, 6, 2, 6)]
    assert spaet and spaet[0].werte == (6 + 2, 6 + 6)
    # der Zähler im letzten Ereignis ist der Endstand
    last = r.ereignisse[-1]
    assert (last.erzeugt, last.dominiert, last.zu_spaet) == (r.erzeugt, r.dominiert, r.zu_spaet)


def test_without_events_the_log_is_empty(hand_netz):
    assert A.label_setting(hand_netz, 10).ereignisse == ()


@pytest.mark.parametrize("T, kosten", [(7, None), (8, 16), (9, 12), (10, 12), (11, 12), (12, 8), (13, 8), (14, 8), (15, 7), (16, 7)])
def test_staircase_equals_the_enumeration_in_every_step(hand_netz, hand_wege, T, kosten):
    zulaessig = [c for c, t in hand_wege.values() if t <= T]
    assert (min(zulaessig) if zulaessig else None) == kosten      # Handrechnung aus den Summen
    r = A.label_setting(hand_netz, T)
    assert (None if r.bester is None else r.bester[0]) == kosten


def test_label_counts_over_the_limit_match_the_hand_script(hand_netz):
    # Rohausgabe des unabhängigen Handskripts der Planung (Standardbibliothek, ohne diesen Kern), T = 7 bis 16
    assert [A.label_setting(hand_netz, T).erzeugt for T in range(7, 17)] == [10, 12, 15, 15, 17, 18, 19, 19, 20, 21]


def test_without_a_limit_the_front_has_the_four_pareto_pairs_and_21_labels(hand_netz, hand_wege):
    front = A.label_setting(hand_netz, math.inf)
    assert front.ziel_labels == ((7, 15), (8, 12), (12, 9), (16, 8))
    assert front.erzeugt == A.label_setting(hand_netz, 999).erzeugt == 21
    # die Paare sind genau die nicht dominierten Paare der elf Wege
    paare = set(hand_wege.values())
    assert set(front.ziel_labels) == {p for p in paare if not any(q != p and q[0] <= p[0] and q[1] <= p[1] for q in paare)}
    assert sum(len(v) for v in front.lebend.values()) == 15      # lebende Labels je Knoten 1, 1, 2, 1, 3, 3, 4


def test_staircase_function_rows(hand_netz):
    zeilen = A.treppe(hand_netz, range(7, 17))
    assert [z["kosten"] for z in zeilen] == [None, 16, 12, 12, 12, 8, 8, 8, 7, 7]
    assert zeilen[2]["weg"] == (0, 2, 5, 6) and zeilen[2]["zeit"] == 9


def test_fastest_time_of_the_hand_network(hand_netz, hand_wege):
    assert A.schnellste_zeit(hand_netz) == min(t for c, t in hand_wege.values()) == 1 + 1 + 6


def test_path_checker_rejects_wrong_paths(hand_netz):
    assert A.pruefe_weg(hand_netz, (0, 2, 5, 6), 10) == (12, 9)
    for bad in ((0, 2, 5), (1, 2, 5, 6), (0, 5, 6), ()):
        with pytest.raises(ValueError):
            A.pruefe_weg(hand_netz, bad, 99)
    with pytest.raises(ValueError):
        A.pruefe_weg(hand_netz, (0, 1, 4, 6), 10)             # Zeit 15 > 10


# --- Mini-Kundeninstanz -------------------------------------------------------------------------------------------------------------------

def test_tour_cost_and_time_by_hand(mini_kunden):
    inst, pi = mini_kunden
    assert A.tour_kosten(inst, pi, (1, 2)) == pytest.approx((5 + 5 + 10) - (12 + 14))
    assert A.tour_zeit(inst, (1, 2)) == pytest.approx((5 + 5 + 10) + 2 * 10)
    assert A.tour_kosten(inst, pi, (1,)) == pytest.approx(10 - 12)
    assert A.tour_zeit(inst, (1,)) == pytest.approx(10 + 10)
    assert A.tour_kosten(inst, pi, (2,)) == pytest.approx(20 - 14)


def test_pricing_on_the_mini_instance_by_hand(mini_kunden):
    inst, pi = mini_kunden
    r = A.praemienweg(inst, pi, 40, 2)
    assert r.bester[1] == (1, 2) and r.bester[0] == pytest.approx(-6) and r.bester[2] == pytest.approx(40)
    r39 = A.praemienweg(inst, pi, 39, 2)                       # Tour [1, 2] braucht 40: nur [1] bleibt, Kosten -2
    assert r39.bester[1] == (1,) and r39.bester[0] == pytest.approx(-2)
    assert A.praemienweg(inst, pi, 20, 2).bester[1] == (1,)    # Zeit genau 20: zulässig
    assert A.praemienweg(inst, pi, 19, 2).bester is None       # nicht einmal [1] passt


def test_latest_arrival_and_reachability(mini_kunden):
    inst, _ = mini_kunden
    assert A.spaeteste_ankunft(inst, 40) == [0.0, 40 - 10 - 5, 40 - 10 - 10]
    assert A.kunde_erreichbar(inst, 20, 1) and not A.kunde_erreichbar(inst, 19, 1)     # 5 + 10 + 5 = 20
    assert A.kunde_erreichbar(inst, 30, 2) and not A.kunde_erreichbar(inst, 29, 2)     # 10 + 10 + 10 = 30


def test_memory_masks_on_a_line():
    inst = baue_instanz([(0, 0), (1, 0), (2, 0), (5, 0), (9, 0)])
    assert A.ng_masken(inst, 1) == [0, 1 << 1, 1 << 2, 1 << 3, 1 << 4]
    m2 = A.ng_masken(inst, 2)
    assert m2[1] == (1 << 1) | (1 << 2) and m2[3] == (1 << 3) | (1 << 2) and m2[4] == (1 << 4) | (1 << 3)
    assert A.ng_masken(inst, 4)[1] == 0b11110                   # alle vier Kunden


def test_memory_decides_whether_a_customer_is_visited_twice():
    # Kunden bei 1 und 2 auf einer Linie, hohe Prämien; Bedienzeit 10. Tour [1, 2, 1]: Fahrt 4, Zeit 4 + 30 = 34; [1, 2, 1, 2]: Zeit 6 + 40 = 46 > 40.
    inst = baue_instanz([(0, 0), (1, 0), (2, 0)])
    pi = (0.0, 50.0, 50.0)
    k1 = A.praemienweg(inst, pi, 40, 1)
    assert k1.bester[1] == (1, 2, 1) and k1.bester[0] == pytest.approx(4 - 150)      # k = 1: Wiederkehr nach einem anderen Kunden (1-2-1) bleibt erlaubt
    assert not A.ist_elementar(k1.bester[1])
    k2 = A.praemienweg(inst, pi, 40, 2)
    assert sorted(k2.bester[1]) == [1, 2] and A.ist_elementar(k2.bester[1])          # Gedächtnis 2 enthält den Nachbarn
    assert k2.bester[0] == pytest.approx(4 - 100)


def test_tour_checker_rejects_wrong_results(mini_kunden):
    inst, pi = mini_kunden
    assert A.pruefe_tour(inst, pi, (1, 2), 40, -6, 40)
    assert not A.pruefe_tour(inst, pi, (1, 2), 39, -6, 40)       # Grenze verletzt
    assert not A.pruefe_tour(inst, pi, (1, 2), 40, -5, 40)       # falsche Kosten
    assert not A.pruefe_tour(inst, pi, (1, 3), 40, -6, 40)       # Kunde 3 gibt es nicht
    assert not A.pruefe_tour(inst, pi, (), 40, 0, 0)


# --- Instanzgenerator ---------------------------------------------------------------------------------------------------------------------

def test_instance_is_deterministic_and_a_prefix_property_holds():
    a = S.instanz_aus_seed(12, 5)
    assert a == S.instanz_aus_seed(12, 5) != S.instanz_aus_seed(12, 6)
    b = S.instanz_aus_seed(20, 5)
    assert b.pts[:13] == a.pts                       # die ersten 12 Kunden sind bei gleichem Zufalls-Seed dieselben
    assert a.pts[0] == (50.0, 50.0) and all(0 <= x <= 100 and 0 <= y <= 100 for x, y in a.pts)
    assert all(a.d[i][j] == pytest.approx(math.dist(a.pts[i], a.pts[j])) for i in range(13) for j in range(13))
    assert S.praemien_erste_runde(a)[3] == pytest.approx(2 * a.d[0][3]) and S.praemien_erste_runde(a)[0] == 0


def test_splitmix64_reference_values():
    """Bekannte Ausgaben von SplitMix64 mit Zufalls-Seed 0. Die Werte stammen aus dem Gedächtnis, nicht aus einer eingesehenen Quelle (Stand der Einsicht:
    keine); der Test schützt vor einem Tippfehler in Konstanten oder Schiebeweiten, er ist kein Literaturbeleg."""
    from wmg_rng import SplitMix64

    g = SplitMix64(0)
    assert g.next() == 0xE220A8397B1DCDAF
    assert g.next() == 0x6E789E6AA1B965F4
    assert 0.0 <= SplitMix64(1).random() < 1.0


def test_worst_case_at_the_slider_maximum_finishes_under_the_label_cap():
    """Kein Hänger am Regler-Maximum (n, T und k am Maximum): Rechnung endet innerhalb der Label-Obergrenze; keine Zeit-Assertion."""
    inst = S.instanz_aus_seed(C.N_MAX, 0)
    r = A.praemienweg(inst, S.praemien_erste_runde(inst), C.T_MAX, C.K_MAX, max_labels=C.LABEL_CAP)
    assert r.erzeugt > 0 and (r.abgebrochen or r.erzeugt <= C.LABEL_CAP + C.N_MAX)
