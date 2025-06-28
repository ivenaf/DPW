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

# Funktion zur Berechnung von wirtschaftlichen Kennzahlen (mit realistischen Werten)
def calculate_financial_metrics(location):
    # In einer echten Anwendung würden diese Daten aus einer Datenbank kommen
    # Hier simulieren wir realistische Beispieldaten basierend auf dem Standort
    
    # Zufällige, aber konsistente Daten für einen gegebenen Standort generieren
    import hashlib
    
    # Hash aus ID generieren für konsistente "Zufallszahlen"
    hash_obj = hashlib.md5(location['id'].encode())
    hash_value = int(hash_obj.hexdigest()[:8], 16) 
    np.random.seed(hash_value % (2**32 - 1))
    
    # Realistische Wirtschaftliche Kennzahlen berechnen
    # Investitionskosten für eine Digitale Säule: 20.000-35.000€
    investment = np.random.randint(20000, 35000)
    
    # Mehr Seiten = mehr Einnahmen
    sides = 1
    if location['seiten'] == 'doppelseitig':
        sides = 2
    elif location['seiten'] == 'dreiseitig':
        sides = 3
        
    # Jahreseinnahmen basierend auf Standort und Seiten
    # Realistische jährliche Einnahmen pro Seite: 2.000-4.000€
    revenue_factor = 1.0
    if location['eigentuemer'] == 'Stadt':
        revenue_factor = 1.15  # Städtische Standorte haben bessere Performance
    
    leistungswert = float(location.get('leistungswert', 0) or 0)
    if leistungswert > 0:
        revenue_factor *= (1 + leistungswert/200)  # Reduzierter Einfluss
    
    annual_revenue = np.random.randint(2000, 4000) * sides * revenue_factor
    
    # Betriebskosten: 40-50% der Einnahmen
    operating_costs = annual_revenue * np.random.uniform(0.4, 0.5)
    
    # Gewinn
    annual_profit = annual_revenue - operating_costs
    
    # ROI berechnen: Realistischer Bereich 5-10%
    roi = (annual_profit / investment) * 100
    
    # Amortisationszeit in Jahren: Typisch 8-12 Jahre
    payback_period = investment / annual_profit
    
    # NPV über 10 Jahre mit 8% Diskontierungsrate
    discount_rate = 0.08
    cash_flows = [-investment]
    for year in range(1, 11):
        # Leichte Steigerung der jährlichen Einnahmen
        year_profit = annual_profit * (1 + 0.02) ** (year - 1)
        cash_flows.append(year_profit)
    
    npv = sum(cf / (1 + discount_rate) ** i for i, cf in enumerate(cash_flows))
    
    return {
        'investment': investment,
        'annual_revenue': annual_revenue,
        'operating_costs': operating_costs,
        'annual_profit': annual_profit,
        'roi': roi,
        'payback_period': payback_period,
        'npv': npv
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
        message = f"Standort vom CEO genehmigt. Wirtschaftliche Kennzahlen: ROI {financial_metrics['roi']:.1f}%, Amortisation {financial_metrics['payback_period']:.1f} Jahre."
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
    display_df = df[['id', 'standort', 'stadt', 'eigentuemer', 'vermarktungsform', 'created_at']].copy()
    display_df.columns = ['ID', 'Standort', 'Stadt', 'Eigentümer', 'Vermarktungsform', 'Erfasst am']
    
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
                
                # Definition von Tooltip-Texten für KPIs
                kpi_tooltips = {
                    'investment': "Die Gesamtkosten für die Installation der Digitalen Säule inkl. Fundament, Hardware, Display und Montage.",
                    'annual_revenue': "Die erwarteten jährlichen Bruttoeinnahmen aus Werbebuchungen, basierend auf Standortqualität und Sichtkontakten.",
                    'operating_costs': "Jährliche Kosten für Stromverbrauch, Wartung, Versicherung und Standortmiete.",
                    'annual_profit': "Jährliche Einnahmen abzüglich der Betriebskosten (ohne Abschreibung der Investition).",
                    'roi': "Return on Investment: Jährlicher Gewinn geteilt durch die Investition, ausgedrückt als Prozentsatz. Zeigt die jährliche Rendite.",
                    'payback_period': "Die Zeit in Jahren, bis die anfängliche Investition durch die Gewinne zurückgezahlt ist.",
                    'npv': "Net Present Value: Der Barwert aller zukünftigen Cashflows über 10 Jahre, abzüglich der Anfangsinvestition (Diskontierungsrate 8%)."
                }
                
                # Erstellen des HTML für die saubere Tabelle mit korrektem Formatting
                html_table = """
                <table style="width:100%; border-collapse: collapse;">
                    <tr>
                        <th style="text-align:left; padding:10px; border-bottom:1px solid #ddd; background-color:#f5f5f5;">Kennzahl</th>
                        <th style="text-align:right; padding:10px; border-bottom:1px solid #ddd; background-color:#f5f5f5;">Wert</th>
                    </tr>
                    <tr>
                        <td style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">Investitionskosten <span class='tooltip' title='{0}'>ℹ️</span></td>
                        <td style="text-align:right; padding:10px; border-bottom:1px solid #ddd;">{1:,.0f} €</td>
                    </tr>
                    <tr>
                        <td style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">Jährliche Einnahmen <span class='tooltip' title='{2}'>ℹ️</span></td>
                        <td style="text-align:right; padding:10px; border-bottom:1px solid #ddd;">{3:,.0f} €</td>
                    </tr>
                    <tr>
                        <td style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">Jährliche Betriebskosten <span class='tooltip' title='{4}'>ℹ️</span></td>
                        <td style="text-align:right; padding:10px; border-bottom:1px solid #ddd;">{5:,.0f} €</td>
                    </tr>
                    <tr>
                        <td style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">Jährlicher Gewinn <span class='tooltip' title='{6}'>ℹ️</span></td>
                        <td style="text-align:right; padding:10px; border-bottom:1px solid #ddd;">{7:,.0f} €</td>
                    </tr>
                    <tr>
                        <td style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">ROI <span class='tooltip' title='{8}'>ℹ️</span></td>
                        <td style="text-align:right; padding:10px; border-bottom:1px solid #ddd;">{9:.1f} %</td>
                    </tr>
                    <tr>
                        <td style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">Amortisationszeit <span class='tooltip' title='{10}'>ℹ️</span></td>
                        <td style="text-align:right; padding:10px; border-bottom:1px solid #ddd;">{11:.1f} Jahre</td>
                    </tr>
                    <tr>
                        <td style="text-align:left; padding:10px; border-bottom:1px solid #ddd;">Kapitalwert (NPV) <span class='tooltip' title='{12}'>ℹ️</span></td>
                        <td style="text-align:right; padding:10px; border-bottom:1px solid #ddd;">{13:,.0f} €</td>
                    </tr>
                </table>
                """.format(
                    kpi_tooltips['investment'],
                    financial['investment'],
                    kpi_tooltips['annual_revenue'],
                    financial['annual_revenue'],
                    kpi_tooltips['operating_costs'],
                    financial['operating_costs'],
                    kpi_tooltips['annual_profit'],
                    financial['annual_profit'],
                    kpi_tooltips['roi'],
                    financial['roi'],
                    kpi_tooltips['payback_period'],
                    financial['payback_period'],
                    kpi_tooltips['npv'],
                    financial['npv']
                )
                
                # Anzeigen der Tabelle
                st.markdown(html_table, unsafe_allow_html=True)
                
                # Cashflow-Modell für 5 Jahre
                st.markdown("### 5-Jahres Cashflow-Projektion")
                
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
                
                # Empfehlung basierend auf den Kennzahlen (mit realistischeren Kriterien)
                st.markdown("### Automatische Bewertung")
                
                score = 0
                max_score = 4  # Strategischer Wert wurde entfernt
                criteria = []
                
                # ROI-Kriterium (realistischere Werte)
                if financial['roi'] > 8:
                    score += 1
                    criteria.append("✅ ROI > 8%")
                elif financial['roi'] > 5:
                    score += 0.5
                    criteria.append("⚠️ ROI zwischen 5% und 8%")
                else:
                    criteria.append("❌ ROI < 5%")
                
                # Amortisationszeit-Kriterium (realistischere Werte)
                if financial['payback_period'] < 8:
                    score += 1
                    criteria.append("✅ Amortisation < 8 Jahre")
                elif financial['payback_period'] < 10:
                    score += 0.5
                    criteria.append("⚠️ Amortisation zwischen 8 und 10 Jahren")
                else:
                    criteria.append("❌ Amortisation > 10 Jahre")
                    
                # NPV-Kriterium (realistischere Werte)
                if financial['npv'] > 15000:
                    score += 1
                    criteria.append("✅ NPV > 15.000 €")
                elif financial['npv'] > 5000:
                    score += 0.5
                    criteria.append("⚠️ NPV zwischen 5.000 € und 15.000 €")
                else:
                    criteria.append("❌ NPV < 5.000 €")
                
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
                
                st.markdown(f"#### Bewertung: {score}/{max_score} Punkte ({score_percentage:.1f}%)")
                st.progress(score / max_score)
                
                # Empfehlungstext
                if score >= 3:
                    st.success("**Empfehlung: Genehmigen** - Der Standort zeigt eine sehr gute wirtschaftliche Perspektive.")
                elif score >= 2:
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
2. Baurechtlicher Genehmigung

**Besonderheiten der Digitalen Säule:**
- Höhere Investition im Vergleich zu klassischen Werbeträgern
- Längerer wirtschaftlicher Betrachtungszeitraum

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

# CSS für Tooltips verbessern
st.markdown("""
<style>
/* Basis-Tooltip-Stil */
.tooltip {
    position: relative;
    display: inline-block;
    cursor: help;
    margin-left: 5px;
}

.tooltip:hover::after {
    content: attr(title);
    position: absolute;
    left: 0;
    top: -45px;
    min-width: 250px;
    max-width: 300px;
    padding: 8px 12px;
    border-radius: 4px;
    background-color: #333;
    color: white;
    font-size: 14px;
    z-index: 1000;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    white-space: normal;
    line-height: 1.4;
}
</style>
""", unsafe_allow_html=True)

# Verbindung schließen am Ende
conn.close()