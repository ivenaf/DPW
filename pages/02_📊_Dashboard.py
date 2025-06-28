import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('werbetraeger.db', check_same_thread=False)
c = conn.cursor()

# Verfügbare Spalten in der Datenbank prüfen
def get_available_columns():
    c.execute("PRAGMA table_info(locations)")
    columns_info = c.fetchall()
    return {col[1] for col in columns_info}  # Set mit verfügbaren Spaltennamen

available_columns = get_available_columns()

# Seiteneinstellungen
st.set_page_config(layout="wide", page_title="Dashboard", page_icon="📊")
st.title("Dashboard (Link to SAC Dashboard)")

# Zeitraumfilter
st.sidebar.header("Zeitraumfilter")
date_options = ["Letzte 30 Tage", "Letztes Quartal", "Letztes Jahr", "Alle"]
selected_timeframe = st.sidebar.selectbox("Zeitraum", date_options)

# Vermarktungsform-Filter
c.execute('SELECT DISTINCT vermarktungsform FROM locations')
marketing_forms = [form[0] for form in c.fetchall() if form[0] is not None]
if marketing_forms:
    selected_forms = st.sidebar.multiselect("Vermarktungsform", marketing_forms, default=marketing_forms)
else:
    selected_forms = []

# Query-Parameter basierend auf Filtern
where_clauses = []
params = []

if selected_timeframe != "Alle":
    if selected_timeframe == "Letzte 30 Tage":
        date_threshold = (datetime.now() - timedelta(days=30)).isoformat()
    elif selected_timeframe == "Letztes Quartal":
        date_threshold = (datetime.now() - timedelta(days=90)).isoformat()
    elif selected_timeframe == "Letztes Jahr":
        date_threshold = (datetime.now() - timedelta(days=365)).isoformat()
    
    where_clauses.append("created_at >= ?")
    params.append(date_threshold)

if selected_forms:
    placeholders = ", ".join(["?" for _ in selected_forms])
    where_clauses.append(f"vermarktungsform IN ({placeholders})")
    params.extend(selected_forms)

where_clause = " AND ".join(where_clauses) if where_clauses else ""
query_suffix = f" WHERE {where_clause}" if where_clause else ""


# KPIs berechnen
c.execute(f'SELECT COUNT(*) FROM locations{query_suffix}', params)
total = c.fetchone()[0] or 0

# Parameter für weitere Abfragen klonen
status_params = params.copy()

# In Bearbeitung: Alle mit status='active' außer die, die bereits fertig sind
if where_clause:
    # Wichtig: Wir zählen nur die aktiven Einträge, die noch nicht fertig sind
    status_query_suffix = f"{query_suffix} AND status = 'active' AND current_step != 'fertig'"
    rejected_query_suffix = f"{query_suffix} AND status = 'rejected'"
    completed_query_suffix = f"{query_suffix} AND current_step = 'fertig'"
else:
    status_query_suffix = " WHERE status = 'active' AND current_step != 'fertig'"
    rejected_query_suffix = " WHERE status = 'rejected'"
    completed_query_suffix = " WHERE current_step = 'fertig'"

# Aktive Standorte im Prozess (nicht fertig)
c.execute(f'SELECT COUNT(*) FROM locations{status_query_suffix}', status_params)
in_progress = c.fetchone()[0] or 0

# Abgelehnte Standorte
c.execute(f'SELECT COUNT(*) FROM locations{rejected_query_suffix}', status_params)
rejected = c.fetchone()[0] or 0

# Fertige Standorte
c.execute(f'SELECT COUNT(*) FROM locations{completed_query_suffix}', status_params)
completed = c.fetchone()[0] or 0

# Prüfen, ob die Summe stimmt (es sollte total = in_progress + rejected + completed sein)
if total != (in_progress + rejected + completed):
    # Falls nicht, korrigiere in_progress durch Neuberechnung
    in_progress = total - rejected - completed

