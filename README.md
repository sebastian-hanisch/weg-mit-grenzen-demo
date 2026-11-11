# Ressourcenweg – der billigste Weg mit Grenze – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-weg-mit-grenzen-demo.streamlit.app/)**

Demo der Reihe „Ressourcenwege und Spaltenerzeugung“ in der „Konzepte“-Reihe der Website „Sebastian Hanisch – Operations Research und Machine Learning“. Sie ist der Einstieg in die Frage, wie man in einem Netz den **billigsten Weg findet, wenn die Zeit eine Grenze hat**. Das Vehikel ist ein Netz mit 7 Knoten, das sich von Hand nachrechnen lässt, und eine selbst erzeugte Kundeninstanz im Stil der Solomon-Benchmarks (nicht die Originalinstanzen), an der die Zahl der Labels gemessen wird. Solche Wegsuchen sind das Teilproblem („Pricing“) der Spaltenerzeugung, etwa in [crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo); diese Demo erklärt das Verfahren dahinter.

## Kernfrage

Der billigste Weg und der billigste **zulässige** Weg sind verschiedene Wege, sobald eine Grenze gilt. Um den zweiten zu finden, genügt pro Knoten keine Zahl mehr (der kleinste Kostenwert wie bei Dijkstra), sondern eine Liste von **Labels** aus (Kosten, verbrauchte Zeit). Wie lang diese Listen werden, hängt davon ab, wie viel Zeit die Grenze erlaubt. Ein **Label** steht für einen Weg bis zu einem Knoten; ein Label **dominiert** ein anderes am selben Knoten, wenn es höchstens so viel kostet und höchstens so viel Zeit braucht.

## Modell

- **Handnetz:** 7 Knoten (0 = Start, 6 = Ziel), 12 Kanten mit ganzzahligen Kosten und Zeiten, keine Kreise. Gesucht ist der billigste Weg von 0 nach 6 mit Gesamtzeit höchstens T (genau T ist zulässig).
- **Kundeninstanz:** Depot in der Mitte eines Quadrats von 100 × 100, 8 bis 20 gleichverteilte Kunden, Fahrzeit gleich Entfernung, Bedienzeit 10 je Kunde. Gesucht ist die Tour ab Depot und zurück mit den kleinsten Kosten, wobei die Kosten die Entfernungen **minus eine Prämie je besuchtem Kunden** sind (das Doppelte seiner Entfernung zum Depot). Die Gesamtzeit einschließlich Rückweg darf T nicht übersteigen. Ein Label merkt sich zusätzlich, welche der k nächsten Kunden jedes besuchten Kunden (den Kunden selbst eingerechnet) schon dran waren (Gedächtnis k); bei k = 1 merkt es sich nur den zuletzt besuchten Kunden selbst, die Wiederkehr nach einem anderen Kunden (a-b-a) bleibt erlaubt.
- Die Formeln stehen im Expander **📐 Mathematische Formulierung** der App mit Lesehilfe und Symboltabelle.

## Methodik

Label-Setting: Das offene Label mit der kleinsten Zeit wird über jede ausgehende Kante verlängert; übersteigt die neue Zeit die Grenze, entsteht das Label nicht. Ein neues Label, das von einem lebenden Label des Knotens dominiert wird, wird verworfen; ein neues Label, das lebende Labels dominiert, verdrängt sie. Am Ziel liegt am Ende die Liste der nicht dominierten (Kosten, Zeit)-Paare; das billigste ist die Antwort. Gezählt werden **erzeugte Labels**, nicht Sekunden. Dazu stehen im Handnetz Dijkstra (nur Kosten) und eine Aufzählung aller Wege als Gegenprobe.

Fünf Experimente in der App: (1) das Handnetz Schritt für Schritt, (2) die Treppe der Kosten gegen die Grenze, (3) ein Größenregler für Kundeninstanzen, (4) Bänder aus festen Messreihen, (5) die Brücke zu Dijkstra und zur Pareto-Front.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an festen Instanzen. Die Zahl-zu-Test-Tabelle am Ende dieses Abschnitts nennt für jede Zahl den Test.

