import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import uuid
import time

# Streamlit-Seiteneinstellungen
st.set_page_config(layout="wide", page_title="Fertigstellung")

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('werbetraeger.db', check_same_thread=False)
c = conn.cursor()

st.title("Fertigstellung")
st.write("Finale Abnahme, Dokumentation und Übergabe der Digitalen Säule in den Betrieb.")

# Funktion zum Laden aller Standorte in der Fertigstellungsphase
def load_completion_locations():
    c.execute('''
    SELECT id, erfasser, datum, standort, stadt, lat, lng, eigentuemer, 
           umruestung, seiten, vermarktungsform, created_at, ist_date
    FROM locations 
    WHERE status = 'active' AND current_step = 'fertigstellung'
    ORDER BY created_at DESC
    ''')
    
    locations = c.fetchall()
    
    if not locations:
        return pd.DataFrame()
    
    # In DataFrame umwandeln
    df = pd.DataFrame(locations, columns=[
        'id', 'erfasser', 'datum', 'standort', 'stadt', 'lat', 'lng',
        'eigentuemer', 'umruestung', 'seiten', 'vermarktungsform', 'created_at', 'ist_date'
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
           bauantrag_datum, plan_date, ist_date, build_status, contractor, power_connection
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

# Funktion zum Fertigstellen des Standorts
def complete_location(location_id, completion_data):
    now = datetime.now().isoformat()
    history_id = str(uuid.uuid4())
    
    # Status auf "completed" setzen
    c.execute('''
    UPDATE locations
    SET status = ?, current_step = ?, completion_date = ?, 
        final_inspection = ?, network_id = ?, dms_id = ?
    WHERE id = ?
    ''', (
        'completed', 'fertig', now,
        completion_data.get('final_inspection', ''),
        completion_data.get('network_id', ''),
        completion_data.get('dms_id', ''),
        location_id
    ))
    
    # Workflow-History-Eintrag erstellen
    c.execute('''
    INSERT INTO workflow_history VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        history_id, 
        location_id, 
        "fertigstellung", 
        "completed", 
        f"Standort fertiggestellt und in Betrieb genommen. Netzwerk-ID: {completion_data.get('network_id', '')}, DMS-ID: {completion_data.get('dms_id', '')}",
        st.session_state.get('username', 'Fertigstellung'),
        now
    ))
    
    conn.commit()
    return True

# Simulieren eines eingeloggten Benutzers (in einer echten App würde hier ein Login-System stehen)
if 'username' not in st.session_state:
    st.session_state.username = "Frank Fertigsteller"
    st.session_state.role = "Fertigstellung"

# Anzeigen aller Standorte in der Fertigstellungsphase
st.subheader("Standorte in der finalen Fertigstellung")

# Spalten für die Datenbank hinzufügen, falls sie noch nicht existieren
try:
    c.execute("PRAGMA table_info(locations)")
    columns = c.fetchall()
    column_names = [col[1] for col in columns]
    
    # Felder für Abschluss hinzufügen, falls sie noch nicht existieren
    if 'completion_date' not in column_names:
        c.execute('ALTER TABLE locations ADD COLUMN completion_date TEXT')
    if 'final_inspection' not in column_names:
        c.execute('ALTER TABLE locations ADD COLUMN final_inspection TEXT')
    if 'network_id' not in column_names:
        c.execute('ALTER TABLE locations ADD COLUMN network_id TEXT')
    if 'dms_id' not in column_names:
        c.execute('ALTER TABLE locations ADD COLUMN dms_id TEXT')
    
    conn.commit()
except:
    # Bei Fehler weitermachen
    pass

df = load_completion_locations()

if df.empty:
    st.info("Aktuell gibt es keine Standorte in der finalen Fertigstellungsphase.")
else:
    # Liste der Standorte anzeigen
    st.write(f"**{len(df)} Standorte** zur finalen Fertigstellung.")
    
    # Vereinfachte Tabelle für die Übersicht
    display_df = df[['standort', 'stadt', 'vermarktungsform', 'seiten', 'ist_date']].copy()
    display_df.columns = ['Standort', 'Stadt', 'Vermarktungsform', 'Seiten', 'Fertiggestellt am']
    
    # Datum formatieren
    display_df['Fertiggestellt am'] = pd.to_datetime(display_df['Fertiggestellt am']).dt.strftime('%d.%m.%Y')
    
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
        tab1, tab2, tab3, tab4 = st.tabs(["Standortdetails", "Finale Freigabe", "Workflow-Historie", "Dokumentation"])
        
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
                    st.markdown(f"**Aufbau abgeschlossen am:** {location.get('ist_date')}")
                    st.markdown(f"**Aufbau durchgeführt von:** {location.get('contractor')}")
                    st.markdown(f"**Bauauftrags-Status:** {location.get('build_status')}")
                    st.markdown(f"**Stromanschluss-Status:** {location.get('power_connection')}")
                
                # Karte anzeigen
                st.subheader("Standort auf Karte")
                map_data = pd.DataFrame({
                    'lat': [float(location.get('lat'))],
                    'lon': [float(location.get('lng'))]
                })
                st.map(map_data, zoom=15)
        
        with tab2:
            st.subheader("Finale Freigabe")
            
            # Formular für finale Freigabe
            with st.form("final_approval_form"):
                st.markdown("### Freigabe-Checkliste")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Checkliste für die finale Abnahme
                    check1 = st.checkbox("✓ Bauliche Abnahme erfolgt", value=True)
                    check2 = st.checkbox("✓ Elektrische Abnahme erfolgt", value=True)
                    check3 = st.checkbox("✓ Netzwerkverbindung getestet", value=True)
                    check4 = st.checkbox("✓ Content-Management-System eingerichtet", value=True)
                    check5 = st.checkbox("✓ Test-Content erfolgreich angezeigt", value=True)
                    check6 = st.checkbox("✓ Dokumentation vollständig", value=False)
                
                with col2:
                    # Netzwerk- und System-IDs
                    st.markdown("### System-Integration")
                    network_id = st.text_input("Netzwerk-ID", placeholder="z.B. DS-1234")
                    dms_id = st.text_input("Content-Management-System ID", placeholder="z.B. CMS-5678")
                    
                    # Datum der finalen Abnahme
                    final_inspection = st.date_input(
                        "Datum der finalen Abnahme",
                        value=datetime.now()
                    )
                
                # Notizen zur finalen Freigabe
                notes = st.text_area(
                    "Anmerkungen zur Fertigstellung",
                    placeholder="Besonderheiten, Hinweise für Betrieb und Wartung..."
                )
                
                # Daten für die Fertigstellung
                completion_data = {
                    'final_inspection': final_inspection.isoformat(),
                    'network_id': network_id,
                    'dms_id': dms_id,
                    'notes': notes
                }
                
                # Prüfen, ob alle Checklisten-Punkte erfüllt sind
                all_checks_passed = check1 and check2 and check3 and check4 and check5 and check6
                
                # HIER BEGINNT DIE ÄNDERUNG - Button immer aktiviert lassen
                # Warnmeldungen anzeigen, wenn nicht alle Bedingungen erfüllt sind
                if not all_checks_passed:
                    st.warning("⚠️ Bitte alle Checklisten-Punkte abhaken für die finale Freigabe.")
                
                if not network_id and not dms_id:
                    st.warning("⚠️ Bitte mindestens eine ID (Netzwerk-ID oder CMS-ID) eingeben.")
                
                # Button IMMER aktiv lassen
                submitted = st.form_submit_button(
                    "Finale Freigabe erteilen und Standort in Betrieb nehmen",
                    type="primary"
                )
                
                # Validierung NACH dem Klicken durchführen
                if submitted:
                    if not all_checks_passed:
                        st.error("❌ Bitte alle Checklisten-Punkte abhaken!")
                    elif not (network_id or dms_id):
                        st.error("❌ Bitte mindestens eine ID (Netzwerk-ID oder CMS-ID) eingeben!")
                    else:
                        # Netzwerk-ID und DMS-ID formatieren
                        if network_id and not network_id.startswith("DS-"):
                            network_id = f"DS-{network_id}"
                            
                        if dms_id and not dms_id.startswith("CMS-"):
                            dms_id = f"CMS-{dms_id}"
                        
                        completion_data['network_id'] = network_id
                        completion_data['dms_id'] = dms_id
                        
                        # Standort als fertiggestellt markieren
                        success = complete_location(selected_location, completion_data)
                        
                        if success:
                            st.balloons()  # Visuelle Belohnung für die Fertigstellung
                            st.success("🎉 Standort wurde erfolgreich fertiggestellt und in Betrieb genommen!")
                            
                            # Fortschrittsbalken zeigen zur visuellen Bestätigung
                            progress_bar = st.progress(0)
                            for i in range(101):
                                time.sleep(0.01)
                                progress_bar.progress(i)
                            
                            st.info("Dieser Standort wird nun im Dashboard als 'Fertig' angezeigt.")
                            st.info("Der gesamte Workflow für diesen Standort ist abgeschlossen. Der Standort ist betriebsbereit.")
                            
                            # Seite nach kurzer Verzögerung neu laden
                            time.sleep(2)
                            st.rerun()
        
        with tab3:
            st.subheader("Workflow-Historie")
            
            # Workflow-Historie des Standorts laden
            history_df = load_workflow_history(selected_location)
            
            if not history_df.empty:
                # Prozessdauer berechnen
                start_date = pd.to_datetime(history_df['Zeitstempel'].iloc[0])
                end_date = pd.to_datetime(history_df['Zeitstempel'].iloc[-1])
                duration = (end_date - start_date).days
                
                st.info(f"Gesamtdauer des Prozesses: **{duration} Tage** (von {start_date.strftime('%d.%m.%Y')} bis {end_date.strftime('%d.%m.%Y')})")
                
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
            st.subheader("Abschlussdokumentation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Technische Dokumentation")
                
                # Generierung von System-Informationen für Digitale Säule
                if location.get('vermarktungsform') == "Digitale Säule":
                    st.markdown("#### Displays")
                    st.markdown("""
                    * **Typ:** Full-HD LED Display
                    * **Auflösung:** 1920x1080 Pixel
                    * **Helligkeit:** 2500 cd/m²
                    * **Hersteller:** Digital Vision GmbH
                    * **Modell:** DV-OUT-2023
                    """)
                    
                    st.markdown("#### Netzwerktechnik")
                    st.markdown("""
                    * **Router:** Cisco 4G/LTE Industrial Router
                    * **Verbindung:** LTE Advanced
                    * **Backup:** Automatischer Failover auf sekundäre SIM
                    * **IP-Adresse:** Dynamisch (DHCP)
                    * **VPN:** Site-to-Site zu Ströer NOC
                    """)
                    
                    st.markdown("#### Elektronik")
                    st.markdown("""
                    * **Stromversorgung:** 400V, 16A
                    * **Sicherungsautomat:** 3x16A, FI-Schutzschalter 30mA
                    * **Notabschaltung:** Vorhanden, Außenzugang
                    * **Klimatisierung:** Temperaturgeregelte Lüftung
                    """)
                    
                    # Download-Schaltfläche für die technische Dokumentation (Dummy)
                    st.download_button(
                        label="Technische Dokumentation herunterladen",
                        data="Technische Dokumentation der Digitalen Säule",
                        file_name=f"Technische_Dokumentation_{location.get('standort', 'Standort')}.pdf",
                        mime="application/pdf",
                    )
            
            with col2:
                st.markdown("### Betriebsanleitung")
                
                st.markdown("""
                #### Nutzungshinweise
                * Standortzugriff: Schlüssel für Wartungszugang im NOC hinterlegt
                * Notfallnummer bei technischen Problemen: +49 123 456789
                * Wartungsintervall: Vierteljährlich
                
                #### Zuständigkeiten
                * Technischer Support: Ströer Service-Team
                * Content-Management: Digital Media Team
                * Vor-Ort-Wartung: Regionaler Service-Partner
                
                #### Systempflege
                * Software-Updates erfolgen automatisch über das Netzwerk
                * Hardware-Checks gemäß Wartungsplan
                * Display-Kalibrierung jährlich
                """)
                
                # Upload-Bereich für zusätzliche Dokumente
                st.markdown("### Zusätzliche Dokumente")
                uploaded_file = st.file_uploader("Dokument hochladen", type=['pdf', 'doc', 'docx'])
                
                if uploaded_file:
                    st.success(f"Datei {uploaded_file.name} erfolgreich hochgeladen")
                
                # QR-Code für schnellen Zugriff auf Standortinformationen
                st.markdown("### Wartungs-QR-Code")
                st.markdown("Scan für schnellen Zugriff auf Standortinformationen und Wartungsanleitung:")
                
                # Hier würden wir in einer echten App einen QR-Code mit Link zu diesem Standort generieren
                st.code(f"https://stroeer.werbetraeger.db/standort/{selected_location}")

# Sidebar mit Workflow-Information
st.sidebar.title("Workflow-Information")
st.sidebar.markdown("""
### Aktueller Schritt: Fertigstellung

In diesem letzten Schritt wird die Digitale Säule final abgenommen und in Betrieb genommen:

1. Finale Qualitätskontrolle und Abnahme
2. Integration ins Netzwerk und Content-Management-System
3. Erstellung der Abschlussdokumentation
4. Übergabe vom Projekt in den regulären Betrieb

**Besonderheiten der Digitalen Säule:**
- Einrichtung der Netzwerkverbindung und Remote-Management
- Kalibrierung der Displays für optimale Darstellungsqualität
- Einrichtung des Content-Management-Systems
- Digitale Dokumentation für einfache Wartung und Service
""")

st.sidebar.markdown("""
### Workflow der Digitalen Säule:
1. ✅ Erfassung durch Akquisiteur
2. ✅ Leiter Akquisitionsmanagement
3. ~~Niederlassungsleiter~~ (übersprungen)
4. ✅ Baurecht
5. ✅ CEO
6. ✅ Bauteam
7. 🔄 **Fertigstellung**
""")

# Verbindung schließen am Ende
conn.close()