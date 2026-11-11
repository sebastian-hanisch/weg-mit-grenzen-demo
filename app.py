"""Ressourcenweg – der billigste Weg mit Grenze: interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zeigt an einem Handnetz mit 7 Knoten und an Kundeninstanzen, warum der billigste Weg unter einer Zeitgrenze eine Liste von Labels
(Kosten, Zeit) je Knoten braucht und wie stark diese Listen mit der Grenze wachsen. Aufbau nach DEMO-PLAYBOOK §2.

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import wmg_algorithm as A
import wmg_constants as C
import wmg_evaluation as ev
import wmg_visualization as V
from wmg_layout import dunkles_design, kopf_css
from wmg_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from wmg_texts import ASSUMPTIONS_MARKDOWN

st.set_page_config(page_title="Ressourcenweg – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _hand(T):
    return ev.analyse_hand(T)


@st.cache_data(show_spinner=False)
def _gross(settings):
    return ev.analyse_gross(settings)


@st.cache_data(show_spinner=False)
def _baender(name):
    return ev.lade_baender(name)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in wmg_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🛣️ Ressourcenweg – der billigste Weg mit Grenze")
st.markdown(
    """
Jede Kante eines Netzes hat **Kosten** und braucht **Zeit**. Der billigste Weg lässt sich mit **Dijkstra** finden, solange die Zeit keine Rolle spielt. Gilt eine **Zeitgrenze T**,
kann der billigste Weg zu langsam sein, und der **billigste zulässige Weg** ist ein anderer. Dann genügt pro Knoten keine Zahl mehr, sondern eine Liste von **Labels**
(Kosten, verbrauchte Zeit). Diese Demo rechnet das an einem Netz mit 7 Knoten von Hand nach und misst, wie schnell die Listen wachsen, wenn die Grenze weiter wird.
Solche Wegsuchen mit Grenze sind das Teilproblem („Pricing“) der Spaltenerzeugung, etwa bei der Tourenplanung.

Weiter unten: fünf Experimente (🔬), der Abschnitt **🚧 Wo die Annahmen enden** und die Expander **📐 Mathematische Formulierung** und **⚠️ Annahmen, Grenzen und bekannte Probleme**.
"""
)

with st.expander("So funktioniert das Label-Setting mit Zeitgrenze", expanded=True):
    st.markdown(
        """
1. **Label:** Ein Label an einem Knoten steht für einen Weg dorthin und besteht aus (Kosten, verbrauchte Zeit). Am Start liegt das Label (0, 0).
2. **Verlängern:** Das Verfahren nimmt das offene Label mit der **kleinsten Zeit** und verlängert es über jede ausgehende Kante: Kosten und Zeit der Kante kommen dazu.
   Übersteigt die neue Zeit die Grenze T, entsteht das Label gar nicht erst (genau T ist zulässig).
3. **Dominanz:** Ein Label **dominiert** ein anderes am selben Knoten, wenn es höchstens so viel kostet **und** höchstens so viel Zeit braucht. Das dominierte Label wird verworfen.
4. **Am Ziel** bleibt eine Liste nicht dominierter Labels. Das mit den kleinsten Kosten ist der gesuchte Weg. Die ganze Liste ist die Antwort auf jede Grenze zugleich: Zu jeder Grenze T gehört das billigste Label mit Zeit höchstens T.
5. **Dijkstra als Sonderfall:** Zählen nur die Kosten, bleibt je Knoten ein Label übrig. Mit der Zeit als zweiter Größe können an einem Knoten mehrere Labels nebeneinander bestehen, weil keines das andere dominiert.

