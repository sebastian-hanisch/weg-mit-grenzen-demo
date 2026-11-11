"""Kennzahlen, Verdikt-Logik (reine Funktionen: (Art, Text)), Texte der Schritt-für-Schritt-Ansicht und Lader der festen Messreihen.

Jedes Verdikt der App ist eine Funktion `verdict_*(...) -> (Art, Text)`; die App ruft `getattr(st, Art)(Text)`, `tests/test_verdicts.py`
prüft Schwellen und jede Zahl im Text an handgesetzten Werten."""

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

import wmg_algorithm as A
import wmg_constants as C
from wmg_scenario import HANDNETZ, Instanz, Netz, instanz_aus_seed, praemien_erste_runde

DATA = Path(__file__).resolve().parent / "data"


# --- Zahlenformat (deutsch) ---------------------------------------------------------------------------------------------------------------

def zahl(x, stellen: int = 0) -> str:
    """Deutsche Schreibweise: Dezimalkomma, geschütztes Leerzeichen als Tausendertrenner; ganze Zahlen ohne Nachkommastellen."""
    if stellen == 0:
        if isinstance(x, float) and x.is_integer():
            x = int(x)
        text = f"{x:,}"
    else:
        text = f"{x:,.{stellen}f}"
    return text.replace(",", " ").replace(".", ",")


def prozent(x: float) -> str:
    return zahl(round(x, 1), 1) + " %"


def weg_text(weg) -> str:
    return "-".join(str(v) for v in weg)


# --- Analysen -----------------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Settings:
    t_hand: int = C.DEFAULT_T_HAND
    n: int = C.DEFAULT_N
    t: int = C.DEFAULT_T
    k: int = C.DEFAULT_K
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class HandAnalyse:
    T: float
    netz: Netz
    ergebnis: A.NetzErgebnis        # Label-Setting bei T, mit Ereignisprotokoll
    dijkstra: tuple | None          # (Kosten, Zeit, Weg) des billigsten Weges ohne Grenze
    gesetzt: int                    # von Dijkstra gesetzte Knoten (ein Wert je Knoten)
    schnellste: float | None        # kleinste Zeit eines Weges
    front: A.NetzErgebnis           # Label-Setting ohne Grenze (T = ∞): alle nicht dominierten Paare am Ziel
    wege: list                      # Aufzählung aller Wege (Kosten, Zeit, Weg)
    treppe: list                    # Zeilen je T = T_HAND_MIN bis T_HAND_MAX
    fehler: str | None              # Befund der Prüfung des Ergebnisses (None = in Ordnung)


def aus_front_ablesen(ziel_paare, T: float):
    """Die Frage „billigster Weg mit Zeit <= T“ aus der fertigen Front abgelesen: das billigste Paar (Kosten, Zeit) mit Zeit <= T, sonst None."""
    zulaessig = [p for p in ziel_paare if p[1] <= T]
    return min(zulaessig) if zulaessig else None


def analyse_hand(T: int) -> HandAnalyse:
    netz = HANDNETZ
    erg = A.label_setting(netz, T, ereignisse=True)
    dij, gesetzt = A.dijkstra(netz)
    front = A.label_setting(netz, math.inf)
    wege = A.alle_wege(netz)
    treppe = A.treppe(netz, range(C.T_HAND_MIN, C.T_HAND_MAX + 1))
    fehler = None
    try:
        if erg.bester is not None:
            kosten, zeit = A.pruefe_weg(netz, erg.bester[2], T)
            if (kosten, zeit) != erg.bester[:2]:
                fehler = "Kosten oder Zeit des Weges stimmen nicht mit der Nachrechnung überein."
        zulaessig = [w for w in wege if w[1] <= T]
        erwartet = zulaessig[0][0] if zulaessig else None
        if erwartet != (None if erg.bester is None else erg.bester[0]):
            fehler = "Die Aufzählung aller Wege liefert andere Kosten als das Label-Setting."
    except ValueError as e:
        fehler = str(e)
    return HandAnalyse(T, netz, erg, dij, gesetzt, A.schnellste_zeit(netz), front, wege, treppe, fehler)


