"""Eigenschaftstests (ORACLE-PLAYBOOK §5.2): Beziehungen, die für das Verfahren gelten müssen, ohne dass man das richtige Ergebnis kennt.

Je Eigenschaft 20 bis 60 Zufallsnetze mit festem Zufalls-Seed (Pythons `random.Random`, nur für die Netze der Tests). Netze ohne Kante mit Zeit 0, wo die
Eigenschaft die Abarbeitungsreihenfolge berührt (Umnummerieren): bei positiver Zeit je Kante steht jeder Dominierer schon fest, bevor das dominierte Label
an der Reihe ist, die Zahl der Labels hängt dann nicht an der Nummerierung."""

import math
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest

import wmg_algorithm as A
import wmg_scenario as S
from conftest import baue_instanz

ROOT = Path(__file__).resolve().parent.parent


def zufallsnetz(rng, n, dichte=0.45, zeit_min=1):
    kanten = [(a, b, rng.randint(0, 9), rng.randint(zeit_min, 9)) for a in range(n) for b in range(n) if a != b and rng.random() < dichte]
    return kanten


def netz_aus(n, kanten, start=0, ziel=None):
    return S.Netz(n, tuple(S.Kante(*k) for k in kanten), start, n - 1 if ziel is None else ziel)


def test_cost_of_the_best_feasible_path_never_rises_with_the_limit():
    rng = random.Random(1)
    for _ in range(40):
        n = rng.randint(3, 8)
        netz = netz_aus(n, zufallsnetz(rng, n))
        reihe = [A.label_setting(netz, T).bester for T in range(0, 40)]
        kosten = [math.inf if b is None else b[0] for b in reihe]
        assert all(a >= b for a, b in zip(kosten, kosten[1:]))
        # sobald ein Weg zulässig ist, bleibt er es
        assert all(b is not None for b in reihe[next((i for i, b in enumerate(reihe) if b is not None), len(reihe)):])


def test_time_of_the_result_is_within_the_limit_and_equals_the_recomputed_time():
    rng = random.Random(2)
    for _ in range(40):
        n = rng.randint(3, 8)
        netz = netz_aus(n, zufallsnetz(rng, n))
        for T in (3, 8, 15, 30):
            r = A.label_setting(netz, T)
            if r.bester is not None:
                assert r.bester[1] <= T
                assert A.pruefe_weg(netz, r.bester[2], T) == r.bester[:2]


def test_without_a_limit_the_result_equals_dijkstra():
    rng = random.Random(3)
    for _ in range(50):
        n = rng.randint(3, 8)
        netz = netz_aus(n, zufallsnetz(rng, n))
        dij, _ = A.dijkstra(netz)
        frei = A.label_setting(netz, math.inf)
        assert (dij is None) == (frei.bester is None)
        if dij is not None:
            assert dij[0] == frei.bester[0]
            assert dij[1] == frei.bester[1]          # bei gleichen Kosten gilt in beiden die kleinere Zeit


def test_renumbering_the_nodes_changes_neither_costs_nor_label_counts():
    rng = random.Random(4)
    for _ in range(40):
        n = rng.randint(3, 8)
        kanten = zufallsnetz(rng, n)
        perm = list(range(n))
        rng.shuffle(perm)
        umnummeriert = [(perm[a], perm[b], c, t) for a, b, c, t in kanten]
        for T in (5, 12, 25):
            r1 = A.label_setting(netz_aus(n, kanten, 0, n - 1), T)
            r2 = A.label_setting(netz_aus(n, umnummeriert, perm[0], perm[n - 1]), T)
            assert (r1.bester is None) == (r2.bester is None)
            if r1.bester:
                assert r1.bester[:2] == r2.bester[:2]
            assert (r1.erzeugt, r1.dominiert, r1.zu_spaet) == (r2.erzeugt, r2.dominiert, r2.zu_spaet), (kanten, perm, T)