# Gesamte durchschnittliche Durchlaufzeit
c.execute('''
    SELECT AVG(julianday(h_end.timestamp) - julianday(h_start.timestamp))
    FROM workflow_history h_start
    JOIN workflow_history h_end ON h_start.location_id = h_end.location_id
    WHERE h_start.step = 'erfassung' 
    AND h_end.step = 'fertig'
''')
avg_total_duration = c.fetchone()[0]
avg_total_days = round(avg_total_duration) if avg_total_duration else 0

# Erfolgsquote berechnen
success_rate = round((completed / total * 100), 1) if total > 0 else 0

# Alle KPIs in einer Zeile
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Gesamt", total)
col2.metric("In Bearbeitung", in_progress)
col3.metric("Abgelehnt", rejected)
col4.metric("Abgeschlossen", completed)
col5.metric("Ø Gesamtdauer", f"{avg_total_days} Tage")
col6.metric("Erfolgsquote", f"{success_rate}%")

# Prozessschritte definieren
steps = ['erfassung', 'leiter_akquisition', 'niederlassungsleiter', 'baurecht', 'widerspruch', 'ceo', 'bauteam', 'fertig']
step_names = ['Erfassung', 'Leiter Akq.', 'Niederl.leiter', 'Baurecht', 'Widerspruch', 'CEO', 'Bauteam', 'Fertig']

# Diagnose: Finde Standorte, die "in Bearbeitung" sind, aber keinen gültigen Schritt haben
diagnose_params = params.copy()
if where_clause:
    diagnose_query = f"{query_suffix} AND status = 'active' AND current_step != 'fertig' AND current_step NOT IN ({','.join(['?']*len(steps[:-1]))})"
else:
    diagnose_query = f" WHERE status = 'active' AND current_step != 'fertig' AND current_step NOT IN ({','.join(['?']*len(steps[:-1]))})"

diagnose_params.extend(steps[:-1])
c.execute(f'SELECT COUNT(*), current_step FROM locations{diagnose_query} GROUP BY current_step', diagnose_params)
missing_steps = c.fetchall()

# Wenn "versteckte" Standorte gefunden wurden, zeige einen Hinweis
if missing_steps and sum(count for count, _ in missing_steps) > 0:
    st.warning(f"""
    **Hinweis:** {sum(count for count, _ in missing_steps)} Standorte sind als "In Bearbeitung" markiert, 
    haben aber einen nicht standardmäßigen Prozessschritt: 
    {', '.join([f'"{step}" ({count})' for count, step in missing_steps if step])}
    """)

# Dann füge den fehlenden Schritt zur Liste hinzu, falls vorhanden
extra_count = 0
if missing_steps:
    for count, step in missing_steps:
        extra_count += count
        if step and step not in steps:
            # Optional: Füge den Schritt zum Funnel hinzu
            steps.append(step)
            step_names.append(step.capitalize())  # Einfache Formatierung

# Prozess Funnel mit eindeutiger Datenhandhabung
st.header("Prozess-Funnel")

counts = []

# Zähle nur AKTIVE Standorte in jedem Schritt (ausgenommen "fertig")
active_step_counts = []
for step in steps[:-1]:  # Alle außer "fertig"
    step_params = params.copy()
    if where_clause:
        step_query = f"{query_suffix} AND current_step = ? AND status = 'active'"
    else:
        step_query = f" WHERE current_step = ? AND status = 'active'"
    
    step_params.append(step)
    c.execute(f'SELECT COUNT(*) FROM locations{step_query}', step_params)
    active_step_counts.append(c.fetchone()[0] or 0)

# Fertige Standorte (sollte gleich dem KPI "Abgeschlossen" sein)
active_step_counts.append(completed)  # Verwende direkt den "Abgeschlossen"-Wert für "Fertig"

# Aktualisiere die Counts-Liste
counts = active_step_counts

