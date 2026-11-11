"""Orakel-Tests (ORACLE-PLAYBOOK §2, §5; DEMO-PLAYBOOK §12): das Label-Setting gegen einen anderen Rechenweg.

Orakel dieser Datei, keines benutzt den Kern der Demo:
1. Handnetz und Zufallsnetze (mit und ohne Kreise, auch Kanten mit Zeit 0): Tiefensuche über alle einfachen Wege. Verglichen werden der
   billigste zulässige Weg je Grenze, die Front der nicht dominierten (Kosten, Zeit)-Paare am Ziel und die lebenden Labels je Knoten.
2. Dijkstra: networkx (`dijkstra_path_length`) gegen das Label-Setting ohne Grenze und gegen `wmg_algorithm.dijkstra`.
3. Kundeninstanz: Tiefensuche über alle Touren (Kunden höchstens einmal, Zeit und Kosten selbst gerechnet) gegen `praemienweg` mit k = Zahl der Kunden.
Das Orakel wurde vorher am Handbeispiel geprüft (Test `test_oracle_on_the_hand_example`). Laufzeit der Datei unter 10 Sekunden."""

import math
import random

import pytest

import wmg_algorithm as A
import wmg_scenario as S
from conftest import HAND, HAND_WEGE, baue_instanz


# --- Orakel 1: Tiefensuche im Netz ---------------------------------------------------------------------------------------------------------

def alle_einfachen_wege(n, kanten, start, ziel):
    """Orakel: alle einfachen Wege start -> ziel als Liste (Kosten, Zeit, Weg); `kanten` = [(von, nach, Kosten, Zeit)]. Eigene Tiefensuche."""
    ausgehend = {}
    for a, b, c, t in kanten:
        ausgehend.setdefault(a, []).append((b, c, t))
    wege = []

    def rec(v, weg, c, t):
        if v == ziel:
            wege.append((c, t, tuple(weg)))
            return
        for b, cc, tt in ausgehend.get(v, []):
            if b not in weg:
                rec(b, weg + [b], c + cc, t + tt)

    rec(start, [start], 0, 0)
    return wege


def pareto(paare):
    """Nicht dominierte (Kosten, Zeit)-Paare einer Menge, doppelte Paare einmal."""
    paare = set(paare)
    return sorted(p for p in paare if not any(q != p and q[0] <= p[0] and q[1] <= p[1] for q in paare))


def zufallsnetz(rng, n, dichte, zeit_min=1):
    kanten = []
    for a in range(n):
        for b in range(n):
            if a != b and rng.random() < dichte:
                kanten.append((a, b, rng.randint(0, 9), rng.randint(zeit_min, 9)))
    return kanten


def als_netz(n, kanten, start, ziel):
    return S.Netz(n, tuple(S.Kante(*k) for k in kanten), start, ziel)


def test_oracle_on_the_hand_example():
    """Das Orakel selbst am Handbeispiel: die elf Wege mit den Summen der Kantenwerte."""
    wege = alle_einfachen_wege(7, [(a, b, c, t) for (a, b), (c, t) in HAND.items()], 0, 6)
    assert {w: (c, t) for c, t, w in wege} == HAND_WEGE
    assert pareto([(c, t) for c, t, _ in wege]) == [(7, 15), (8, 12), (12, 9), (16, 8)]


@pytest.mark.parametrize("zeit_min", [1, 0])
def test_best_feasible_path_matches_enumeration_on_random_networks(zeit_min):
    rng = random.Random(20261110 + zeit_min)
    pruefungen = 0
    for _ in range(120):
        n = rng.randint(3, 7)
        kanten = zufallsnetz(rng, n, rng.choice([0.25, 0.4, 0.6]), zeit_min)
        netz = als_netz(n, kanten, 0, n - 1)
        wege = alle_einfachen_wege(n, kanten, 0, n - 1)
        grenzen = sorted({t for _, t, _ in wege}) + [0, 3, 10_000]
        for T in grenzen:
            zulaessig = [(c, t, w) for c, t, w in wege if t <= T]
            r = A.label_setting(netz, T)
            if zulaessig:
                assert r.bester is not None, (kanten, T)
                assert r.bester[0] == min(c for c, _, _ in zulaessig), (kanten, T)
                assert A.pruefe_weg(netz, r.bester[2], T) == r.bester[:2]
            else:
                assert r.bester is None, (kanten, T)
            pruefungen += 1
    assert pruefungen > 500


def test_front_and_all_live_labels_match_the_pareto_sets_of_the_enumeration():
    rng = random.Random(77)
    for _ in range(80):
        n = rng.randint(3, 7)
        kanten = zufallsnetz(rng, n, 0.45)
        netz = als_netz(n, kanten, 0, n - 1)
        r = A.label_setting(netz, math.inf)
        assert list(r.ziel_labels) == pareto([(c, t) for c, t, _ in alle_einfachen_wege(n, kanten, 0, n - 1)])
        for v in range(1, n):          # Knoten 0 hat zusätzlich das Startlabel (0, 0)
            erwartet = pareto([(c, t) for c, t, _ in alle_einfachen_wege(n, kanten, 0, v)])
            assert list(r.lebend[v]) == erwartet, (kanten, v)


