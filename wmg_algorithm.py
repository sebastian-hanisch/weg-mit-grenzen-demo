"""Kern der Demo (reine Python-Standardbibliothek): Label-Setting mit einer Zeitgrenze.

Ein **Label** ist ein Eintrag (Kosten, verbrauchte Zeit) an einem Knoten für einen Weg dorthin. Das Verfahren arbeitet die Labels
nach wachsender Zeit ab, verlängert jedes über alle ausgehenden Kanten und verwirft eine Verlängerung, deren Zeit die Grenze T
übersteigt. Ein Label **dominiert** ein anderes am selben Knoten, wenn es nicht mehr kostet und nicht mehr Zeit braucht.

Aufbau nach DEMO-PLAYBOOK §1b: jede Regel ist eine Funktion mit expliziten Ein- und Ausgaben, es gibt keinen versteckten Zustand,
`label_setting` und `praemienweg` rufen die Regeln nur der Reihe nach auf. Zwei Verfahren:

* `label_setting`: Handnetz, billigster Weg von Start nach Ziel mit Zeit <= T (mit Ereignisprotokoll für die Schritt-für-Schritt-Ansicht);
* `praemienweg`: Kundeninstanz, Rundweg ab Depot mit Prämien je Kunde und Zeitgrenze T (mit Gedächtnis der k nächsten Kunden).

Gezählt werden erzeugte Labels (die Messgröße, hardwareunabhängig), nie Sekunden."""

import heapq
import math
from dataclasses import dataclass, field

from wmg_scenario import Instanz, Netz

EPS = 1e-9


# --- gemeinsame Regeln ------------------------------------------------------------------------------------------------------------------

@dataclass
class Label:
    """Eintrag an einem Knoten: Kosten und Zeit des Weges dorthin, Gedächtnis (Bitmaske besuchter Kunden), Vorgänger-Label, Dominiert-Marke."""

    knoten: int
    kosten: float
    zeit: float
    mem: int = 0
    eltern: int = -1
    tot: bool = False


def dominiert(a: Label, b: Label) -> bool:
    """a dominiert b: Kosten und Zeit von a sind höchstens so groß wie die von b und das Gedächtnis von a ist eine Teilmenge des Gedächtnisses von b.

    Ohne Gedächtnis (mem = 0, Handnetz) bleibt die Regel auf Kosten und Zeit beschränkt. Gleiche Werte dominieren sich gegenseitig:
    das früher eingefügte Label bleibt."""
    return a.kosten <= b.kosten + EPS and a.zeit <= b.zeit + EPS and (a.mem & ~b.mem) == 0


def einfuegen(labels: list[Label], lebend: list[int], neu: int) -> tuple[int | None, list[int]]:
    """Dominanzprüfung für das neue Label `labels[neu]` gegen die lebenden Labels (Indizes) seines Knotens.

    Rückgabe (Dominierer, Verdrängte): Wird das neue Label von einem lebenden dominiert, ist der erste Index der Dominierer und es gibt
    keine Verdrängten. Sonst ist der Dominierer None, und Verdrängte sind die lebenden Labels, die das neue dominiert (sie werden hier
    NICHT verändert; der Aufrufer markiert sie und bereinigt `lebend`)."""
    n = labels[neu]
    for o in lebend:
        if dominiert(labels[o], n):
            return o, []
    return None, [o for o in lebend if dominiert(n, labels[o])]


def weg_von(labels: list[Label], idx: int) -> tuple[int, ...]:
    """Knotenfolge vom Start bis zum Label `idx` (über die Vorgänger-Verweise)."""
    weg = []
    x = idx
    while x != -1:
        weg.append(labels[x].knoten)
        x = labels[x].eltern
    return tuple(reversed(weg))


