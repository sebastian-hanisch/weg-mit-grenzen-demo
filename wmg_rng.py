"""SplitMix64 (Vigna): kleiner, gut gemischter 64-Bit-Zufallsgenerator in reiner Ganzzahl-Arithmetik.

numpy garantiert keine versionsstabilen Zufallsströme, die CI installiert die neueste Version; SplitMix64 liefert auf jeder
Plattform und in jeder Python-Version dieselbe Zahlenfolge. Der Instanzgenerator (`wmg_scenario.make_instanz`) bekommt den
Generator übergeben und ruft nur `uniform` auf; so lässt sich in einem Test auch `random.Random` einsetzen."""

_MASK = (1 << 64) - 1


class SplitMix64:
    """64-Bit-Zufallsgenerator (Vigna), reine Ganzzahl-Arithmetik."""

    def __init__(self, seed: int):
        self.state = seed & _MASK

    def next(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & _MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
        return z ^ (z >> 31)

    def random(self) -> float:
        """Gleitkommazahl im halboffenen Intervall [0, 1) mit 53 Bit (wie bei Pythons random)."""
        return (self.next() >> 11) / float(1 << 53)

    def uniform(self, a: float, b: float) -> float:
        return a + (b - a) * self.random()
