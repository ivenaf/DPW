import streamlit as st
import plotly.graph_objects as go
import networkx as nx
import math  # Math-Modul für die Pfeilrichtungsberechnung

# Streamlit-Seiteneinstellungen für volle Breite
st.set_page_config(layout="wide")

# Titel mit verbesserter Sichtbarkeit
st.markdown("<h3 style='text-align: center; color: #1E3D59; margin-bottom: 20px;'></h3>", unsafe_allow_html=True) # needed to not have the title at the very top
st.subheader("Workflow der Digitalen Säule")
st.write("""Die Digitale Säule unterscheidet sich von anderen Vermarktungsformen:
1. **Seitenanzahl**: Kann auch dreiseitig erfasst werden (nicht nur ein- oder doppelseitig)
2. **Workflow**: Überspringt den Niederlassungsleiter im Genehmigungsprozess""")

# Graph erstellen
G = nx.DiGraph()

# Knoten hinzufügen mit Beschreibungen
nodes = {
    'A': {'label': 'Erfassung durch Akquisiteur', 
          'desc': 'Standortdaten werden erfasst, inklusive spezifischer Merkmale der Digitalen Säule',
          'color': '#D6EAF8', 'border': '#2E86C1'},
    'B': {'label': 'Leiter Akquisitionsmanagement', 
          'desc': 'Bewertet und genehmigt/lehnt ab',
          'color': '#D6EAF8', 'border': '#2E86C1'},
    'C': {'label': 'Niederlassungsleiter (übersprungen)', 
          'desc': 'Dieser Schritt wird bei der Digitalen Säule übersprungen',
          'color': '#EBF5FB', 'border': '#85C1E9', 'dash': 'dash'},
    'D': {'label': 'Baurecht', 
          'desc': 'Bauanträge werden bei der Stadt eingereicht',
          'color': '#D6EAF8', 'border': '#2E86C1'},
    'E': {'label': 'Klage/Widerspruch?', 
          'desc': 'Entscheidung, ob bei Ablehnung Widerspruch eingelegt wird',
          'color': '#FCF3CF', 'border': '#F1C40F'},
    'E1': {'label': 'Klage-/Widerspruchsverfahren', 
           'desc': 'Rechtliches Verfahren nach Ablehnung des Bauantrags',
           'color': '#FDEBD0', 'border': '#F39C12'},
    'F': {'label': 'CEO', 
          'desc': 'Finale Genehmigungsstufe durch den CEO',
          'color': '#D6EAF8', 'border': '#2E86C1'},
    'G': {'label': 'Bauteam', 
          'desc': 'Umsetzung des Aufbaus, Eingabe von Stromanschluss, PLAN und IST-Aufbaudatum',
          'color': '#D6EAF8', 'border': '#2E86C1'},
    'H': {'label': 'Fertigstellung', 
          'desc': 'Werbeträger ist aufgebaut und bereit für die Vermarktung',
          'color': '#D4EFDF', 'border': '#27AE60'},
    'X1': {'label': 'Prozess unterbrochen', 
           'desc': 'Prozessabbruch nach Ablehnung durch Leiter Akquisitionsmanagement',
           'color': '#FADBD8', 'border': '#E74C3C'},
    'X2': {'label': 'Prozess unterbrochen', 
           'desc': 'Prozessabbruch nach Ablehnung des Bauantrags ohne Widerspruch',
           'color': '#FADBD8', 'border': '#E74C3C'},
    'X3': {'label': 'Prozess unterbrochen', 
           'desc': 'Prozessabbruch nach erfolglosem Widerspruchsverfahren',
           'color': '#FADBD8', 'border': '#E74C3C'},
    'X4': {'label': 'Prozess unterbrochen', 
           'desc': 'Prozessabbruch nach Ablehnung durch CEO',
           'color': '#FADBD8', 'border': '#E74C3C'}
}

# Knoten zum Graph hinzufügen
for node, attrs in nodes.items():
    G.add_node(node, **attrs)