funnel_df = pd.DataFrame({
    'Step': step_names,
    'Anzahl': counts
})

# Verbesserte Funnel-Visualisierung
fig_funnel = px.funnel(funnel_df, x='Anzahl', y='Step')

# Layout und Farbgebung anpassen
fig_funnel.update_layout(
    margin=dict(l=10, r=10, t=10, b=20),
    height=500,
    font=dict(size=14),
    hoverlabel=dict(bgcolor="#F1FAEE", font_size=14),
    plot_bgcolor='rgba(0,0,0,0)'
)

# Balkenfarbe anpassen und Hover-Text verbessern
fig_funnel.update_traces(
    marker=dict(color="#457B9D", line=dict(width=1, color="#1D3557")),
    hovertemplate='%{y}: <b>%{x}</b> Standorte<extra></extra>'
)

st.plotly_chart(fig_funnel, use_container_width=True)

# Hinweis nur anzeigen, wenn tatsächlich ein Unterschied besteht
funnel_sum = sum(counts[:-1])  # Summe ohne "Fertig"
if funnel_sum != in_progress:
    st.caption(f"Hinweis: Die Summe der Standorte im Funnel ({funnel_sum}) weicht vom KPI 'In Bearbeitung' ({in_progress}) ab. Dies kann auf inkonsistente Datenzustände hindeuten.")

# Aufteilung nach Vermarktungsform
st.header("Aufteilung nach Vermarktungsform")

if selected_forms:
    form_counts = []
    for form in selected_forms:
        form_params = params.copy()
        if where_clause:
            form_query = f"{query_suffix} AND vermarktungsform = ?"
        else:
            form_query = " WHERE vermarktungsform = ?"
        
        form_params.append(form)
        c.execute(f'SELECT COUNT(*) FROM locations{form_query}', form_params)
        form_counts.append(c.fetchone()[0] or 0)
    
    form_df = pd.DataFrame({
        'Vermarktungsform': selected_forms,
        'Anzahl': form_counts
    })
    
    fig_forms = px.bar(form_df, x='Vermarktungsform', y='Anzahl', color='Vermarktungsform')
    st.plotly_chart(fig_forms, use_container_width=True)

# Detailierte Aufteilung nach Status und Vermarktungsform
st.header("Status nach Vermarktungsform")
status_list = ['active', 'rejected']
status_names = ['In Bearbeitung', 'Abgelehnt']

data = []
for form in selected_forms:
    form_data = {'Vermarktungsform': form}
    
    for status, status_name in zip(status_list, status_names):
        status_params = params.copy()
        if where_clause:
            status_query = f"{query_suffix} AND vermarktungsform = ? AND status = ?"
        else:
            status_query = " WHERE vermarktungsform = ? AND status = ?"
        
        status_params.extend([form, status])
        c.execute(f'SELECT COUNT(*) FROM locations{status_query}', status_params)
        form_data[status_name] = c.fetchone()[0] or 0
        
    # Fertiggestellte separat zählen
    completed_params = params.copy()
    if where_clause:
        completed_query = f"{query_suffix} AND vermarktungsform = ? AND current_step = 'fertig'"
    else:
        completed_query = " WHERE vermarktungsform = ? AND current_step = 'fertig'"
    
    completed_params.append(form)
    c.execute(f'SELECT COUNT(*) FROM locations{completed_query}', completed_params)
    form_data['Fertig'] = c.fetchone()[0] or 0
    
    data.append(form_data)

if data:
    status_df = pd.DataFrame(data)
    melted_df = pd.melt(status_df, id_vars=['Vermarktungsform'], 
                        value_vars=['In Bearbeitung', 'Abgelehnt', 'Fertig'],
                        var_name='Status', value_name='Anzahl')
    
    fig_status = px.bar(melted_df, x='Vermarktungsform', y='Anzahl', 
                       color='Status', barmode='group')
    st.plotly_chart(fig_status, use_container_width=True)

