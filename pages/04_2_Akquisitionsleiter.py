import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import uuid

# Streamlit-Seiteneinstellungen
st.set_page_config(layout="wide", page_title="Standort genehmigen")

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('werbetraeger.db', check_same_thread=False)
c = conn.cursor()

st.title("Standorte genehmigen")
st.write("Als Leiter Akquisitionsmanagement genehmigen oder lehnen Sie hier neue Standorte ab.")

# Funktion zum Laden aller Standorte, die auf Genehmigung durch den Leiter Akquisitionsmanagement warten
def load_pending_locations():
    c.execute('''
    SELECT id, erfasser, datum, standort, stadt, lat, lng, leistungswert, eigentuemer, 
           umruestung, alte_nummer, seiten, vermarktungsform, created_at
    FROM locations 
    WHERE status = 'active' AND current_step= 'leiter_akquisition'
    ORDER BY created_at DESC
    ''')
    
    locations = c.fetchall()
    
    if not locations:
        return pd.DataFrame()
    
    # In DataFrame umwandeln
    df = pd.DataFrame(locations, columns=[
        'id', 'erfasser', 'datum', 'standort', 'stadt', 'lat', 'lng', 'leistungswert',
        'eigentuemer', 'umruestung', 'alte_nummer', 'seiten', 'vermarktungsform', 'created_at'
    ])
    
    # Formatierungen anwenden
    df['umruestung'] = df['umruestung'].apply(lambda x: 'Umrüstung' if x else 'Neustandort')
    df['eigentuemer'] = df['eigentuemer'].apply(lambda x: 'Stadt' if x == 'Stadt' else 'Privat')
    
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

# Funktion zum Genehmigen oder Ablehnen eines Standorts
def process_location(location_id, approve, reason):
    now = datetime.now().isoformat()
    history_id = str(uuid.uuid4())
    location = load_location_details(location_id)
    
    if approve:
        # Genehmigen: Bei der Digitalen Säule überspringen wir den Niederlassungsleiter
        if location['vermarktungsform'] == "Digitale Säule":
            next_step = "baurecht"
        else:
            next_step = "niederlassungsleiter"
        status = "active"
        action = "approved"
        message = "Standort genehmigt"
    else:
        # Ablehnung
        next_step = "abgelehnt"
        status = "abgelehnt"
        action = "rejected"
        message = f"Standort abgelehnt: {reason}"
    
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
        "leiter_akquisition", 
        action, 
        message, 
        st.session_state.get('username', 'Leiter Akquisition'),
        now
    ))
    
    conn.commit()
    return True

# Simulieren eines eingeloggten Benutzers (in einer echten App würde hier ein Login-System stehen)
if 'username' not in st.session_state:
    st.session_state.username = "Max Mustermann"
    st.session_state.role = "Leiter Akquisition"

# Anzeigen aller wartenden Standorte
st.subheader("Wartende Standorte")

df = load_pending_locations()

if df.empty:
    st.info("Aktuell gibt es keine Standorte, die auf Genehmigung warten.")
