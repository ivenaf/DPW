import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import uuid
import numpy as np

# Streamlit-Seiteneinstellungen
st.set_page_config(layout="wide", page_title="CEO Genehmigung")

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('werbetraeger.db', check_same_thread=False)
c = conn.cursor()

st.title("CEO-Genehmigung")
st.write("Finale wirtschaftliche Bewertung und Genehmigung der Standorte für die Digitalen Säulen.")

# Funktion zum Laden aller Standorte, die auf CEO-Entscheidung warten
def load_ceo_locations():
    c.execute('''
    SELECT id, erfasser, datum, standort, stadt, lat, lng, eigentuemer, 
           umruestung, seiten, vermarktungsform, created_at
    FROM locations 
    WHERE status = 'active' AND current_step = 'ceo'
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

# Funktion zur Berechnung von wirtschaftlichen Kennzahlen
def calculate_financial_metrics(location):
    # In einer echten Anwendung würden diese Daten aus einer Datenbank kommen
    # Hier simulieren wir Beispieldaten basierend auf dem Standort
    
    # Zufällige, aber konsistente Daten für einen gegebenen Standort generieren
    import hashlib
    
    # Hash aus ID generieren für konsistente "Zufallszahlen"
    # Modifizieren wir den Seed-Wert, damit er innerhalb des gültigen Bereichs liegt
    hash_obj = hashlib.md5(location['id'].encode())
    # Nur die ersten 8 Zeichen des Hex-Digest nehmen, um einen kleineren Wert zu erhalten
    hash_value = int(hash_obj.hexdigest()[:8], 16) 
    np.random.seed(hash_value % (2**32 - 1))  # Begrenzung auf den gültigen Bereich
    
    # Wirtschaftliche Kennzahlen berechnen (simuliert)
    investment = np.random.randint(45000, 75000)  # Investitionen für Digitale Säule
    
    # Mehr Seiten = mehr Einnahmen
    sides = 1
    if location['seiten'] == 'doppelseitig':
        sides = 2
    elif location['seiten'] == 'dreiseitig':
        sides = 3
        
    # Jahreseinnahmen basierend auf Standort und Seiten
    revenue_factor = 1.0
    if location['eigentuemer'] == 'Stadt':
        revenue_factor = 1.2  # Städtische Standorte haben bessere Performance
    
    leistungswert = float(location.get('leistungswert', 0) or 0)
    if leistungswert > 0:
        revenue_factor *= (1 + leistungswert/100)
    
    annual_revenue = np.random.randint(15000, 25000) * sides * revenue_factor
    
    # Betriebskosten
    operating_costs = annual_revenue * np.random.uniform(0.15, 0.25)
    
    # Gewinn
    annual_profit = annual_revenue - operating_costs
    
    # ROI berechnen
    roi = (annual_profit / investment) * 100
    
    # Amortisationszeit in Jahren
    payback_period = investment / annual_profit
    
    # NPV über 10 Jahre mit 8% Diskontierungsrate
    discount_rate = 0.08
    cash_flows = [-investment]
    for year in range(1, 11):
        # Leichte Steigerung der jährlichen Einnahmen
        year_profit = annual_profit * (1 + 0.02) ** (year - 1)
        cash_flows.append(year_profit)
    
    npv = sum(cf / (1 + discount_rate) ** i for i, cf in enumerate(cash_flows))
    
    # Strategischer Wert (1-10)
    strategic_value = np.random.randint(6, 11)
    
    return {
        'investment': round(investment),
        'annual_revenue': round(annual_revenue),
        'operating_costs': round(operating_costs),
        'annual_profit': round(annual_profit),
        'roi': round(roi, 2),
        'payback_period': round(payback_period, 2),
        'npv': round(npv),
        'strategic_value': strategic_value
    }

# Funktion zum Verarbeiten der CEO-Entscheidung
def process_ceo_decision(location_id, approve, reason, financial_metrics):
    now = datetime.now().isoformat()
    history_id = str(uuid.uuid4())
    
    if approve:
        # Genehmigen: Weiter zum Bauteam
        next_step = "bauteam"
        status = "active"
        action = "approved"
        message = f"Standort vom CEO genehmigt. Wirtschaftliche Kennzahlen: ROI {financial_metrics['roi']}%, Amortisation {financial_metrics['payback_period']} Jahre."
    else:
        # Ablehnen: Prozess beenden
        next_step = "abgelehnt"
        status = "rejected"
        action = "rejected"
        message = f"Standort vom CEO abgelehnt. Grund: {reason}"
    
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
        "ceo", 
        action, 
        message, 
        st.session_state.get('username', 'CEO'),
        now
    ))
    
    conn.commit()
    return True

# Simulieren eines eingeloggten Benutzers (in einer echten App würde hier ein Login-System stehen)
if 'username' not in st.session_state:
    st.session_state.username = "Max Mustermann"
    st.session_state.role = "CEO"

# Anzeigen aller Standorte im CEO-Genehmigungsschritt
st.subheader("Standorte zur Genehmigung")

df = load_ceo_locations()

if df.empty:
    st.info("Aktuell gibt es keine Standorte zur CEO-Genehmigung.")
else:
    # Liste der Standorte anzeigen
    st.write(f"**{len(df)} Standorte** warten auf Ihre Genehmigung.")
    
    # Vereinfachte Tabelle für die Übersicht
    display_df = df[['standort', 'stadt', 'eigentuemer', 'vermarktungsform', 'created_at']].copy()
    display_df.columns = ['Standort', 'Stadt', 'Eigentümer', 'Vermarktungsform', 'Erfasst am']
    
    # Datum formatieren
    display_df['Erfasst am'] = pd.to_datetime(display_df['Erfasst am']).dt.strftime('%d.%m.%Y')
    
    st.dataframe(display_df, hide_index=True)
    
    # Auswahl für detaillierte Ansicht
    selected_location = st.selectbox(
        "Standort zur Prüfung auswählen:",
        options=df['id'].tolist(),
        format_func=lambda x: f"{df[df['id'] == x]['standort'].iloc[0]}, {df[df['id'] == x]['stadt'].iloc[0]} ({df[df['id'] == x]['vermarktungsform'].iloc[0]})"
    )
    
    if selected_location:
        st.markdown("---")
        
        # Tabs für verschiedene Ansichten
        tab1, tab2, tab3, tab4 = st.tabs(["Standortdetails", "Wirtschaftlichkeit", "Workflow-Historie", "Entscheidung"])
        
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
                    st.markdown(f"**Erfasst von:** {location.get('erfasser')}")
                    st.markdown(f"**Datum der Akquisition:** {location.get('datum')}")
                    st.markdown(f"**Koordinaten:** {location.get('lat')}, {location.get('lng')}")
                    st.markdown(f"**Eigentümer:** {location.get('eigentuemer')}")
                    st.markdown(f"**Leistungswert:** {location.get('leistungswert')}")
                    if location.get('bauantrag_datum'):
                        st.markdown(f"**Bauantrag genehmigt am:** {location.get('bauantrag_datum')}")
                
                # Karte anzeigen
                st.subheader("Standort auf Karte")
                map_data = pd.DataFrame({
                    'lat': [float(location.get('lat'))],
                    'lon': [float(location.get('lng'))]
                })
                st.map(map_data, zoom=15)
        
        with tab2:
            st.subheader("Wirtschaftliche Kennzahlen")
            
            # Wirtschaftliche Kennzahlen berechnen
            if location:
                financial = calculate_financial_metrics(location)
                
                # Investition und Erträge
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Investition & Ertrag")
                    st.metric("Investitionskosten", f"{financial['investment']:,} €")
                    st.metric("Jährliche Einnahmen", f"{financial['annual_revenue']:,} €")
                    st.metric("Jährliche Betriebskosten", f"{financial['operating_costs']:,} €")
                    st.metric("Jährlicher Gewinn", f"{financial['annual_profit']:,} €")
                
                with col2:
                    st.markdown("##### Rentabilität")
                    
                    # ROI-Anzeige - korrigierte Version für die delta_color
                    if financial['roi'] > 25:
                        roi_delta = f"+{financial['roi']-25}% über Ziel"
                        delta_color = "normal"  # grün (positiv)
                    elif financial['roi'] < 15:
                        roi_delta = f"{financial['roi']-15}% unter Ziel"
                        delta_color = "inverse"  # rot (negativ)
                    else:
                        roi_delta = None
                        delta_color = "off"
                        
                    st.metric("Return on Investment (ROI)", f"{financial['roi']} %", delta=roi_delta, delta_color=delta_color)
                    
                    # Amortisationszeit - korrigierte Version
                    if financial['payback_period'] < 3:
                        payback_delta = f"{3-financial['payback_period']:.1f} Jahre schneller"
                        payback_color = "normal"  # grün (positiv)
                    elif financial['payback_period'] > 5:
                        payback_delta = f"{financial['payback_period']-5:.1f} Jahre langsamer"
                        payback_color = "inverse"  # rot (negativ)
                    else:
                        payback_delta = None
                        payback_color = "off"
                        
                    st.metric("Amortisationszeit", f"{financial['payback_period']} Jahre", delta=payback_delta, delta_color=payback_color)
                    st.metric("Kapitalwert (NPV)", f"{financial['npv']:,} €")
                    
                    # Strategischer Wert als Fortschrittsbalken
                    st.markdown(f"**Strategischer Wert:** {financial['strategic_value']}/10")
                    st.progress(financial['strategic_value']/10)
                
                # Cashflow-Modell für 5 Jahre
                st.subheader("5-Jahres Cashflow-Projektion")
                
                years = list(range(6))  # Jahre 0-5
                cashflows = [-financial['investment']]  # Jahr 0 ist die Investition
                
                for year in range(1, 6):
                    # Leichte Steigerung der jährlichen Einnahmen
                    year_profit = financial['annual_profit'] * (1 + 0.02) ** (year - 1)
                    cashflows.append(round(year_profit))
                
                # Kumulierter Cashflow
                cumulative = [cashflows[0]]
                for i in range(1, len(cashflows)):
                    cumulative.append(cumulative[i-1] + cashflows[i])
                
                # Dataframe für das Chart erstellen
                cashflow_df = pd.DataFrame({
                    'Jahr': years,
                    'Jährlicher Cashflow': cashflows,
                    'Kumulierter Cashflow': cumulative
                })
                
                # Chart anzeigen
                st.bar_chart(cashflow_df.set_index('Jahr')[['Jährlicher Cashflow', 'Kumulierter Cashflow']])
                
                # Empfehlung basierend auf den Kennzahlen
                st.subheader("Automatische Bewertung")
                
                score = 0
                max_score = 5
                criteria = []
                
                # ROI-Kriterium
                if financial['roi'] > 25:
                    score += 1
                    criteria.append("✅ ROI > 25%")
                elif financial['roi'] > 15:
                    score += 0.5
                    criteria.append("⚠️ ROI zwischen 15% und 25%")
                else:
                    criteria.append("❌ ROI < 15%")
                
                # Amortisationszeit-Kriterium
                if financial['payback_period'] < 3:
                    score += 1
                    criteria.append("✅ Amortisation < 3 Jahre")
                elif financial['payback_period'] < 5:
                    score += 0.5
                    criteria.append("⚠️ Amortisation zwischen 3 und 5 Jahren")
                else:
                    criteria.append("❌ Amortisation > 5 Jahre")
                    
                # NPV-Kriterium
                if financial['npv'] > 100000:
                    score += 1
                    criteria.append("✅ NPV > 100.000 €")
                elif financial['npv'] > 50000:
                    score += 0.5
                    criteria.append("⚠️ NPV zwischen 50.000 € und 100.000 €")
                else:
                    criteria.append("❌ NPV < 50.000 €")
                    
                # Strategischer Wert-Kriterium
                if financial['strategic_value'] >= 9:
                    score += 1
                    criteria.append("✅ Hoher strategischer Wert (9-10)")
                elif financial['strategic_value'] >= 7:
                    score += 0.5
                    criteria.append("⚠️ Mittlerer strategischer Wert (7-8)")
                else:
                    criteria.append("❌ Niedriger strategischer Wert (<7)")
                
                # Leistungswert-Kriterium
                leistungswert = float(location.get('leistungswert', 0) or 0)
                if leistungswert > 80:
                    score += 1
                    criteria.append("✅ Leistungswert > 80")
                elif leistungswert > 60:
                    score += 0.5
                    criteria.append("⚠️ Leistungswert zwischen 60 und 80")
                else:
                    criteria.append("❌ Leistungswert < 60")
                
                # Gesamtbewertung anzeigen
                score_percentage = (score / max_score) * 100
                
                st.markdown(f"##### Bewertung: {score}/{max_score} Punkte ({score_percentage:.1f}%)")
                st.progress(score / max_score)
                
                # Empfehlungstext
                if score >= 4:
                    st.success("**Empfehlung: Genehmigen** - Der Standort zeigt eine sehr gute wirtschaftliche Perspektive.")
                elif score >= 2.5:
                    st.warning("**Empfehlung: Mit Vorbehalt genehmigen** - Der Standort zeigt eine akzeptable wirtschaftliche Perspektive.")
                else:
                    st.error("**Empfehlung: Ablehnen** - Der Standort erfüllt die wirtschaftlichen Anforderungen nicht ausreichend.")
                
                # Einzelne Kriterien auflisten
                st.markdown("##### Bewertungskriterien:")
                for criterion in criteria:
                    st.markdown(criterion)
                
                # Hinweis zu möglichen Fehlerquellen
                st.caption("Hinweis: Diese Bewertung basiert auf Projektionen und unterliegt Unsicherheiten. Die finale Entscheidung obliegt dem CEO.")
        
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
                    elif status in ['objection', 'pending']:
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
            st.subheader("Entscheidung treffen")
            
            # Speichern der Finanzkennzahlen in der Session, damit wir sie bei der Entscheidung haben
            if location:
                financial = calculate_financial_metrics(location)
                st.session_state.financial_metrics = financial
            
            col1, col2 = st.columns(2)
            
            with col1:
                decision = st.radio(
                    "Standort genehmigen?",
                    ["Ja, genehmigen", "Nein, ablehnen"],
                    help="Bei Genehmigung wird der Standort an das Bauteam weitergeleitet."
                )
            
            with col2:
                reason = ""
                if decision == "Nein, ablehnen":
                    reason_options = [
                        "Wirtschaftlichkeit nicht ausreichend",
                        "Strategischer Wert zu gering",
                        "Bessere Alternativstandorte vorhanden",
                        "Zu lange Amortisationszeit",
                        "Zu hohe Investitionskosten",
                        "Anderer Grund"
                    ]
                    
                    reason_selection = st.selectbox("Grund für Ablehnung:", reason_options)
                    
                    if reason_selection == "Anderer Grund":
                        reason = st.text_input("Bitte spezifizieren:", key="custom_reason")
                    else:
                        reason = reason_selection
            
            # Bestätigungsbutton
            if st.button("Entscheidung bestätigen", type="primary"):
                is_approve = decision == "Ja, genehmigen"
                
                if not is_approve and not reason:
                    st.error("Bitte geben Sie einen Grund für die Ablehnung an.")
                else:
                    success = process_ceo_decision(selected_location, is_approve, reason, 
                                                  st.session_state.get('financial_metrics', {}))
                    
                    if success:
                        if is_approve:
                            st.success("Standort wurde genehmigt und wird an das Bauteam weitergeleitet.")
                        else:
                            st.success("Standort wurde abgelehnt. Der Projektworkflow wurde beendet.")
                        
                        # Aktualisieren der Standortliste
                        st.rerun()

# Sidebar mit Workflow-Information
st.sidebar.title("Workflow-Information")
st.sidebar.markdown("""
### Aktueller Schritt: CEO-Genehmigung

In diesem Schritt entscheidet der CEO über die finale Freigabe des Standorts basierend auf:

1. Wirtschaftlicher Betrachtung (ROI, Amortisationszeit)
2. Strategischem Wert des Standorts
3. Baurechtlicher Genehmigung

**Besonderheiten der Digitalen Säule:**
- Höhere Investition im Vergleich zu klassischen Werbeträgern
- Längerer wirtschaftlicher Betrachtungszeitraum
- Strategische Bedeutung des digitalen Netzwerks

**Bei Genehmigung:** Weiterleitung an das Bauteam zur Umsetzung
**Bei Ablehnung:** Ende des Workflows
""")

st.sidebar.markdown("""
### Workflow der Digitalen Säule:
1. ✅ Erfassung durch Akquisiteur
2. ✅ Leiter Akquisitionsmanagement
3. ~~Niederlassungsleiter~~ (übersprungen)
4. ✅ Baurecht
5. 🔄 **CEO**
6. ➡️ Bauteam
7. ➡️ Fertigstellung
""")

# Verbindung schließen am Ende
conn.close()