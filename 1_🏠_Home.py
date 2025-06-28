import streamlit as st
import sqlite3
import os

# Logo zur Sidebar hinzufügen
from config import add_logo
add_logo()

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('werbetraeger.db', check_same_thread=False)
c = conn.cursor()

# Tabellen erstellen, falls sie noch nicht existieren
def create_tables():
    c.execute('''
    CREATE TABLE IF NOT EXISTS locations (
        id TEXT PRIMARY KEY,
        erfasser TEXT,
        datum TEXT,
        standort TEXT,
        stadt TEXT,
        lat REAL,
        lng REAL,
        leistungswert TEXT,
        eigentuemer TEXT,
        umruestung BOOLEAN,
        alte_nummer TEXT,
        seiten TEXT,
        vermarktungsform TEXT,
        status TEXT,
        current_step TEXT,
        created_at TEXT
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS workflow_history (
        id TEXT PRIMARY KEY,
        location_id TEXT,
        step TEXT,
        status TEXT,
        comment TEXT,
        user TEXT,
        timestamp TEXT,
        FOREIGN KEY (location_id) REFERENCES locations (id)
    )
    ''')
    conn.commit()

create_tables()

# CSS für optimiertes Layout
st.markdown("""
<style>
    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .home-text p {
        line-height: 1.5;
        max-width: 600px;  /* Textbreite begrenzen */
    }
    .custom-header {
        margin-bottom: 1rem;
    }
    .stMarkdown {
        max-width: 600px;  /* Breiteren Textbereich */
    }
</style>
""", unsafe_allow_html=True)

# App-Header - außerhalb der Spalten
st.markdown('<h1 class="custom-header">Digital Workflow Tool</h1>', unsafe_allow_html=True)

# Verbesserte Spaltenaufteilung (breiter und weniger hoch)
col1, col2 = st.columns([2, 1])

with col1:
    # Kompakterer Text
    st.write("""
    Dieses Tool unterstützt den Aufbauprozess unserer digitalen Werbeträger, indem es den gesamten Workflow abbildet.
    """)
    
    st.subheader("Neue Vermarktungsform: Digitale Säule")
    
    # Bulletpoints mit einzelnen Markdown-Anweisungen für separate Zeilen
    st.markdown("Die neue Vermarktungsform \"Digitale Säule\" unterscheidet sich durch:")
    
    st.markdown("• Kann ein-, zwei- oder **dreiseitig** aufgebaut werden")
    st.markdown("• Überspringt den Genehmigungsschritt des Niederlassungsleiters")
    
    st.subheader("Inhalt:")
    st.markdown("• Prozessdiagramm") 
    st.markdown("• Dashboard mit Kennzahlen")
    st.markdown("• GeoMap")
    st.markdown("• Workflow-Navigation")

with col2:
    # Bild etwas tiefer platzieren
    st.write("")
    st.write("")
    st.write("")  # Mehr Abstand nach oben
    
    image_path = "säule3.png"
    if os.path.exists(image_path):
        st.image(image_path, width=300)
    else:
        st.error("Bild nicht gefunden: säule3.png")