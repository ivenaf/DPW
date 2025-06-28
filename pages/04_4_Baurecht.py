import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import uuid
import random

# Streamlit-Seiteneinstellungen
st.set_page_config(layout="wide", page_title="Baurecht")

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('werbetraeger.db', check_same_thread=False)
c = conn.cursor()

st.title("Baurecht")
st.write("Verwaltung von Bauanträgen und behördlichen Genehmigungen für die Digitalen Säulen.")

# Funktion zum Laden aller Standorte, die im Baurechtsschritt sind
def load_baurecht_locations():
    c.execute('''
    SELECT id, erfasser, datum, standort, stadt, lat, lng, eigentuemer, 
           umruestung, seiten, vermarktungsform, created_at
    FROM locations 
    WHERE status = 'active' AND current_step = 'baurecht'
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
    df = pd.DataFrame(history, columns=['Schritt', 'Aktion', 'Nachricht', 'Benutzer', 'Zeitstempel'])
    return df

# Funktion zum Laden eines spezifischen Standorts mit allen Details
def load_location_details(location_id):
    c.execute('''
    SELECT id, erfasser, datum, standort, stadt, lat, lng, leistungswert, eigentuemer, 
           umruestung, alte_nummer, seiten, vermarktungsform, status, current_step, created_at
    FROM locations 
    WHERE id = ?
    ''', (location_id,))
    
    location = c.fetchone()
    
    if not location:
        return None
    
    return {
        'id': location[0],
        'erfasser': location[1],
        'datum': location[2],
        'standort': location[3],
        'stadt': location[4],
        'lat': location[5],
        'lng': location[6],
        'leistungswert': location[7],
        'eigentuemer': 'Stadt' if location[8] == 'Stadt' else 'Privat',
        'umruestung': 'Umrüstung' if location[9] else 'Neustandort',
        'alte_nummer': location[10],
        'seiten': location[11],
        'vermarktungsform': location[12],
        'status': location[13],
        'current_step': location[14],
        'created_at': location[15]
    }

# Funktion zum Aktualisieren des Bauantrags
def update_bauantrag(location_id, antragsdaten, status):
    now = datetime.now().isoformat()
    history_id = str(uuid.uuid4())
    
    # Antragsdatum in der Datenbank speichern (in einer echten App würden hier mehr Daten gespeichert werden)
    c.execute('''
    UPDATE locations
    SET bauantrag_datum = ?
    WHERE id = ?
    ''', (antragsdaten['antragsdatum'], location_id))
    
    # Workflow-History-Eintrag erstellen
    c.execute('''
    INSERT INTO workflow_history VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        history_id, 
        location_id, 
        "baurecht", 
        "submitted",  # Dies sollte 'status' sein
        f"Bauantrag eingereicht: {antragsdaten['antragsnummer']}", 
        st.session_state.get('username', 'Baurecht-Team'),
        now
    ))
    
    conn.commit()
    return True

