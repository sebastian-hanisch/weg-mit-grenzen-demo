"""Erzeugt die festen Messreihen (Bänder) der Demo als JSON unter data/.

    python tools/messreihe_baender.py zeitgrenze
        Rechnet die Reihe über die Zeitgrenze T neu (n = 20 Kunden, Gedächtnis k = 5, Zufalls-Seeds 0 bis 11) und schreibt
        data/baender_zeitgrenze.json.
    python tools/messreihe_baender.py fensterbreite PFAD/out_v1_n30.txt
        Liest die Rohzeilen einer früheren Messreihe (Spaltenerzeugung bis zur Konvergenz, 30 Kunden, Fensterbreite 40/100/200,
        6 Instanzen je Zelle) und schreibt data/baender_fensterbreite.json; gerechnet wird dabei nichts, nur zusammengefasst.

Gezählt werden erzeugte Labels, nie Sekunden. Jede Zeile des JSON nennt ihre Quelle."""

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import wmg_algorithm as A  # noqa: E402
import wmg_constants as C  # noqa: E402
import wmg_scenario as S  # noqa: E402


def messung_zeitgrenze(T: int, n: int = C.BAND_N, k: int = C.BAND_K, seeds=C.SWEEP_SEEDS) -> dict:
    """Ein Aufruf des Verfahrens je Instanz (Zufalls-Seed), Prämien der ersten Runde, Last unbegrenzt, Fenster weit offen."""
    labels, anteile, erreichbar, mit_route = [], [], [], 0
    for seed in seeds:
        inst = S.instanz_aus_seed(n, seed)
        r = A.praemienweg(inst, S.praemien_erste_runde(inst), T, k, max_labels=10 ** 9)
        assert not r.abgebrochen
        labels.append(r.erzeugt)
        anteile.append(r.dominiert / r.erzeugt)
        erreichbar.append(r.erreichbar)
        mit_route += 1 if r.bester is not None else 0
    return {
        "T": T,
        "instanzen": len(seeds),
        "labels_je_instanz": labels,
        "labels_median": statistics.median(labels),
        "labels_mittel": round(statistics.mean(labels), 1),
        "labels_max": max(labels),
        "dominiert_mittel_prozent": round(100 * statistics.mean(anteile), 1),
        "erreichbar_median": statistics.median(erreichbar),
        "instanzen_mit_route": mit_route,
        "quelle": f"tools/messreihe_baender.py zeitgrenze: n = {n}, k = {k}, Zufalls-Seeds {seeds[0]} bis {seeds[-1]}, T = {T}",
    }


def schreibe_json(pfad: Path, daten: dict) -> None:
    """Mit Zeilenende LF auf jeder Plattform."""
    with open(pfad, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(daten, ensure_ascii=False, indent=1) + "\n")


def schreibe_zeitgrenze() -> None:
    zeilen = [messung_zeitgrenze(T) for T in C.BAND_T]
    out = {
        "beschreibung": "Ein Aufruf des Verfahrens je Instanz; n = 20 Kunden, Gedächtnis k = 5, 12 Instanzen (Zufalls-Seeds 0 bis 11), Zeitfenster weit offen, "
                        "Last unbegrenzt, Prämien der ersten Runde (je Kunde das Doppelte der Entfernung zum Depot).",
        "zeilen": zeilen,
    }
    (ROOT / "data" / "baender_zeitgrenze.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for z in zeilen:
        print(z["T"], z["labels_median"], z["labels_mittel"], z["labels_max"], z["dominiert_mittel_prozent"], z["erreichbar_median"], z["instanzen_mit_route"])


def schreibe_fensterbreite(pfad: Path) -> None:
    quelle = pfad.name
    roh: dict[tuple[int, int], list] = {}
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        f = zeile.split()
        if len(f) != 11 or f[0] != "30":
            continue
        breite, seed, k = int(f[1]), int(f[2]), int(f[3])
        roh.setdefault((breite, k), []).append((seed, int(f[8]), float(f[9]), int(f[10])))
    zeilen = []
    for (breite, k), werte in sorted(roh.items()):
        if k not in (1, 5):
            continue
        assert all(w[3] == 0 for w in werte), (breite, k)       # keine abgebrochene Rechnung in den ausgewählten Zellen
        labels = [w[1] for w in werte]
        zeilen.append({
            "breite": breite, "k": k, "instanzen": len(werte),
            "labels_je_instanz": labels,
            "labels_median": statistics.median(labels),
            "labels_mittel": round(statistics.mean(labels), 1),
            "labels_max": max(labels),
            "dominiert_mittel_prozent": round(100 * statistics.mean(w[2] for w in werte), 1),
            "quelle": f"{quelle}: Zeilen mit n = 30, Fensterbreite {breite}, k = {k}, Zufalls-Seeds {werte[0][0]} bis {werte[-1][0]} der Messreihe",
        })
    out = {
        "beschreibung": "Summe der Labels aller Pricing-Aufrufe einer Spaltenerzeugung bis zur Konvergenz; 30 Kunden, Zeitfenster der Breite 40/100/200, "
                        "Kapazität 70, 6 Instanzen je Zelle. Rohzeilen einer früheren Messreihe, hier nur zusammengefasst, nicht neu gerechnet.",
        "zeilen": zeilen,
    }
    (ROOT / "data" / "baender_fensterbreite.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for z in zeilen:
        print(z["breite"], z["k"], z["instanzen"], z["labels_median"], z["labels_mittel"], z["labels_max"], z["dominiert_mittel_prozent"])


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "zeitgrenze":
        schreibe_zeitgrenze()
    elif len(sys.argv) >= 3 and sys.argv[1] == "fensterbreite":
        schreibe_fensterbreite(Path(sys.argv[2]))
    else:
        print(__doc__)
        sys.exit(2)
