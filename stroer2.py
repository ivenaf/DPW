import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import uuid

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

# Hauptfunktion
def main():
    st.title("Digitale Werbeträger - Workflow Tool")
    
    # Seitenleiste mit Navigation
    menu = ["Standort erfassen", "Standorte verwalten", "Workflow bearbeiten", "Dashboard"]
    choice = st.sidebar.selectbox("Menü", menu)
    
    if choice == "Standort erfassen":
        st.subheader("Neuen Standort erfassen")
        create_location_form()
    
    elif choice == "Standorte verwalten":
        st.subheader("Standorte verwalten")
        show_locations()
    
    elif choice == "Workflow bearbeiten":
        st.subheader("Workflow bearbeiten")
        process_workflow()
    
    elif choice == "Dashboard":
        st.subheader("Dashboard")
        show_dashboard()

# Formular zur Standorterfassung
def create_location_form():
    with st.form(key='location_form'):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name des Erfassers", max_chars=50)
            datum = st.date_input("Datum der Akquisition")
            standort = st.text_input("Standortbezeichnung (Straßenname)")
            stadt = st.text_input("Ort (Stadt)")
            lat = st.number_input("Breitengrad", -90.0, 90.0, 50.0)
            lng = st.number_input("Längengrad", -180.0, 180.0, 10.0)
        
        with col2:
            leistungswert = st.text_input("Leistungswert der Werbeträgerseite")
            eigentuemer = st.selectbox("Eigentümer des Standortes", ["Privater Eigentümer", "Stadt"])
            umruestung = st.radio("Neustandort oder Umrüstung", ["Neustandort", "Umrüstung"])
            
            alte_nummer = ""
            if umruestung == "Umrüstung":
                alte_nummer = st.text_input("Alte Werbeträgernummer")
            
            vermarktungsform = st.selectbox("Vermarktungsform", 
                                         ["Roadside-Screen", "City-Screen", "MegaVision", "SuperMotion", "Digitale Säule"])
            
            seiten_options = ["einseitig", "doppelseitig"]
            if vermarktungsform == "Digitale Säule":
                seiten_options.append("dreiseitig")
            
            seiten = st.selectbox("Anzahl der Seiten", seiten_options)
        
        # Bilder hochladen
        st.write("Bilder in unterschiedlichen Entfernungen je Werbeträgerseite")
        uploaded_files = st.file_uploader("Bilder hochladen", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])
        
        submit = st.form_submit_button("Standort speichern")
        
        if submit:
            if not name or not standort or not stadt:
                st.error("Bitte füllen Sie alle Pflichtfelder aus.")
            elif umruestung == "Umrüstung" and not alte_nummer:
                st.error("Bitte geben Sie die alte Werbeträgernummer an.")
            elif not uploaded_files:
                st.error("Bitte laden Sie mindestens ein Bild hoch.")
            else:
                # Speichern der Daten
                location_id = str(uuid.uuid4())
                c.execute('''
                INSERT INTO locations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    location_id, name, datum.isoformat(), standort, stadt, lat, lng,
                    leistungswert, eigentuemer, umruestung == "Umrüstung", alte_nummer,
                    seiten, vermarktungsform, "active", "leiter_akquisition", 
                    datetime.now().isoformat()
                ))
                
                # Workflow-History-Eintrag erstellen
                history_id = str(uuid.uuid4())
                c.execute('''
                INSERT INTO workflow_history VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    history_id, location_id, "erfassung", "completed", 
                    "Standort erfasst", name, datetime.now().isoformat()
                ))
                
                conn.commit()
                st.success("Standort erfolgreich gespeichert.")

