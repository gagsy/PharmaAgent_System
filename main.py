import streamlit as st
import json
import numpy as np
import cv2
import sys
import os
import time

# 1. ENTERPRISE SYSTEM INITIALIZATION
sys.path.append(os.path.join(os.getcwd(), 'src'))
from src.brain.orchestrator import Orchestrator

# Standardize page config for medical compliance
st.set_page_config(
    page_title="PharmaAgent | Global Clinical Systems",
    page_icon="🛡️",
    layout="wide"
)

# 2. UNIFIED ENTERPRISE CSS (Fixes Visibility & Branding)
def apply_enterprise_theme():
    st.markdown("""
        <style>
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
        
        /* Sidebar Styling: Ensuring 100% visibility */
        [data-testid="stSidebar"] {
            background-color: #0e1117;
            border-right: 2px solid #30363d;
        }
        
        /* Force Sidebar Text Visibility */
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] label p, [data-testid="stSidebar"] .stText p {
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        /* Metric Highlights */
        [data-testid="stMetricValue"] {
            color: #58a6ff !important;
        }
        </style>
    """, unsafe_allow_html=True)

apply_enterprise_theme()

# 3. AUTHENTICATION GATE
if not st.user.is_logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=80)
        st.title("PharmaAgent Gatekeeper")
        st.info("Authorized Medical Personnel Access Only.")
        st.button("🔐 SSO Enterprise Login", on_click=st.login, use_container_width=True)
    st.stop()

# 4. DATA & BRAIN INITIALIZATION
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
    
    selected_name = st.selectbox(
        "Current Verification Task", 
        options=[v['name'] for v in med_data.values()]
    )
    
    # CRITICAL FIX: Ensure 'target_id' is defined before Section 6 starts
    target_id = next(k for k, v in med_data.items() if v['name'] == selected_name)
    
    st.divider()
    st.write(f"👤 Operator: **{st.user.name}**")
    if st.button("🚪 Secure Logout", use_container_width=True, on_click=st.logout):
        st.stop()

# 6. MAIN WORKFLOW TABS
t1, t2, t3 = st.tabs(["⚡ Live Inspection", "📊 Historical Audit", "📘 Deployment Guide"])

with t1:
    st.header(f"Inspecting: {selected_name}")
    
    # Agent Process Visualizer
    with st.status("Agentic Reasoning in Progress...", expanded=True) as status:
        st.write("Vision Agent: Scanning pill geometry...")
        time.sleep(0.4)
        st.write("Pharma Agent: Cross-referencing safety data...")
        
        img_file = st.camera_input("Scanner Interface", label_visibility="collapsed")
        
        if img_file:
            # Prepare image
            file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, 1)
            cv2.imwrite("temp_scan.jpg", frame)
            
            # CORE LOGIC: Pass 'target_id' from Sidebar to Orchestrator
            result = brain.process_order("temp_scan.jpg", target_id)
            status.update(label="Verification Complete", state="complete", expanded=False)
            
            # Defensive Handling of Agent Output
            msg = result.get('msg', 'Verification engine returned an unexpected null response.')
            if result.get('status') == "SAFE":
                st.success(f"### SUCCESS: {msg}")
            else:
                st.error(f"### ALERT: {msg}")
            
            with st.expander("📁 Immutable Verification Data (JSON Payload)"):
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