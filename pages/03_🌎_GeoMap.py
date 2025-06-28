import streamlit as st
import pandas as pd
import sqlite3
import pydeck as pdk
import numpy as np

# Seiteneinstellungen
st.set_page_config(page_title="GeoMap", page_icon="🗺️", layout="wide")
st.title("Geografische Übersicht der Standorte")

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('werbetraeger.db', check_same_thread=False)
c = conn.cursor()

# Farben je nach Bearbeitungsschritt definieren
step_colors = {
    'erfassung': [31, 119, 180],           # Blau
    'leiter_akquisition': [255, 127, 14],  # Orange
    'niederlassungsleiter': [44, 160, 44], # Grün
    'baurecht': [214, 39, 40],             # Rot
    'widerspruch': [148, 103, 189],        # Lila
    'ceo': [140, 86, 75],                  # Braun
    'bauteam': [227, 119, 194],            # Rosa
    'fertig': [44, 160, 44],               # Grün
    'rejected': [128, 128, 128]            # Grau für abgelehnte
}



# Filter für Ansicht
st.sidebar.header("Filter")

# Vermarktungsform-Filter
c.execute('SELECT DISTINCT vermarktungsform FROM locations')
marketing_forms = [form[0] for form in c.fetchall() if form[0] is not None]
if marketing_forms:
    selected_forms = st.sidebar.multiselect("Vermarktungsform", marketing_forms, default=marketing_forms)
else:
    selected_forms = []

# Status-Filter
status_options = ["active", "rejected", "all"]
selected_status = st.sidebar.radio("Status", status_options, index=0, format_func=lambda x: "Aktiv" if x == "active" else ("Abgelehnt" if x == "rejected" else "Alle"))

# Bearbeitungsschritt-Filter
c.execute('SELECT DISTINCT current_step FROM locations')
steps = [step[0] for step in c.fetchall() if step[0] is not None]
if steps:
    selected_steps = st.sidebar.multiselect("Bearbeitungsschritt", steps, default=steps)
else:
    selected_steps = []

# SQL-Abfrage mit Filtern
query = "SELECT id, standort, stadt, lat, lng, status, current_step, vermarktungsform FROM locations WHERE 1=1"
params = []

if selected_forms:
    placeholders = ", ".join(["?" for _ in selected_forms])
    query += f" AND vermarktungsform IN ({placeholders})"
    params.extend(selected_forms)

if selected_status != "all":
    query += " AND status = ?"
    params.append(selected_status)

if selected_steps:
    placeholders = ", ".join(["?" for _ in selected_steps])
    query += f" AND current_step IN ({placeholders})"
    params.extend(selected_steps)

# Nur Standorte mit gültigen Koordinaten anzeigen
query += " AND lat IS NOT NULL AND lng IS NOT NULL"

# Daten abrufen
c.execute(query, params)
locations = c.fetchall()

if not locations:
    st.warning("Keine Standorte mit den ausgewählten Filtern gefunden.")
else:
    # Daten für die Karte vorbereiten
    df = pd.DataFrame(locations, columns=['id', 'standort', 'stadt', 'lat', 'lng', 'status', 'current_step', 'vermarktungsform'])
    
    

    # Farbzuweisung basierend auf current_step oder status
    df['color'] = df.apply(
        lambda row: step_colors.get(row['current_step'], step_colors.get('rejected')) if row['status'] != 'rejected' else step_colors['rejected'], 
        axis=1
    )
    
    # Erstellen der Legende
    st.sidebar.subheader("Legende")
    
    # Sammle alle in den aktuell angezeigten Daten verwendeten Schritte
    used_steps = df['current_step'].unique().tolist()
    if 'rejected' in df['status'].unique():
        used_steps.append('rejected')
    
    # Zeige die Legende mit den korrekten Farben
    for step in sorted(used_steps):
        color = step_colors.get(step, [128, 128, 128])  # Grau als Fallback
        color_hex = "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])
        label = step.capitalize()
        if step == 'rejected':
            label = "Abgelehnt"
        
        st.sidebar.markdown(f'<div style="display: flex; align-items: center; margin-bottom: 5px;">'
                          f'<div style="width: 15px; height: 15px; background-color: {color_hex}; margin-right: 8px;"></div>'
                          f'<div>{label}</div></div>', unsafe_allow_html=True)

    # Zusätzliche Statistik
    st.sidebar.subheader("Statistik")
    st.sidebar.write(f"Anzahl der Standorte: {len(df)}")
    
    # Standorte pro Schritt zählen
    step_counts = df['current_step'].value_counts().to_dict()
    for step, count in sorted(step_counts.items()):
        st.sidebar.write(f"{step.capitalize()}: {count}")

    # Erstellen der Karte mit PyDeck
    view_state = pdk.ViewState(
        latitude=df['lat'].mean(),
        longitude=df['lng'].mean(),
        zoom=5,
        pitch=0
    )

    # Erstellen des Scatterplot-Layers mit Punkten
    layer = pdk.Layer(
        'ScatterplotLayer',
        df,
        get_position=['lng', 'lat'],
        get_color='color',
        get_radius=100,  # Punktgröße
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True
    )

    # Tooltip für Hover-Effekt
    tooltip = {
        "html": "<b>Standort:</b> {standort}<br/><b>Stadt:</b> {stadt}<br/><b>Status:</b> {status}<br/><b>Schritt:</b> {current_step}<br/><b>Vermarktungsform:</b> {vermarktungsform}",
        "style": {
            "backgroundColor": "white",
            "color": "black"
        }
    }

    # Karte rendern
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=view_state,
        layers=[layer],
        tooltip=tooltip
    ))

    