**Handnetz** (7 Knoten, 12 Kanten, ganze Zahlen):

- Es gibt 11 Wege vom Start zum Ziel. Dijkstra nach Kosten liefert den Weg 0-1-4-6 mit Kosten 7 und Zeit 15. Bei T = 10 ist er unzulässig; der billigste zulässige Weg ist 0-2-5-6 mit Kosten 12 und Zeit 9, also 5 Kosteneinheiten teurer.
- Die Kosten des besten zulässigen Weges bilden eine **Treppe** über T: bei T = 8 sind es 16, bei T = 9 bis 11 sind es 12, bei T = 12 bis 14 sind es 8 und ab T = 15 sind es 7; bei T = 7 gibt es keinen zulässigen Weg. Die Stufen sind genau die vier nicht dominierten (Kosten, Zeit)-Paare am Ziel: (7, 15), (8, 12), (12, 9) und (16, 8).
- Bei T = 10 erzeugt das Verfahren 15 Labels (mit dem Start), davon werden 3 durch Dominanz verworfen oder verdrängt, und 5 Verlängerungen entstehen wegen Zeit > T gar nicht erst. Erzeugte Labels für T = 7 bis 16: 10, 12, 15, 15, 17, 18, 19, 19, 20, 21.
- Ohne Grenze (T unbegrenzt) erzeugt das Verfahren 21 Labels, 15 davon bleiben am Ende lebendig (je Knoten 1, 1, 2, 1, 3, 3, 4). Dijkstra setzt je Knoten einen Wert, also 7. Aus der Front lässt sich für T = 10 ablesen: Kosten 12 bei Zeit 9; die eingebaute Grenze liefert dasselbe mit 15 statt 21 Labels.

**Kundeninstanz, ein Aufruf des Verfahrens je Instanz** (20 Kunden, Gedächtnis k = 5, 12 Instanzen mit den Zufalls-Seeds 0 bis 11, Zeitfenster weit offen, Kapazität unbegrenzt, Prämien der ersten Runde; Median, Mittel und Maximum der erzeugten Labels):

| Zeitgrenze T | erreichbare Kunden (Median) | Labels (Median) | Labels (Mittel) | Labels (Maximum) | dominiert (Mittel) | Instanzen mit Gewinn-Tour |
|---|---|---|---|---|---|---|
| 60 | 3,5 | 4,5 | 5,0 | 13 | 0,0 % | 1 von 12 |
| 80 | 7,0 | 15,5 | 21,5 | 67 | 1,6 % | 12 von 12 |
| 100 | 13,5 | 51 | 74,7 | 295 | 9,2 % | 12 von 12 |
| 150 | 20,0 | 874 | 1 138,2 | 4 076 | 55,6 % | 12 von 12 |
| 200 | 20,0 | 5 284 | 6 191,3 | 14 697 | 80,4 % | 12 von 12 |
| 250 | 20,0 | 14 728 | 16 693,2 | 31 052 | 88,1 % | 12 von 12 |
| 300 | 20,0 | 26 678,5 | 30 430,2 | 52 013 | 90,7 % | 12 von 12 |

„Gewinn-Tour“ heißt: Es gibt eine zulässige Tour mit negativen Kosten, die Prämien übersteigen also die Fahrt.