else:
    # Liste der Standorte anzeigen
    st.write(f"**{len(df)} Standorte** warten auf Ihre Genehmigung.")
    
    # Vereinfachte Tabelle für die Übersicht
    display_df = df[['id', 'erfasser', 'datum', 'standort', 'stadt', 'vermarktungsform']].copy()
    display_df.columns = ['ID','Erfasser', 'Datum', 'Standort', 'Stadt', 'Vermarktungsform']
    
    st.dataframe(display_df, hide_index=True)
    
    # Auswahl für detaillierte Ansicht
    selected_location = st.selectbox(
        "Standort zur Prüfung auswählen:",
        options=df['id'].tolist(),
        format_func=lambda x: f"{df[df['id'] == x]['standort'].iloc[0]}, {df[df['id'] == x]['stadt'].iloc[0]} ({df[df['id'] == x]['vermarktungsform'].iloc[0]})"
    )
    
    if selected_location:
        st.markdown("---")
        st.subheader("Standortdetails prüfen")
        
        # Laden der detaillierten Standortinformationen
        location = load_location_details(selected_location)
        
        if location:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Standort:** {location['standort']}")
                st.markdown(f"**Stadt:** {location['stadt']}")
                st.markdown(f"**Erfasst von:** {location['erfasser']}")
                st.markdown(f"**Datum der Akquisition:** {location['datum']}")
                st.markdown(f"**Vermarktungsform:** {location['vermarktungsform']}")
                if location['vermarktungsform'] == "Digitale Säule":
                    st.markdown("**Hinweis:** Bei der Digitalen Säule wird der Niederlassungsleiter im Workflow übersprungen.")
                
            with col2:
                st.markdown(f"**Koordinaten:** {location['lat']}, {location['lng']}")
                st.markdown(f"**Art:** {location['umruestung']}")
                if location['umruestung'] == 'Umrüstung':
                    st.markdown(f"**Alte Werbeträgernummer:** {location['alte_nummer']}")
                st.markdown(f"**Seiten:** {location['seiten']}")
                st.markdown(f"**Eigentümer:** {location['eigentuemer']}")
                st.markdown(f"**Leistungswert:** {location['leistungswert']}")
            
            # Karte anzeigen
            st.subheader("Standort auf Karte")
            map_data = pd.DataFrame({
                'lat': [float(location['lat'])],
                'lon': [float(location['lng'])]
            })
            st.map(map_data, zoom=15)
            
            # Bilder anzeigen (müsste in einer echten Anwendung aus der Datenbank geladen werden)
            st.subheader("Bilder des Standorts")
            st.info("Bildervorschau hier (in der Demo-Version nicht implementiert)")
            
            # Genehmigungsprozess
            st.markdown("---")
            st.subheader("Entscheidung")
            
            col1, col2 = st.columns(2)
            
            with col1:
                approve = st.radio("Standort genehmigen?", ["Ja, genehmigen", "Nein, ablehnen"], index=0)
            
            with col2:
                reason = ""
                if approve == "Nein, ablehnen":
                    reason_options = [
                        "Standort entspricht nicht den Qualitätsanforderungen",
                        "Standort bereits belegt",
                        "Standort nicht wirtschaftlich",
                        "Fehlende oder unvollständige Angaben",
                        "Anderer Grund"
                    ]
                    
                    reason_selection = st.selectbox("Grund für Ablehnung:", reason_options)
                    
                    if reason_selection == "Anderer Grund":
                        reason = st.text_input("Bitte spezifizieren:")
                    else:
                        reason = reason_selection
            
            # Bestätigungsbutton
            if st.button("Entscheidung bestätigen", type="primary"):
                is_approve = approve == "Ja, genehmigen"
                
                if not is_approve and not reason:
                    st.error("Bitte geben Sie einen Grund für die Ablehnung an.")
                else:
                    success = process_location(selected_location, is_approve, reason)
                    
                    if success:
                        if is_approve:
                            if location['vermarktungsform'] == "Digitale Säule":
                                st.success("Standort wurde genehmigt und wird direkt an das Baurecht weitergeleitet.")
                            else:
                                st.success("Standort wurde genehmigt und wird an den Niederlassungsleiter weitergeleitet.")
                        else:
                            st.success("Standort wurde abgelehnt. Der Erfasser wird informiert.")
                        
                        # Aktualisieren der Standortliste
                        st.rerun()

# Sidebar mit Workflow-Information
st.sidebar.title("Workflow-Information")
st.sidebar.markdown("""
### Aktueller Schritt: Genehmigung durch Leiter Akquisitionsmanagement

In diesem Schritt entscheiden Sie als Leiter Akquisitionsmanagement über die Freigabe des erfassten Standorts.

**Bei der Digitalen Säule:**
- Nach Ihrer Genehmigung geht der Prozess **direkt zum Baurecht**
- Der Niederlassungsleiter wird übersprungen

**Bei anderen Vermarktungsformen:**
- Nach Ihrer Genehmigung geht der Prozess zum Niederlassungsleiter
""")

st.sidebar.markdown("""
### Workflow der Digitalen Säule:
1. ✅ Erfassung durch Akquisiteur
2. 🔄 **Leiter Akquisitionsmanagement**
3. ~~Niederlassungsleiter~~ (übersprungen)
4. ➡️ Baurecht
5. ➡️ CEO
6. ➡️ Bauteam
7. ➡️ Fertigstellung
""")