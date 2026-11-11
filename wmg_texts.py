"""Längere Texte der App an einer Stelle: App und README zeigen denselben Wortlaut (`tests/test_claims.py` sucht den Text der App in der README)."""

ASSUMPTIONS_MARKDOWN = """\
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
"""
