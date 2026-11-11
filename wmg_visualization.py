"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben.

Kantenbeschriftungen und Label-Listen sind `add_annotation`-Aufrufe (mit Hintergrund), keine Text-Spuren (DEMO-PLAYBOOK §3)."""

import plotly.graph_objects as go

import wmg_constants as C

# Lage der Knoten des Handnetzes (von Hand gesetzt, 7 Knoten): Schichten von links nach rechts.
POSITIONEN = {0: (0.0, 1.0), 1: (1.0, 2.0), 3: (1.0, 0.0), 2: (2.0, 1.5), 4: (3.0, 2.0), 5: (3.0, 0.0), 6: (4.0, 1.0)}
KANTENLABEL_HINTERGRUND = "rgba(255,255,255,0.88)"
# Lage der Kantenbeschriftung auf der Kante (0 = Anfang, 1 = Ende); Standard 0,5. Verschoben, wo sie sonst die Label-Listen unter den Knoten überdeckt.
KANTENLABEL_T = {(3, 4): 0.25, (4, 5): 0.75}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360, legend=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)", showlegend=legend,
                      legend=dict(orientation="h", y=-0.2))
    return lock_axes(fig)


def _kanten_paare(weg):
    return set(zip(weg, weg[1:])) if weg else set()


def build_netz(netz, weg=None, dijkstra_weg=None, lebend=None, kante_aktiv=None, knoten_aktiv=None, T=None):
    """Das Netz mit Kante (Kosten / Zeit). `weg`: gewählter Weg (grün), `dijkstra_weg`: billigster Weg ohne Grenze (orange, gestrichelt),
    `lebend`: je Knoten die lebenden Labels ((Nr, Kosten, Zeit), ...) als Liste unter dem Knoten, `kante_aktiv`: (von, nach) der betrachteten Kante."""
    fig = go.Figure()
    gewaehlt, billig = _kanten_paare(weg), _kanten_paare(dijkstra_weg)
    for e in netz.kanten:
        (x0, y0), (x1, y1) = POSITIONEN[e.von], POSITIONEN[e.nach]
        paar = (e.von, e.nach)
        farbe, breite = C.COLOR_EDGE, 1.5
        if paar == kante_aktiv:
            farbe, breite = C.COLOR_ACTIVE, 3
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.1,
                           arrowwidth=breite, arrowcolor=farbe, standoff=17, startstandoff=17, text="")
        lt = KANTENLABEL_T.get(paar, 0.5)
        fig.add_annotation(x=x0 + lt * (x1 - x0), y=y0 + lt * (y1 - y0), text=f"{e.kosten} / {e.zeit}", showarrow=False, font=dict(size=11),
                           bgcolor=KANTENLABEL_HINTERGRUND, borderpad=1)
    for paare, farbe, strich, name in ((billig, C.COLOR_DIJKSTRA, "dash", "billigster Weg ohne Grenze (Dijkstra)"), (gewaehlt, C.COLOR_BEST, "solid", "billigster zulässiger Weg")):
        if not paare:
            continue
        xs, ys = [], []
        for a, b in sorted(paare):
            xs += [POSITIONEN[a][0], POSITIONEN[b][0], None]
            ys += [POSITIONEN[a][1], POSITIONEN[b][1], None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=farbe, width=7 if farbe == C.COLOR_DIJKSTRA else 4, dash=strich), name=name, hoverinfo="skip"))
    farben = [C.COLOR_ACTIVE if v == knoten_aktiv else C.COLOR_NODE for v in range(netz.n)]
    fig.add_trace(go.Scatter(x=[POSITIONEN[v][0] for v in range(netz.n)], y=[POSITIONEN[v][1] for v in range(netz.n)], mode="markers+text",
                             text=[str(v) for v in range(netz.n)], textfont=dict(color="white", size=14),
                             marker=dict(size=34, color=farben, line=dict(color="white", width=2)), showlegend=False,
                             hovertemplate="Knoten %{text}<extra></extra>"))
    for v, name in ((netz.start, "Start"), (netz.ziel, "Ziel")):
        x, y = POSITIONEN[v]
        fig.add_annotation(x=x, y=y + 0.32, text=f"<b>{name}</b>", showarrow=False, font=dict(size=12))
    if lebend is not None:
        for v in range(netz.n):
            zeilen = [f"L{nr}: {k:g} / {z:g}" for nr, k, z in lebend[v]]
            if zeilen:
                x, y = POSITIONEN[v]
                fig.add_annotation(x=x, y=y - 0.34, text="<br>".join(zeilen), showarrow=False, yanchor="top", font=dict(size=10),
                                   bgcolor="rgba(76,120,168,0.12)", borderpad=2)
    fig.update_xaxes(range=[-0.5, 4.5], visible=False)
    fig.update_yaxes(range=[-1.5, 2.6] if lebend is not None else [-0.6, 2.6], visible=False)
    return _base(fig, height=430 if lebend is not None else 330)


def build_treppe(zeilen, t_aktuell, dijkstra_zeit, paare):
    """Kosten des billigsten zulässigen Weges gegen die Zeitgrenze (Treppe). `paare`: die nicht dominierten (Kosten, Zeit)-Paare am Ziel
    als Markierung der Stufen; Bereich T < Zeit des billigsten Weges getönt (dort bindet die Grenze)."""
    ts = [z["T"] for z in zeilen]
    ys = [z["kosten"] for z in zeilen]
    fig = go.Figure()
    fig.add_vrect(x0=ts[0] - 0.5, x1=dijkstra_zeit - 0.5, fillcolor="rgba(217,138,43,0.12)", line_width=0, layer="below")
    fig.add_annotation(x=(ts[0] - 0.5 + dijkstra_zeit - 0.5) / 2, y=1, yref="paper", text="Grenze bindet", showarrow=False, font=dict(size=11))
    fig.add_trace(go.Scatter(x=ts, y=ys, mode="lines", line=dict(color=C.COLOR_LINE, width=3, shape="hv"), connectgaps=False, name="Kosten des besten zulässigen Weges",
                             hovertemplate="T = %{x}: Kosten %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[p[1] for p in paare], y=[p[0] for p in paare], mode="markers", marker=dict(size=11, color=C.COLOR_BEST, symbol="diamond"),
                             name="nicht dominierte Paare (Zeit, Kosten) am Ziel", hovertemplate="Paar: Zeit %{x}, Kosten %{y}<extra></extra>"))
    fig.add_vline(x=t_aktuell, line=dict(color=C.COLOR_ACTIVE, width=2, dash="dot"))
    fig.add_annotation(x=t_aktuell, y=0, yref="paper", text=f"T = {t_aktuell}", showarrow=False, yanchor="bottom", xanchor="left", font=dict(size=11, color=C.COLOR_ACTIVE))
    fig.update_xaxes(title_text="Zeitgrenze T", range=[ts[0] - 0.5, ts[-1] + 0.5], dtick=1)
    ymax = max(y for y in ys if y is not None)
    fig.update_yaxes(title_text="Kosten", range=[0, ymax + 2])
    return _base(fig)


def build_karte(inst, tour, praemien, T, erreichbar):
    """Kundenkarte: Depot (Quadrat), Kunden (Kreise, Größe = Prämie, grau = einzeln nicht erreichbar), gefundene Tour als Linie.
    Gleicher Maßstab in x und y: `scaleanchor` nur mit autorange, der Rand kommt über zwei unsichtbare Eckpunkte (DEMO-PLAYBOOK §3)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, C.GRID], y=[0, C.GRID], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    if tour:
        folge = (0,) + tuple(tour) + (0,)
        fig.add_trace(go.Scatter(x=[inst.pts[i][0] for i in folge], y=[inst.pts[i][1] for i in folge], mode="lines", line=dict(color=C.COLOR_BEST, width=3),
                                 name="beste Tour", hoverinfo="skip"))
    idx = list(range(1, inst.n + 1))
    farben = [C.COLOR_NODE if erreichbar[i] else C.COLOR_OTHER for i in idx]
    fig.add_trace(go.Scatter(x=[inst.pts[i][0] for i in idx], y=[inst.pts[i][1] for i in idx], mode="markers+text", text=[str(i) for i in idx],
                             textposition="top center", textfont=dict(size=10),
                             marker=dict(size=[8 + praemien[i] / 8 for i in idx], color=farben, line=dict(color="white", width=1)), name="Kunde (Größe = Prämie)",
                             customdata=[[praemien[i], inst.d[0][i]] for i in idx],
                             hovertemplate="Kunde %{text}<br>Prämie %{customdata[0]:.1f}<br>Entfernung zum Depot %{customdata[1]:.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[inst.pts[0][0]], y=[inst.pts[0][1]], mode="markers", marker=dict(size=16, symbol="square", color="#222"), name="Depot",
                             hovertemplate="Depot<extra></extra>"))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    return _base(fig, height=460)


