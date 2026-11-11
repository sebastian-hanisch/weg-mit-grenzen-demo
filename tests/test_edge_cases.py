"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): kleinste Netze, Grenze genau gleich der Zeit eines Weges,
Kanten mit Zeit 0, Start gleich Ziel, nicht erreichbares Ziel, Kundeninstanzen mit einem und zwei Kunden."""

import math

import pytest

import wmg_algorithm as A
import wmg_constants as C
import wmg_scenario as S
from conftest import baue_instanz


def test_exactly_two_nodes_and_one_edge():
    """n = 2: der kleinste Fall mit einem Weg."""
    netz = S.Netz(2, (S.Kante(0, 1, 5, 3),), 0, 1)
    assert A.label_setting(netz, 3).bester == (5, 3, (0, 1))          # Zeit genau T ist zulässig
    assert A.label_setting(netz, 2).bester is None
    assert A.dijkstra(netz)[0] == (5, 3, (0, 1))


def test_limit_smaller_than_every_time_gives_no_path_and_no_pair(hand_netz):
    r = A.label_setting(hand_netz, 7)       # der schnellste Weg braucht 8
    assert r.bester is None and r.ziel_labels == ()
    assert A.schnellste_zeit(hand_netz) == 8


def test_limit_exactly_equal_to_the_time_of_a_path_is_feasible(hand_netz):
    assert A.label_setting(hand_netz, 8).bester == (16, 8, (0, 3, 4, 6))
    assert A.label_setting(hand_netz, 15).bester[:2] == (7, 15)       # genau die Zeit des billigsten Weges


def test_start_equals_goal():
    netz = S.Netz(3, (S.Kante(0, 1, 2, 2), S.Kante(1, 0, 2, 2)), 0, 0)
    r = A.label_setting(netz, 10)
    assert r.bester == (0, 0, (0,)) and r.ziel_labels == ((0, 0),)


def test_goal_without_access_and_node_without_edges():
    netz = S.Netz(4, (S.Kante(0, 1, 1, 1), S.Kante(2, 3, 1, 1)), 0, 3)
    r = A.label_setting(netz, 99)
    assert r.bester is None and A.dijkstra(netz)[0] is None and A.schnellste_zeit(netz) is None
    assert A.alle_wege(netz) == []
    assert r.lebend[2] == () and r.lebend[3] == ()


def test_edges_with_time_zero_and_a_zero_cycle_terminate():
    """Kante mit Zeit 0 und ein Kreis aus Kosten 0 und Zeit 0: das Verfahren endet, weil das gleiche Label das alte nur dominiert."""
    netz = S.Netz(3, (S.Kante(0, 1, 0, 0), S.Kante(1, 0, 0, 0), S.Kante(1, 2, 4, 0), S.Kante(0, 2, 7, 0)), 0, 2)
    r = A.label_setting(netz, 0)
    assert r.bester == (4, 0, (0, 1, 2))
    assert r.erzeugt < 20


def test_equal_labels_keep_the_earlier_one():
    netz = S.Netz(4, (S.Kante(0, 1, 2, 2), S.Kante(0, 2, 2, 2), S.Kante(1, 3, 3, 3), S.Kante(2, 3, 3, 3)), 0, 3)
    r = A.label_setting(netz, 10)
    assert r.ziel_labels == ((5, 5),) and r.bester[2] == (0, 1, 3)    # beide Wege gleich: der zuerst gebildete bleibt
    assert r.dominiert == 1


def test_pricing_with_one_customer():
    inst = baue_instanz([(0, 0), (3, 4)])               # d01 = 5, Bedienzeit 10: Tour braucht 20
    r = A.praemienweg(inst, (0.0, 12.0), 20, 1)
    assert r.bester[1] == (1,) and r.bester[0] == pytest.approx(10 - 12) and r.erreichbar == 1
    assert A.praemienweg(inst, (0.0, 12.0), 19, 1).bester is None
    assert A.praemienweg(inst, (0.0, 10.0), 99, 1).bester is None      # Prämie gleich Fahrt: keine Verbesserung


def test_pricing_with_two_customers_and_zero_premiums():
    inst = baue_instanz([(0, 0), (3, 4), (6, 8)])
    r = A.praemienweg(inst, (0.0, 0.0, 0.0), 200, 2)
    assert r.bester is None and r.erreichbar == 2


def test_memory_larger_than_the_number_of_customers_equals_full_memory():
    inst = S.instanz_aus_seed(8, 2)
    pi = S.praemien_erste_runde(inst)
    a = A.praemienweg(inst, pi, 150, 8)
    b = A.praemienweg(inst, pi, 150, 12)
    assert (a.erzeugt, a.dominiert, a.bester) == (b.erzeugt, b.dominiert, b.bester)


def test_label_cap_aborts_the_calculation():
    inst = S.instanz_aus_seed(12, 1)
    r = A.praemienweg(inst, S.praemien_erste_runde(inst), 250, 5, max_labels=500)
    assert r.abgebrochen and 500 < r.erzeugt < 600


def test_no_limit_in_the_customer_instance_is_not_a_hang_for_two_customers():
    """T unendlich: Kunden höchstens einmal (k = n), die Rechnung endet, weil das Gedächtnis jeden Kunden nur einmal zulässt."""
    inst = baue_instanz([(0, 0), (3, 4), (6, 8)])
    r = A.praemienweg(inst, (0.0, 12.0, 14.0), math.inf, 2)
    assert r.bester[1] == (1, 2)


def test_regler_extremes_run_without_a_hang():
    """Jede Regler-Kombination an den Rändern endet (n und k am Minimum und Maximum, T am Minimum und Maximum) innerhalb der Label-Obergrenze."""
    for n in (C.N_MIN, 14):
        for T in (C.T_MIN, 200):
            for k in (C.K_MIN, C.K_MAX):
                inst = S.instanz_aus_seed(n, 0)
                r = A.praemienweg(inst, S.praemien_erste_runde(inst), T, k, max_labels=C.LABEL_CAP)
                assert r.erzeugt > 0
