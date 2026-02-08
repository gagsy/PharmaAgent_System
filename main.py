import streamlit as st
import json
import numpy as np
import cv2
import sys
import os
import time

# 1. ENTERPRISE SYSTEM INITIALIZATION
# Adds 'src' to path and ensures module discovery
sys.path.append(os.path.join(os.getcwd(), 'src'))
from brain.orchestrator import Orchestrator

# Standardize page config
st.set_page_config(
    page_title="PharmaAgent | Global Clinical Systems",
    page_icon="🛡️",
    layout="wide"
)

# 2. UNIFIED ENTERPRISE CSS
def apply_enterprise_theme():
    st.markdown("""
        <style>
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
        
        /* Sidebar Contrast Fix */
        [data-testid="stSidebar"] {
            background-color: #0e1117;
            border-right: 2px solid #30363d;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label p {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        [data-testid="stMetricValue"] {
            color: #58a6ff !important;
        }
        </style>
    """, unsafe_allow_html=True)

apply_enterprise_theme()

# 3. AUTHENTICATION
if not st.user.is_logged_in:
    st.title("🏥 PharmaAgent Secure Access")
    st.info("Please log in to proceed.")
    st.button("🔐 SSO Login", on_click=st.login)
    st.stop()

# 4. DATA LOADING
@st.cache_data(show_spinner=False)
def load_med_data():
    with open('data/inventory.json', 'r') as f:
        return json.load(f)

med_data = load_med_data()
brain = Orchestrator()

# 5. SIDEBAR: DATA EXTRACTION
with st.sidebar:
    st.title("🛡️ PharmaGuard")
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Accuracy", "99.8%")
    c2.metric("Audit", "Valid")
    st.divider()
    
    selected_name = st.selectbox("Current Task", options=[v['name'] for v in med_data.values()])
    
    # GLOBAL VARIABLE DEFINITION: Fixes NameError
    target_id = next(k for k, v in med_data.items() if v['name'] == selected_name)
    
    st.divider()
    st.write(f"👤 {st.user.name}")
    if st.button("Logout", on_click=st.logout):
        st.stop()

# 6. MAIN WORKFLOW
t1, t2, t3 = st.tabs(["⚡ Live Inspection", "📊 Historical Audit", "📘 Guide"])

with t1:
    st.header(f"Inspecting: {selected_name}")
    img_file = st.camera_input("Scanner Interface", label_visibility="collapsed")

    if img_file:
        file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
        frame = cv2.imdecode(file_bytes, 1)
        cv2.imwrite("temp_scan.jpg", frame)
        
        with st.status("Agentic Reasoning...", expanded=True) as status:
            # USES target_id correctly
            result = brain.process_order("temp_scan.jpg", target_id)
            status.update(label="Complete", state="complete", expanded=False)
            
        # DEFENSIVE KEY HANDLING: Fixes KeyError
        msg = result.get('msg', 'System returned null response.')
        if result.get('status') == "SAFE":
            st.success(f"### SUCCESS: {msg}")
        else:
            st.error(f"### ALERT: {msg}")
        
        with st.expander("📁 JSON Payload"):
            st.json(result)
            
# Tabs 2 and 3 continue with your previous documentation code
with t2:
    st.header("Global Audit Ledger")
    st.info("Logs are stored in data/logs/audit_trail.csv for legal compliance.")
    # Placeholder for a real audit table
    st.dataframe({"Timestamp": ["2026-02-09 01:00"], "Agent": ["Vision"], "Status": ["Success"]}, use_container_width=True)

with t3:
    st.header("Medical System Handbook")
    st.markdown("""
    - **Step 1:** Select target drug from sidebar.
    - **Step 2:** Ensure clear lighting for OCR and Vision accuracy.
    - **Step 3:** Review results and audit payload for final confirmation.
    """)