# Funktion zum Anzeigen der Standorte
def show_locations():
    c.execute('SELECT * FROM locations')
    result = c.fetchall()
    
    if result:
        locations_df = pd.DataFrame(result, columns=[
            'ID', 'Erfasser', 'Datum', 'Standort', 'Stadt', 'Lat', 'Lng',
            'Leistungswert', 'Eigentümer', 'Umrüstung', 'Alte Nummer',
            'Seiten', 'Vermarktungsform', 'Status', 'Aktueller Step', 'Erstellt'
        ])
        
        # Filteroptionen
        st.sidebar.header("Filter")
        status_filter = st.sidebar.multiselect(
            "Status",
            options=list(locations_df['Status'].unique()),
            default=list(locations_df['Status'].unique())
        )
        
        form_filter = st.sidebar.multiselect(
            "Vermarktungsform",
            options=list(locations_df['Vermarktungsform'].unique()),
            default=list(locations_df['Vermarktungsform'].unique())
        )
        
        filtered_df = locations_df[
            locations_df['Status'].isin(status_filter) &
            locations_df['Vermarktungsform'].isin(form_filter)
        ]
        
        st.write(f"{len(filtered_df)} Standorte gefunden")
        st.dataframe(filtered_df, height=400)
        
        # Details für ausgewählten Standort anzeigen
        selected_id = st.selectbox("Standort-Details anzeigen", filtered_df['ID'].tolist())
        if selected_id:
            show_location_details(selected_id)
    else:
        st.info("Keine Standorte gefunden.")

# Funktion zur Anzeige von Standortdetails
def show_location_details(location_id):
    c.execute('SELECT * FROM locations WHERE id = ?', (location_id,))
    location = c.fetchone()
    
    if location:
        st.subheader(f"Standort: {location[3]}, {location[4]}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Vermarktungsform:** {location[12]}")
            st.write(f"**Seiten:** {location[11]}")
            st.write(f"**Status:** {location[13]}")
            st.write(f"**Aktueller Step:** {location[14]}")
        
        with col2:
            st.write(f"**Erfasser:** {location[1]}")
            st.write(f"**Datum:** {location[2]}")
            st.write(f"**Umrüstung:** {'Ja' if location[9] else 'Nein'}")
            if location[9]:
                st.write(f"**Alte Nummer:** {location[10]}")
        
        # Workflow-Historie anzeigen
        st.subheader("Workflow-Historie")
        c.execute('SELECT * FROM workflow_history WHERE location_id = ? ORDER BY timestamp', (location_id,))
        history = c.fetchall()
        
        if history:
            history_df = pd.DataFrame(history, columns=[
                'ID', 'Standort ID', 'Step', 'Status', 'Kommentar', 'Bearbeiter', 'Timestamp'
            ])
            st.dataframe(history_df[['Step', 'Status', 'Kommentar', 'Bearbeiter', 'Timestamp']])
        else:
            st.info("Keine Workflow-Historie gefunden.")

