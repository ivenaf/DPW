import streamlit as st
import graphviz

st.title("Workflow der Digitalen Säule")

st.write("""Die Digitale Säule unterscheidet sich von anderen Vermarktungsformen:

1. **Seitenanzahl**: Kann auch dreiseitig erfasst werden (nicht nur ein- oder doppelseitig)
2. **Workflow**: Überspringt den Niederlassungsleiter im Genehmigungsprozess
""")

# Graphviz Diagramm erstellen
graph = graphviz.Digraph()
graph.attr(rankdir='TB')  # Vertikale Ausrichtung (Top to Bottom)

# Knoten mit Farbgebung definieren
# Haupt-Workflow-Schritte in Blau
graph.node('A', 'Erfassung durch Akquisiteur', shape='box', style='filled', fillcolor='#D6EAF8', color='#2E86C1')
graph.node('B', 'Leiter Akquisitionsmanagement', shape='box', style='filled', fillcolor='#D6EAF8', color='#2E86C1')
graph.node('D', 'Baurecht', shape='box', style='filled', fillcolor='#D6EAF8', color='#2E86C1')
graph.node('F', 'CEO', shape='box', style='filled', fillcolor='#D6EAF8', color='#2E86C1')
graph.node('G', 'Bauteam', shape='box', style='filled', fillcolor='#D6EAF8', color='#2E86C1')
graph.node('H', 'Fertigstellung', shape='box', style='filled', fillcolor='#D4EFDF', color='#27AE60')  # Grün für Abschluss

# Entscheidungsknoten in Gelb
graph.node('E', 'Klage/Widerspruch?', shape='diamond', style='filled', fillcolor='#FCF3CF', color='#F1C40F')
graph.node('E1', 'Klage-/Widerspruchsverfahren', shape='box', style='filled', fillcolor='#FDEBD0', color='#F39C12')

# Prozessabbrüche in Rot
graph.node('X1', 'Prozess unterbrochen', shape='ellipse', style='filled', fillcolor='#FADBD8', color='#E74C3C')
graph.node('X2', 'Prozess unterbrochen', shape='ellipse', style='filled', fillcolor='#FADBD8', color='#E74C3C')
graph.node('X3', 'Prozess unterbrochen', shape='ellipse', style='filled', fillcolor='#FADBD8', color='#E74C3C')
graph.node('X4', 'Prozess unterbrochen', shape='ellipse', style='filled', fillcolor='#FADBD8', color='#E74C3C')

# Kanten definieren
graph.edge('A', 'B')
graph.edge('B', 'D', label='Genehmigung', color='#27AE60', penwidth='2.0')
graph.edge('B', 'X1', label='Ablehnung', color='#E74C3C', penwidth='2.0')
graph.edge('D', 'F', label='Bauantrag genehmigt', color='#27AE60', penwidth='2.0')
graph.edge('D', 'E', label='Bauantrag abgelehnt', color='#E74C3C', penwidth='2.0')
graph.edge('E', 'E1', label='Ja', color='#F39C12', penwidth='2.0')
graph.edge('E', 'X2', label='Nein', color='#E74C3C', penwidth='2.0')
graph.edge('E1', 'F', label='Erfolg', color='#27AE60', penwidth='2.0')
graph.edge('E1', 'X3', label='Misserfolg', color='#E74C3C', penwidth='2.0')
graph.edge('F', 'G', label='Genehmigung', color='#27AE60', penwidth='2.0')
graph.edge('F', 'X4', label='Ablehnung', color='#E74C3C', penwidth='2.0')
graph.edge('G', 'H', label='Aufbau + Stromanschluss', color='#27AE60', penwidth='2.0')

# Hinweis auf übersprungenen Schritt mit Farbakzent
graph.attr(label='Hinweis: Niederlassungsleiter wird übersprungen', labelloc='t', fontcolor='#3498DB', fontsize='16')

# Übersprungenen Schritt als gestrichelte Box anzeigen - neben dem Hauptpfad
graph.node('C', 'Niederlassungsleiter\n(übersprungen)', shape='box', style='dashed,filled', fillcolor='#EBF5FB', color='#85C1E9')
graph.edge('C', 'X1', style='invis')  # Unsichtbare Kante zur korrekten Positionierung

# Gestrichelte Linien für den übersprungenen Pfad
graph.edge('B', 'C', label='Standard-\nWorkflow', style='dashed', color='#85C1E9')
graph.edge('C', 'D', label='Standard-\nWorkflow', style='dashed', color='#85C1E9')

# Graph anzeigen mit Größenanpassung
st.graphviz_chart(graph, use_container_width=True)

# Erklärung mit farblichen Hervorhebungen
st.info("""
**Wichtig:** Bei der Digitalen Säule wird der Workflow-Schritt **'Niederlassungsleiter'** 
übersprungen, wodurch der Prozess nach Genehmigung durch den Leiter Akquisitionsmanagement 
direkt an das Baurecht weitergeleitet wird.
""")