# Kanten definieren mit Beschreibungen
edges = [
    ('A', 'B', {'label': '', 'color': 'gray', 'width': 1}),
    ('B', 'D', {'label': 'Genehmigung', 'color': '#27AE60', 'width': 2}),
    ('B', 'X1', {'label': 'Ablehnung', 'color': '#E74C3C', 'width': 2}),
    ('D', 'F', {'label': 'Bauantrag genehmigt', 'color': '#27AE60', 'width': 2}),
    ('D', 'E', {'label': 'Bauantrag abgelehnt', 'color': '#E74C3C', 'width': 2}),
    ('E', 'E1', {'label': 'Ja', 'color': '#F39C12', 'width': 2}),
    ('E', 'X2', {'label': 'Nein', 'color': '#E74C3C', 'width': 2}),
    ('E1', 'F', {'label': 'Erfolg', 'color': '#27AE60', 'width': 2}),
    ('E1', 'X3', {'label': 'Misserfolg', 'color': '#E74C3C', 'width': 2}),
    ('F', 'G', {'label': 'Genehmigung', 'color': '#27AE60', 'width': 2}),
    ('F', 'X4', {'label': 'Ablehnung', 'color': '#E74C3C', 'width': 2}),
    ('G', 'H', {'label': 'Aufbau + Stromanschluss', 'color': '#27AE60', 'width': 2}),
    ('B', 'C', {'label': '\n', 'color': '#85C1E9', 'width': 1, 'dash': 'dash'}),
    ('C', 'D', {'label': '\n', 'color': '#85C1E9', 'width': 1, 'dash': 'dash'})
]

for source, target, attrs in edges:
    G.add_edge(source, target, **attrs)

# Layout erstellen - Mehr Abstand zwischen den Schritten
pos = {
    'A': [0, 0],
    'B': [2.0, 0],       # Mehr Abstand (vorher 1.2)
    'C': [3.5, 0.8],     # Mehr Abstand (vorher 2.1)
    'D': [5.0, 0],       # Mehr Abstand (vorher 3.0)
    'E': [7.0, -0.8],    # Mehr Abstand (vorher 4.2)
    'E1': [8.5, -1.2],   # Mehr Abstand (vorher 5.1)
    'F': [10.0, 0],      # Mehr Abstand (vorher 6.0)
    'G': [12.0, 0],      # Mehr Abstand (vorher 7.2)
    'H': [14.0, 0],      # Mehr Abstand (vorher 8.4)
    'X1': [3.5, -0.8],   # Mehr Abstand (entsprechend angepasst)
    'X2': [7.0, -1.6],   # Mehr Abstand (entsprechend angepasst)
    'X3': [10.0, -1.2],  # Mehr Abstand (entsprechend angepasst)
    'X4': [12.0, -0.8],  # Mehr Abstand (entsprechend angepasst)
}

# Workflow-Visualisierung erstellen
fig = go.Figure()

# NEUE PFEILE IMPLEMENTIERUNG: Verbindungen mit Pfeilen statt einfacher Linien