# Funktion zum Verarbeiten der Bauantragsentscheidung
def process_bauantrag_entscheidung(location_id, genehmigt, grund=None, widerspruch=False):
    now = datetime.now().isoformat()
    history_id = str(uuid.uuid4())
    
    if genehmigt:
        # Bauantrag genehmigt - zum CEO weiterleiten
        next_step = "ceo"
        status = "active"
        action = "approved"
        message = "Bauantrag genehmigt. Weiterleitung an CEO zur finalen Genehmigung."
    else:
        if widerspruch:
            # Widerspruch einlegen
            next_step = "widerspruch"
            status = "active"
            action = "objection"
            message = f"Bauantrag abgelehnt. Widerspruch eingeleitet. Grund: {grund}"
        else:
            # Keine Widerspruchseinlegung - Prozess beenden
            next_step = "abgebrochen"
            status = "rejected"
            action = "rejected"
            message = f"Bauantrag abgelehnt. Prozess beendet. Grund: {grund}"
    
    # Status aktualisieren
    c.execute('''
    UPDATE locations
    SET status = ?, current_step = ?
    WHERE id = ?
    ''', (status, next_step, location_id))
    
    # Workflow-History-Eintrag erstellen
    c.execute('''
    INSERT INTO workflow_history VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        history_id, 
        location_id, 
        "baurecht", 
        action,  # Hier wird 'action' verwendet, aber es sollte 'status' sein
        message, 
        st.session_state.get('username', 'Baurecht-Team'),
        now
    ))
    
    conn.commit()
    return True

# Simulieren eines eingeloggten Benutzers (in einer echten App würde hier ein Login-System stehen)
if 'username' not in st.session_state:
    st.session_state.username = "Barbara Baurecht"
    st.session_state.role = "Baurecht"

# Anzeigen aller Standorte im Baurechtsschritt
st.subheader("Standorte im Baurechtsschritt")

df = load_baurecht_locations()

if df.empty:
    st.info("Aktuell gibt es keine Standorte im Baurechtsschritt.")
else:
    # Liste der Standorte anzeigen
    st.write(f"**{len(df)} Standorte** im Baurechtsschritt.")
    
    # Vereinfachte Tabelle für die Übersicht
    display_df = df[['id', 'standort', 'stadt', 'eigentuemer', 'vermarktungsform', 'created_at']].copy()
    display_df.columns = ['ID', 'Standort', 'Stadt', 'Eigentümer', 'Vermarktungsform', 'Erfasst am']
    
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
        tab1, tab2, tab3 = st.tabs(["Standortdetails", "Bauantrag", "Historie"])
        
        location = load_location_details(selected_location)
        
        with tab1:
            st.subheader("Standortdetails")
            
            if location:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Standort:** {location['standort']}")
                    st.markdown(f"**Stadt:** {location['stadt']}")
                    st.markdown(f"**Vermarktungsform:** {location['vermarktungsform']}")
                    st.markdown(f"**Seiten:** {location['seiten']}")
                    st.markdown(f"**Art:** {location['umruestung']}")
                    if location['umruestung'] == 'Umrüstung':
                        st.markdown(f"**Alte Werbeträgernummer:** {location['alte_nummer']}")
                    
                with col2:
                    st.markdown(f"**Erfasst von:** {location['erfasser']}")
                    st.markdown(f"**Datum der Akquisition:** {location['datum']}")
                    st.markdown(f"**Koordinaten:** {location['lat']}, {location['lng']}")
                    st.markdown(f"**Eigentümer:** {location['eigentuemer']}")
                    st.markdown(f"**Leistungswert:** {location['leistungswert']}")
                
                # Karte anzeigen
                st.subheader("Standort auf Karte")
                map_data = pd.DataFrame({
                    'lat': [float(location['lat'])],
                    'lon': [float(location['lng'])]
                })
                st.map(map_data, zoom=15)
        
        with tab2:
            st.subheader("Bauantrag erstellen/bearbeiten")
            
            # Status prüfen (in einer echten App würden wir den tatsächlichen Status des Bauantrags aus der Datenbank laden)
            has_existing_application = 'bauantrag_status' in st.session_state and st.session_state.bauantrag_status.get(selected_location) == "eingereicht"
            
            if has_existing_application:
                st.success("Bauantrag wurde eingereicht.")
                
                # Anzeigen des Bauantragsstatus (simulierte Daten)
                if 'bauantrag_daten' in st.session_state and selected_location in st.session_state.bauantrag_daten:
                    antragsdaten = st.session_state.bauantrag_daten[selected_location]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Antragsnummer:** {antragsdaten['antragsnummer']}")
                        st.markdown(f"**Eingereicht am:** {antragsdaten['antragsdatum']}")
                    with col2:
                        st.markdown(f"**Zuständiges Amt:** {antragsdaten['amt']}")
                        st.markdown(f"**Kontaktperson:** {antragsdaten['kontakt']}")
                
                # Entscheidung zum Bauantrag
                st.subheader("Entscheidung der Behörde")
                
                behorden_entscheidung = st.radio(
                    "Wie hat die Behörde entschieden?",
                    options=["Genehmigt", "Abgelehnt"],
                    horizontal=True
                )
                
                if behorden_entscheidung == "Genehmigt":
                    if st.button("Genehmigung bestätigen", type="primary"):
                        success = process_bauantrag_entscheidung(selected_location, True)
                        if success:
                            st.success("Bauantrag genehmigt! Standort wird an den CEO zur finalen Genehmigung weitergeleitet.")
                            st.rerun()
                else:
                    # Bei Ablehnung - Grund erfassen und entscheiden, ob Widerspruch eingelegt wird
                    grund = st.text_area("Begründung der Ablehnung", placeholder="Geben Sie die Begründung der Behörde ein...")
                    
                    widerspruch = st.radio(
                        "Soll Widerspruch eingelegt werden?",
                        options=["Ja, Widerspruch einlegen", "Nein, Prozess beenden"],
                        horizontal=True
                    )
                    
                    if st.button("Ablehnung verarbeiten", type="primary"):
                        if not grund:
                            st.error("Bitte geben Sie die Begründung der Ablehnung ein.")
                        else:
                            widerspruch_einlegen = widerspruch == "Ja, Widerspruch einlegen"
                            success = process_bauantrag_entscheidung(selected_location, False, grund, widerspruch_einlegen)
                            
                            if success:
                                if widerspruch_einlegen:
                                    st.success("Widerspruchsverfahren eingeleitet!")
                                else:
                                    st.success("Prozess wurde beendet aufgrund der Ablehnung des Bauantrags.")
                                st.rerun()
            else:
                st.info("Erstellen Sie einen neuen Bauantrag für diesen Standort.")
                
                # Formular für einen neuen Bauantrag
                with st.form(key="bauantrag_form"):
                    st.write("Bauantragsdaten eingeben")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        antragsnummer = st.text_input(
                            "Antragsnummer",
                            value=f"BA-{datetime.now().year}-{random.randint(1000, 9999)}"
                        )
                        antragsdatum = st.date_input(
                            "Antragsdatum",
                            value=datetime.now()
                        )
                    
                    with col2:
                        amt = st.text_input(
                            "Zuständiges Amt",
                            value=f"Bauamt {location['stadt']}"
                        )
                        kontakt = st.text_input(
                            "Kontaktperson",
                            placeholder="Name des Sachbearbeiters"
                        )
                    
                    anlagen = st.multiselect(
                        "Anlagen zum Bauantrag",
                        options=[
                            "Lageplan", 
                            "Grundriss", 
                            "Ansichtszeichnungen", 
                            "Statik", 
                            "Baubeschreibung",
                            "Eigentümerzustimmung",
                            "Typenprüfung"
                        ],
                        default=["Lageplan", "Grundriss", "Ansichtszeichnungen"]
                    )
                    
                    anmerkungen = st.text_area(
                        "Anmerkungen",
                        placeholder="Zusätzliche Informationen zum Bauantrag"
                    )
                    
                    submit_bauantrag = st.form_submit_button("Bauantrag einreichen")
                    
                    if submit_bauantrag:
                        # In einer echten App würden wir diese Daten in der Datenbank speichern
                        antragsdaten = {
                            'antragsnummer': antragsnummer,
                            'antragsdatum': antragsdatum.strftime('%Y-%m-%d'),
                            'amt': amt,
                            'kontakt': kontakt,
                            'anlagen': anlagen,
                            'anmerkungen': anmerkungen
                        }
                        
                        # Speichern in Session State für die Demo
                        if 'bauantrag_daten' not in st.session_state:
                            st.session_state.bauantrag_daten = {}
                        if 'bauantrag_status' not in st.session_state:
                            st.session_state.bauantrag_status = {}
                            
                        st.session_state.bauantrag_daten[selected_location] = antragsdaten
                        st.session_state.bauantrag_status[selected_location] = "eingereicht"
                        
                        # Speichern in der Datenbank
                        update_bauantrag(selected_location, antragsdaten, "eingereicht")
                        
                        st.success("Bauantrag erfolgreich eingereicht!")
                        st.rerun()
        
        with tab3:
            st.subheader("Workflow-Historie")
            
            # Workflow-Historie des Standorts laden
            history_df = load_workflow_history(selected_location)
            
            if not history_df.empty:
                # Formatierungen für bessere Lesbarkeit
                history_df['Zeitstempel'] = pd.to_datetime(history_df['Zeitstempel']).dt.strftime('%d.%m.%Y, %H:%M Uhr')
                
                # Anzeigen der Historie mit farbiger Markierung
                for idx, row in history_df.iterrows():
                    if row['Aktion'] == 'approved':
                        emoji = "✅"
                        color = "green"
                    elif row['Aktion'] == 'rejected':
                        emoji = "❌"
                        color = "red"
                    elif row['Aktion'] == 'objection':
                        emoji = "⚠️"
                        color = "orange"
                    else:
                        emoji = "ℹ️"
                        color = "blue"
                    
                    st.markdown(
                        f"<div style='padding:10px; margin-bottom:10px; border-left: 3px solid {color};'>"
                        f"<strong>{emoji} {row['Schritt'].title()}</strong> ({row['Zeitstempel']})<br>"
                        f"{row['Nachricht']}<br>"
                        f"<small>Bearbeitet von: {row['Benutzer']}</small>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )
            else:
                st.info("Keine Workflow-Historie für diesen Standort verfügbar.")

# Sidebar mit Workflow-Information
st.sidebar.title("Workflow-Information")
st.sidebar.markdown("""
### Aktueller Schritt: Baurecht

In diesem Schritt werden folgende Aufgaben erledigt:

1. Bauantrag bei der Stadt einreichen
2. Genehmigungsprozess überwachen
3. Bei Genehmigung: Weiterleitung an CEO
4. Bei Ablehnung: Entscheidung über Widerspruch

**Hinweis bei Digitalen Säulen:**
Die Digitale Säule hat den Niederlassungsleiter im Genehmigungsprozess übersprungen und wurde direkt vom Leiter Akquisitionsmanagement an das Baurecht weitergeleitet.
""")

st.sidebar.markdown("""
### Workflow der Digitalen Säule:
1. ✅ Erfassung durch Akquisiteur
2. ✅ Leiter Akquisitionsmanagement
3. ~~Niederlassungsleiter~~ (übersprungen)
4. 🔄 **Baurecht**
5. ➡️ CEO
6. ➡️ Bauteam
7. ➡️ Fertigstellung
""")

# Falls kein Bauantrags-Schema in der Datenbank existiert, erstellen wir es hier
# In einer echten Anwendung würde dies im Init-Skript geschehen
try:
    c.execute('ALTER TABLE locations ADD COLUMN bauantrag_datum TEXT')
except:
    # Spalte existiert bereits
    pass

conn.commit()