import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import uuid

# Streamlit-Seiteneinstellungen
st.set_page_config(layout="wide", page_title="Bauteam")

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('werbetraeger.db', check_same_thread=False)
c = conn.cursor()

st.title("Bauteam")
st.write("Planung und Durchführung der Baumaßnahmen für die genehmigten Digitalen Säulen.")

# Funktion zum Laden aller Standorte für das Bauteam
def load_bauteam_locations():
    c.execute('''
    SELECT id, erfasser, datum, standort, stadt, lat, lng, eigentuemer, 
           umruestung, seiten, vermarktungsform, created_at
    FROM locations 
    WHERE status = 'active' AND current_step = 'bauteam'
    ORDER BY created_at DESC
    ''')
    
    locations = c.fetchall()
    
    if not locations:
        return pd.DataFrame()
    
    # In DataFrame umwandeln
    df = pd.DataFrame(locations, columns=[
        'id', 'erfasser', 'datum', 'standort', 'stadt', 'lat', 'lng',
        'eigentuemer', 'umruestung', 'seiten', 'vermarktungsform', 'created_at'
    ])
    
    # Formatierungen anwenden
    df['umruestung'] = df['umruestung'].apply(lambda x: 'Umrüstung' if x else 'Neustandort')
    df['eigentuemer'] = df['eigentuemer'].apply(lambda x: 'Stadt' if x == 'Stadt' else 'Privat')
    
    return df

# Funktion zum Laden der Historie eines Standorts
def load_workflow_history(location_id):
    c.execute('''
    SELECT step, status, comment, user, timestamp
    FROM workflow_history
    WHERE location_id = ?
    ORDER BY timestamp ASC
    ''', (location_id,))
    
    history = c.fetchall()
    
    if not history:
        return pd.DataFrame()
    
    # In DataFrame umwandeln
    df = pd.DataFrame(history, columns=['Schritt', 'Status', 'Kommentar', 'Benutzer', 'Zeitstempel'])
    return df

# Funktion zum Laden eines spezifischen Standorts mit allen Details
def load_location_details(location_id):
    c.execute('''
    SELECT id, erfasser, datum, standort, stadt, lat, lng, leistungswert, eigentuemer, 
           umruestung, alte_nummer, seiten, vermarktungsform, status, current_step, created_at,
           bauantrag_datum
    FROM locations 
    WHERE id = ?
    ''', (location_id,))
    
    location = c.fetchone()
    
    if not location:
        return None
    
    # Alle Spalten in der DB ermitteln
    c.execute('PRAGMA table_info(locations)')
    columns = c.fetchall()
    column_names = [col[1] for col in columns]
    
    # Dictionary erstellen mit allen Werten
    location_dict = {column_names[i]: location[i] for i in range(len(location))}
    
    # Einige Werte formatieren
    location_dict['eigentuemer'] = 'Stadt' if location_dict.get('eigentuemer') == 'Stadt' else 'Privat'
    location_dict['umruestung'] = 'Umrüstung' if location_dict.get('umruestung') == 1 else 'Neustandort'
    
    return location_dict

