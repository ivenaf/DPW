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

st.write("Wähle einen Prozessschritt aus, um direkt dorthin zu navigieren. Die Prozessschritte folgen dem definierten Workflow.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Prozessschritte:")
    
    if st.button(" ✏️ 1. Erfassung", use_container_width=True):
        st.switch_page("pages/04_1_Erfassung.py")
        
    if st.button(" 👔 2. Leiter Akquisition", use_container_width=True):
        st.switch_page("pages/04_2_Akquisitionsleiter.py")
        
    if st.button(" 🏢 3. Niederlassungsleiter Genehmigung", use_container_width=True):
        st.switch_page("pages/04_3_Niederlassungsleiter.py")
        
    if st.button(" 🏛️ 4. Baurecht", use_container_width=True):
        st.switch_page("pages/04_4_Baurecht.py")
        
    if st.button(" 💼 5. CEO Genehmigung", use_container_width=True):
        st.switch_page("pages/04_5_CEO_Genehmigung.py")
        
    if st.button(" 🏗️ 6. Bauteam", use_container_width=True):
        st.switch_page("pages/04_6_Bauteam.py")
        
    if st.button(" ✅ 7. Fertigstellung", use_container_width=True):
        st.switch_page("pages/04_7_Fertigstellung.py")

with col2:
    st.subheader("Analyse & Tools:")
    
    if st.button("📊 Dashboard", use_container_width=True):
        st.switch_page("pages/02_📊_Dashboard.py")
        
    if st.button("🔍 Standort-Suche", use_container_width=True):
        st.switch_page("pages/Standort_Suche.py")
    
    if st.button("🎫 Open a Ticket", use_container_width=True):
        st.switch_page("pages/Ticket.py")
        
    st.write('*Einige Seiten sind noch in Arbeit oder nicht verfügbar.')