**Warum das funktioniert:** Ein Label, das teurer und langsamer ist als ein anderes am selben Knoten, kann auf jeder Fortsetzung nur mehr kosten und mehr Zeit brauchen. Es wird nie
Teil eines besseren zulässigen Weges und darf entfallen.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Handnetz (7 Knoten)**")
    t_hand = st.slider("Zeitgrenze T im Handnetz", *bounds("t_hand"), key="t_hand",
                       help="Höchste erlaubte Gesamtzeit eines Weges vom Start (Knoten 0) zum Ziel (Knoten 6). Wirkt auf die Abschnitte Ergebnis, Experiment 1, 2 und 5.")
    st.markdown("**Kundeninstanz (Experiment 3)**")
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help="Zahl der Kunden; das Depot liegt in der Mitte des Quadrats.")
    t = st.slider("Zeitgrenze T der Kundeninstanz", *bounds("t_slider"), step=C.T_STEP, key="t_slider",
                  help="Höchste Gesamtzeit einer Tour: Fahrzeit plus Bedienzeit 10 je Kunde, einschließlich Rückweg zum Depot.")
    k = st.slider("Gedächtnis k", *bounds("k_slider"), key="k_slider",
                  help="Ein Label merkt sich, ob die k nächsten Kunden jedes besuchten Kunden (den Kunden selbst eingerechnet) schon dran waren. Bei k = 1 merkt es sich nur den zuletzt besuchten Kunden selbst; die Wiederkehr nach einem anderen Kunden (a-b-a) bleibt erlaubt.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"t_hand": int(t_hand), "n_slider": int(n), "t_slider": int(t), "k_slider": int(k), "seed_input": int(seed)})

settings = ev.Settings(int(t_hand), int(n), int(t), int(k), int(seed))
h = _hand(settings.t_hand)
e = h.ergebnis
if h.fehler:
    st.error(f"Prüfung des Ergebnisses fehlgeschlagen: {h.fehler}")

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: das Handnetz")
dk, dz, dweg = h.dijkstra
m1, m2, m3 = st.columns(3)
m1.metric("Billigster Weg ohne Grenze (Dijkstra)", f"Kosten {dk}", delta=f"Zeit {dz}", delta_color="off")
if e.bester is not None:
    bk, bz, bweg = e.bester
    # Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2).
    m2.metric(f"Billigster zulässiger Weg (T = {settings.t_hand})", f"Kosten {bk}", delta=f"{bk - dk:+d} Kosten gegen Dijkstra", delta_color="inverse")
else:
    bweg = None
    m2.metric(f"Billigster zulässiger Weg (T = {settings.t_hand})", "kein zulässiger Weg", delta=f"schnellster Weg: Zeit {h.schnellste}", delta_color="off")
m3.metric("Erzeugte Labels", f"{e.erzeugt}", delta=f"davon {e.dominiert} dominiert", delta_color="off")
st.plotly_chart(V.build_netz(h.netz, weg=bweg, dijkstra_weg=dweg), width="stretch", key="net_chart")
st.caption("Jede Kante ist mit Kosten / Zeit beschriftet. Orange gestrichelt: der billigste Weg ohne Grenze (Dijkstra). Grün: der billigste Weg mit Zeit höchstens T. Verlaufen beide gleich, liegt grün auf orange.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Ist der billigste Weg auch der billigste zulässige Weg?")
kind, text = ev.verdict_grenze(settings.t_hand, h.dijkstra, e.bester, h.schnellste)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 1: Schritt für Schritt -----------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Das Handnetz Schritt für Schritt")
st.caption(f"Zeitgrenze T = {settings.t_hand} aus der Seitenleiste. Unter jedem Knoten stehen die lebenden Labels als Lnr: Kosten / Zeit. Mit dem Regler (oder den Knöpfen) gehen Sie durch das Verfahren.")
letzter = len(e.ereignisse) - 1
if st.session_state.get("schritt_fuer_t") != settings.t_hand:
    st.session_state["schritt"] = letzter
    st.session_state["schritt_fuer_t"] = settings.t_hand
st.session_state["schritt"] = max(0, min(int(st.session_state.get("schritt", letzter)), letzter))


def _schritt_zurueck():
    st.session_state["schritt"] = max(0, st.session_state["schritt"] - 1)


def _schritt_weiter():
    st.session_state["schritt"] = min(letzter, st.session_state["schritt"] + 1)


c_zurueck, c_regler, c_weiter = st.columns([1, 4, 1], vertical_alignment="bottom")
c_zurueck.button("◀ Zurück", on_click=_schritt_zurueck, width="stretch", key="btn_zurueck")
c_weiter.button("Weiter ▶", on_click=_schritt_weiter, width="stretch", key="btn_weiter")
schritt = c_regler.slider("Schritt", 0, letzter, key="schritt", help="Schritt 0 ist der Start, der letzte Schritt das fertige Verfahren.")
ev_s = e.ereignisse[schritt]
st.info(f"**Schritt {schritt} von {letzter}.** {ev.ereignis_text(ev_s, settings.t_hand)}")
s1, s2, s3 = st.columns(3)
s1.metric("Erzeugte Labels", ev_s.erzeugt)
s2.metric("Dominiert", ev_s.dominiert)
s3.metric("Wegen Zeit > T nicht gebildet", ev_s.zu_spaet)
lebend = {v: ev_s.lebend[v] for v in range(h.netz.n)}
aktiv = ev_s.knoten if ev_s.art == "nimm" else None
kante = (ev_s.kante[0], ev_s.kante[1]) if ev_s.kante else None
ende_weg = bweg if ev_s.art == "ende" else None
st.plotly_chart(V.build_netz(h.netz, weg=ende_weg, lebend=lebend, kante_aktiv=kante, knoten_aktiv=aktiv), width="stretch", key="step_chart")
with st.expander("Alle Schritte als Liste"):
    st.markdown("\n".join(f"{i}. {ev.ereignis_text(x, settings.t_hand)}" for i, x in enumerate(e.ereignisse)))
kind, text = ev.verdict_schritte(settings.t_hand, e)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 2: Treppe ------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Die Treppe – Kosten gegen Zeitgrenze")
st.caption("Handnetz, für jede Grenze von 7 bis 16 ein eigener Lauf. Die Rauten sind die nicht dominierten (Zeit, Kosten)-Paare am Ziel: Sie sind die Stufen.")
st.plotly_chart(V.build_treppe(h.treppe, settings.t_hand, dz, [(k_, z_) for k_, z_ in h.front.ziel_labels]), width="stretch", key="stairs_chart")
paare = set(h.front.ziel_labels)
tab = pd.DataFrame([
    {"Weg": ev.weg_text(w), "Kosten": c, "Zeit": z, f"zulässig bei T = {settings.t_hand}": "ja" if z <= settings.t_hand else "nein", "nicht dominiert": "ja" if (c, z) in paare else "nein"}
    for c, z, w in h.wege
])
st.markdown(f"Alle {len(h.wege)} Wege vom Start zum Ziel (Aufzählung), nach Kosten sortiert:")
st.dataframe(tab, hide_index=True, width="stretch")
kind, text = ev.verdict_treppe(h.treppe, dz)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 3: Größenregler ------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Größenregler – Kunden, Prämien und eine Zeitgrenze")
st.markdown(
    f"""
Eine Kundeninstanz im Stil der Solomon-Benchmarks (selbst erzeugt, nicht die Originalinstanzen): Das Depot liegt in der Mitte eines Quadrats von 100 × 100, die Kunden sind gleichverteilt,
die Fahrzeit ist die Entfernung, jede Bedienung dauert {int(C.SERVICE_TIME)}. Gesucht ist die billigste **Tour** ab Depot und zurück. Ihre Kosten sind die Entfernungen **minus eine Prämie je besuchtem Kunden**
(das Doppelte seiner Entfernung zum Depot). Bei der Spaltenerzeugung heißen solche Prämien Dualpreise; hier sind es feste Zahlen. So kann eine Tour negative Kosten haben, also Gewinn bringen.
Die Gesamtzeit der Tour einschließlich Rückweg darf T nicht überschreiten."""
)
with st.spinner("Das Verfahren läuft …"):
    g = _gross(settings)
if g.fehler:
    st.error(f"Prüfung des Ergebnisses fehlgeschlagen: {g.fehler}")
r = g.ergebnis
tour = r.bester[1] if r.bester else ()
anteil = 100 * r.dominiert / r.erzeugt if r.erzeugt else 0.0
g1, g2, g3, g4 = st.columns(4)
g1.metric("Erzeugte Labels", ev.zahl(r.erzeugt))
g2.metric("Davon dominiert", ev.prozent(anteil))
g3.metric("Einzeln erreichbare Kunden", f"{r.erreichbar} von {settings.n}")
g4.metric("Kosten der besten Tour", ev.zahl(r.bester[0], 2) if r.bester else "keine Tour mit Gewinn")
erreichbar = [False] + [A.kunde_erreichbar(g.inst, settings.t, j) for j in range(1, settings.n + 1)]
st.plotly_chart(V.build_karte(g.inst, tour, g.praemien, settings.t, erreichbar), width="stretch", key="map_chart")
st.caption("Quadrat: Depot. Kreise: Kunden, die Größe zeigt die Prämie; grau: Kunden, die auch allein (Depot, Kunde, Depot) nicht innerhalb der Zeitgrenze zu bedienen sind. Grün: die beste Tour.")
elementar = A.ist_elementar(tour) if r.bester else None
kind, text = ev.verdict_gross(settings.t, settings.n, settings.k, r, elementar)
getattr(st, kind)(text)
st.caption(
    f"Eine Rechnung, ein Zufalls-Seed ({settings.seed}). Rechenzeit dieser Rechnung: {g.sekunden:.1f} s; Sekunden hängen von der Last der Maschine ab und sind nicht festgeschrieben, "
    "gezählt werden Labels. Prämien: Dualpreise der ersten Runde, nicht einer konvergierten Spaltenerzeugung."
)

st.markdown("---")

# --- Experiment 4: Bänder ------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Bänder aus festen Messreihen")
zg = _baender("zeitgrenze")
fb = _baender("fensterbreite")
st.markdown(f"**Labels gegen die Zeitgrenze.** {zg['beschreibung']} Je Zeile ein Pricing-Aufruf je Instanz.")
st.plotly_chart(V.build_baender(zg["zeilen"]), width="stretch", key="band_chart")
tabelle_t = pd.DataFrame([
    {"Zeitgrenze T": z["T"], "Instanzen": z["instanzen"], "erreichbare Kunden (Median)": ev.zahl(z["erreichbar_median"], 1), "Labels (Median)": ev.zahl(z["labels_median"], 1 if z["labels_median"] % 1 else 0),
     "Labels (Mittel)": ev.zahl(z["labels_mittel"], 1), "Labels (Maximum)": ev.zahl(z["labels_max"]), "dominiert (Mittel)": ev.prozent(z["dominiert_mittel_prozent"]),
     "Instanzen mit Gewinn-Tour": z["instanzen_mit_route"]}
    for z in zg["zeilen"]
])
st.dataframe(tabelle_t, hide_index=True, width="stretch")
kind, text = ev.verdict_baender(zg["zeilen"], "T", "der Zeitgrenze", "T")
getattr(st, kind)(text)
st.markdown(
    f"**Dieselbe Frage in der ganzen Spaltenerzeugung.** {fb['beschreibung']} Hier steht nicht die Zeitgrenze, sondern die **Fensterbreite** (wie weit die Zeitfenster der Kunden geöffnet sind)."
)
st.plotly_chart(V.build_baender_breite(fb["zeilen"]), width="stretch", key="band_width_chart")
tabelle_b = pd.DataFrame([
    {"Fensterbreite": z["breite"], "Gedächtnis k": z["k"], "Instanzen": z["instanzen"], "Labels (Median)": ev.zahl(z["labels_median"], 1 if z["labels_median"] % 1 else 0),
     "Labels (Mittel)": ev.zahl(z["labels_mittel"], 1), "Labels (Maximum)": ev.zahl(z["labels_max"]), "dominiert (Mittel)": ev.prozent(z["dominiert_mittel_prozent"])}
    for z in fb["zeilen"]
])
st.dataframe(tabelle_b, hide_index=True, width="stretch")
for kk in (1, 5):
    kind, text = ev.verdict_baender([z for z in fb["zeilen"] if z["k"] == kk], "breite", f"der Fensterbreite (k = {kk})", "Breite")
    getattr(st, kind)(text)
st.caption(
    "Hinweise: nur 12 Instanzen je Zelle bei der Zeitgrenze (20 Kunden), nur 6 Instanzen je Breite bei der Fensterbreite (30 Kunden); Prämien der ersten Runde, nicht einer konvergierten Spaltenerzeugung; "
    "Sekunden hängen von der Last der Maschine ab und sind nicht festgeschrieben. Ein Median aus 6 Instanzen ist das Mittel der beiden mittleren Werte (deshalb die Nachkommastelle 5)."
)
with st.expander("Quellen der Zeilen"):
    for z in zg["zeilen"] + fb["zeilen"]:
        st.markdown(f"- {z['quelle']}")

st.markdown("---")

# --- Experiment 5: Brücke ------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Brücke zu Dijkstra und zur Pareto-Front")
st.markdown(
    "Dieselbe Rechnung im Handnetz mit drei Fragen: nur Kosten (**Dijkstra**: ein Eintrag je Knoten), **alle nicht dominierten (Kosten, Zeit)-Paare ohne Grenze** "
    "(die **Pareto-Front** am Ziel, zu der die Demo [multicriteria-demo](https://github.com/sebastian-hanisch/multicriteria-demo) mehr zeigt) und das **Verfahren mit eingebauter Grenze T**. "
    "Aus der Front lässt sich jede Grenze ablesen; die eingebaute Grenze erzeugt dasselbe Ergebnis mit weniger Labels. "
    "Der Fall ohne Zeit ist [dijkstra-demo](https://github.com/sebastian-hanisch/dijkstra-demo)."
)
st.plotly_chart(V.build_bruecke([("Dijkstra: gesetzte Knoten", h.gesetzt), ("Front: erzeugte Labels (ohne Grenze)", h.front.erzeugt), (f"Grenze T = {settings.t_hand}: erzeugte Labels", e.erzeugt)]),
                width="stretch", key="bridge_chart")
st.caption("Das Verfahren ohne Grenze ist dasselbe Label-Setting mit T = ∞. Dijkstra setzt je Knoten einen Wert; die Balken zählen verschiedene Dinge (gesetzte Knoten, erzeugte Labels) und sind nur als Größenordnung nebeneinandergestellt.")
kind, text = ev.verdict_bruecke(settings.t_hand, e, h.front)
getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Was zeigt es |
|---|---|---|
| **Nur Kosten und Zeit entscheiden über Dominanz.** | Mit einer zweiten begrenzten Größe (Kapazität) oder mit Zeitfenstern genügt der Vergleich zweier Werte nicht mehr; die Messreihe über die Fensterbreite rechnet mit Fenstern und Kapazität 70 in einer ganzen Spaltenerzeugung und ist mit der Reihe über T nicht direkt vergleichbar. | Experiment 4 |
| **Die Kosten sind nicht negativ.** | Im Handnetz stimmt der Vergleich mit Dijkstra nur für nichtnegative Kosten; das Label-Setting selbst braucht nichtnegative Zeiten. In der Kundeninstanz sind die Kosten wegen der Prämien negativ, und das Verfahren endet nur, weil jede Fahrt Zeit braucht und T begrenzt. | Experiment 3 |
| **Gedächtnis k = 5 reicht, um Kreise zu vermeiden.** | Mit k kleiner als die Zahl der Kunden kann eine Tour einen Kunden mehrfach besuchen; die Demo meldet das und rechnet nicht weiter dagegen an. | Experiment 3 |
| **Gemessen wird an 12 bzw. 6 Instanzen je Zelle.** | Die Spanne zwischen Median und Maximum ist groß (Tabelle in Experiment 4); eine einzelne Instanz kann deutlich vom Median abweichen. | Experiment 4 |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** *Gegeben:* ein gerichtetes Netz mit Kosten und Zeit je Kante, ein Start, ein Ziel und eine Zeitgrenze. *Gesucht:* der Weg vom Start zum Ziel mit den kleinsten Kosten,
dessen Gesamtzeit die Grenze nicht übersteigt. *Verfahren:* Label-Setting mit Dominanz.

| Symbol | Bedeutung |
|---|---|
| $G = (V, E)$ | gerichtetes Netz mit Knoten $V$ und Kanten $E$ |
| $c_e,\ t_e$ | Kosten und Zeit der Kante $e$ (nicht negativ) |
| $s,\ z$ | Start und Ziel |
| $T$ | Zeitgrenze |
| $(c, t)$ | Label: Kosten und verbrauchte Zeit eines Weges bis zu einem Knoten |
| $\mathcal{P}_z$ | Menge der nicht dominierten Labels am Ziel |
| $d_{ab},\ \sigma$ | Entfernung (= Fahrzeit) von $a$ nach $b$ und Bedienzeit je Kunde (Kundeninstanz) |
| $\pi_j$ | Prämie von Kunde $j$, hier $2\,d_{0j}$ |
| $N_k(j)$ | die $k$ nächsten Kunden von $j$ einschließlich $j$ (Gedächtnis) |

**Problem im Handnetz.** Gesucht ist ein Weg $P$ von $s$ nach $z$ mit

$$\min_{P} \sum_{e \in P} c_e \qquad \text{unter} \qquad \sum_{e \in P} t_e \le T .$$

**Verlängerung.** Aus einem Label $(c, t)$ am Knoten $v$ entsteht über die Kante $e = (v, w)$ das Label

$$(c + c_e,\; t + t_e) \quad \text{nur falls} \quad t + t_e \le T .$$

**Dominanz.** Ein Label $(c, t)$ dominiert $(c', t')$ am selben Knoten, wenn

$$c \le c' \quad \text{und} \quad t \le t' .$$

**Treppe.** Die Kosten des besten zulässigen Weges als Funktion der Grenze:

$$f(T) = \min \{\, c \mid (c, t) \in \mathcal{P}_z,\ t \le T \,\} .$$

**Kundeninstanz.** Eine Tour $0 \to j_1 \to \dots \to j_m \to 0$ hat die Kosten und die Gesamtzeit

$$\sum_{i=0}^{m} d_{j_i j_{i+1}} - \sum_{i=1}^{m} \pi_{j_i}, \qquad \sum_{i=0}^{m} d_{j_i j_{i+1}} + m\,\sigma \le T \qquad (j_0 = j_{m+1} = 0).$$

Ein Label merkt sich zusätzlich die Menge $M$ der Kunden, an die es sich erinnert. Nach der Fahrt zu Kunde $j$ gilt

$$M' = (M \cap N_k(j)) \cup \{j\}, \qquad \text{und } j \text{ darf nicht in } M \text{ liegen.}$$

$(c, t, M)$ dominiert $(c', t', M')$ nur, wenn zusätzlich

$$M \subseteq M' .$$

**Literatur.** Irnich, Desaulniers (2005): *Shortest Path Problems with Resource Constraints*, in: Column Generation, Springer, S. 33–65, Standardreferenz zu Problem, Labeling und Dominanz; Desrochers, Soumis (1988): *A generalized permanent labelling algorithm for the shortest path problem with time windows*, INFOR 26(3), S. 191–212. Beide nur als Verzeichniseinträge gesehen, weder Abstract noch Volltext gelesen; keine Zahl der Demo stammt aus der Literatur. Hansen (1980) und Martins (1984) für das Label-Setting zur Pareto-Front: so in der README von multicriteria-demo genannt, hier nicht gelesen.
        """
    )

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(ASSUMPTIONS_MARKDOWN)

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html)."
)
