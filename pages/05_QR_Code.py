import streamlit as st
import qrcode
from io import BytesIO

st.set_page_config(page_title="App QR-Code", page_icon="🔗", layout="centered")
st.title("🔗 QR-Code für den Schnellzugriff")

# Link zur App (hier anpassen!)
app_url = "https://ivenaf-dpw-1--home-ynwloa.streamlit.app/"  # <-- Passe diesen Link an!

st.write("Scanne diesen QR-Code, um die App direkt auf deinem Smartphone oder Tablet zu öffnen:")

# QR-Code generieren
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    box_size=10,
    border=2,
)
qr.add_data(app_url)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")

# Bild in Bytes umwandeln und anzeigen
buf = BytesIO()
img.save(buf, format="PNG")
st.image(buf.getvalue(), width=250)

st.markdown(f"**App-Link:** [{app_url}]({app_url})")
st.info("Tipp: Du kannst den QR-Code auch herunterladen, indem du mit Rechtsklick darauf klickst und 'Bild speichern unter...' wählst.")