# Durchschnittliche Durchlaufzeiten
st.header("Durchschnittliche Verweildauer pro Step (Tage)")

try:
    step_durations = {}
    for i in range(len(steps) - 1):
        current_step = steps[i]
        next_step = steps[i + 1]
        
        c.execute('''
        SELECT AVG(julianday(h2.timestamp) - julianday(h1.timestamp))
        FROM workflow_history h1
        JOIN workflow_history h2 ON h1.location_id = h2.location_id
        WHERE h1.step = ? AND h2.step = ?
        ''', (current_step, next_step))
        
        avg_days = c.fetchone()[0]
        if avg_days:
            step_durations[step_names[i]] = round(avg_days, 1)
        else:
            step_durations[step_names[i]] = 0

    if step_durations:
        duration_df = pd.DataFrame({
            'Step': list(step_durations.keys()),
            'Durchschnittliche Dauer (Tage)': list(step_durations.values())
        })
        
        fig_duration = px.bar(duration_df, x='Step', y='Durchschnittliche Dauer (Tage)')
        st.plotly_chart(fig_duration, use_container_width=True)
    else:
        st.info("Keine Durchlaufzeitdaten verfügbar.")
except Exception as e:
    st.warning(f"Konnte Durchlaufzeiten nicht berechnen: {str(e)}")

# Detailübersicht Standorte
st.header("Detailübersicht Standorte")

