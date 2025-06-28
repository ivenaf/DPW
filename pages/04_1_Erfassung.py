import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import uuid
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# Streamlit-Seiteneinstellungen
st.set_page_config(layout="wide", page_title="Standort erfassen")

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('werbetraeger.db', check_same_thread=False)
c = conn.cursor()

# Initialisiere session_state für seiten-Variable
if 'seiten' not in st.session_state:
    st.session_state.seiten = "einseitig"

st.title("Standort erfassen")

# Funktion für die Geocodierung
@st.cache_data
def get_coordinates(address):
    """
    Adresse in Geokoordinaten umwandeln unter Verwendung von Nominatim (OpenStreetMap).
    Returns: (latitude, longitude) oder None bei Fehlern
    """
    try:
        geolocator = Nominatim(user_agent="stroer_digital_saeule")
        location = geolocator.geocode(address, timeout=10)
        if location:
            return (location.latitude, location.longitude, location.raw)
        return None
    except (GeocoderTimedOut, GeocoderUnavailable):
        return None

# Geokoordinaten-Berechner in einem Expander
with st.expander("🔍 Geokoordinaten-Berechner", expanded=False):
    geo_col1, geo_col2 = st.columns([2, 1])
    
    with geo_col1:
        st.markdown("### Adresse eingeben")
        geo_street = st.text_input("Straße und Hausnummer", placeholder="z.B. Holzmarktstraße 70", key="geo_street")
        geo_city_col, geo_postal_col = st.columns(2)
        with geo_city_col:
            geo_city = st.text_input("Stadt", placeholder="z.B. Berlin", key="geo_city")
        with geo_postal_col:
            geo_postal = st.text_input("PLZ", placeholder="z.B. 10179", key="geo_postal")
        
        geo_address = f"{geo_street}, {geo_postal} {geo_city}, Deutschland" if geo_street and geo_city else ""
        
        if st.button("Koordinaten berechnen", disabled=not (geo_street and geo_city)):
            if geo_address:
                with st.spinner("Berechne Koordinaten..."):
                    result = get_coordinates(geo_address)
                    if result:
                        lat, lon, raw_data = result
                        st.session_state.calculated_lat = lat
                        st.session_state.calculated_lon = lon
                        st.session_state.calculated_address = raw_data.get('display_name', geo_address)
                        st.success(f"Koordinaten gefunden: {lat:.6f}, {lon:.6f}")
                    else:
                        st.error("Keine Koordinaten für diese Adresse gefunden. Bitte Eingabe prüfen.")
    
    with geo_col2:
        # Karte mit Marker anzeigen
        st.markdown("### Kartenansicht")
        if 'calculated_lat' in st.session_state and 'calculated_lon' in st.session_state:
            map_data = pd.DataFrame({
                'lat': [st.session_state.calculated_lat],
                'lon': [st.session_state.calculated_lon]
            })
            st.map(map_data, zoom=15)
            st.markdown(f"**Gefundene Adresse:**  \n{st.session_state.calculated_address}")
        else:
            st.info("Geben Sie eine Adresse ein und berechnen Sie die Koordinaten, um sie hier anzuzeigen")
    
    st.markdown("""
    #### So funktioniert's:
    1. Geben Sie Straße, Stadt und PLZ ein
    2. Klicken Sie auf "Koordinaten berechnen"
    3. Die gefundenen Koordinaten werden automatisch ins Formular übernommen
    """)

# Seiten-Auswahl außerhalb des Formulars (da wir Buttons benutzen)
st.markdown("### Anzahl der Seiten")

# Zeige die Vermarktungsform-Auswahl außerhalb des Formulars
vermarktungsform = st.selectbox(
    "Vermarktungsform",
    ["Digitale Säule", "Roadside-Screen", "City-Screen", "MegaVision", "SuperMotion"],
    index=0  # Standardwert ist "Digitale Säule"
)

# Callback-Funktion für Vermarktungsform-Änderungen
def update_seiten_options():
    if vermarktungsform != "Digitale Säule" and st.session_state.seiten == "dreiseitig":
        st.session_state.seiten = "einseitig"

# Führe die Callback-Funktion aus, wenn sich die Vermarktungsform ändert
update_seiten_options()

# Vollständig neuer Ansatz mit einer versteckten Spalte
col1, col2, col3 = st.columns(3)

with col1:
    ein = st.button("einseitig", key="btn_einseitig", 
                 use_container_width=True,
                 type="primary" if st.session_state.seiten == "einseitig" else "secondary")
    if ein:
        st.session_state.seiten = "einseitig"

with col2:
    zwei = st.button("doppelseitig", key="btn_doppelseitig", 
                  use_container_width=True,
                  type="primary" if st.session_state.seiten == "doppelseitig" else "secondary")
    if zwei:
        st.session_state.seiten = "doppelseitig"