st.header("Erklärung zum Workflow der Digitalen Säule")

st.write("""
Der Workflow für die Digitale Säule besteht aus folgenden Schritten:

1. **Erfassung durch Akquisiteur**: Standortdaten werden erfasst, inklusive spezifischer Merkmale der Digitalen Säule

2. **Leiter Akquisitionsmanagement**: Bewertet und genehmigt/lehnt ab
   - Bei <span style="color:#27AE60">Genehmigung</span>: Weiter zu Baurecht (Niederlassungsleiter wird übersprungen)
   - Bei <span style="color:#E74C3C">Ablehnung</span>: Prozess wird unterbrochen

3. **Baurecht**: Bauanträge werden bei der Stadt eingereicht
   - Bei <span style="color:#27AE60">Genehmigung</span>: Weiter zum CEO
   - Bei <span style="color:#E74C3C">Ablehnung</span>: Option zur Klage/Widerspruch

4. **Klage/Widerspruch** (optional):
   - Bei <span style="color:#27AE60">Erfolg</span>: Weiter zum CEO
   - Bei <span style="color:#E74C3C">Misserfolg</span>: Prozess wird unterbrochen

5. **CEO**: Finale Genehmigungsstufe
   - Bei <span style="color:#27AE60">Genehmigung</span>: Weiter zum Bauteam
   - Bei <span style="color:#E74C3C">Ablehnung</span>: Prozess wird unterbrochen

6. **Bauteam**: Umsetzung des Aufbaus, Eingabe von Stromanschluss, PLAN und IST-Aufbaudatum

7. **Fertigstellung**: Werbeträger ist aufgebaut und bereit für die Vermarktung
""", unsafe_allow_html=True)

# Besonderheiten in einem farbigen Container hervorheben
st.markdown("""
<div style="background-color:#EBF5FB; padding:15px; border-radius:5px; border-left:5px solid #3498DB">
<h3 style="color:#2E86C1">Besonderheiten der Digitalen Säule:</h3>
<ol>
<li>Der Workflow-Schritt <b>"Niederlassungsleiter"</b> wird übersprungen</li>
<li>Die Digitale Säule kann als einzige Vermarktungsform auch <b>dreiseitig</b> erfasst werden</li>
</ol>
</div>
""", unsafe_allow_html=True)

# Zusätzlich: Visueller Vergleich mit Standardworkflow
st.subheader("Vergleich mit Standardworkflow")
col1, col2 = st.columns(2)

with col1:
    st.markdown("<h4 style='text-align:center; color:#3498DB'>Standardworkflow</h4>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; background-color:#F8F9F9; padding:10px; border-radius:5px">
    Erfassung<br>↓<br>
    Leiter Akquisition<br>↓<br>
    <b style='color:#3498DB'>Niederlassungsleiter</b><br>↓<br>
    Baurecht<br>↓<br>
    CEO<br>↓<br>
    Bauteam<br>↓<br>
    Fertigstellung
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("<h4 style='text-align:center; color:#3498DB'>Workflow Digitale Säule</h4>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; background-color:#F8F9F9; padding:10px; border-radius:5px">
    Erfassung<br>↓<br>
    Leiter Akquisition<br>↓<br>
    <span style="color:lightgray;">- - - - - - - -</span><br>
    Baurecht<br>↓<br>
    CEO<br>↓<br>
    Bauteam<br>↓<br>
    Fertigstellung
    </div>
    """, unsafe_allow_html=True)

# Legende für die Farben
st.subheader("Legende")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="display:flex; align-items:center; margin-bottom:10px;">
        <div style="width:20px; height:20px; background-color:#D6EAF8; border:1px solid #2E86C1; margin-right:10px;"></div>
        <div>Workflow-Schritt</div>
    </div>
    <div style="display:flex; align-items:center;">
        <div style="width:20px; height:20px; background-color:#FCF3CF; border:1px solid #F1C40F; margin-right:10px;"></div>
        <div>Entscheidungspunkt</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="display:flex; align-items:center; margin-bottom:10px;">
        <div style="width:20px; height:20px; background-color:#D4EFDF; border:1px solid #27AE60; margin-right:10px;"></div>
        <div>Abschluss</div>
    </div>
    <div style="display:flex; align-items:center;">
        <div style="width:20px; height:20px; background-color:#FADBD8; border:1px solid #E74C3C; margin-right:10px;"></div>
        <div>Prozessabbruch</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="display:flex; align-items:center; margin-bottom:10px;">
        <div style="height:2px; width:40px; background-color:#27AE60; margin-right:10px;"></div>
        <div>Genehmigung</div>
    </div>
    <div style="display:flex; align-items:center;">
        <div style="height:2px; width:40px; background-color:#E74C3C; margin-right:10px;"></div>
        <div>Ablehnung</div>
    </div>
    """, unsafe_allow_html=True)