# --- Handnetz: Label-Setting mit Zeitgrenze ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Ereignis:
    """Ein Schritt des Verfahrens für die Schritt-für-Schritt-Ansicht (Daten, kein Text: der Text steht in wmg_evaluation.ereignis_text)."""

    art: str                                       # start | nimm | ueberspringe | zu_spaet | neu | verworfen | verdraengt | ende
    label: int | None = None                       # betroffenes Label
    werte: tuple[float, float] | None = None       # (Kosten, Zeit) des betroffenen Labels bzw. der zu späten Verlängerung
    knoten: int | None = None                      # Knoten des betroffenen Labels
    kante: tuple[int, int, float, float] | None = None   # (von, nach, Kosten, Zeit) der betrachteten Kante
    anderes: int | None = None                     # das andere Label (Dominierer bzw. Verdrängtes)
    anderes_werte: tuple[float, float] | None = None
    lebend: tuple = ()                             # Stand nach dem Schritt: je Knoten ((Nr, Kosten, Zeit), ...)
    erzeugt: int = 0
    dominiert: int = 0
    zu_spaet: int = 0


@dataclass(frozen=True)
class NetzErgebnis:
    erzeugt: int                                   # erzeugte Labels einschließlich Start und der sofort verworfenen
    dominiert: int                                 # durch Dominanz verworfene oder verdrängte Labels
    zu_spaet: int                                  # Verlängerungen, die wegen Zeit > T gar nicht erst gebildet wurden
    lebend: dict                                   # Knoten -> aufsteigend sortierte Tupel (Kosten, Zeit) der lebenden Labels
    ziel_labels: tuple                             # nicht dominierte (Kosten, Zeit) am Ziel, nach Kosten sortiert
    bester: tuple | None                           # (Kosten, Zeit, Weg) des billigsten Weges am Ziel, sonst None
    ereignisse: tuple = field(default=())


def _schnappschuss(labels: list[Label], am_knoten: dict) -> tuple:
    return tuple(tuple((i, labels[i].kosten, labels[i].zeit) for i in am_knoten[v]) for v in sorted(am_knoten))


def verlaengere(label: Label, kosten: float, zeit: float, T: float):
    """Verlängerung über eine Kante: (Kosten, Zeit) des neuen Labels, oder None, wenn die Zeit die Grenze T übersteigt (<= T ist zulässig)."""
    z = label.zeit + zeit
    if z > T:
        return None
    return label.kosten + kosten, z


def label_setting(netz: Netz, T: float, ereignisse: bool = False) -> NetzErgebnis:
    """Billigster Weg von netz.start nach netz.ziel mit Gesamtzeit <= T durch Label-Setting mit Dominanz.

    Die Labels werden nach (Zeit, Kosten, Nummer) abgearbeitet. T = math.inf ergibt alle nicht dominierten (Kosten, Zeit)-Paare am Ziel."""
    labels = [Label(netz.start, 0, 0)]
    am_knoten = {v: [] for v in range(netz.n)}
    am_knoten[netz.start] = [0]
    heap = [(0, 0, 0)]
    erzeugt, dom, spaet = 1, 0, 0
    log: list[Ereignis] = []

    def ereignis(art, **kw):
        if ereignisse:
            log.append(Ereignis(art, lebend=_schnappschuss(labels, am_knoten), erzeugt=erzeugt, dominiert=dom, zu_spaet=spaet, **kw))

    ereignis("start", label=0, knoten=netz.start, werte=(0, 0))
    while heap:
        _, _, li = heapq.heappop(heap)
        L = labels[li]
        if L.tot:
            ereignis("ueberspringe", label=li, knoten=L.knoten, werte=(L.kosten, L.zeit))
            continue
        ereignis("nimm", label=li, knoten=L.knoten, werte=(L.kosten, L.zeit))
        for e in netz.nachbarn(L.knoten):
            kante = (e.von, e.nach, e.kosten, e.zeit)
            neu_werte = verlaengere(L, e.kosten, e.zeit, T)
            if neu_werte is None:
                spaet += 1
                ereignis("zu_spaet", label=li, knoten=L.knoten, kante=kante, werte=(L.kosten + e.kosten, L.zeit + e.zeit))
                continue
            labels.append(Label(e.nach, neu_werte[0], neu_werte[1], 0, li))
            nid = len(labels) - 1
            erzeugt += 1
            dominierer, verdraengt = einfuegen(labels, am_knoten[e.nach], nid)
            if dominierer is not None:
                labels[nid].tot = True
                dom += 1
                o = labels[dominierer]
                ereignis("verworfen", label=nid, knoten=e.nach, kante=kante, werte=neu_werte, anderes=dominierer, anderes_werte=(o.kosten, o.zeit))
                continue
            for o in verdraengt:
                labels[o].tot = True
                dom += 1
                am_knoten[e.nach].remove(o)
                ereignis("verdraengt", label=nid, knoten=e.nach, kante=kante, werte=neu_werte, anderes=o, anderes_werte=(labels[o].kosten, labels[o].zeit))
            am_knoten[e.nach].append(nid)
            heapq.heappush(heap, (neu_werte[1], neu_werte[0], nid))
            ereignis("neu", label=nid, knoten=e.nach, kante=kante, werte=neu_werte)
    ende = sorted((labels[o].kosten, labels[o].zeit, o) for o in am_knoten[netz.ziel])
    bester = None
    if ende:
        k, z, o = ende[0]
        bester = (k, z, weg_von(labels, o))
    lebend = {v: tuple(sorted((labels[o].kosten, labels[o].zeit) for o in am_knoten[v])) for v in range(netz.n)}
    ereignis("ende", werte=None if bester is None else (bester[0], bester[1]))
    return NetzErgebnis(erzeugt, dom, spaet, lebend, tuple((k, z) for k, z, _ in ende), bester, tuple(log))