# Für jede Kante einen eigenen Pfeil erstellen mit Pfeilspitze
for edge in G.edges():
    source, target = edge
    x0, y0 = pos[source]
    x1, y1 = pos[target]
    
    attrs = G.edges[edge]
    color = attrs['color']
    width = attrs['width']
    dash_style = 'dash' if attrs.get('dash') == 'dash' else None
    
    # Berechne den Abstand, um die Pfeilspitze vor dem Knoten zu platzieren
    node_size = 40 if 'X' in target else 60
    node_radius = node_size / 150  # Anpassung für die Pfeilspitzenposition
    
    # Vektor von source zu target
    dx = x1 - x0
    dy = y1 - y0
    dist = (dx**2 + dy**2)**0.5
    
    # Normalisierte Richtung
    if dist > 0:  # Vermeide Division durch Null
        nx = dx / dist
        ny = dy / dist
    else:
        nx, ny = 0, 0
    
    # Endpunkt etwas vor dem Zielknoten platzieren
    arrow_end_x = x1 - nx * node_radius
    arrow_end_y = y1 - ny * node_radius
    
    # Füge den Pfeil als Linie mit Markierung am Ende hinzu
    fig.add_trace(go.Scatter(
        x=[x0, arrow_end_x],
        y=[y0, arrow_end_y],
        mode='lines',
        line=dict(
            color=color, 
            width=width,
            dash=dash_style
        ),
        hoverinfo='none'
    ))
    
    # Füge die Pfeilspitze als separates Symbol hinzu, wenn es keine gestrichelte Linie ist
    if dash_style != 'dash':
        # Pfeilspitze nur für durchgezogene Linien hinzufügen
        fig.add_trace(go.Scatter(
            x=[arrow_end_x],
            y=[arrow_end_y],
            mode='markers',
            marker=dict(
                symbol='triangle-right',
                size=10 * width,  # Größe proportional zur Linienbreite
                color=color,
                angle=(-90 + (180 * (0.5 * 3.14159 + (0 if dy == 0 else (dy / abs(dy)) * (0 if dx == 0 else math.atan(dx / dy))))) % 360) if dy != 0 else (0 if dx >= 0 else 180),
                line=dict(width=0)
            ),
            hoverinfo='none'
        ))

# Kantentext hinzufügen
edge_labels = []
edge_label_x = []
edge_label_y = []

for edge in G.edges():
    source, target = edge
    attrs = G.edges[edge]
    if attrs.get('label'):
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        edge_labels.append(attrs['label'])
        edge_label_x.append((x0 + x1) / 2)
        edge_label_y.append((y0 + y1) / 2 + 0.1)

# Knoten hinzufügen mit größerer Schrift
fig.add_trace(go.Scatter(
    x=[pos[node][0] for node in G.nodes()],
    y=[pos[node][1] for node in G.nodes()],
    mode='markers+text',
    text=[nodes[node]['label'] for node in G.nodes()],
    textfont=dict(size=14),  # Größere Schriftgröße (vorher 9)
    marker=dict(
        showscale=False,
        color=[nodes[node]['color'] for node in G.nodes()],
        size=[40 if 'X' in node else 60 for node in G.nodes()],
        line_width=[1 if nodes[node].get('dash') == 'dash' else 2 for node in G.nodes()],
        line_color=[nodes[node]['border'] for node in G.nodes()]
    ),
    textposition="bottom center",
    hovertext=[f"{nodes[node]['label']}<br>{nodes[node]['desc']}" for node in G.nodes()],
    hoverinfo="text"
))

# Kantentext hinzufügen mit größerer Schrift
if edge_labels:
    fig.add_trace(go.Scatter(
        x=edge_label_x,
        y=edge_label_y,
        mode="text",
        text=edge_labels,
        textfont=dict(size=14),  # Größere Schriftgröße (vorher 8)
        hoverinfo="none"
    ))

# Layout anpassen - Minimale Margins und mehr Höhe
fig.update_layout(
    showlegend=False,
    hovermode='closest',
    margin=dict(b=10, l=0, r=0, t=10, pad=0),  # Minimale Margins
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    height=500,  # Mehr Höhe (vorher 450)
    plot_bgcolor='rgba(0,0,0,0)',
    autosize=True
)

# Zoom und Range anpassen, damit alles sichtbar ist
fig.update_xaxes(range=[-1, 15])  # Größerer Bereich (vorher -0.5, 9)
fig.update_yaxes(range=[-2.0, 1.3])  

# CSS für engere Margins im Streamlit Container und deutlicheren Titel
st.markdown("""
<style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem;}
    div.stPlotlyChart {margin-top: 0px; margin-bottom: 10px;}
    h1 {margin-bottom: 0.5rem !important; padding-bottom: 0.5rem !important;}
</style>
""", unsafe_allow_html=True)

# Vertikaler Abstand vor dem Diagramm (Luft unter der Einleitung)
st.markdown("<br>", unsafe_allow_html=True)

# Interaktives Diagram anzeigen mit voller Breite
st.plotly_chart(fig, use_container_width=True)