def test_live_labels_at_a_limit_are_the_pareto_pairs_of_the_paths_within_the_limit():
    rng = random.Random(5)
    for _ in range(60):
        n = rng.randint(3, 7)
        kanten = zufallsnetz(rng, n, 0.5)
        netz = als_netz(n, kanten, 0, n - 1)
        T = rng.randint(2, 15)
        r = A.label_setting(netz, T)
        erwartet = pareto([(c, t) for c, t, _ in alle_einfachen_wege(n, kanten, 0, n - 1) if t <= T])
        assert list(r.ziel_labels) == erwartet


# --- Orakel 2: Dijkstra mit networkx --------------------------------------------------------------------------------------------------------

def test_dijkstra_and_label_setting_without_limit_match_networkx():
    nx = pytest.importorskip("networkx")
    rng = random.Random(11)
    geprueft = 0
    for _ in range(100):
        n = rng.randint(3, 8)
        kanten = zufallsnetz(rng, n, 0.4)
        g = nx.DiGraph()
        g.add_nodes_from(range(n))
        for a, b, c, t in kanten:
            g.add_edge(a, b, weight=c)
        netz = als_netz(n, kanten, 0, n - 1)
        dij, gesetzt = A.dijkstra(netz)
        frei = A.label_setting(netz, math.inf)
        if nx.has_path(g, 0, n - 1):
            erwartet = nx.dijkstra_path_length(g, 0, n - 1)
            assert dij[0] == erwartet and frei.bester[0] == erwartet
            geprueft += 1
        else:
            assert dij is None and frei.bester is None
        assert gesetzt == len(nx.descendants(g, 0)) + 1          # Dijkstra setzt genau die erreichbaren Knoten, je einen Wert
    assert geprueft > 40


# --- Orakel 3: Tiefensuche über alle Touren der Kundeninstanz -------------------------------------------------------------------------------

def beste_tour(inst, pi, T):
    """Orakel: billigste elementare Tour ab Depot (reduzierte Kosten = Entfernungen minus Prämien), Gesamtzeit <= T; Zeit und Kosten selbst gerechnet.
    Liefert (Kosten, Tour) oder (0.0, None), wenn keine Tour negative Kosten hat."""
    n = len(inst.pts) - 1
    best = [0.0, None]

    def rec(i, zeit, kosten, besucht, tour):
        for j in range(1, n + 1):
            if j in besucht:
                continue
            z = zeit + inst.d[i][j] + inst.svc
            if z + inst.d[j][0] > T + 1e-9:
                continue
            c = kosten + inst.d[i][j] - pi[j]
            # Rückfahrt zum Depot beendet die Tour
            if c + inst.d[j][0] < best[0] - 1e-9:
                best[0], best[1] = c + inst.d[j][0], tuple(tour + [j])
            rec(j, z, c, besucht | {j}, tour + [j])

    rec(0, 0.0, 0.0, frozenset(), [])
    return best[0], best[1]


def zufallsinstanz(rng, n):
    return baue_instanz([(50.0, 50.0)] + [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n)])


def test_pricing_with_full_memory_matches_enumeration_of_all_tours():
    rng = random.Random(2026)
    mit_tour = 0
    for fall in range(60):
        n = rng.randint(2, 6)
        inst = zufallsinstanz(rng, n)
        pi = (0.0,) + tuple(inst.d[0][i] * rng.uniform(0.8, 2.6) for i in range(1, n + 1))
        for T in (40, 80, 130, 220):
            erwartet, tour = beste_tour(inst, pi, T)
            r = A.praemienweg(inst, pi, T, n)
            if tour is None:
                assert r.bester is None, (fall, T)
            else:
                mit_tour += 1
                assert r.bester is not None, (fall, T)
                assert r.bester[0] == pytest.approx(erwartet, abs=1e-6), (fall, T)
                assert A.ist_elementar(r.bester[1])
                assert A.pruefe_tour(inst, pi, r.bester[1], T, r.bester[0], r.bester[2])
    assert mit_tour > 40


def test_reachable_customers_match_the_closed_formula():
    rng = random.Random(3)
    for _ in range(30):
        inst = zufallsinstanz(rng, 8)
        for T in (40, 80, 120, 200):
            erwartet = sum(1 for j in range(1, 9) if 2 * inst.d[0][j] + inst.svc <= T + 1e-9)
            assert A.praemienweg(inst, (0.0,) * 9, T, 3).erreichbar == erwartet


def test_a_smaller_memory_never_gives_a_worse_tour_than_full_memory():
    """Relaxierung: k < n lässt mehr Touren zu (auch mit Wiederholung), also nie höhere Kosten als die elementare Rechnung."""
    rng = random.Random(8)
    for _ in range(25):
        n = rng.randint(3, 6)
        inst = zufallsinstanz(rng, n)
        pi = (0.0,) + tuple(inst.d[0][i] * rng.uniform(1.0, 2.6) for i in range(1, n + 1))
        voll = A.praemienweg(inst, pi, 150, n).bester
        klein = A.praemienweg(inst, pi, 150, 1).bester
        wert = lambda b: 0.0 if b is None else b[0]   # noqa: E731
        assert wert(klein) <= wert(voll) + 1e-9