@dataclass(frozen=True)
class GrossAnalyse:
    inst: Instanz
    praemien: tuple
    T: int
    k: int
    ergebnis: A.PraemienErgebnis
    fehler: str | None
    sekunden: float = field(default=0.0, compare=False)   # Rechenzeit nur zur Information, nie in einem Vergleich oder Test


def analyse_gross(s: Settings) -> GrossAnalyse:
    t0 = time.perf_counter()
    inst = instanz_aus_seed(s.n, s.seed)
    praemien = praemien_erste_runde(inst)
    erg = A.praemienweg(inst, praemien, s.t, s.k, max_labels=C.LABEL_CAP)
    fehler = None
    if erg.bester is not None:
        rc, weg, zeit = erg.bester
        if not A.pruefe_tour(inst, praemien, weg, s.t, rc, zeit):
            fehler = "Kosten, Zeit oder Zeitgrenze der Tour stimmen nicht mit der Nachrechnung überein."
    return GrossAnalyse(inst, praemien, s.t, s.k, erg, fehler, time.perf_counter() - t0)


# --- feste Messreihen ---------------------------------------------------------------------------------------------------------------------

def lade_baender(name: str) -> dict:
    """Liest data/baender_<name>.json (name: zeitgrenze oder fensterbreite)."""
    return json.loads((DATA / f"baender_{name}.json").read_text(encoding="utf-8"))


def faktoren(werte: list) -> list[float]:
    """Faktor von Stufe zu Stufe: jeder Wert geteilt durch den vorherigen."""
    return [b / a for a, b in zip(werte, werte[1:])]


# --- Verdikte -----------------------------------------------------------------------------------------------------------------------------

def verdict_grenze(T, dijkstra, bester, schnellste) -> tuple[str, str]:
    """Kernfrage der Handnetz-Ansicht: verletzt der billigste Weg die Grenze, bindet sie nicht, oder gibt es keinen zulässigen Weg?"""
    if bester is None:
        t_min = "keine" if schnellste is None else zahl(schnellste)
        return "warning", f"**Kein zulässiger Weg:** Der schnellste Weg braucht Zeit {t_min}, die Grenze ist T = {zahl(T)}."
    dk, dz, dw = dijkstra
    bk, bz, bw = bester
    if dz > T:
        return "warning", (f"**Der billigste Weg verletzt die Grenze:** {weg_text(dw)} kostet {zahl(dk)}, braucht aber Zeit {zahl(dz)} > T = {zahl(T)}. "
                           f"Der billigste zulässige Weg ist {weg_text(bw)} mit Kosten {zahl(bk)} und Zeit {zahl(bz)}: die Grenze kostet {zahl(bk - dk)} Kosteneinheiten.")
    return "success", (f"**Die Grenze bindet nicht:** Der billigste Weg {weg_text(dw)} kostet {zahl(dk)} und braucht Zeit {zahl(dz)} ≤ T = {zahl(T)}; "
                       "die Grenze ändert das Ergebnis nicht.")


def verdict_schritte(T, erg: A.NetzErgebnis) -> tuple[str, str]:
    """Verdikt der Schritt-für-Schritt-Ansicht: Zählung am Ende des Verfahrens."""
    paare = ", ".join(f"({zahl(k)}, {zahl(z)})" for k, z in erg.ziel_labels) or "keine"
    return "info", (f"Bei T = {zahl(T)} erzeugt das Verfahren {zahl(erg.erzeugt)} Labels (mit dem Start), davon {zahl(erg.dominiert)} durch Dominanz verworfen oder verdrängt; "
                    f"{zahl(erg.zu_spaet)} Verlängerungen entstehen wegen Zeit > T gar nicht erst. Am Ziel bleiben diese (Kosten, Zeit)-Paare: {paare}.")


