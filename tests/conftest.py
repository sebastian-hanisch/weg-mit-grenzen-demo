"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).

Das Handnetz steht hier unabhängig vom Szenario-Modul noch einmal von Hand (Tabelle der Aufgabe: Kante, Kosten, Zeit); ein Test
prüft, dass das Szenario-Modul dieselben Zahlen enthält. Die erwarteten Werte stehen in den Tests als Rechnung (Summen der Kantenwerte),
nicht als abgeschriebene Ergebnisse des Codes."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wmg_scenario import Instanz, Kante, Netz  # noqa: E402

# Handnetz von Hand: (von, nach, Kosten, Zeit); Knoten 0 = Start, Knoten 6 = Ziel; keine Kreise
HAND = {
    (0, 1): (2, 4), (0, 2): (4, 2), (0, 3): (8, 1),
    (1, 2): (1, 3), (1, 4): (3, 5),
    (2, 4): (2, 4), (2, 5): (5, 2),
    (3, 4): (6, 1), (3, 5): (2, 3),
    (4, 5): (1, 2), (4, 6): (2, 6),
    (5, 6): (3, 5),
}

# Die elf Wege von 0 nach 6 mit (Kosten, Zeit) als Summe der Kantenwerte: Kosten (c) und Zeit (t) je Kante laut HAND.
HAND_WEGE = {
    (0, 1, 4, 6): (2 + 3 + 2, 4 + 5 + 6),
    (0, 1, 2, 4, 6): (2 + 1 + 2 + 2, 4 + 3 + 4 + 6),
    (0, 2, 4, 6): (4 + 2 + 2, 2 + 4 + 6),
    (0, 1, 4, 5, 6): (2 + 3 + 1 + 3, 4 + 5 + 2 + 5),
    (0, 1, 2, 4, 5, 6): (2 + 1 + 2 + 1 + 3, 4 + 3 + 4 + 2 + 5),
    (0, 2, 4, 5, 6): (4 + 2 + 1 + 3, 2 + 4 + 2 + 5),
    (0, 1, 2, 5, 6): (2 + 1 + 5 + 3, 4 + 3 + 2 + 5),
    (0, 2, 5, 6): (4 + 5 + 3, 2 + 2 + 5),
    (0, 3, 5, 6): (8 + 2 + 3, 1 + 3 + 5),
    (0, 3, 4, 6): (8 + 6 + 2, 1 + 1 + 6),
    (0, 3, 4, 5, 6): (8 + 6 + 1 + 3, 1 + 1 + 2 + 5),
}


@pytest.fixture
def hand_netz():
    return Netz(7, tuple(Kante(a, b, c, t) for (a, b), (c, t) in HAND.items()), 0, 6)


@pytest.fixture
def hand_wege():
    return dict(HAND_WEGE)


def baue_instanz(punkte, svc=10.0):
    """Instanz aus Punkten (Index 0 = Depot) mit euklidischen Entfernungen."""
    d = tuple(tuple(math.dist(a, b) for b in punkte) for a in punkte)
    return Instanz(tuple(punkte), d, svc)


@pytest.fixture
def mini_kunden():
    """Depot (0, 0), Kunde 1 bei (3, 4), Kunde 2 bei (6, 8). Entfernungen: d01 = 5, d12 = 5, d02 = 10; Bedienzeit 10.
    Prämien 12 und 14 (von Hand gesetzt). Tour [1, 2]: Fahrt 5 + 5 + 10 = 20, Prämien 26, Kosten -6, Zeit 20 + 2 * 10 = 40.
    Tour [1]: Fahrt 10, Kosten 10 - 12 = -2, Zeit 20. Tour [2]: Fahrt 20, Kosten 20 - 14 = 6 (keine Verbesserung), Zeit 30."""
    return baue_instanz([(0, 0), (3, 4), (6, 8)]), (0.0, 12.0, 14.0)
