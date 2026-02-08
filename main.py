import streamlit as st
import json
import numpy as np
import cv2
import sys
import os

# Adds the 'src' directory to the Python search path
sys.path.append(os.path.join(os.getcwd(), 'src'))
from src.brain.orchestrator import Orchestrator

# 1. PROFESSIONAL UI CONFIGURATION
st.set_page_config(page_title="PharmaAgent Enterprise", layout="wide", page_icon="💊")

# Professional Branding: Hide Streamlit default elements
st.markdown("""
    <style>
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    #stDecoration {display:none;}
    </style>
    """, unsafe_allow_html=True)

# 2. AUTHENTICATION GATE (OIDC)
# In 2026, st.user is the standard for secure access
if not st.user.is_logged_in:
    st.title("🏥 PharmaAgent Secure Access")
    st.info("Authorized Personnel Only. Please log in to proceed.")
    st.button("Log in with Google", on_click=st.login)
    st.stop()

# 3. DYNAMIC DATA LOADING
@st.cache_data
def load_med_data():
    with open('data/inventory.json', 'r') as f:
        return json.load(f)

med_data = load_med_data()

# Sidebar: Enterprise Logout & User Info
with st.sidebar:
    st.image("https://via.placeholder.com/150?text=PharmaAgent+Logo") # Add your brand logo here
    st.write(f"Logged in as: **{st.user.name}**")
    st.write(f"ID: `{st.user.sub[:8]}...`")
    if st.button("Logout", on_click=st.logout):
        st.stop()
    st.divider()
    
    selected_name = st.selectbox(
        "Select Target Medication", 
        options=[details['name'] for details in med_data.values()]
    )

target_pill_id = next(k for k, v in med_data.items() if v['name'] == selected_name)

# 4. PROFESSIONAL NAVIGATION SYSTEM (₹2Cr Valuation Feature)
tab_verify, tab_guide, tab_audit = st.tabs(["📷 Live Verification", "📘 App Guide", "🛠 System Audit"])

with tab_verify:
    st.header(f"Verifying: {selected_name}")
    brain = Orchestrator()
    img_file = st.camera_input("Scan pill for verification")

    if img_file:
        file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
        frame = cv2.imdecode(file_bytes, 1)
        cv2.imwrite("temp_scan.jpg", frame)
        
        with st.spinner("Agents performing cross-reference safety checks..."):
            result = brain.process_order("temp_scan.jpg", target_pill_id)
            
        # DEFENSIVE ERROR HANDLING (Prevents the 'KeyError: msg')
        # Use .get() to provide fallback text if the agent fails to return a message
        msg = result.get('msg', 'Agent failed to provide detailed verification message.')
        status = result.get('status', 'ERROR')

        if status == "SAFE":
            st.success(f"✅ {msg}")
        else:
            st.error(f"🚨 {msg}")

        # Expanded Technical Details for Buyer Vetting
        with st.expander("🔍 View Technical Verification Trail (JSON)"):
            st.json(result)

with tab_guide:
    st.header("Hospital Deployment Guide")
    st.markdown("""
    ### Quick Start
    1. **Login:** Use your hospital OIDC credentials.
    2. **Target:** Select the medication from the sidebar.
    3. **Scan:** Use a high-resolution camera for the best AI accuracy.
    """)

with tab_audit:
    st.header("Technical Architecture & Compliance")
    st.write("This application uses a Multi-Agentic OODA loop for verification.")
    st.info("All transactions are logged to the persistent `data/logs/` directory for HIPAA compliance.")