# Funktion zum Aktualisieren der Bau-Informationen
def update_build_info(location_id, build_data):
    now = datetime.now().isoformat()
    history_id = str(uuid.uuid4())
    
    # Benutzerdefinierte Felder für Bau-Informationen in der Datenbank speichern
    # In einer echten App würden wir eine separate Tabelle für detaillierte Bau-Informationen haben
    try:
        # Prüfen, ob Spalten bereits existieren
        c.execute("PRAGMA table_info(locations)")
        columns = c.fetchall()
        column_names = [col[1] for col in columns]
        
        # Felder für Baudaten hinzufügen, falls sie noch nicht existieren
        if 'plan_date' not in column_names:
            c.execute('ALTER TABLE locations ADD COLUMN plan_date TEXT')
        if 'ist_date' not in column_names:
            c.execute('ALTER TABLE locations ADD COLUMN ist_date TEXT')
        if 'build_status' not in column_names:
            c.execute('ALTER TABLE locations ADD COLUMN build_status TEXT')
        if 'contractor' not in column_names:
            c.execute('ALTER TABLE locations ADD COLUMN contractor TEXT')
        if 'power_connection' not in column_names:
            c.execute('ALTER TABLE locations ADD COLUMN power_connection TEXT')
    except:
        # Bei Fehler weitermachen - Spalten existieren möglicherweise bereits
        pass
    
    # Update der Bau-Informationen in der Locations-Tabelle
    c.execute('''
    UPDATE locations
    SET plan_date = ?, ist_date = ?, build_status = ?, contractor = ?, power_connection = ?
    WHERE id = ?
    ''', (
        build_data.get('plan_date', ''),
        build_data.get('ist_date', ''),
        build_data.get('build_status', ''),
        build_data.get('contractor', ''),
        build_data.get('power_connection', ''),
        location_id
    ))
    
    # Workflow-History-Eintrag erstellen
    c.execute('''
    INSERT INTO workflow_history VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        history_id, 
        location_id, 
        "bauteam", 
        "updated", 
        f"Bau-Informationen aktualisiert: {build_data.get('build_status', '')}",
        st.session_state.get('username', 'Bauteam'),
        now
    ))
    
    conn.commit()
    return True

# Funktion zum Abschließen des Bauvorhabens und Weiterleiten zur Fertigstellung
def complete_build(location_id, build_data):
    now = datetime.now().isoformat()
    history_id = str(uuid.uuid4())
    
    # Status aktualisieren
    c.execute('''
    UPDATE locations
    SET status = ?, current_step = ?, ist_date = ?
    WHERE id = ?
    ''', ('active', 'fertigstellung', build_data.get('ist_date', now), location_id))
    
    # Workflow-History-Eintrag erstellen
    c.execute('''
    INSERT INTO workflow_history VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        history_id, 
        location_id, 
        "bauteam", 
        "completed", 
        f"Bau abgeschlossen. Weitergeleitet zur Fertigstellung. IST-Datum: {build_data.get('ist_date', now)}",
        st.session_state.get('username', 'Bauteam'),
        now
    ))
    
    conn.commit()
    return True

# Simulieren eines eingeloggten Benutzers (in einer echten App würde hier ein Login-System stehen)
if 'username' not in st.session_state:
    st.session_state.username = "Bernd Bauleiter"
    st.session_state.role = "Bauteam"

# Anzeigen aller Standorte für das Bauteam
st.subheader("Standorte in Umsetzung")

df = load_bauteam_locations()

if df.empty:
    st.info("Aktuell gibt es keine Standorte in der Bauphase.")
