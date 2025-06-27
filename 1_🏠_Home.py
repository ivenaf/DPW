import streamlit as st
import sqlite3


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

# App-Header mit Firmennamen und Logo



# Home-Seiteninhalte
st.header("Willkommen im Ströer Digital Workflow Tool")

st.write("""
Dieses Tool unterstützt den Aufbauprozess unserer digitalen Werbeträger, indem es den gesamten Workflow von der
Erfassung neuer Standorte bis zur finalen Genehmigung und Aufbau abbildet.

### Neue Vermarktungsform: Digitale Säule

Die neue Vermarktungsform "Digitale Säule" unterscheidet sich durch folgende Merkmale:
- Kann ein-, zwei- oder **dreiseitig** aufgebaut werden
- Überspringt den Genehmigungsschritt des Niederlassungsleiters

### Inhalt:
- Visualisierung des Workflows für die Digitale Säule (Prozessdiagramm)
- Dashboard mit wichtigen Kennzahlen
- Workflow-Bearbeitung für die Genehmigungsschritte (Navigation)
- GeoMap 


""")