# Workflow-Bearbeitung
def process_workflow():
    # Rollen für den Demo-Zweck
    role = st.sidebar.selectbox(
        "Rolle auswählen (Demo)",
        ["Leiter Akquisitionsmanagement", "Niederlassungsleiter", "Baurecht", "CEO", "Bauteam"]
    )
    
    # Standorte für den aktuellen Step laden
    current_step = role.lower().replace(" ", "_")
    
    # Bei Digitaler Säule speziellen Workflow beachten
    if current_step == "niederlassungsleiter":
        c.execute('''
        SELECT * FROM locations 
        WHERE current_step = ? AND vermarktungsform != "Digitale Säule"
        ''', (current_step,))
    else:
        # Für Bauteam nur genehmigte Standorte
        if current_step == "bauteam":
            c.execute('''
            SELECT * FROM locations 
            WHERE current_step = ? AND status = "active"
            ''', (current_step,))
        else:
            c.execute('''
            SELECT * FROM locations 
            WHERE current_step = ? AND status = "active"
            ''', (current_step,))
    
    result = c.fetchall()
    
    if result:
        locations_df = pd.DataFrame(result, columns=[
            'ID', 'Erfasser', 'Datum', 'Standort', 'Stadt', 'Lat', 'Lng',
            'Leistungswert', 'Eigentümer', 'Umrüstung', 'Alte Nummer',
            'Seiten', 'Vermarktungsform', 'Status', 'Aktueller Step', 'Erstellt'
        ])
        
        st.write(f"{len(locations_df)} Standorte zur Bearbeitung")
        st.dataframe(locations_df[['Standort', 'Stadt', 'Vermarktungsform', 'Seiten', 'Erstellt']])
        
        # Standort zur Bearbeitung auswählen
        selected_id = st.selectbox("Standort bearbeiten", locations_df['ID'].tolist())
        
        if selected_id:
            selected_row = locations_df[locations_df['ID'] == selected_id].iloc[0]
            st.subheader(f"Standort bearbeiten: {selected_row['Standort']}, {selected_row['Stadt']}")
            
            # Formular zur Entscheidung
            with st.form(key='workflow_form'):
                entscheidung = st.radio("Entscheidung", ["Genehmigen", "Ablehnen"])
                kommentar = st.text_area("Kommentar")
                
                submit = st.form_submit_button("Speichern")
                
                if submit:
                    # Nächsten Workflow-Schritt bestimmen
                    next_step = ""
                    if entscheidung == "Genehmigen":
                        vermarktungsform = selected_row['Vermarktungsform']
                        
                        if current_step == "leiter_akquisition":
                            if vermarktungsform == "Digitale Säule":
                                next_step = "baurecht"  # Skip Niederlassungsleiter
                            else:
                                next_step = "niederlassungsleiter"
                        elif current_step == "niederlassungsleiter":
                            next_step = "baurecht"
                        elif current_step == "baurecht":
                            next_step = "ceo"
                        elif current_step == "ceo":
                            next_step = "bauteam"
                        elif current_step == "bauteam":
                            next_step = "fertig"
                            
                        new_status = "active"
                        workflow_status = "approved"
                    else:
                        new_status = "rejected"
                        next_step = "rejected"
                        workflow_status = "rejected"
                    
                    # Status in der Datenbank aktualisieren
                    c.execute('''
                    UPDATE locations 
                    SET status = ?, current_step = ? 
                    WHERE id = ?
                    ''', (new_status, next_step, selected_id))
                    
                    # Workflow-Historie aktualisieren
                    history_id = str(uuid.uuid4())
                    c.execute('''
                    INSERT INTO workflow_history VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        history_id, selected_id, current_step, workflow_status,
                        kommentar, role, datetime.now().isoformat()
                    ))
                    
                    conn.commit()
                    st.success(f"Entscheidung gespeichert. Neuer Status: {new_status}, Nächster Step: {next_step}")
    else:
        st.info(f"Keine Standorte für {role} zur Bearbeitung.")

# Dashboard anzeigen
def show_dashboard():
    st.subheader("Aktueller Prozessüberblick")
    
    # KPIs berechnen
    c.execute('SELECT COUNT(*) FROM locations')
    total = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM locations WHERE status = "active" AND current_step != "fertig"')
    in_progress = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM locations WHERE status = "rejected"')
    rejected = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM locations WHERE current_step = "fertig"')
    completed = c.fetchone()[0]
    
    # KPI-Anzeige
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Gesamt", total)
    col2.metric("In Bearbeitung", in_progress)
    col3.metric("Abgelehnt", rejected)
    col4.metric("Abgeschlossen", completed)
    
    # Prozess Funnel
    st.subheader("Prozess-Funnel")
    steps = ['erfassung', 'leiter_akquisition', 'niederlassungsleiter', 'baurecht', 'ceo', 'bauteam', 'fertig']
    counts = []
    
    for step in steps:
        c.execute('SELECT COUNT(*) FROM locations WHERE current_step = ? OR (status = "active" AND current_step > ?)', (step, step))
        counts.append(c.fetchone()[0])
    
    funnel_df = pd.DataFrame({
        'Step': ['Erfassung', 'Leiter Akq.', 'Niederl.leiter', 'Baurecht', 'CEO', 'Bauteam', 'Fertig'],
        'Anzahl': counts
    })
    st.bar_chart(funnel_df.set_index('Step'))
    
    # Aufteilung nach Vermarktungsform
    st.subheader("Aufteilung nach Vermarktungsform")
    c.execute('SELECT vermarktungsform, COUNT(*) FROM locations GROUP BY vermarktungsform')
    forms = c.fetchall()
    
    if forms:
        form_df = pd.DataFrame(forms, columns=['Vermarktungsform', 'Anzahl'])
        st.bar_chart(form_df.set_index('Vermarktungsform'))
    
    # Zeitliche Entwicklung
    st.subheader("Zeitliche Entwicklung")
    c.execute('''
    SELECT date(created_at), COUNT(*) 
    FROM locations 
    GROUP BY date(created_at) 
    ORDER BY date(created_at)
    ''')
    dates = c.fetchall()
    
    if dates:
        date_df = pd.DataFrame(dates, columns=['Datum', 'Neue Standorte'])
        st.line_chart(date_df.set_index('Datum'))

if __name__ == '__main__':
    main()