else:
    # Liste der Standorte anzeigen
    st.write(f"**{len(df)} Standorte** in der Bauphase.")
    
    # Vereinfachte Tabelle für die Übersicht
    display_df = df[['standort', 'stadt', 'vermarktungsform', 'seiten', 'created_at']].copy()
    display_df.columns = ['Standort', 'Stadt', 'Vermarktungsform', 'Seiten', 'Erfasst am']
    
    # Datum formatieren
    display_df['Erfasst am'] = pd.to_datetime(display_df['Erfasst am']).dt.strftime('%d.%m.%Y')
    
    st.dataframe(display_df, hide_index=True)
    
    # Auswahl für detaillierte Ansicht
    selected_location = st.selectbox(
        "Standort auswählen:",
        options=df['id'].tolist(),
        format_func=lambda x: f"{df[df['id'] == x]['standort'].iloc[0]}, {df[df['id'] == x]['stadt'].iloc[0]} ({df[df['id'] == x]['vermarktungsform'].iloc[0]})"
    )
    
    if selected_location:
        st.markdown("---")
        
        # Tabs für verschiedene Ansichten
        tab1, tab2, tab3, tab4 = st.tabs(["Standortdetails", "Bauplanung", "Workflow-Historie", "Dokumente"])
        
        location = load_location_details(selected_location)
        
        with tab1:
            st.subheader("Standortdetails")
            
            if location:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Standort:** {location.get('standort')}")
                    st.markdown(f"**Stadt:** {location.get('stadt')}")
                    st.markdown(f"**Vermarktungsform:** {location.get('vermarktungsform')}")
                    st.markdown(f"**Seiten:** {location.get('seiten')}")
                    st.markdown(f"**Art:** {location.get('umruestung')}")
                    if location.get('umruestung') == 'Umrüstung':
                        st.markdown(f"**Alte Werbeträgernummer:** {location.get('alte_nummer')}")
                    
                with col2:
                    st.markdown(f"**Eigentümer:** {location.get('eigentuemer')}")
                    st.markdown(f"**Leistungswert:** {location.get('leistungswert')}")
                    st.markdown(f"**Bauantrag genehmigt am:** {location.get('bauantrag_datum')}")
                    st.markdown(f"**Koordinaten:** {location.get('lat')}, {location.get('lng')}")
                    
                
                # Karte anzeigen
                st.subheader("Standort auf Karte")
                map_data = pd.DataFrame({
                    'lat': [float(location.get('lat'))],
                    'lon': [float(location.get('lng'))]
                })
                st.map(map_data, zoom=15)
        
        with tab2:
            st.subheader("Bauplanung und -fortschritt")
            
            # Status prüfen und bereits eingetragene Baudaten laden
            build_status = location.get('build_status', '')
            plan_date = location.get('plan_date', '')
            ist_date = location.get('ist_date', '')
            contractor = location.get('contractor', '')
            power_connection = location.get('power_connection', '')
            
            # Formular zur Bauplanung
            with st.form("build_planning_form"):
                st.write("Bitte geben Sie die Bauplanungsdaten ein:")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    plan_date_input = st.date_input(
                        "Geplantes Aufbaudatum (PLAN)",
                        value=datetime.fromisoformat(plan_date) if plan_date else datetime.now() + timedelta(days=14),
                        min_value=datetime.now()
                    )
                    
                    ist_date_input = st.date_input(
                        "Tatsächliches Aufbaudatum (IST)",
                        value=datetime.fromisoformat(ist_date) if ist_date else None,
                        min_value=datetime.now() - timedelta(days=30),
                        help="Leer lassen, wenn noch nicht realisiert"
                    )
                    
                    build_status_input = st.selectbox(
                        "Status der Baumaßnahme",
                        options=[
                            "Nicht begonnen",
                            "In Planung",
                            "Materialbestellung",
                            "Fundament vorbereitet",
                            "Gerüstaufbau",
                            "Elektrik installiert",
                            "Display montiert",
                            "Inbetriebnahme",
                            "Abgeschlossen"
                        ],
                        index=0 if not build_status else None,
                        format_func=lambda x: f"▶ {x}" if x == build_status else x
                    )
                
                with col2:
                    contractor_input = st.text_input(
                        "Beauftragter Subunternehmer",
                        value=contractor,
                        placeholder="Name des Bauunternehmens"
                    )
                    
                    power_connection_input = st.selectbox(
                        "Status Stromanschluss",
                        options=[
                            "Nicht beantragt",
                            "Beantragt",
                            "Genehmigt",
                            "In Vorbereitung",
                            "Installiert",
                            "Aktiv"
                        ],
                        index=0 if not power_connection else None,
                        format_func=lambda x: f"▶ {x}" if x == power_connection else x
                    )
                    
                    # Zusätzliche Felder für die Digitale Säule
                    if location.get('vermarktungsform') == "Digitale Säule":
                        st.info("📌 **Hinweis Digitale Säule**: Bitte auf ausreichende Stromversorgung und Netzwerkverbindung achten!")
                        # Hier könnten weitere spezifische Felder für die Digitale Säule hinzugefügt werden
                
                build_notes = st.text_area(
                    "Anmerkungen zum Bauvorhaben",
                    placeholder="Besonderheiten, Herausforderungen, zusätzliche Informationen..."
                )
                
                build_data = {
                    'plan_date': plan_date_input.isoformat(),
                    'ist_date': ist_date_input.isoformat() if ist_date_input is not None else '',
                    'build_status': build_status_input,
                    'contractor': contractor_input,
                    'power_connection': power_connection_input,
                    'notes': build_notes
                }
                
                col1, col2 = st.columns(2)
                
                with col1:
                    submit_button = st.form_submit_button("Baudaten speichern")
                
                with col2:
                    # Button für vollständige Fertigstellung nur aktivieren, 
                    # wenn alle notwendigen Daten vorhanden sind
                    ist_complete = (
                        build_status_input == "Abgeschlossen" and
                        ist_date_input is not None and
                        power_connection_input in ["Installiert", "Aktiv"]
                    )
                    
                    if ist_complete:
                        completion_msg = "Standort als fertig melden und zur Fertigstellung weiterleiten"
                    else:
                        completion_msg = "Bitte alle Arbeiten abschließen, um den Standort als fertig zu melden"
                    
                    complete_button = st.form_submit_button(
                        "Als fertiggestellt markieren", 
                        disabled=not ist_complete,
                        help=completion_msg
                    )
                
                if submit_button:
                    success = update_build_info(selected_location, build_data)
                    
                    if success:
                        st.success("Baudaten wurden erfolgreich gespeichert!")
                        st.rerun()
                
                if complete_button and ist_complete:
                    success = complete_build(selected_location, build_data)
                    
                    if success:
                        st.success("Standort als fertiggestellt markiert und zur finalen Fertigstellung weitergeleitet!")
                        st.rerun()
            
            # Visualisierung des Fortschritts
            if build_status:
                st.subheader("Baufortschritt")
                
                # Fortschrittsstufen und ihre Werte
                progress_steps = {
                    "Nicht begonnen": 0,
                    "In Planung": 0.1,
                    "Materialbestellung": 0.2,
                    "Fundament vorbereitet": 0.4,
                    "Gerüstaufbau": 0.6,
                    "Elektrik installiert": 0.7,
                    "Display montiert": 0.8,
                    "Inbetriebnahme": 0.9,
                    "Abgeschlossen": 1.0
                }
                
                # Aktuellen Fortschritt anzeigen
                current_progress = progress_steps.get(build_status, 0)
                st.progress(current_progress)
                
                # Zeitplanung anzeigen
                if plan_date:
                    plan_date_dt = datetime.fromisoformat(plan_date)
                    days_to_plan = (plan_date_dt - datetime.now()).days
                    
                    if days_to_plan > 0:
                        st.info(f"🗓️ Geplante Fertigstellung in {days_to_plan} Tagen ({plan_date_dt.strftime('%d.%m.%Y')})")
                    elif days_to_plan < 0:
                        st.error(f"⚠️ Geplanter Termin überschritten um {abs(days_to_plan)} Tage ({plan_date_dt.strftime('%d.%m.%Y')})")
                    else:
                        st.warning(f"🚨 Plantermin ist heute ({plan_date_dt.strftime('%d.%m.%Y')})")
        
        with tab3:
            st.subheader("Workflow-Historie")
            
            # Workflow-Historie des Standorts laden
            history_df = load_workflow_history(selected_location)
            
            if not history_df.empty:
                # Formatierungen für bessere Lesbarkeit
                history_df['Zeitstempel'] = pd.to_datetime(history_df['Zeitstempel']).dt.strftime('%d.%m.%Y, %H:%M Uhr')
                
                # Anzeigen der Historie mit farbiger Markierung
                for idx, row in history_df.iterrows():
                    status = row['Status'].lower() if pd.notna(row['Status']) else ""
                    if status in ['approved', 'completed']:
                        emoji = "✅"
                        color = "green"
                    elif status in ['rejected', 'failed']:
                        emoji = "❌"
                        color = "red"
                    elif status in ['objection', 'pending', 'updated']:
                        emoji = "⚠️"
                        color = "orange"
                    else:
                        emoji = "ℹ️"
                        color = "blue"
                    
                    st.markdown(
                        f"<div style='padding:10px; margin-bottom:10px; border-left: 3px solid {color};'>"
                        f"<strong>{emoji} {row['Schritt'].title()}</strong> ({row['Zeitstempel']})<br>"
                        f"{row['Kommentar']}<br>"
                        f"<small>Bearbeitet von: {row['Benutzer']}</small>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )
            else:
                st.info("Keine Workflow-Historie für diesen Standort verfügbar.")
        
        with tab4:
            st.subheader("Dokumente")
            
            # In einer echten Anwendung würden hier Dokumente hochgeladen und angezeigt werden
            
            # Demo-Implementierung für Dokumente
            st.write("Hier können Sie Dokumente für den Standort hochladen und einsehen.")
            
            # Dokumenten-Tabs
            doc_tab1, doc_tab2, doc_tab3 = st.tabs(["Bauzeichnungen", "Genehmigungen", "Abnahmeprotokolle"])
            
            with doc_tab1:
                st.markdown("#### Bauzeichnungen")
                
                # Upload-Option
                uploaded_file = st.file_uploader("Bauzeichnung hochladen", type=['pdf', 'jpg', 'png'])
                
                if location.get('vermarktungsform') == "Digitale Säule":
                    # Beispiel-Dokumente für Digitale Säule
                    st.markdown("##### Vorhandene Zeichnungen:")
                    st.markdown("""
                    * 📄 [Fundament_Digitale_Säule.pdf]() - *hochgeladen am 12.05.2023*
                    * 📄 [Elektroanschluss_Schema.pdf]() - *hochgeladen am 14.05.2023*
                    * 📄 [Display_Integration.pdf]() - *hochgeladen am 15.05.2023*
                    """)
                else:
                    # Andere Werbeträgerformate
                    st.info("Keine Bauzeichnungen vorhanden. Bitte laden Sie die erforderlichen Dokumente hoch.")
            
            with doc_tab2:
                st.markdown("#### Genehmigungen")
                
                # Anzeigen der Genehmigungsdokumente
                st.markdown("""
                * 📄 [Baugenehmigung_Stadt.pdf]() - *erhalten am 22.04.2023*
                * 📄 [Zustimmung_Eigentümer.pdf]() - *hochgeladen am 05.04.2023*
                * 📄 [Netzanschluss_Genehmigung.pdf]() - *erhalten am 28.04.2023*
                """)
                
                # Upload-Option
                uploaded_genehmigung = st.file_uploader("Genehmigung hochladen", type=['pdf'])
            
            with doc_tab3:
                st.markdown("#### Abnahmeprotokolle")
                
                # Status der Abnahme anzeigen
                if build_status == "Abgeschlossen":
                    st.success("✅ Standort fertiggestellt und bereit zur finalen Abnahme")
                else:
                    st.warning("⚠️ Standort noch nicht fertiggestellt - keine Abnahme möglich")
                
                # Upload-Option
                uploaded_protokoll = st.file_uploader("Abnahmeprotokoll hochladen", type=['pdf'])
                
                # Checkliste für die Abnahme
                if build_status in ["Inbetriebnahme", "Abgeschlossen"]:
                    st.markdown("#### Abnahme-Checkliste")
                    
                    st.checkbox("Standsicherheit geprüft", value=True)
                    st.checkbox("Elektrische Funktion getestet", value=True)
                    st.checkbox("Display-Funktionalität bestätigt", value=True)
                    st.checkbox("Netzwerkverbindung hergestellt", value=True)
                    st.checkbox("Optische Mängel geprüft", value=True)
                    
                    st.text_area("Anmerkungen zur Abnahme", placeholder="Besonderheiten bei der Abnahme...")
                    
                    st.button("Abnahmeprotokoll generieren", disabled=True)

# Sidebar mit Workflow-Information
st.sidebar.title("Workflow-Information")
st.sidebar.markdown("""
### Aktueller Schritt: Bauteam

In diesem Schritt erfolgt die praktische Umsetzung des genehmigten Standorts:

1. Planung des Aufbaus und Terminierung
2. Beauftragung von Subunternehmern
3. Organisation des Stromanschlusses (besonders wichtig für Digitale Säule)
4. Durchführung und Überwachung der Bauarbeiten
5. Abnahme und Qualitätssicherung

**Besonderheiten der Digitalen Säule:**
- Höhere Anforderungen an Stromversorgung und Netzanbindung
- Spezielle Display-Installation und -Kalibrierung
- Erhöhte Sicherheitsanforderungen an die elektrische Installation
""")

st.sidebar.markdown("""
### Workflow der Digitalen Säule:
1. ✅ Erfassung durch Akquisiteur
2. ✅ Leiter Akquisitionsmanagement
3. ~~Niederlassungsleiter~~ (übersprungen)
4. ✅ Baurecht
5. ✅ CEO
6. 🔄 **Bauteam**
7. ➡️ Fertigstellung
""")

# Verbindung schließen am Ende
conn.close()