- Der Median der Labels liegt bei 6 von 6 Stufenwechseln mindestens um den Faktor 1,5 höher als auf der Stufe davor (kleinster Faktor 1,81 von T = 250 auf 300, größter 17,14 von T = 100 auf 150). Von T = 60 auf T = 300 steigt der Median um den Faktor 5 928,6.
- Ab T = 150 ist der Median der einzeln erreichbaren Kunden 20, also alle; das Wachstum von T = 150 auf T = 300 (Median-Faktor 30,5) kommt in dieser Reihe nicht von neuen Kunden.
- Bei T = 60 hat nur 1 von 12 Instanzen eine Tour mit negativen Kosten, ab T = 80 haben alle 12 eine.
- Gedächtnis k bei T = 200 (20 Kunden, dieselben 12 Instanzen): Der Median der Labels beträgt bei k = 1, 2, 3, 5, 8 der Reihe nach 2 436,5, 3 071,5, 3 766, 5 284 und 7 428,5; in allen 12 Instanzen nimmt die Zahl der Labels mit k nicht ab. Bei T = 100 gilt das nicht in allen Instanzen.

**Dieselbe Frage in einer ganzen Spaltenerzeugung** (frühere Messreihe, nicht in dieser Demo neu gerechnet: 30 Kunden, Zeitfenster der Breite 40, 100 und 200, Kapazität 70, 6 Instanzen je Zelle, Summe der Labels aller Pricing-Aufrufe bis zur Konvergenz). Hier steht nicht die Zeitgrenze, sondern die **Fensterbreite**:

| Fensterbreite | Gedächtnis k | Labels (Median) | Labels (Mittel) | Labels (Maximum) | dominiert (Mittel) |
|---|---|---|---|---|---|
| 40 | 1 | 16 938,5 | 18 507,0 | 27 482 | 82,3 % |
| 40 | 5 | 20 904,5 | 24 961,8 | 40 811 | 78,2 % |
| 100 | 1 | 57 329,5 | 58 388,8 | 69 898 | 87,2 % |
| 100 | 5 | 92 037,5 | 89 481,5 | 102 222 | 84,3 % |
| 200 | 1 | 160 456,5 | 170 765,2 | 223 226 | 91,4 % |
| 200 | 5 | 348 903,5 | 362 708,8 | 543 446 | 89,5 % |

Der Median der Labels liegt bei beiden Gedächtnisgrößen in beiden Stufenwechseln (Breite 40 auf 100 und 100 auf 200) mindestens um den Faktor 1,5 höher: bei k = 1 mit den Faktoren 3,38 und 2,80, bei k = 5 mit 4,40 und 3,79. Ein Median aus 6 Instanzen ist das Mittel der beiden mittleren Werte, deshalb kann er auf ,5 enden (hier tut er es in allen sechs Zellen).

**Voreinstellungen der Kundeninstanz** (Zufalls-Seed 7, k = 5): Mit 12 Kunden und T = 100 erzeugt das Verfahren 22 Labels (davon 1 dominiert), die beste Tour hat 3 Kunden und Kosten -57,30. Mit 20 Kunden und T = 150 sind es 798 Labels (davon 465 dominiert), alle 20 Kunden sind einzeln erreichbar, die beste Tour hat 4 Kunden. Mit 20 Kunden und T = 250 sind es 12 728 Labels (davon 11 035 dominiert), die beste Tour hat 7 Kunden und Kosten -440,83.

**Gegenprobe mit einer unabhängigen früheren Implementierung.** Rechnet man die 12 Instanzen der Messreihe über T mit Pythons `random.Random(seed)` statt mit dem Zufalls-Seed dieser Demo, liefert dieser Kern dieselben Mediane wie ein früheres Mess-Skript ohne Last: 8, 21 und 65,5 bei T = 60, 80, 100 sowie 938,5 und 5 831 bei T = 150 und 200. Das frühere Skript liegt nicht im Repo; die Übereinstimmung mit ihm ist hier nicht nachprüfbar, nachprüfbar sind die Mediane mit `random.Random` (`tests/test_claims.py::test_cross_check_with_the_earlier_implementation`).

