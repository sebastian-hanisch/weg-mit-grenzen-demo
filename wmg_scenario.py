"""Szenarien: das Handnetz (7 Knoten, feste ganze Zahlen) und die Solomon-artige Kundeninstanz (selbst erzeugt, nicht die Originalinstanzen).

Beide Szenarien sind reine Daten ohne Rechenregel. Die Kundeninstanz bekommt ihren Zufall über einen übergebenen Generator
(`wmg_rng.SplitMix64`), nie aus einem Modul-Global."""

import math
from dataclasses import dataclass

import wmg_constants as C
from wmg_rng import SplitMix64


@dataclass(frozen=True)
class Kante:
    von: int
    nach: int
    kosten: int
    zeit: int


@dataclass(frozen=True)
class Netz:
    """Gerichtetes Netz; je Kante Kosten und Zeit (nichtnegativ). `kanten` in fester Reihenfolge: sie bestimmt die Reihenfolge der Verlängerungen."""

    n: int
    kanten: tuple[Kante, ...]
    start: int
    ziel: int

    def __post_init__(self):
        for e in self.kanten:
            if e.kosten < 0 or e.zeit < 0:
                raise ValueError(f"Kante {e.von}->{e.nach}: Kosten und Zeit dürfen nicht negativ sein")
            if not (0 <= e.von < self.n and 0 <= e.nach < self.n):
                raise ValueError(f"Kante {e.von}->{e.nach} verweist auf einen Knoten außerhalb von 0 bis {self.n - 1}")
        if not (0 <= self.start < self.n and 0 <= self.ziel < self.n):
            raise ValueError("Start und Ziel müssen Knoten des Netzes sein")

    def nachbarn(self, v: int) -> tuple[Kante, ...]:
        """Ausgehende Kanten von v in der Reihenfolge von `kanten`."""
        return tuple(e for e in self.kanten if e.von == v)


# Handnetz: Knoten 0 (Start) bis 6 (Ziel), je Kante (Kosten, Zeit); keine Kreise. Rechnung von Hand: 11 Wege von 0 nach 6.
HAND_KANTEN = (
    (0, 1, 2, 4), (0, 2, 4, 2), (0, 3, 8, 1),
    (1, 2, 1, 3), (1, 4, 3, 5),
    (2, 4, 2, 4), (2, 5, 5, 2),
    (3, 4, 6, 1), (3, 5, 2, 3),
    (4, 5, 1, 2), (4, 6, 2, 6),
    (5, 6, 3, 5),
)
HANDNETZ = Netz(7, tuple(Kante(*k) for k in HAND_KANTEN), 0, 6)


@dataclass(frozen=True)
class Instanz:
    """Kunden im Quadrat 100 x 100, Knoten 0 ist das Depot. Fahrzeit = Entfernung (euklidisch), Bedienzeit je Kunde `svc`."""

    pts: tuple[tuple[float, float], ...]
    d: tuple[tuple[float, ...], ...]
    svc: float = C.SERVICE_TIME

    @property
    def n(self) -> int:
        """Zahl der Kunden (ohne Depot)."""
        return len(self.pts) - 1


def make_instanz(n: int, rng) -> Instanz:
    """Depot in der Mitte, n Kunden gleichverteilt im Quadrat. Der Generator kommt von außen (nur `uniform` wird aufgerufen)."""
    kunden = [(rng.uniform(0, C.GRID), rng.uniform(0, C.GRID)) for _ in range(n)]
    pts = ((C.GRID / 2, C.GRID / 2),) + tuple(kunden)
    d = tuple(tuple(math.dist(a, b) for b in pts) for a in pts)
    return Instanz(pts, d)


def instanz_aus_seed(n: int, seed: int) -> Instanz:
    """Dieselbe Eingabe (n, Zufalls-Seed) gibt immer dieselbe Instanz; die ersten n Kunden sind bei gleichem Zufalls-Seed für jedes n gleich."""
    return make_instanz(n, SplitMix64(seed))


def praemien_erste_runde(inst: Instanz) -> tuple[float, ...]:
    """Prämie je Kunde: das Doppelte seiner Entfernung zum Depot (Index 0 = Depot, Prämie 0)."""
    return (0.0,) + tuple(2 * inst.d[0][i] for i in range(1, inst.n + 1))
