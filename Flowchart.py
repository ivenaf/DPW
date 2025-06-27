import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import graphviz

def main():
    st.title("Workflow der Digitalen Säule")
    
    st.write("""
    ## Unterschied zu anderen Vermarktungsformen
    
    Die Digitale Säule unterscheidet sich von anderen Vermarktungsformen:
    
    1. **Seitenanzahl**: Kann auch dreiseitig erfasst werden (nicht nur ein- oder doppelseitig)
    2. **Workflow**: Überspringt den Niederlassungsleiter im Genehmigungsprozess
    """)
    
    # Option für Visualisierung wählen
    viz_type = st.radio(
        "Visualisierungstyp auswählen:",
        ("Graphviz (empfohlen)", "Interaktiver Graph")
    )
    
    if viz_type == "Graphviz (empfohlen)":
        show_graphviz_workflow()
    else:
        show_agraph_workflow()

def show_graphviz_workflow():
    # Graphviz Diagramm erstellen
    graph = graphviz.Digraph()
    graph.attr(rankdir='TB')
    
    # Knoten definieren
    graph.node('A', 'Erfassung durch Akquisiteur', shape='box')
    graph.node('B', 'Leiter Akquisitionsmanagement', shape='box')
    graph.node('D', 'Baurecht', shape='box')
    graph.node('E', 'Klage/Widerspruch?', shape='diamond')
    graph.node('E1', 'Klage-/Widerspruchsverfahren', shape='box')
    graph.node('F', 'CEO', shape='box')
    graph.node('G', 'Bauteam', shape='box')
    graph.node('H', 'Fertigstellung', shape='box')
    graph.node('X1', 'Prozess unterbrochen', shape='ellipse', style='filled', fillcolor='lightgray')
    graph.node('X2', 'Prozess unterbrochen', shape='ellipse', style='filled', fillcolor='lightgray')
    graph.node('X3', 'Prozess unterbrochen', shape='ellipse', style='filled', fillcolor='lightgray')
    graph.node('X4', 'Prozess unterbrochen', shape='ellipse', style='filled', fillcolor='lightgray')
    
    # Kanten definieren
    graph.edge('A', 'B')
    graph.edge('B', 'D', label='Genehmigung')
    graph.edge('B', 'X1', label='Ablehnung')
    graph.edge('D', 'F', label='Bauantrag genehmigt')
    graph.edge('D', 'E', label='Bauantrag abgelehnt')
    graph.edge('E', 'E1', label='Ja')
    graph.edge('E', 'X2', label='Nein')
    graph.edge('E1', 'F', label='Erfolg')
    graph.edge('E1', 'X3', label='Misserfolg')
    graph.edge('F', 'G', label='Genehmigung')
    graph.edge('F', 'X4', label='Ablehnung')
    graph.edge('G', 'H', label='Aufbau + Stromanschluss')
    
    # Hinweis auf übersprungenen Schritt
    graph.attr(label='Hinweis: Niederlassungsleiter wird übersprungen', labelloc='t')
    
    st.graphviz_chart(graph)
    
    st.info("""
    **Wichtig:** Bei der Digitalen Säule wird der Workflow-Schritt 'Niederlassungsleiter' 
    übersprungen, wodurch der Prozess nach Genehmigung durch den Leiter Akquisitionsmanagement 
    direkt an das Baurecht weitergeleitet wird.
    """)

def show_agraph_workflow():
    # Knoten erstellen
    nodes = [
        Node(id="A", label="Erfassung durch Akquisiteur", size=25),
        Node(id="B", label="Leiter Akquisitionsmanagement", size=25),
        Node(id="D", label="Baurecht", size=25),
        Node(id="E", label="Klage/Widerspruch?", size=20, symbolType="diamond"),
        Node(id="E1", label="Klage-/Widerspruchsverfahren", size=25),
        Node(id="F", label="CEO", size=25),
        Node(id="G", label="Bauteam", size=25),
        Node(id="H", label="Fertigstellung", size=25),
        Node(id="X1", label="Prozess unterbrochen", size=20, color="lightgray"),
        Node(id="X2", label="Prozess unterbrochen", size=20, color="lightgray"),
        Node(id="X3", label