def build_baender(zeilen):
    """Labels je Zeitgrenze: Median, Mittel und Maximum über die festen Instanzen (logarithmische Achse)."""
    ts = [z["T"] for z in zeilen]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts, y=[z["labels_max"] for z in zeilen], mode="lines+markers", line=dict(color="rgba(76,120,168,0.4)", dash="dot"), name="Maximum",
                             hovertemplate="T = %{x}: Maximum %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=ts, y=[z["labels_mittel"] for z in zeilen], mode="lines+markers", line=dict(color="rgba(76,120,168,0.7)", dash="dash"), name="Mittel",
                             hovertemplate="T = %{x}: Mittel %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=ts, y=[z["labels_median"] for z in zeilen], mode="lines+markers", line=dict(color=C.COLOR_LINE, width=3), name="Median",
                             hovertemplate="T = %{x}: Median %{y:,.0f}<extra></extra>"))
    fig.update_xaxes(title_text="Zeitgrenze T", tickvals=ts)
    fig.update_yaxes(title_text="erzeugte Labels (logarithmisch)", type="log")
    return _base(fig)


def build_baender_breite(zeilen):
    """Median der Labels je Fensterbreite, getrennt nach Gedächtnis k (Balken, gemeinsame Achse)."""
    fig = go.Figure()
    for k, farbe in ((1, "rgba(76,120,168,0.55)"), (5, C.COLOR_LINE)):
        sel = [z for z in zeilen if z["k"] == k]
        fig.add_trace(go.Bar(x=[str(z["breite"]) for z in sel], y=[z["labels_median"] for z in sel], name=f"k = {k}", marker_color=farbe,
                             hovertemplate="Breite %{x}: Median %{y:,.0f}<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text="Fensterbreite", type="category")
    fig.update_yaxes(title_text="Labels (Median, Summe aller Pricing-Aufrufe)")
    return _base(fig)


def build_bruecke(zeilen):
    """Zahl der Einträge je Verfahren: Balken mit (Name, Zahl)."""
    fig = go.Figure(go.Bar(x=[z[0] for z in zeilen], y=[z[1] for z in zeilen], marker_color=[C.COLOR_DIJKSTRA, C.COLOR_LINE, C.COLOR_BEST][: len(zeilen)],
                           text=[str(z[1]) for z in zeilen], textposition="outside", hovertemplate="%{x}: %{y}<extra></extra>"))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Labels", rangemode="tozero")
    return _base(fig, height=320, legend=False)
