import streamlit as st
import os

# Seiteneinstellungen
st.set_page_config(
    page_title="Workflow Navigation",
    page_icon="🧭",
    layout="wide"
)




# Custom CSS für bessere Button-Gestaltung
st.markdown("""
<style>
    div.stButton > button {
        margin-bottom: 12px;
        border-radius: 6px;
    }
    div.stButton > button:hover {
        background-color: #f0f2f6;
        border-color: #FF6600;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧭 Workflow Navigation")

st.write("Wähle einen Prozessschritt aus, um direkt dorthin zu navigieren. Die Prozessschritte folgen dem definierten Workflow der Digitalen Säule.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Prozessschritte:")
    
    # WICHTIG: Die Dateinamen müssen GENAU übereinstimmen
    if st.button(" ✏️ 1. Erfassung", use_container_width=True):
        st.switch_page("pages/04_1_Erfassung.py")  # Passe dies an den tatsächlichen Dateinamen an
        
    if st.button(" 👔 2. Leiter Akquisition", use_container_width=True):
        st.switch_page("pages/04_2_Akquisitionsleiter.py")  # Passe dies an
        
    if st.button(" 🏛️ 3. Baurecht", use_container_width=True):
        st.switch_page("pages/04_3_Baurecht.py")  # Passe dies an
        
    if st.button(" 💼 4. CEO Genehmigung", use_container_width=True):
        st.switch_page("pages/04_4_CEO_Genehmigung.py")  # Passe dies an
        
    if st.button(" 🏗️ 5. Bauteam", use_container_width=True):
        st.switch_page("pages/04_5_Bauteam.py")  # Passe dies an
        
    if st.button(" ✅ 6. Fertigstellung", use_container_width=True):
        st.switch_page("pages/04_6_Fertigstellung.py")  # Passe dies an

with col2:
    st.subheader("Analyse & Tools:")
    
    if st.button("📊 Dashboard", use_container_width=True):
        st.switch_page("pages/02_📊_Dashboard.py")  # Passe dies an
        
    if st.button("🔍 Standort-Suche", use_container_width=True):
        st.switch_page("pages/Standort_Suche.py")  # Passe dies an
        
        
 