| Zahl | Test |
|---|---|
| Handnetz: 11 Wege, Dijkstra, T = 10, Treppe, Zählungen | `tests/test_claims.py::test_handnetz_claims`, `tests/test_algorithm.py` |
| Labels für T = 7 bis 16, ohne Grenze 21 und 15, Brücke | `tests/test_claims.py::test_handnetz_label_counts_and_bridge` |
| Tabelle über T (Mediane, Mittel, Maximum, dominiert, erreichbar, Gewinn-Tour) | `tests/test_claims.py::test_readme_tables_are_generated_from_the_data`, `tests/test_baender.py` (Neuberechnung aller 12 Instanzen für T bis 200, Stichprobe für T = 250 und 300) |
| Faktoren 1,81 / 17,14 / 5 928,6 / 30,5, 6 von 6 Stufenwechseln | `tests/test_claims.py::test_growth_claims_over_the_limit` |
| Gewinn-Tour 1 von 12 bei T = 60 | `tests/test_claims.py::test_growth_claims_over_the_limit` |
| Gedächtnis k bei T = 200 | `tests/test_claims.py::test_memory_claim_at_t200` |
| Tabelle über die Fensterbreite und ihre Faktoren | `tests/test_claims.py::test_readme_tables_are_generated_from_the_data`, `tests/test_claims.py::test_window_width_factors`, `tests/test_baender.py` (Zusammenfassung aus den Einzelwerten; nicht neu rechenbar) |
| Voreinstellungen der Kundeninstanz | `tests/test_claims.py::test_size_presets_numbers` |
| Gegenprobe mit `random.Random` | `tests/test_claims.py::test_cross_check_with_the_earlier_implementation` |

## Befunde und Korrekturen gegenüber der früheren Messreihe

- In einer früheren Messreihe derselben Frage (n = 20, k = 5, 12 Instanzen, T = 60 bis 300) ging die Last der Kunden in die Dominanzregel ein, obwohl die Kapazität unbegrenzt war und sie nie binden konnte. Das macht Dominanz schwächer und die Label-Zahl größer: bei T = 150 war der Median 1 039,5 statt 938,5, bei T = 200 7 744 statt 5 831 (gleiche Instanzen, `random.Random`). Diese Demo lässt die nicht bindende Last weg; bis T = 100 sind beide Reihen gleich (8, 21, 65,5), ab T = 150 gilt die Zahl ohne Last. Die Tabelle oben ist neu gerechnet; die früheren Zahlen für T ≥ 150 stehen nur hier und sind nicht durch einen Test belegt (der Kern dieser Demo kennt keine Last).
- Die Instanzen der Messreihe über T stammen aus dem Zufalls-Seed-Generator dieser Demo (SplitMix64), nicht aus Pythons `random`; die Zahlen unterscheiden sich daher von der früheren Messreihe auch bei kleinen T (Median bei T = 60: 4,5 statt 8).

## Ehrliche Grenzen

Annahmen, Grenzen und bekannte Probleme (derselbe Wortlaut wie im Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** der App):

**Annahmen**

- **Handnetz:** 7 Knoten, 12 Kanten, ganze Zahlen für Kosten und Zeit je Kante, keine Kreise. Kosten und Zeit sind nicht negativ.
- **Kundeninstanz:** selbst erzeugt im Stil der Solomon-Benchmarks (nicht die Originalinstanzen), 8 bis 20 Kunden gleichverteilt im Quadrat 100 × 100, Fahrzeit gleich Entfernung, Bedienzeit 10 je Kunde, Zeitfenster weit offen, Kapazität unbegrenzt.
- **Prämien:** je Kunde das Doppelte seiner Entfernung zum Depot (die Dualpreise der ersten Runde einer Spaltenerzeugung, nicht die einer konvergierten).
- **Messgröße:** erzeugte Labels. Sekunden stehen nur zur Information da und sind nicht festgeschrieben.

**Grenzen**

- Es gibt genau eine begrenzte Größe, die Zeit. Über Dominanz entscheiden Kosten und Zeit (in der Kundeninstanz zusätzlich das Gedächtnis).
- Die Messreihe über die Zeitgrenze hat 12 Instanzen je Zelle (20 Kunden), die über die Fensterbreite 6 Instanzen je Zelle (30 Kunden): Median, Mittel und Maximum, keine Aussage über die ganze Verteilung.
- Die Reihe über die Fensterbreite stammt aus einer früheren Messreihe und wird in der Demo nicht neu gerechnet. Die Zeitgrenze bei 30 oder mehr Kunden ist nicht gemessen.
- Keine Aussage über öffentliche Benchmarks, andere Programmiersprachen oder Rechner.