def dijkstra(netz: Netz) -> tuple[tuple | None, int]:
    """Dijkstra nur nach Kosten (kennt keine Zeitgrenze); bei gleichen Kosten gilt die kleinere Zeit.

    Rückgabe ((Kosten, Zeit, Weg) zum Ziel oder None, Zahl der gesetzten Knoten): ein Wert je Knoten statt einer Liste von Labels."""
    best = {netz.start: (0, 0, (netz.start,))}
    heap = [(0, 0, netz.start)]
    fertig = set()
    while heap:
        c, t, v = heapq.heappop(heap)
        if v in fertig:
            continue
        fertig.add(v)
        weg = best[v][2]
        for e in netz.nachbarn(v):
            cand = (c + e.kosten, t + e.zeit)
            if e.nach not in best or cand < best[e.nach][:2]:
                best[e.nach] = (cand[0], cand[1], weg + (e.nach,))
                heapq.heappush(heap, (cand[0], cand[1], e.nach))
    return best.get(netz.ziel), len(fertig)


def schnellste_zeit(netz: Netz) -> float | None:
    """Kleinste Zeit eines Weges von Start nach Ziel (Dijkstra nach Zeit), None ohne Weg."""
    best = {netz.start: 0}
    heap = [(0, netz.start)]
    fertig = set()
    while heap:
        t, v = heapq.heappop(heap)
        if v in fertig:
            continue
        fertig.add(v)
        for e in netz.nachbarn(v):
            if e.nach not in best or t + e.zeit < best[e.nach]:
                best[e.nach] = t + e.zeit
                heapq.heappush(heap, (t + e.zeit, e.nach))
    return best.get(netz.ziel)


def alle_wege(netz: Netz) -> list[tuple]:
    """Aufzählung aller einfachen Wege von Start nach Ziel als (Kosten, Zeit, Weg), nach (Kosten, Zeit) sortiert: die Gegenprobe für kleine Netze."""
    wege = []

    def rec(v, weg, c, t):
        if v == netz.ziel:
            wege.append((c, t, tuple(weg)))
            return
        for e in netz.nachbarn(v):
            if e.nach not in weg:
                rec(e.nach, weg + [e.nach], c + e.kosten, t + e.zeit)

    rec(netz.start, [netz.start], 0, 0)
    return sorted(wege)