def verdict_treppe(zeilen: list, dijkstra_zeit) -> tuple[str, str]:
    """Verdikt der Treppe: Zahl der Stufen, kleinste zulässige Grenze, Grenze ab der sie nicht mehr bindet. Zeilen: Dicts mit T und kosten (None = unzulässig)."""
    gueltig = [z for z in zeilen if z["kosten"] is not None]
    if not gueltig:
        return "warning", "In diesem Bereich der Grenze gibt es keinen zulässigen Weg."
    stufen = sorted({z["kosten"] for z in gueltig}, reverse=True)
    t_erst = gueltig[0]["T"]
    binden_bis = max((z["T"] for z in zeilen if z["T"] < dijkstra_zeit), default=None)
    text = (f"Von T = {zahl(zeilen[0]['T'])} bis T = {zahl(zeilen[-1]['T'])} nehmen die Kosten des besten zulässigen Weges {zahl(len(stufen) - 1)}-mal ab, "
            f"von {zahl(stufen[0])} auf {zahl(stufen[-1])} (insgesamt {zahl(len(stufen))} Stufen). ")
    text += f"Kleinste zulässige Grenze: T = {zahl(t_erst)}. "
    if binden_bis is None:
        text += f"Die Grenze bindet in diesem Bereich nirgends (der billigste Weg braucht Zeit {zahl(dijkstra_zeit)})."
    else:
        text += f"Die Grenze bindet für T < {zahl(dijkstra_zeit)} (so lange braucht der billigste Weg)."
    return "info", text


def verdict_gross(T, n, k, erg: A.PraemienErgebnis, elementar: bool | None) -> tuple[str, str]:
    """Verdikt des Größenreglers: abgebrochen, keine Tour mit negativen Kosten, oder die gefundene Tour; dazu Labels und Anteil dominiert."""
    anteil = 100 * erg.dominiert / erg.erzeugt if erg.erzeugt else 0.0
    zaehlung = (f"Das Verfahren erzeugt {zahl(erg.erzeugt)} Labels, davon {prozent(anteil)} durch Dominanz verworfen oder verdrängt. "
                f"Bei T = {zahl(T)} sind {zahl(erg.erreichbar)} von {zahl(n)} Kunden einzeln erreichbar (Hin- und Rückfahrt zum Depot samt Bedienzeit innerhalb der Grenze).")
    if erg.abgebrochen:
        return "warning", f"**Abgebrochen:** Nach {zahl(erg.erzeugt)} erzeugten Labels hat die Rechnung aufgehört (Obergrenze {zahl(C.LABEL_CAP)}); die Zahlen sind untere Schranken. {zaehlung}"
    if erg.bester is None:
        return "info", f"**Keine Tour mit negativen Kosten:** Keine zulässige Tour bringt mehr Prämie ein, als sie an Fahrt kostet. {zaehlung}"
    rc, weg, zeit = erg.bester
    zusatz = "" if elementar else f" Der Weg besucht einen Kunden mehrfach: bei k = {zahl(k)} ist das erlaubt."
    return "success", (f"**Beste Tour:** {zahl(len(weg))} Kunden, Kosten {zahl(rc, 2)} (Entfernungen minus Prämien), Gesamtzeit {zahl(zeit, 1)} ≤ T = {zahl(T)}.{zusatz} {zaehlung}")


def verdict_baender(zeilen: list, schluessel: str, wovon: str, stufe: str, faktor_min: float = C.FAKTOR_WAECHST) -> tuple[str, str]:
    """Verdikt einer Messreihe: bei wie vielen Stufenwechseln liegt der Median der Labels mindestens um `faktor_min` höher als auf der Stufe davor?

    `wovon`: das, wogegen gemessen wird, mit Artikel (z. B. „der Zeitgrenze“); `stufe`: der Name der Stufe im Text (z. B. „T“)."""
    meds = [z["labels_median"] for z in zeilen]
    fs = faktoren(meds)
    waechst = sum(1 for f in fs if f >= faktor_min)
    stufen = [z[schluessel] for z in zeilen]
    kern = f"Der Median der Labels liegt bei {zahl(waechst)} von {zahl(len(fs))} Stufenwechseln mindestens um den Faktor {zahl(faktor_min, 1)} höher"
    if waechst == len(fs):
        urteil = f"Die Label-Zahl wächst mit {wovon}: "
    elif waechst == 0:
        urteil = f"Gleichauf bei {wovon}: "
    else:
        urteil = f"Die Label-Zahl wächst mit {wovon} nur zwischen einem Teil der Stufen: "
    med0 = zahl(meds[0], 1 if meds[0] % 1 else 0)
    med1 = zahl(meds[-1], 1 if meds[-1] % 1 else 0)
    return "info", (f"{urteil}{kern} (kleinster Faktor {zahl(min(fs), 2)}, größter {zahl(max(fs), 2)}). "
                    f"Bei {stufe} = {zahl(stufen[0])} liegt der Median bei {med0}, bei {stufe} = {zahl(stufen[-1])} bei {med1} (Faktor {zahl(meds[-1] / meds[0], 1)}).")


