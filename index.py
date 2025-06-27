import os

# Verzeichnisse
base_dir = os.path.dirname(__file__)
pages_dir = os.path.join(base_dir, "pages")
workflow_dir = os.path.join(pages_dir, "Workflow")

# Stellen Sie sicher, dass der Workflow-Ordner existiert
if not os.path.exists(workflow_dir):
    workflow_dir = os.path.join(pages_dir, "01_Prozessschritte")  # Alternativer Name
    if not os.path.exists(workflow_dir):
        print("Weder 'Workflow' noch '01_Prozessschritte' Ordner gefunden.")
        exit(1)

# Index-Datei erstellen
index_content = """
import streamlit as st

st.set_page_config(page_title="Workflow-Übersicht", page_icon="🔄")

st.title("Workflow der Digitalen Säule")

st.write('''
## Prozessschritte im Überblick

Der Workflow der Digitalen Säule umfasst folgende Schritte:

1. **Erfassung** - Neue Standorte werden durch den Akquisiteur erfasst
2. **Leiter Akquisition** - Prüfung durch den Leiter der Akquisition
3. **Baurecht** - Baurechtliche Prüfung und Genehmigung
4. **CEO-Genehmigung** - Wirtschaftliche Freigabe durch den CEO
5. **Bauteam** - Planung und Durchführung der Baumaßnahmen
6. **Fertigstellung** - Abnahme und Inbetriebnahme der Digitalen Säule

Wählen Sie einen Prozessschritt aus der Seitenleiste, um zum entsprechenden Arbeitsbereich zu navigieren.
''')

st.info("⚠️ Hinweis: Die Digitale Säule überspringt den Genehmigungsschritt des Niederlassungsleiters.")
"""

# Index-Datei im Workflow-Ordner erstellen
index_path = os.path.join(workflow_dir, "00_Workflow_Index.py")
with open(index_path, "w") as f:
    f.write(index_content)

print(f"Index-Datei erstellt: {index_path}")
print("Starte Streamlit neu mit: streamlit run 1_Home.py")