with col3:
    # Nur anzeigen, wenn Digitale Säule gewählt ist
    if vermarktungsform == "Digitale Säule":
        drei = st.button("dreiseitig", key="btn_dreiseitig", 
                      use_container_width=True,
                      type="primary" if st.session_state.seiten == "dreiseitig" else "secondary")
        if drei:
            st.session_state.seiten = "dreiseitig"
    else:
        # Leere Spalte, wenn nicht Digitale Säule
        st.empty()

# Die aktuelle Auswahl in einer versteckten Variable speichern
seiten = st.session_state.seiten

# Aktualisieren des Session-States nach Formularvalidierung 
if vermarktungsform != "Digitale Säule" and seiten == "dreiseitig":
    seiten = "einseitig"
    st.session_state.seiten = "einseitig"

# Hauptformular für die Standorterfassung
with st.form(key='location_form'):
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Name des Erfassers", max_chars=50)
        datum = st.date_input("Datum der Akquisition")
        standort = st.text_input("Standortbezeichnung (Straßenname)", 
                               value=geo_street if 'calculated_address' in st.session_state else "")
        stadt = st.text_input("Ort (Stadt)", 
                            value=geo_city if 'calculated_address' in st.session_state else "")
        
        # Verwende die berechneten Koordinaten, wenn vorhanden
        default_lat = st.session_state.calculated_lat if 'calculated_lat' in st.session_state else 50.0
        default_lon = st.session_state.calculated_lon if 'calculated_lon' in st.session_state else 10.0
        
        lat = st.number_input("Breitengrad", -90.0, 90.0, default_lat, format="%.6f")
        lng = st.number_input("Längengrad", -180.0, 180.0, default_lon, format="%.6f")
    
    with col2:
        leistungswert = st.text_input("Leistungswert der Werbeträgerseite")
        eigentuemer = st.selectbox("Eigentümer des Standortes", ["Privater Eigentümer", "Stadt"])
        umruestung = st.radio("Neustandort oder Umrüstung", ["Neustandort", "Umrüstung"])
        
        alte_nummer = ""
        if umruestung == "Umrüstung":
            alte_nummer = st.text_input("Alte Werbeträgernummer")
            
        # Anzeige der ausgewählten Vermarktungsform (ohne Auswahl)
        st.write(f"**Ausgewählte Vermarktungsform:** {vermarktungsform}")
        
        # Anzeige der ausgewählten Seitenanzahl (ohne Auswahl)
        st.write(f"**Ausgewählte Seitenanzahl:** {seiten}")
    
    # Bilder hochladen - außerhalb der Spalten, aber innerhalb des Formulars
    st.write("Bilder in unterschiedlichen Entfernungen je Werbeträgerseite")
    uploaded_files = st.file_uploader("Bilder hochladen", accept_multiple_files=True, 
                                      type=['jpg', 'png', 'jpeg'])

    # Submit-Button richtig platzieren (innerhalb des form-Blocks)
    submit_button = st.form_submit_button("Standort speichern")
    
    # Wichtig: Überprüfe, ob der Button gedrückt wurde
    if submit_button:
        if not name or not standort or not stadt:
            st.error("Bitte füllen Sie alle Pflichtfelder aus.")
        elif umruestung == "Umrüstung" and not alte_nummer:
            st.error("Bitte geben Sie die alte Werbeträgernummer an.")
        elif not uploaded_files:
            st.error("Bitte laden Sie mindestens ein Bild hoch.")
        else:
            location_id = str(uuid.uuid4())
            # Immer zuerst zum Leiter Akquisition!
            next_step = "leiter_akquisition"
            c.execute('''
            INSERT INTO locations (id, erfasser, datum, standort, stadt, lat, lng, 
                                  leistungswert, eigentuemer, umruestung, alte_nummer, 
                                  seiten, vermarktungsform, status, current_step, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                location_id, name, datum.isoformat(), standort, stadt, lat, lng,
                leistungswert, eigentuemer, umruestung == "Umrüstung", alte_nummer,
                seiten, vermarktungsform, "active", next_step, 
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
            st.success(f"Standort erfolgreich gespeichert! Die Standort-ID lautet: {location_id}. Der nächste Workflow-Schritt wurde eingeleitet.")
            
            # Session-State zurücksetzen
            if 'calculated_lat' in st.session_state:
                del st.session_state.calculated_lat
            if 'calculated_lon' in st.session_state:
                del st.session_state.calculated_lon
            if 'calculated_address' in st.session_state:
                del st.session_state.calculated_address

# Hinweise zur Erfassung
st.markdown("""
### Hinweise zur Erfassung:

- Alle mit * markierten Felder sind Pflichtfelder
- Nutzen Sie den Geokoordinaten-Berechner für eine präzise Standortbestimmung
- Bei Umrüstungen muss die alte Werbeträgernummer angegeben werden
- Bei der Digitalen Säule kann auch eine dreiseitige Variante ausgewählt werden
- Fügen Sie für jede Seite des Werbeträgers mindestens ein Bild hinzu
""")