def test_scaling_costs_and_times_scales_the_result_and_keeps_the_label_counts():
    rng = random.Random(5)
    for _ in range(40):
        n = rng.randint(3, 8)
        kanten = zufallsnetz(rng, n)
        T = rng.randint(5, 25)
        r1 = A.label_setting(netz_aus(n, kanten), T)
        gross = [(a, b, 3 * c, 2 * t) for a, b, c, t in kanten]
        r2 = A.label_setting(netz_aus(n, gross), 2 * T)
        assert (r1.erzeugt, r1.dominiert, r1.zu_spaet) == (r2.erzeugt, r2.dominiert, r2.zu_spaet)
        assert (r1.bester is None) == (r2.bester is None)
        if r1.bester:
            assert (3 * r1.bester[0], 2 * r1.bester[1]) == r2.bester[:2]


def test_no_pareto_pair_at_the_goal_is_dominated_and_live_labels_are_pairwise_incomparable():
    rng = random.Random(6)
    for _ in range(50):
        n = rng.randint(3, 8)
        r = A.label_setting(netz_aus(n, zufallsnetz(rng, n)), rng.choice([8, 20, math.inf]))
        for paare in list(r.lebend.values()) + [r.ziel_labels]:
            for p in paare:
                assert not any(q != p and q[0] <= p[0] and q[1] <= p[1] for q in paare)
            assert len(set(paare)) == len(paare)


def test_number_of_live_labels_per_node_is_at_most_the_pareto_pairs_of_the_paths_there():
    from test_oracle_weg_mit_grenzen import alle_einfachen_wege, pareto

    rng = random.Random(7)
    for _ in range(30):
        n = rng.randint(3, 7)
        kanten = zufallsnetz(rng, n)
        r = A.label_setting(netz_aus(n, kanten), 20)
        for v in range(1, n):
            paare = pareto([(c, t) for c, t, _ in alle_einfachen_wege(n, kanten, 0, v) if t <= 20])
            assert len(r.lebend[v]) <= len(paare)


def test_a_larger_limit_never_creates_fewer_labels_in_the_hand_network(hand_netz):
    erzeugt = [A.label_setting(hand_netz, T).erzeugt for T in range(7, 17)]
    assert all(a <= b for a, b in zip(erzeugt, erzeugt[1:]))


def test_pricing_cost_never_rises_with_the_time_limit():
    for seed in range(12):
        inst = S.instanz_aus_seed(10, seed)
        pi = S.praemien_erste_runde(inst)
        rc = []
        for T in (60, 90, 120, 160, 220):
            b = A.praemienweg(inst, pi, T, 5).bester
            rc.append(0.0 if b is None else b[0])
        assert all(a >= b - 1e-9 for a, b in zip(rc, rc[1:])), (seed, rc)


def test_same_seed_gives_the_same_output_and_other_seed_a_different_one():
    def lauf(seed):
        inst = S.instanz_aus_seed(12, seed)
        r = A.praemienweg(inst, S.praemien_erste_runde(inst), 120, 5)
        return r.erzeugt, r.dominiert, r.bester

    assert lauf(3) == lauf(3)
    assert lauf(3) != lauf(4)


def test_a_second_process_with_other_hash_seeds_gives_the_same_numbers():
    """Keine Abhängigkeit von der Reihenfolge in Mengen oder Wörterbüchern: dasselbe Szenario in zwei Prozessen mit PYTHONHASHSEED 1 und 2 (DEMO-PLAYBOOK §1d)."""
    code = (
        "import wmg_algorithm as A, wmg_scenario as S, math\n"
        "inst = S.instanz_aus_seed(12, 9)\n"
        "r = A.praemienweg(inst, S.praemien_erste_runde(inst), 130, 5)\n"
        "h = A.label_setting(S.HANDNETZ, 10)\n"
        "print(r.erzeugt, r.dominiert, r.bester, h.erzeugt, h.dominiert, h.lebend)\n"
    )
    ausgaben = []
    for hashseed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=hashseed)
        p = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
        assert p.returncode == 0, p.stderr
        ausgaben.append(p.stdout)
    assert ausgaben[0] == ausgaben[1] and ausgaben[0].strip()