def verdict_bruecke(T, ergebnis: A.NetzErgebnis, front: A.NetzErgebnis) -> tuple[str, str]:
    """Verdikt der Brücke: Was die Front liefert, was die eingebaute Grenze spart."""
    abgelesen = aus_front_ablesen(front.ziel_labels, T)
    spart = front.erzeugt - ergebnis.erzeugt
    if abgelesen is None:
        return "warning", (f"Aus den {zahl(len(front.ziel_labels))} Paaren der Front lässt sich für T = {zahl(T)} nichts ablesen: kein Paar ist so schnell. "
                           f"Mit eingebauter Grenze erzeugt das Verfahren {zahl(ergebnis.erzeugt)} Labels statt {zahl(front.erzeugt)} ohne Grenze.")
    k, z = abgelesen
    ersparnis = f"spart {zahl(spart)} von {zahl(front.erzeugt)} Labels" if spart > 0 else f"spart hier nichts ({zahl(front.erzeugt)} Labels ohne Grenze, {zahl(ergebnis.erzeugt)} mit Grenze)"
    return "info", (f"Aus den {zahl(len(front.ziel_labels))} Paaren der Front gelesen: für T = {zahl(T)} Kosten {zahl(k)} bei Zeit {zahl(z)}. "
                    f"Mit eingebauter Grenze kommt dasselbe heraus, und die Grenze {ersparnis}.")


# --- Texte der Schritt-für-Schritt-Ansicht ------------------------------------------------------------------------------------------------

def label_text(nr, kosten, zeit, knoten=None) -> str:
    teile = f"Knoten {knoten}, " if knoten is not None else ""
    return f"L{nr} = ({teile}Kosten {zahl(kosten)}, Zeit {zahl(zeit)})"


def ereignis_text(e: A.Ereignis, T) -> str:
    """Der Satz zu einem Ereignis des Verfahrens (reine Funktion der Daten des Ereignisses)."""
    if e.art == "start":
        return f"Start: {label_text(0, 0, 0, e.knoten)}."
    if e.art == "nimm":
        return f"Nimm {label_text(e.label, *e.werte, e.knoten)}: das offene Label mit der kleinsten Zeit. Es wird über jede ausgehende Kante verlängert."
    if e.art == "ueberspringe":
        return f"L{e.label} (Knoten {e.knoten}, Kosten {zahl(e.werte[0])}, Zeit {zahl(e.werte[1])}) ist inzwischen dominiert und wird übersprungen."
    v, w, kk, kz = e.kante if e.kante else (None, None, None, None)
    if e.art == "zu_spaet":
        return f"Kante {v}→{w} (Kosten {zahl(kk)}, Zeit {zahl(kz)}): Zeit {zahl(e.werte[1])} > T = {zahl(T)}, das Label wird gar nicht erst gebildet."
    if e.art == "neu":
        return f"Kante {v}→{w}: {label_text(e.label, *e.werte, e.knoten)} bleibt."
    if e.art == "verworfen":
        ak, az = e.anderes_werte
        return (f"Kante {v}→{w}: {label_text(e.label, *e.werte, e.knoten)} wird von L{e.anderes} dominiert "
                f"(Kosten {zahl(ak)} ≤ {zahl(e.werte[0])}, Zeit {zahl(az)} ≤ {zahl(e.werte[1])}) und verworfen.")
    if e.art == "verdraengt":
        ak, az = e.anderes_werte
        return (f"Kante {v}→{w}: {label_text(e.label, *e.werte, e.knoten)} dominiert das alte L{e.anderes} "
                f"(Kosten {zahl(ak)}, Zeit {zahl(az)}); L{e.anderes} entfällt.")
    if e.art == "ende":
        if e.werte is None:
            return "Fertig: Am Ziel liegt kein Label, es gibt keinen zulässigen Weg."
        return f"Fertig: Das billigste Label am Ziel hat Kosten {zahl(e.werte[0])} und Zeit {zahl(e.werte[1])}."
    raise ValueError(f"unbekannte Ereignisart {e.art}")