def pruefe_weg(netz: Netz, weg: tuple[int, ...], T: float) -> tuple[float, float]:
    """Unabhängiger Prüfer: der Weg beginnt am Start, endet am Ziel, nutzt nur vorhandene Kanten und hat Zeit <= T. Rückgabe (Kosten, Zeit); sonst ValueError."""
    if not weg or weg[0] != netz.start or weg[-1] != netz.ziel:
        raise ValueError("Der Weg beginnt nicht am Start oder endet nicht am Ziel")
    kanten = {(e.von, e.nach): e for e in netz.kanten}
    kosten = zeit = 0
    for a, b in zip(weg, weg[1:]):
        if (a, b) not in kanten:
            raise ValueError(f"Die Kante {a}->{b} gibt es nicht")
        kosten += kanten[(a, b)].kosten
        zeit += kanten[(a, b)].zeit
    if zeit > T:
        raise ValueError(f"Die Zeit {zeit} überschreitet die Grenze {T}")
    return kosten, zeit


def treppe(netz: Netz, grenzen) -> list[dict]:
    """Kosten des billigsten zulässigen Weges je Zeitgrenze (Label-Setting je Grenze); Kosten None, wenn kein Weg zulässig ist."""
    zeilen = []
    for T in grenzen:
        r = label_setting(netz, T)
        zeilen.append({
            "T": T, "kosten": None if r.bester is None else r.bester[0], "zeit": None if r.bester is None else r.bester[1],
            "weg": None if r.bester is None else r.bester[2], "erzeugt": r.erzeugt, "dominiert": r.dominiert,
            "lebend": sum(len(x) for x in r.lebend.values()),
        })
    return zeilen


# --- Kundeninstanz: Rundweg mit Prämien und Zeitgrenze ----------------------------------------------------------------------------------

def ng_masken(inst: Instanz, k: int) -> list[int]:
    """Gedächtnis-Maske je Kunde j: die k nächsten Kunden einschließlich j selbst (Bitmaske, Bit i = Kunde i). Bei k = 1 besteht die Maske nur aus j selbst; die Wiederkehr nach einem anderen Kunden bleibt erlaubt."""
    masken = [0] * (inst.n + 1)
    for j in range(1, inst.n + 1):
        nah = sorted(range(1, inst.n + 1), key=lambda i: (inst.d[j][i], i))[:k]
        m = 1 << j
        for i in nah:
            m |= 1 << i
        masken[j] = m
    return masken


def spaeteste_ankunft(inst: Instanz, T: float) -> list[float]:
    """Späteste Ankunft je Kunde: danach reicht die Zeit für Bedienung und Rückweg zum Depot nicht mehr (Gesamtzeit der Tour <= T)."""
    return [0.0] + [T - inst.svc - inst.d[j][0] for j in range(1, inst.n + 1)]


def kunde_erreichbar(inst: Instanz, T: float, j: int) -> bool:
    """Kann Kunde j auf einer Tour allein (Depot, j, Depot) innerhalb der Zeitgrenze T bedient werden?"""
    return inst.d[0][j] <= T - inst.svc - inst.d[j][0]


@dataclass(frozen=True)
class PraemienErgebnis:
    erzeugt: int
    dominiert: int
    abgebrochen: bool                  # Abbruch bei LABEL_CAP-artiger Obergrenze: Zahlen sind dann untere Schranken
    erreichbar: int                    # Zahl der Kunden, die allein in der Zeitgrenze zu bedienen sind
    bester: tuple | None               # (reduzierte Kosten, Weg ohne Depot, Zeit der Tour) der billigsten Tour mit negativen Kosten, sonst None