# VERBESSERTE DETAILÜBERSICHT - Mit ergänzten KPIs
try:
    # Alle Spalten der Tabelle direkt abfragen
    detail_query = f"SELECT * FROM locations{query_suffix}"
    
    # SQL-Abfrage ausführen
    c.execute(detail_query, params)
    result = c.fetchall()
    
    if result:
        # Spaltenüberschriften direkt aus der Abfrage
        column_names = [description[0] for description in c.description]
        
        # DataFrame erstellen mit allen Spalten
        detail_df = pd.DataFrame(result, columns=column_names)
        
        # Wirtschaftliche KPIs ergänzen/berechnen für jeden Standort
        
        # 1. KPIs, die aus vorhandenen Daten berechnet werden können
        if "leistungswert" in detail_df.columns:
            # Leistungswert-bezogene KPIs
            detail_df["leistungswert"] = pd.to_numeric(detail_df["leistungswert"], errors="coerce").fillna(0)
            
        # Wenn Investitionskosten nicht vorhanden sind, schätzen
        if "investitionskosten" not in detail_df.columns:
            # Standortabhängige Investitionskostenschätzung basierend auf Leistungswert
            if "leistungswert" in detail_df.columns:
                detail_df["investitionskosten"] = detail_df["leistungswert"].apply(
                    lambda lw: lw * 60 if lw > 0 else 60000
                )
            else:
                # Standardwert wenn kein Leistungswert verfügbar
                detail_df["investitionskosten"] = 60000
        
        # Wenn jährliche Einnahmen nicht vorhanden sind, schätzen
        if "jaehrliche_einnahmen" not in detail_df.columns:
            if "leistungswert" in detail_df.columns:
                detail_df["jaehrliche_einnahmen"] = detail_df["leistungswert"].apply(
                    lambda lw: lw * 25 if lw > 0 else 25000
                )
            else:
                detail_df["jaehrliche_einnahmen"] = 25000
        
        # Wenn jährliche Betriebskosten nicht vorhanden sind, schätzen
        if "jaehrliche_betriebskosten" not in detail_df.columns:
            if "leistungswert" in detail_df.columns:
                detail_df["jaehrliche_betriebskosten"] = detail_df["leistungswert"].apply(
                    lambda lw: lw * 8 if lw > 0 else 8000
                )
            else:
                detail_df["jaehrliche_betriebskosten"] = 8000
        
        # Jährlichen Gewinn berechnen
        detail_df["jaehrlicher_gewinn"] = detail_df["jaehrliche_einnahmen"] - detail_df["jaehrliche_betriebskosten"]
        
        # ROI berechnen, wenn nicht vorhanden
        if "roi" not in detail_df.columns or detail_df["roi"].isna().all():
            # ROI als Prozentwert: (Jährlicher Gewinn / Investitionskosten) * 100
            detail_df["roi"] = (detail_df["jaehrlicher_gewinn"] / detail_df["investitionskosten"] * 100).round(2)
            detail_df["roi"] = detail_df["roi"].fillna(0)
        
        # Amortisationszeit berechnen, wenn nicht vorhanden
        if "amortisationszeit" not in detail_df.columns or detail_df["amortisationszeit"].isna().all():
            # Amortisationszeit: Investitionskosten / Jährlicher Gewinn (in Jahren)
            detail_df["amortisationszeit"] = detail_df.apply(
                lambda row: row["investitionskosten"] / row["jaehrlicher_gewinn"] if row["jaehrlicher_gewinn"] > 0 else 0, 
                axis=1
            ).round(1)
        
        # NPV (Net Present Value) berechnen, wenn nicht vorhanden
        if "npv" not in detail_df.columns or detail_df["npv"].isna().all():
            # Einfache NPV-Kalkulation über 10 Jahre mit 5% Diskontierungsrate
            discount_rate = 0.05
            years = 10
            
            def calculate_npv(invest, annual_profit):
                npv = -invest  # Anfangsinvestition negativ
                for year in range(1, years + 1):
                    npv += annual_profit / ((1 + discount_rate) ** year)
                return round(npv)
            
            detail_df["npv"] = detail_df.apply(
                lambda row: calculate_npv(row["investitionskosten"], row["jaehrlicher_gewinn"]), 
                axis=1
            )
        
        # Strategischen Wert schätzen, wenn nicht vorhanden
        if "strategischer_wert" not in detail_df.columns or detail_df["strategischer_wert"].isna().all():
            # Strategischer Wert auf Skala 1-10 basierend auf ROI, Leistungswert und Standort
            detail_df["strategischer_wert"] = 5  # Basiswert
            
            # ROI-Einfluss: Höherer ROI = höherer strategischer Wert
            if "roi" in detail_df.columns:
                detail_df["strategischer_wert"] += detail_df["roi"].apply(
                    lambda r: min(2, r / 15) if r > 0 else 0
                )
            
            # Leistungswert-Einfluss
            if "leistungswert" in detail_df.columns:
                detail_df["strategischer_wert"] += detail_df["leistungswert"].apply(
                    lambda lw: min(2, lw / 2000) if lw > 0 else 0
                )
            
            # Rundung auf eine Dezimalstelle
            detail_df["strategischer_wert"] = detail_df["strategischer_wert"].round(1)
            # Begrenzung auf Skala 1-10
            detail_df["strategischer_wert"] = detail_df["strategischer_wert"].clip(1, 10)
        
        # KPI-Spalten formatieren
        detail_df["investitionskosten_fmt"] = detail_df["investitionskosten"].apply(lambda x: f"{int(x):,} €")
        detail_df["jaehrliche_einnahmen_fmt"] = detail_df["jaehrliche_einnahmen"].apply(lambda x: f"{int(x):,} €/Jahr")
        detail_df["jaehrliche_betriebskosten_fmt"] = detail_df["jaehrliche_betriebskosten"].apply(lambda x: f"{int(x):,} €/Jahr")
        detail_df["jaehrlicher_gewinn_fmt"] = detail_df["jaehrlicher_gewinn"].apply(lambda x: f"{int(x):,} €/Jahr")
        detail_df["roi_fmt"] = detail_df["roi"].apply(lambda x: f"{x:.1f}%")
        detail_df["npv_fmt"] = detail_df["npv"].apply(lambda x: f"{int(x):,} €")
        detail_df["amortisationszeit_fmt"] = detail_df["amortisationszeit"].apply(lambda x: f"{x:.1f} Jahre")
        
        # Auswahl zwischen kompakter und detaillierter Ansicht
        view_type = st.radio(
            "Ansicht:",
            ["Kompakt", "Erweitert (mit allen Daten)"],
            horizontal=True
        )
        
        if view_type == "Kompakt":
            # Wichtige Spalten für die kompakte Ansicht (angepasst für Leistungswert und Geokoordinaten)
            compact_cols = ["id", "erfasser", "standort", "stadt"]
            
            # Füge Leistungswert und Geokoordinaten hinzu, wenn verfügbar
            if "leistungswert" in column_names:
                compact_cols.append("leistungswert")
            if "lat" in column_names and "lng" in column_names:
                compact_cols.extend(["lat", "lng"])
            
            # Weitere Standardspalten
            compact_cols.extend(["eigentuemer", "vermarktungsform", "status", "current_step"])
            
            # Nur verfügbare Spalten anzeigen
            available_compact = [col for col in compact_cols if col in column_names]
            st.dataframe(detail_df[available_compact], height=400, use_container_width=True)
        else:
            # Erweiterte Ansicht mit Tabs
            tabs = st.tabs([
                "Standortdaten", 
                "Wirtschaftlichkeit", 
                "Technische Details", 
                "Genehmigungen"
            ])
            
            with tabs[0]:  # Standortdaten
                standort_cols = ["id", "erfasser", "datum", "standort", "stadt"]
                if "lat" in column_names and "lng" in column_names:
                    standort_cols.extend(["lat", "lng"])
                if "eigentuemer" in column_names:
                    standort_cols.append("eigentuemer")
                standort_cols.extend(["vermarktungsform", "status", "current_step"])
                
                available_standort = [col for col in standort_cols if col in detail_df.columns]
                st.dataframe(detail_df[available_standort], height=400, use_container_width=True)
            
            with tabs[1]:  # Wirtschaftlichkeit
                wirtschaft_cols = ["id", "standort", "stadt", 
                                 "investitionskosten_fmt", "jaehrliche_einnahmen_fmt", 
                                 "jaehrliche_betriebskosten_fmt", "jaehrlicher_gewinn_fmt",
                                 "roi_fmt", "amortisationszeit_fmt", "npv_fmt", "strategischer_wert"]
                
                # Erstelle DataFrame nur mit den relevanten Spalten
                wirtschaft_df = detail_df[["id", "standort", "stadt"]].copy()
                
                # Füge formatierte KPI-Spalten hinzu
                wirtschaft_df["Investitionskosten"] = detail_df["investitionskosten_fmt"]
                wirtschaft_df["Jährl. Einnahmen"] = detail_df["jaehrliche_einnahmen_fmt"]
                wirtschaft_df["Jährl. Betriebskosten"] = detail_df["jaehrliche_betriebskosten_fmt"]
                wirtschaft_df["Jährl. Gewinn"] = detail_df["jaehrlicher_gewinn_fmt"]
                wirtschaft_df["ROI"] = detail_df["roi_fmt"]
                wirtschaft_df["Amortisationszeit"] = detail_df["amortisationszeit_fmt"]
                wirtschaft_df["NPV"] = detail_df["npv_fmt"]
                wirtschaft_df["Strategischer Wert"] = detail_df["strategischer_wert"]
                
                st.dataframe(wirtschaft_df, height=400, use_container_width=True)
            
            with tabs[2]:  # Technische Details
                tech_cols = ["id", "standort", "stadt", "leistungswert"]
                
                if "umruestung" in column_names:
                    tech_cols.append("umruestung")
                if "alte_nummer" in column_names:
                    tech_cols.append("alte_nummer")
                if "seiten" in column_names:
                    tech_cols.append("seiten")
                
                tech_cols.append("vermarktungsform")
                
                available_tech = [col for col in tech_cols if col in detail_df.columns]
                st.dataframe(detail_df[available_tech], height=400, use_container_width=True)
            
            with tabs[3]:  # Genehmigungen
                genehmigung_cols = ["id", "standort", "stadt"]
                
                for col in ["bauantrag_datum", "bauantrag_status", "bauantrag_nummer", "baurecht_entscheidung_datum"]:
                    if col in column_names:
                        genehmigung_cols.append(col)
                
                genehmigung_cols.extend(["status", "current_step"])
                
                available_genehmigung = [col for col in genehmigung_cols if col in detail_df.columns]
                if available_genehmigung:
                    st.dataframe(detail_df[available_genehmigung], height=400, use_container_width=True)
                else:
                    st.info("Keine Genehmigungsdaten verfügbar.")
        
        # Erweiterte CSV-Datei mit allen KPIs
        csv_df = detail_df.copy()
        
        # Spalten umbenennen für bessere Lesbarkeit im Export
        rename_map = {
            "id": "ID",
            "erfasser": "Erfasser",
            "datum": "Datum",
            "standort": "Standort",
            "stadt": "Stadt",
            "lat": "Latitude",
            "lng": "Longitude",
            "leistungswert": "Leistungswert",
            "eigentuemer": "Eigentümer",
            "umruestung": "Umrüstung",
            "alte_nummer": "Alte Nummer",
            "seiten": "Seiten",
            "vermarktungsform": "Vermarktungsform",
            "status": "Status",
            "current_step": "Aktueller Step",
            "investitionskosten": "Investitionskosten (€)",
            "jaehrliche_einnahmen": "Jährl. Einnahmen (€/Jahr)",
            "jaehrliche_betriebskosten": "Jährl. Betriebskosten (€/Jahr)",
            "jaehrlicher_gewinn": "Jährl. Gewinn (€/Jahr)",
            "roi": "ROI (%)",
            "amortisationszeit": "Amortisationszeit (Jahre)",
            "npv": "Kapitalwert NPV (€)",
            "strategischer_wert": "Strategischer Wert (1-10)"
        }
        
        # Nur existierende Spalten umbenennen
        valid_renames = {k: v for k, v in rename_map.items() if k in csv_df.columns}
        csv_df = csv_df.rename(columns=valid_renames)
        
        # Formatspalten entfernen (nur numerische Werte behalten)
        format_cols = [col for col in csv_df.columns if col.endswith('_fmt')]
        csv_df = csv_df.drop(columns=format_cols, errors='ignore')
        
        # CSV-Export mit allen KPIs
        csv = csv_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Export als CSV (mit allen KPIs)",
            data=csv,
            file_name="werbetraeger_report.csv",
            mime="text/csv",
            key="download-csv"
        )
    else:
        st.info("Keine Daten für die gewählten Filter verfügbar.")

except Exception as e:
    st.error(f"Ein Fehler ist aufgetreten: {str(e)}")



st.header("Standort löschen")

# Alle IDs und Standorte für Auswahl abrufen (mit aktuellem Filter)
c.execute(f"SELECT id, standort, stadt FROM locations{query_suffix}", params)
id_rows = c.fetchall()
if id_rows:
    id_options = [f"{row[0]} | {row[1]}, {row[2]}" for row in id_rows]
    selected_id_str = st.selectbox("Zu löschende Standort-ID auswählen:", id_options)
    selected_id = selected_id_str.split(" | ")[0]

    if st.button("Standort unwiderruflich löschen", type="primary"):
        c.execute("DELETE FROM locations WHERE id = ?", (selected_id,))
        c.execute("DELETE FROM workflow_history WHERE location_id = ?", (selected_id,))
        conn.commit()
        st.success(f"Standort mit ID {selected_id} wurde gelöscht.")
        st.rerun()
else:
    st.info("Keine Standorte für Löschung verfügbar.")





# Schließe die Datenbankverbindung
conn.close()