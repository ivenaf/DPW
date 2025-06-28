import streamlit as st
import pandas as pd
import sqlite3
import pydeck as pdk

# Seiteneinstellungen
st.set_page_config(page_title="GeoMap", page_icon="🗺️", layout="wide")
st.title("Geografische Übersicht aller Standorte")

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('werbetraeger.db', check_same_thread=False)
c = conn.cursor()

# Farben je Vermarktungsform definieren
form_colors = {
    'Digitale Säule': [31, 119, 180],
    'Roadside-Screen': [255, 127, 14],
    'City-Screen': [44, 160, 44],
    'MegaVision': [214, 39, 40],
    'SuperMotion': [148, 103, 189],
    # Fallback
    'default': [128, 128, 128]
}

# Alle Standorte mit gültigen Koordinaten laden (inkl. current_step)
c.execute("SELECT id, standort, stadt, lat, lng, vermarktungsform, current_step FROM locations WHERE lat IS NOT NULL AND lng IS NOT NULL")
locations = c.fetchall()

if not locations:
    st.warning("Keine Standorte mit Koordinaten gefunden.")
else:
    df = pd.DataFrame(locations, columns=['id', 'standort', 'stadt', 'lat', 'lng', 'vermarktungsform', 'current_step'])

    # Farbe nach Vermarktungsform zuweisen
    df['color'] = df['vermarktungsform'].apply(lambda x: form_colors.get(x, form_colors['default']))

    # PyDeck-View auf Deutschland
    view_state = pdk.ViewState(
        latitude=51.1634,
        longitude=10.4477,
        zoom=6,
        pitch=0
    )

    # Scatterplot-Layer
    layer = pdk.Layer(
        'ScatterplotLayer',
        df,
        get_position=['lng', 'lat'],
        get_color='color',
        get_radius=100,
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True
    )

    tooltip = {
        "html": (
            "<b>ID:</b> {id}<br/>"
            "<b>Standort:</b> {standort}<br/>"
            "<b>Stadt:</b> {stadt}<br/>"
            "<b>Vermarktungsform:</b> {vermarktungsform}<br/>"
            "<b>Bearbeitungsschritt:</b> {current_step}"
        ),
        "style": {
            "backgroundColor": "white",
            "color": "black"
        }
    }

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=view_state,
        layers=[layer],
        tooltip=tooltip
    ))

    # Legende (horizontal)
    st.subheader("Legende")
    legend_html = '<div style="display: flex; flex-direction: row; gap: 24px; margin-bottom: 10px;">'
    for form, color in form_colors.items():
        if form == 'default':
            continue
        color_hex = "#{:02x}{:02x}{:02x}".format(*color)
        legend_html += (
            f'<div style="display: flex; align-items: center;">'
            f'<div style="width: 15px; height: 15px; background-color: {color_hex}; margin-right: 6px; border-radius: 3px;"></div>'
            f'<div>{form}</div></div>'
        )
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)