**Bekannte Probleme und Unsicherheiten**

- Die beiden Messreihen beantworten dieselbe Frage unter verschiedenen Bedingungen (Zeitgrenze bei weiten Fenstern ohne Kapazität; Fensterbreite in einer ganzen Spaltenerzeugung mit Kapazität 70) und sind nicht direkt vergleichbar.
- Bei Gedächtnis k kleiner als die Zahl der Kunden kann eine Tour einen Kunden mehrfach besuchen; die App meldet das, wenn es vorkommt.
- Die Ansichten wurden mit Streamlits Testwerkzeug und im Browser (Desktop und Telefonbreite) durchgesehen, nicht auf allen Geräten.

## Literatur

- Irnich, Desaulniers (2005): *Shortest Path Problems with Resource Constraints*, in: Column Generation, Springer, S. 33–65 (DOI 10.1007/0-387-25486-2_2). Standardreferenz zu Problem, Labeling und Dominanz. Prüfstand: Angaben (Autoren, Jahr, Seiten, Kapitel) in Verzeichniseinträgen von Springer und EconPapers gesehen; **weder Abstract noch Volltext gelesen**. Keine Zahl dieser Demo stammt aus der Literatur.
- Desrochers, Soumis (1988): *A generalized permanent labelling algorithm for the shortest path problem with time windows*, INFOR 26(3), S. 191–212. Prüfstand: Angaben in einem Literaturverzeichnis einer anderen Arbeit gesehen; Abstract und Volltext nicht gelesen.
- Hansen (1980) und Martins (1984) für das Label-Setting zur Pareto-Front: so in der README von [multicriteria-demo](https://github.com/sebastian-hanisch/multicriteria-demo) genannt, hier nicht gelesen.

## Abgrenzung zu anderen Demos

- [multicriteria-demo](https://github.com/sebastian-hanisch/multicriteria-demo) zeigt das Label-Setting für die ganze Pareto-Front (Zeit gegen CO₂). Hier wirkt die Grenze **im** Verfahren: Labels über der Grenze entstehen nicht, und die Label-Zahl wird gegen den Bereich der Grenze gemessen.
- [dijkstra-demo](https://github.com/sebastian-hanisch/dijkstra-demo) zeigt den Fall ohne Grenze: ein Wert je Knoten.
- [crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo) verwendet ein solches Verfahren als Pricing in einer Fall-Demo; Zahlen von dort werden nicht übernommen.
- [hub-labeling-demo](https://github.com/sebastian-hanisch/hub-labeling-demo) meint mit „Label“ etwas anderes: Einträge in Listen, die für schnelle Abfragen kürzester Wege zusammengeführt werden. Hier ist ein Label ein Weg bis zu einem Knoten mit seinen Kosten und seiner Zeit.

## Tests

152 Tests (`pytest --collect-only -q tests`), alle im Ordner `tests/`:

- **Handrechnung:** `tests/conftest.py` enthält das Handnetz und die Mini-Kundeninstanz von Hand; die erwarteten Werte stehen als Summen der Kantenwerte da (`tests/test_algorithm.py`).
- **Orakel** (`tests/test_oracle_weg_mit_grenzen.py`): Tiefensuche über alle einfachen Wege gegen das Label-Setting auf Zufallsnetzen (auch mit Kreisen und Kanten mit Zeit 0), Front und lebende Labels je Knoten gegen die Pareto-Mengen der Aufzählung, networkx gegen Dijkstra, Tiefensuche über alle Touren gegen das Verfahren mit Gedächtnis k = Zahl der Kunden.
- **Eigenschaften** (`tests/test_eigenschaften_weg_mit_grenzen.py`): Kosten sinken nie mit wachsender Grenze, Zeit des Ergebnisses höchstens T, Ergebnis ohne Grenze gleich Dijkstra, Umnummerieren und Skalieren ändern nichts an den Label-Zahlen, gleicher Zufalls-Seed gleiche Ausgabe auch in einem zweiten Prozess mit anderem Hash-Seed.
- **Aussagen** (`tests/test_claims.py`, `tests/test_baender.py`, `tests/test_verdicts.py`): jede Zahl dieser README, jedes Verdikt mit seinen Schwellen, je Voreinstellung die erwartete Verdikt-Zeile.
- **Oberfläche:** AppTest für Standard, jeden Knopf, jeden Regler am Minimum und Maximum (einzeln und alle zugleich), jede Voreinstellung, Permalink und die Schritt-Ansicht; Layout, Footer und Laufzeit-Importe.
- Ein Test am Regler-Maximum (20 Kunden, T = 300, k = 8) hat nur eine Label-Obergrenze als Schutz, keine Zeit-Assertion.

Die Laufzeit der Suite hängt von der Auslastung der Maschine ab und steht deshalb hier nicht fest.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Kopf, Erklärung, Ergebnis, fünf Experimente, Grenzen, Formeln |
| `data/baender_zeitgrenze.json` | Messreihe über die Zeitgrenze (Einzelwerte je Instanz und Quelle je Zeile) |
| `data/baender_fensterbreite.json` | Zusammenfassung der früheren Messreihe über die Fensterbreite (Einzelwerte und Quelle je Zeile) |
| `requirements-dev.txt` | Laufzeit plus pytest und networkx |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tools/messreihe_baender.py` | erzeugt die beiden JSON-Dateien (Zeitgrenze: neu gerechnet; Fensterbreite: aus den Rohzeilen zusammengefasst) |
| `wmg_algorithm.py` | Kern: Dominanz, Einfügen, Label-Setting im Handnetz mit Ereignisprotokoll, Dijkstra, Aufzählung, Prüfer, Verfahren für die Kundeninstanz |
| `wmg_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Voreinstellungen |
| `wmg_evaluation.py` | Analysen, Verdikte als reine Funktionen, Texte der Schritt-Ansicht, Lader der Messreihen |
| `wmg_layout.py` | Fester Kopf (Stylesheet) |
| `wmg_presets.py` | Permalink (Begrenzen, Einrasten), Schnellstart in der Seitenleiste, aktives Preset hervorgehoben, Zufalls-Seed-Knopf |
| `wmg_rng.py` | SplitMix64 (plattformunabhängiger Zufall) |
| `wmg_scenario.py` | Handnetz und Instanzgenerator der Kundeninstanz |
| `wmg_texts.py` | Annahmen-Text (App und README zeigen denselben Wortlaut) |
| `wmg_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | siehe Abschnitt Tests |

## Bewusst nicht umgesetzt

- **Dominanzregeln im Detail** (wann Dominanz falsch wird, wenn eine Größe fehlt), **Zeitfenster mit Warten**, **eine zweite begrenzte Größe** und **negative Kosten aus Dualpreisen einer laufenden Spaltenerzeugung**: Diese Demo hat nur eine Grenze, die Zeit, und feste Prämien.
- **Elementare Wege**: Das Gedächtnis k ist nur als Regler da, damit sich ein Weg nicht im Kreis dreht; ob k ausreicht, wird nicht geprüft.
- **Zeitgrenze bei 30 oder mehr Kunden**, **Sekunden als Messgröße** und **ein PDF-Export** fehlen.
- Keine Aussagen über öffentliche Benchmarks.

## Lokal ausführen

Die Streamlit-Cloud-Einstellung für die Python-Version ist im Betrieb zu prüfen; die CI testet mit Python 3.12, lokal gemessen wurde mit 3.14. <!-- lint-ok: dezimalpunkt -->

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html).