def praemienweg(inst: Instanz, praemien, T: float, k: int, max_labels: int = 400_000) -> PraemienErgebnis:
    """Billigste Tour ab Depot: Kosten = Entfernungen minus Prämien der besuchten Kunden, Gesamtzeit inklusive Rückweg <= T.

    Label-Setting wie im Handnetz, dazu das Gedächtnis (ng-Maske): ein Label merkt sich die k nächsten Kunden jedes besuchten Kunden,
    damit sich ein Weg nicht im Kreis dreht; bei k = Zahl der Kunden besucht jede Tour jeden Kunden höchstens einmal. Dominanz:
    Kosten, Zeit und Gedächtnis (`dominiert`). Es zählen die erzeugten Labels; bei Überschreiten von `max_labels` bricht die Rechnung ab."""
    n, d, svc = inst.n, inst.d, inst.svc
    ng = ng_masken(inst, k)
    spaet = spaeteste_ankunft(inst, T)
    labels = [Label(0, 0.0, 0.0, 0, -1)]
    am_knoten = [[] for _ in range(n + 1)]
    heap = [(0.0, 0)]
    erzeugt, dom, abgebrochen = 1, 0, False
    ende: list[tuple[float, int]] = []
    while heap:
        _, li = heapq.heappop(heap)
        L = labels[li]
        if L.tot:
            continue
        if erzeugt > max_labels:
            abgebrochen = True
            break
        i = L.knoten
        if i != 0:
            ende.append((L.kosten + d[i][0], li))   # Rückweg zum Depot: die späteste Ankunft garantiert Zeit <= T
        t_ab = L.zeit + (svc if i != 0 else 0.0)
        for j in range(1, n + 1):
            if j == i or (L.mem >> j) & 1:
                continue
            ank = t_ab + d[i][j]
            if ank > spaet[j] + EPS:
                continue
            labels.append(Label(j, L.kosten + d[i][j] - praemien[j], ank, (L.mem & ng[j]) | (1 << j), li))
            nid = len(labels) - 1
            erzeugt += 1
            dominierer, verdraengt = einfuegen(labels, am_knoten[j], nid)
            if dominierer is not None:
                labels[nid].tot = True
                dom += 1
                continue
            for o in verdraengt:
                labels[o].tot = True
                dom += 1
            if verdraengt:
                am_knoten[j] = [o for o in am_knoten[j] if not labels[o].tot]
            am_knoten[j].append(nid)
            heapq.heappush(heap, (ank, nid))
    bester = None
    if ende:
        rc, li = min(ende)
        if rc < -1e-7:
            L = labels[li]
            bester = (rc, weg_von(labels, li)[1:], L.zeit + svc + d[L.knoten][0])
    erreichbar = sum(1 for j in range(1, n + 1) if kunde_erreichbar(inst, T, j))
    return PraemienErgebnis(erzeugt, dom, abgebrochen, erreichbar, bester)


def tour_kosten(inst: Instanz, praemien, weg: tuple[int, ...]) -> float:
    """Reduzierte Kosten einer Tour Depot, weg, Depot: Entfernungen minus Prämien (ein Kunde, der doppelt vorkommt, zählt doppelt)."""
    folge = (0,) + tuple(weg) + (0,)
    return sum(inst.d[a][b] for a, b in zip(folge, folge[1:])) - sum(praemien[j] for j in weg)


def tour_zeit(inst: Instanz, weg: tuple[int, ...]) -> float:
    """Gesamtzeit einer Tour: Fahrzeiten plus Bedienzeit je Kunde (Wiederholungen zählen mit)."""
    folge = (0,) + tuple(weg) + (0,)
    return sum(inst.d[a][b] for a, b in zip(folge, folge[1:])) + inst.svc * len(weg)


def pruefe_tour(inst: Instanz, praemien, weg: tuple[int, ...], T: float, kosten: float, zeit: float) -> bool:
    """Unabhängiger Prüfer: Kunden existieren, Gesamtzeit <= T (Rundung), Kosten und Zeit stimmen mit dem Ergebnis des Verfahrens überein."""
    if not weg or not all(1 <= j <= inst.n for j in weg):
        return False
    z = tour_zeit(inst, weg)
    return z <= T + 1e-6 and abs(z - zeit) < 1e-6 and abs(tour_kosten(inst, praemien, weg) - kosten) < 1e-6


def ist_elementar(weg: tuple[int, ...]) -> bool:
    """Besucht die Tour jeden Kunden höchstens einmal?"""
    return len(set(weg)) == len(weg)
