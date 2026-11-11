"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

# --- Handnetz ---------------------------------------------------------------------------------------------------------------------------
T_HAND_MIN, T_HAND_MAX, DEFAULT_T_HAND = 7, 16, 10   # Zeitgrenze im Handnetz; 7 ist unter der schnellsten Fahrt (8), 15 ist die Zeit des billigsten Weges

# --- Kundeninstanz (Größenregler) --------------------------------------------------------------------------------------------------------
# Komplexität am Regler-Maximum: Die Zahl der Labels wächst mit T und k stark (gemessen mit diesem Kern, Zufalls-Seeds 0 bis 11, n = 20, k = 5:
# Median 4,5 Labels bei T = 60, rund 26 700 bei T = 300; siehe data/baender_zeitgrenze.json); jedes neue Label wird gegen die lebenden Labels seines Knotens geprüft. Deshalb gilt LABEL_CAP.
N_MIN, N_MAX, DEFAULT_N = 8, 20, 12                  # Zahl der Kunden
T_MIN, T_MAX, T_STEP, DEFAULT_T = 60, 300, 10, 100   # Zeitgrenze (Gesamtzeit einer Tour einschließlich Rückweg zum Depot)
K_MIN, K_MAX, DEFAULT_K = 1, 8, 5                    # Gedächtnis: Zahl der nächsten Kunden, an die sich ein Label erinnert
SEED_MAX, DEFAULT_SEED = 999999, 7
SERVICE_TIME = 10.0                                  # Bedienzeit je Kunde
GRID = 100.0                                         # Kantenlänge des Quadrats
LABEL_CAP = 400_000                                  # Abbruch einer Rechnung nach so vielen erzeugten Labels (Schutz vor Hängern)

# --- feste Messreihen -------------------------------------------------------------------------------------------------------------------
SWEEP_SEEDS = tuple(range(12))                       # Zufalls-Seeds 0 bis 11: feste Instanzen für die Messreihe über T
BAND_N, BAND_K = 20, 5
BAND_T = (60, 80, 100, 150, 200, 250, 300)
FAKTOR_WAECHST = 1.5                                 # Verdikt „wächst“ erst ab diesem Faktor zwischen zwei Stufen

# --- Darstellung ------------------------------------------------------------------------------------------------------------------------
COLOR_BEST = "#2F6B65"
COLOR_DIJKSTRA = "#d98a2b"
COLOR_EDGE = "rgba(150,150,150,0.6)"
COLOR_NODE = "#4c78a8"
COLOR_ACTIVE = "#c0392b"
COLOR_OTHER = "rgba(150,150,150,0.55)"
COLOR_LINE = "#4c78a8"

# --- Voreinstellungen (Schnellstart) -----------------------------------------------------------------------------------------------------
PRESETS = {
    "Handnetz, Grenze T = 10": {"t_hand": 10, "n": DEFAULT_N, "t": DEFAULT_T, "k": DEFAULT_K, "seed": DEFAULT_SEED},
    "Handnetz, Grenze bindet nicht (T = 15)": {"t_hand": 15, "n": DEFAULT_N, "t": DEFAULT_T, "k": DEFAULT_K, "seed": DEFAULT_SEED},
    "Handnetz, kein zulässiger Weg (T = 7)": {"t_hand": 7, "n": DEFAULT_N, "t": DEFAULT_T, "k": DEFAULT_K, "seed": DEFAULT_SEED},
    "20 Kunden, Grenze 150": {"t_hand": DEFAULT_T_HAND, "n": 20, "t": 150, "k": DEFAULT_K, "seed": DEFAULT_SEED},
    "20 Kunden, Grenze 250": {"t_hand": DEFAULT_T_HAND, "n": 20, "t": 250, "k": DEFAULT_K, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Handnetz, Grenze T = 10": "Das kleine Netz mit 7 Knoten und der Zeitgrenze 10: der billigste Weg ist zu langsam, der billigste zulässige Weg kostet mehr.",
    "Handnetz, Grenze bindet nicht (T = 15)": "Dasselbe Netz mit Grenze 15: der billigste Weg ist gerade noch zulässig, die Grenze ändert das Ergebnis nicht.",
    "Handnetz, kein zulässiger Weg (T = 7)": "Dasselbe Netz mit Grenze 7: kein Weg vom Start zum Ziel ist so schnell.",
    "20 Kunden, Grenze 150": "Kundeninstanz mit 20 Kunden und Zeitgrenze 150: alle 20 Kunden sind einzeln erreichbar, das Verfahren erzeugt weniger als 1 000 Labels.",
    "20 Kunden, Grenze 250": "Dieselbe Instanz mit Zeitgrenze 250: das Verfahren erzeugt mehr als 10 000 Labels.",
}
