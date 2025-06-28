import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import uuid

st.set_page_config(
    page_title="Niederlassungsleiter Genehmigung",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 3. Niederlassungsleiter Genehmigung")
st.write("In diesem Schritt prüft und genehmigt der Niederlassungsleiter den Standort.")

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('werbetraeger.db', check_same_thread=False)
c = conn.cursor()

# Offene Genehmigungen laden
c.execute("""
    SELECT id, standort, stadt, vermarktungsform, datum
    FROM locations
    WHERE current_step = 'niederlassungsleiter'
""")
rows = c.fetchall()

if rows:
    st.subheader("Offene Genehmigungen")
    df = pd.DataFrame(rows, columns=["ID", "Standort", "Stadt", "Vermarktungsform", "Erfasst am"])
    st.dataframe(df, use_container_width=True)
    
    selected_id = st.selectbox("Standort auswählen:", df["ID"])
    if selected_id:
        st.write(f"Genehmigung für Standort: {selected_id}")
        with st.form("niederlassungsleiter_form"):
            genehmigt = st.radio("Genehmigung durch Niederlassungsleiter:", ["Genehmigt", "Abgelehnt"])
            kommentar = st.text_area("Kommentar (optional):")
            submitted = st.form_submit_button("Speichern")
            if submitted:
                now = datetime.now().isoformat()
                history_id = str(uuid.uuid4())
                if genehmigt == "Genehmigt":
                    # Nach Genehmigung weiter zu baurecht!
                    c.execute('''
                        UPDATE locations
                        SET current_step = ?, status = ?
                        WHERE id = ?
                    ''', ("baurecht", "active", selected_id))
                    c.execute('''
                        INSERT INTO workflow_history VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        history_id, selected_id, "niederlassungsleiter", "approved",
                        kommentar or "Genehmigt", st.session_state.get('username', 'Niederlassungsleiter'), now
                    ))
                    conn.commit()
                    st.success("Genehmigung gespeichert und an Baurecht weitergeleitet.")
                    st.rerun()
                else:
                    # Ablehnung
                    c.execute('''
                        UPDATE locations
                        SET current_step = ?, status = ?
                        WHERE id = ?
                    ''', ("abgelehnt", "abgelehnt", selected_id))
                    c.execute('''
                        INSERT INTO workflow_history VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        history_id, selected_id, "niederlassungsleiter", "rejected",
                        kommentar or "Abgelehnt", st.session_state.get('username', 'Niederlassungsleiter'), now
                    ))
                    conn.commit()
                    st.success("Ablehnung gespeichert.")
                    st.rerun()
else:
    st.info("Keine offenen Genehmigungen vorhanden.")